from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, field_validator


class GeoJSONPolygon(BaseModel):
    type: Literal["Polygon"]
    coordinates: list[list[list[float]]]

    @field_validator("coordinates")
    @classmethod
    def rings_must_be_closed(cls, v: list[list[list[float]]]) -> list[list[list[float]]]:
        for ring in v:
            if len(ring) < 3:
                raise ValueError("polygon ring must have at least 3 coordinates")
            if ring[0] != ring[-1]:
                raise ValueError("polygon ring must be closed (first == last coordinate)")
        return v


class OutputFormat(str, Enum):
    gpkg = "gpkg"
    shp = "shp"


class DownloadRequest(BaseModel):
    polygon: GeoJSONPolygon
    crs: str = "EPSG:28992"
    layers: list[str]
    output_format: OutputFormat = OutputFormat.gpkg


class LayerStatus(str, Enum):
    pending = "pending"
    fetching = "fetching"
    clipping = "clipping"
    done = "done"
    failed = "failed"


class JobState(str, Enum):
    queued = "queued"
    running = "running"
    done = "done"
    error = "error"


class JobStatusResponse(BaseModel):
    job_id: str
    status: JobState
    progress: dict[str, LayerStatus]
    error_detail: str | None = None


class LayerManifestEntry(BaseModel):
    key: str
    label: str
    description: str
    output_kind: Literal["vector"]
    enabled: bool
    notes: str | None = None
    # Included so the frontend can preview features directly from PDOK without going through the backend
    service_type: str
    base_url: str
    collection_or_coverage: str


class JobCreatedResponse(BaseModel):
    job_id: str
    status: JobState
