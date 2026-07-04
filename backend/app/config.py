from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    jobs_dir: Path = Path(__file__).resolve().parent.parent.parent / "data" / "tmp_jobs"
    cvgg_cache_dir: Path = Path(__file__).resolve().parent.parent.parent / "data" / "cvgg_cache"
    tile_cache_dir: Path = Path(__file__).resolve().parent.parent.parent / "data" / "tile_cache"
    output_crs: str = "EPSG:28992"
    max_polygon_area_m2: float = 25_000_000  # 25 km^2 cap to keep PDOK requests/job times bounded
    pdok_page_limit: int = 1000
    pdok_max_pages: int = 50  # hard cap per layer to avoid unbounded pagination loops
    pdok_request_timeout_s: float = 30.0
    pdok_max_retries: int = 3
    pdok_retry_backoff_s: float = 2.0
    cvgg_request_timeout_s: float = 180.0  # national CVGG files run tens-to-hundreds of MB
    cvgg_cache_ttl_s: float = 24 * 3600  # CVGG national files are republished daily
    job_timeout_s: float = 600.0
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]


settings = Settings()
settings.jobs_dir.mkdir(parents=True, exist_ok=True)
settings.cvgg_cache_dir.mkdir(parents=True, exist_ok=True)
settings.tile_cache_dir.mkdir(parents=True, exist_ok=True)
