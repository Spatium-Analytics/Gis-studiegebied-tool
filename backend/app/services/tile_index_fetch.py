"""Client for PDOK collections that are kaartblad tile indexes rather than item-queryable features.

Some PDOK OGC API Features collections (collectionType "3d-container", e.g. the 3D
Basisvoorziening's hoogtestatistieken_gebouwen) don't expose individual features via
bbox/items: each "item" is a tile polygon carrying a download_link to a GeoPackage for
that tile. To fetch features for a study area we: query the tile index by bbox, download
(and cache) the GeoPackage for every tile that intersects, then do a bbox-filtered read
of each and concatenate.
"""

import asyncio
import hashlib
import zipfile
from pathlib import Path

import geopandas as gpd
import httpx
import pandas as pd

from app.config import settings
from app.services.pdok_client import fetch_all_features

_download_locks: dict[str, asyncio.Lock] = {}


def _lock_for(key: str) -> asyncio.Lock:
    if key not in _download_locks:
        _download_locks[key] = asyncio.Lock()
    return _download_locks[key]


async def _ensure_cached_tile(download_link: str) -> Path:
    """Download and extract a single tile's zip (containing one GeoPackage) if not already cached."""
    cache_key = hashlib.sha1(download_link.encode()).hexdigest()
    cache_dir = settings.tile_cache_dir / cache_key

    existing = list(cache_dir.glob("*.gpkg")) if cache_dir.exists() else []
    if existing:
        return existing[0]

    async with _lock_for(cache_key):
        existing = list(cache_dir.glob("*.gpkg")) if cache_dir.exists() else []
        if existing:
            return existing[0]

        cache_dir.mkdir(parents=True, exist_ok=True)
        zip_path = cache_dir / "tile.zip"
        async with httpx.AsyncClient(timeout=settings.cvgg_request_timeout_s, follow_redirects=True) as client:
            resp = await client.get(download_link)
            resp.raise_for_status()
            zip_path.write_bytes(resp.content)

        with zipfile.ZipFile(zip_path) as zf:
            gpkg_names = [n for n in zf.namelist() if n.endswith(".gpkg")]
            if not gpkg_names:
                raise RuntimeError(f"Tegel-bestand {download_link} bevat geen .gpkg")
            zf.extract(gpkg_names[0], cache_dir)
        zip_path.unlink(missing_ok=True)

        return cache_dir / gpkg_names[0]


async def fetch_tile_index_layer(base_url: str, tile_collection: str, bbox: tuple[float, float, float, float]) -> gpd.GeoDataFrame:
    """Fetch features for bbox from a tile-indexed PDOK collection."""
    tile_features = await fetch_all_features(base_url, tile_collection, bbox)
    download_links = sorted(
        {f["properties"]["download_link"] for f in tile_features if f.get("properties", {}).get("download_link")}
    )
    if not download_links:
        return gpd.GeoDataFrame(geometry=[], crs="EPSG:28992")

    gpkg_paths = [await _ensure_cached_tile(link) for link in download_links]
    gdfs = [await asyncio.to_thread(gpd.read_file, p, bbox=bbox) for p in gpkg_paths]
    gdfs = [g for g in gdfs if not g.empty]
    if not gdfs:
        return gpd.GeoDataFrame(geometry=[], crs="EPSG:28992")

    # Tile GeoPackages mix the compound EPSG:7415 (RD New + NAP height) CRS with plain
    # EPSG:28992 depending on tile vintage; the horizontal component is identical in both,
    # so normalize to 28992 (a relabel, not a reprojection) before concatenating.
    gdfs = [g.set_crs("EPSG:28992", allow_override=True) for g in gdfs]
    return gpd.GeoDataFrame(pd.concat(gdfs, ignore_index=True), crs="EPSG:28992")
