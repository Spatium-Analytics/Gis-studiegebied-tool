import uuid

from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse
from shapely.geometry import shape

from app.config import settings
from app.jobs.job_runner import run_job
from app.jobs.store import create, get
from app.layers_registry import LAYERS_BY_KEY
from app.models import DownloadRequest, JobCreatedResponse, JobState, JobStatusResponse
from app.services.reproject import to_28992

router = APIRouter()


@router.post("/jobs", response_model=JobCreatedResponse, status_code=202)
def create_job(req: DownloadRequest, background_tasks: BackgroundTasks) -> JobCreatedResponse:
    unknown = [k for k in req.layers if k not in LAYERS_BY_KEY]
    if unknown:
        raise HTTPException(400, f"Unknown layer key(s): {unknown}")
    disabled = [k for k in req.layers if not LAYERS_BY_KEY[k].enabled]
    if disabled:
        raise HTTPException(400, f"Layer(s) not yet available: {disabled}")
    if not req.layers:
        raise HTTPException(400, "At least one layer must be selected")

    polygon_geojson = req.polygon.model_dump()
    polygon_28992 = to_28992(shape(polygon_geojson), req.crs)
    if polygon_28992.area > settings.max_polygon_area_m2:
        raise HTTPException(
            400,
            f"Studiegebied is te groot ({polygon_28992.area / 1_000_000:.1f} km²). "
            f"Maximum is {settings.max_polygon_area_m2 / 1_000_000:.0f} km². Teken een kleiner gebied.",
        )

    job_id = str(uuid.uuid4())
    create(job_id, req.layers)
    background_tasks.add_task(run_job, job_id, polygon_geojson, req.crs, req.layers, req.output_format)

    return JobCreatedResponse(job_id=job_id, status=JobState.queued)


@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
def job_status(job_id: str) -> JobStatusResponse:
    record = get(job_id)
    if record is None:
        raise HTTPException(404, "Job not found")
    return JobStatusResponse(
        job_id=record.job_id,
        status=record.status,
        progress=record.progress,
        error_detail=record.error_detail,
    )


@router.get("/jobs/{job_id}/download")
def job_download(job_id: str) -> FileResponse:
    record = get(job_id)
    if record is None:
        raise HTTPException(404, "Job not found")
    if record.status != JobState.done or record.result_zip_path is None:
        raise HTTPException(409, f"Job is not finished yet (status: {record.status})")
    return FileResponse(record.result_zip_path, filename="studiegebied.zip", media_type="application/zip")
