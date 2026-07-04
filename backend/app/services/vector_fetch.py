import geopandas as gpd
from shapely.geometry import shape
from shapely.geometry.base import BaseGeometry

from app.layers_registry import LayerDefinition
from app.services.pdok_client import fetch_all_features
from app.services.tile_index_fetch import fetch_tile_index_layer


async def fetch_layer(layer: LayerDefinition, polygon_28992: BaseGeometry) -> gpd.GeoDataFrame:
    """Fetch all features intersecting the polygon's bbox for a vector layer, in EPSG:28992."""
    bbox = polygon_28992.bounds

    if layer.service_type == "tile_index":
        return await fetch_tile_index_layer(layer.base_url, layer.collection_or_coverage, bbox)

    raw_features = await fetch_all_features(layer.base_url, layer.collection_or_coverage, bbox)

    if not raw_features:
        return gpd.GeoDataFrame(geometry=[], crs="EPSG:28992")

    # Filter out null-geometry features (some PDOK collections have attribute-only rows)
    geo_features = [f for f in raw_features if f.get("geometry")]
    if not geo_features:
        return gpd.GeoDataFrame(geometry=[], crs="EPSG:28992")

    geometries = [shape(f["geometry"]) for f in geo_features]
    properties = [f.get("properties", {}) for f in geo_features]
    gdf = gpd.GeoDataFrame(properties, geometry=geometries, crs="EPSG:28992")
    return gdf
