"""In-memory job state store for v1.

Interface is intentionally minimal so it can be swapped for a Redis-backed
store later without touching job_runner.py: get/set/delete by job_id.
"""

from dataclasses import dataclass, field
from pathlib import Path

from app.models import JobState, LayerStatus


@dataclass
class JobRecord:
    job_id: str
    status: JobState = JobState.queued
    progress: dict[str, LayerStatus] = field(default_factory=dict)
    error_detail: str | None = None
    result_zip_path: Path | None = None


_JOBS: dict[str, JobRecord] = {}


def create(job_id: str, layer_keys: list[str]) -> JobRecord:
    record = JobRecord(job_id=job_id, progress={k: LayerStatus.pending for k in layer_keys})
    _JOBS[job_id] = record
    return record


def get(job_id: str) -> JobRecord | None:
    return _JOBS.get(job_id)
