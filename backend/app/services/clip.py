import geopandas as gpd
from shapely.geometry.base import BaseGeometry


def clip_vector(gdf: gpd.GeoDataFrame, polygon: BaseGeometry) -> gpd.GeoDataFrame:
    """Exact clip of vector features to the drawn polygon. Both must already be in EPSG:28992."""
    if gdf.empty:
        return gdf
    polygon_gdf = gpd.GeoDataFrame(geometry=[polygon], crs=gdf.crs)
    return gpd.clip(gdf, polygon_gdf)
