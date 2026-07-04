from pathlib import Path

from shapely.geometry import Polygon, shape

from app.config import settings
from app.jobs.store import get
from app.layers_registry import LAYERS_BY_KEY
from app.models import JobState, LayerStatus, OutputFormat
from app.services.bundler import build_zip, cleanup, write_vector_layer
from app.services.clip import clip_vector
from app.services.reproject import to_28992
from app.services.vector_fetch import fetch_layer


async def run_job(job_id: str, polygon_geojson: dict, polygon_crs: str, layer_keys: list[str], output_format: OutputFormat) -> None:
    record = get(job_id)
    if record is None:
        return

    record.status = JobState.running
    work_dir = settings.jobs_dir / job_id
    work_dir.mkdir(parents=True, exist_ok=True)

    output_files: list[Path] = []
    failures: dict[str, str] = {}

    try:
        polygon: Polygon = to_28992(shape(polygon_geojson), polygon_crs)

        for key in layer_keys:
            layer = LAYERS_BY_KEY[key]
            record.progress[key] = LayerStatus.fetching

            # Each layer is independent: one failing (e.g. a transient PDOK timeout, or an
            # upstream CVGG/tile-cache hiccup) must not discard layers that already succeeded
            # or block layers still to be tried.
            try:
                gdf = await fetch_layer(layer, polygon)
                record.progress[key] = LayerStatus.clipping
                clipped = clip_vector(gdf, polygon)
                if not clipped.empty:
                    output_files.extend(write_vector_layer(clipped, key, work_dir, output_format))

                record.progress[key] = LayerStatus.done

            except Exception as exc:  # noqa: BLE001 - per-layer, surfaced via job status
                record.progress[key] = LayerStatus.failed
                failures[key] = str(exc)

        if output_files:
            zip_path = settings.jobs_dir / f"{job_id}.zip"
            build_zip(work_dir, output_files, zip_path)
            record.result_zip_path = zip_path
            record.status = JobState.done
            if failures:
                record.error_detail = "Niet alle lagen gelukt: " + "; ".join(f"{k}: {v}" for k, v in failures.items())
        else:
            record.status = JobState.error
            record.error_detail = "Alle lagen mislukt: " + "; ".join(f"{k}: {v}" for k, v in failures.items())

    except Exception as exc:  # noqa: BLE001 - failure before/outside the per-layer loop (e.g. bad polygon)
        record.status = JobState.error
        record.error_detail = str(exc)
        for key, status in list(record.progress.items()):
            if status not in (LayerStatus.done,):
                record.progress[key] = LayerStatus.failed

    finally:
        cleanup(work_dir)
