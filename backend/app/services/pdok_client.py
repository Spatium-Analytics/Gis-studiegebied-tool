"""Generic OGC API Features client with bbox filtering and link-based pagination."""

import asyncio

import httpx

from app.config import settings

# OGC API Features requires CRS identified by URI, not "EPSG:xxxx" shorthand.
EPSG_28992_URI = "http://www.opengis.net/def/crs/EPSG/0/28992"


async def _get_with_retry(client: httpx.AsyncClient, url: str, params: dict | None) -> httpx.Response:
    """GET with retries for PDOK's transient 5xx/timeout errors (e.g. dense-area query timeouts).

    PDOK occasionally returns a 500 "querying the features took too long" for busy
    collections (notably bag/adres) even on bboxes well within normal size limits; a
    short retry with backoff resolves most of these without bothering the user.
    """
    last_exc: Exception | None = None
    for attempt in range(settings.pdok_max_retries):
        try:
            resp = await client.get(url, params=params)
            if resp.status_code < 500:
                resp.raise_for_status()
                return resp
            last_exc = httpx.HTTPStatusError(
                f"{resp.status_code} from {url}", request=resp.request, response=resp
            )
        except httpx.TransportError as exc:
            last_exc = exc

        if attempt < settings.pdok_max_retries - 1:
            await asyncio.sleep(settings.pdok_retry_backoff_s * (attempt + 1))

    assert last_exc is not None
    raise last_exc


async def fetch_all_features(base_url: str, collection: str, bbox: tuple[float, float, float, float], bbox_crs: str = EPSG_28992_URI) -> list[dict]:
    """Page through an OGC API Features collection, filtering by bbox, and return raw GeoJSON features.

    Both the bbox filter and the returned geometries are requested in EPSG:28992 directly
    (PDOK's BAG/BRK/3D-basisvoorziening collections natively support this CRS), so no
    reprojection of the fetched features is needed afterwards.
    """
    features: list[dict] = []
    url = f"{base_url.rstrip('/')}/collections/{collection}/items"
    params = {
        "f": "json",
        "limit": settings.pdok_page_limit,
        "bbox": ",".join(str(c) for c in bbox),
        "bbox-crs": bbox_crs,
        "crs": bbox_crs,
    }

    async with httpx.AsyncClient(timeout=settings.pdok_request_timeout_s) as client:
        for _ in range(settings.pdok_max_pages):
            resp = await _get_with_retry(client, url, params)
            data = resp.json()
            features.extend(data.get("features", []))

            next_link = next((link["href"] for link in data.get("links", []) if link.get("rel") == "next"), None)
            if not next_link:
                break
            url = next_link
            params = None  # next link already encodes all query params

    return features
