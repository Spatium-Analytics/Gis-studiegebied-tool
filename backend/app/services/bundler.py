import shutil
import zipfile
from pathlib import Path

import geopandas as gpd

from app.models import OutputFormat


def write_vector_layer(gdf: gpd.GeoDataFrame, layer_key: str, work_dir: Path, output_format: OutputFormat) -> list[Path]:
    """Write one clipped vector layer to disk, returning the file(s) produced."""
    # "fid" collides with the feature-id column GDAL's GPKG/Shapefile drivers manage
    # themselves; some sources (e.g. PDOK tile GeoPackages) carry it as a regular attribute.
    if "fid" in gdf.columns:
        gdf = gdf.drop(columns=["fid"])

    if output_format == OutputFormat.gpkg:
        gpkg_path = work_dir / "studiegebied.gpkg"
        gdf.to_file(gpkg_path, layer=layer_key, driver="GPKG")
        return [gpkg_path]

    shp_dir = work_dir / layer_key
    shp_dir.mkdir(parents=True, exist_ok=True)
    shp_path = shp_dir / f"{layer_key}.shp"
    gdf.to_file(shp_path, driver="ESRI Shapefile")
    return list(shp_dir.glob(f"{layer_key}.*"))


def build_zip(work_dir: Path, output_files: list[Path], zip_path: Path) -> Path:
    """Bundle all produced files (GeoPackage and/or Shapefile sets and/or rasters) into one zip."""
    seen: set[Path] = set()
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in output_files:
            if f in seen or not f.exists():
                continue
            seen.add(f)
            zf.write(f, arcname=f.relative_to(work_dir) if f.is_relative_to(work_dir) else f.name)
    return zip_path


def cleanup(work_dir: Path) -> None:
    shutil.rmtree(work_dir, ignore_errors=True)
