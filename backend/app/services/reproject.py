from pyproj import Transformer
from shapely.geometry.base import BaseGeometry
from shapely.ops import transform

_TO_28992_CACHE: dict[str, Transformer] = {}


def to_28992(geom: BaseGeometry, source_crs: str) -> BaseGeometry:
    """Reproject a shapely geometry from source_crs to EPSG:28992. No-op if already 28992."""
    if source_crs.upper() in ("EPSG:28992", "28992"):
        return geom

    transformer = _TO_28992_CACHE.get(source_crs)
    if transformer is None:
        transformer = Transformer.from_crs(source_crs, "EPSG:28992", always_xy=True)
        _TO_28992_CACHE[source_crs] = transformer

    return transform(transformer.transform, geom)
