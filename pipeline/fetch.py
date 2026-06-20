"""Fetch modern building footprints from OpenStreetMap, with on-disk caching.

Data source: OpenStreetMap via osmnx. OSM data is © OpenStreetMap contributors,
licensed ODbL — attribute it in any published output (the front end does).

Caching: the raw OSM pull is written to ``data/raw/osm_buildings.geojson`` and
reused on subsequent runs so we don't hammer the Overpass API while iterating.
Delete that file (or pass ``force=True``) to refresh.
"""
from __future__ import annotations

import inspect

import geopandas as gpd

from .config import BBOX, OSM_TAGS, RAW_OSM


def _features_from_bbox(bbox, tags):
    """Call osmnx ``features_from_bbox`` in a version-tolerant way.

    osmnx 2.x:  features_from_bbox(bbox=(left, bottom, right, top), tags)
    osmnx 1.x:  features_from_bbox(north, south, east, west, tags)

    We introspect the installed signature (verified at build time to be 2.1.0,
    the 2.x form) and adapt, so a future bump to 1.x-style args won't silently
    transpose our coordinates. ``bbox`` is (W, S, E, N) == (left, bottom, right,
    top).
    """
    import osmnx as ox

    params = inspect.signature(ox.features_from_bbox).parameters
    if "bbox" in params:  # osmnx 2.x
        return ox.features_from_bbox(bbox=bbox, tags=tags)
    # osmnx 1.x fallback: positional north, south, east, west
    west, south, east, north = bbox
    return ox.features_from_bbox(north, south, east, west, tags)


def fetch_footprints(force: bool = False) -> gpd.GeoDataFrame:
    """Return building footprints for the Storrs bbox as a GeoDataFrame.

    Uses the cached GeoJSON if present unless ``force`` is True.
    """
    if RAW_OSM.exists() and not force:
        return gpd.read_file(RAW_OSM)

    gdf = _features_from_bbox(BBOX, OSM_TAGS)

    # Keep only polygonal footprints (OSM also returns building=* nodes/lines).
    gdf = gdf[gdf.geometry.type.isin(["Polygon", "MultiPolygon"])].copy()

    # osmnx returns a MultiIndex (element_type, osmid) and many sparse columns;
    # flatten to a stable id + name and drop list-valued columns that GeoJSON
    # can't serialize.
    gdf = gdf.reset_index()
    if "osmid" in gdf.columns:
        gdf["osm_id"] = gdf["osmid"].astype(str)
    keep = [c for c in ("osm_id", "name", "geometry") if c in gdf.columns]
    gdf = gdf[keep].copy()
    if "name" not in gdf.columns:
        gdf["name"] = None

    gdf = gdf.set_crs("EPSG:4326", allow_override=True)
    RAW_OSM.parent.mkdir(parents=True, exist_ok=True)
    gdf.to_file(RAW_OSM, driver="GeoJSON")
    return gdf


if __name__ == "__main__":  # manual smoke test: python -m pipeline.fetch
    fp = fetch_footprints()
    print(f"fetched {len(fp)} footprints -> {RAW_OSM}")
