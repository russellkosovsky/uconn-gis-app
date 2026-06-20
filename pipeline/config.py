"""Single source of truth for every tunable in the pipeline.

Keep ALL spatial / temporal constants here so the pipeline, the API and the
tests agree on one definition. If you change the cutoff year or the bbox, this
is the only place you should have to edit.
"""
from __future__ import annotations

from pathlib import Path

# --- Repo layout -----------------------------------------------------------
# Resolve paths relative to this file so the pipeline works regardless of the
# current working directory (important: the Makefile and pytest invoke it from
# different places).
ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
RAW = DATA / "raw"
PROCESSED = DATA / "processed"
SEED = DATA / "seed"

SEED_CSV = SEED / "buildings_construction_years.csv"
RAW_OSM = RAW / "osm_buildings.geojson"
OUT_GEOJSON = PROCESSED / "buildings.geojson"

# --- Study area ------------------------------------------------------------
# UConn Storrs campus bounding box, given as (West, South, East, North) in
# WGS84 / EPSG:4326 decimal degrees. This ordering is deliberately the same as
# osmnx 2.x's ``features_from_bbox(bbox=(left, bottom, right, top))`` so we can
# pass BBOX straight through without re-ordering. See DECISIONS.md.
BBOX_W, BBOX_S, BBOX_E, BBOX_N = -72.27, 41.79, -72.24, 41.82
BBOX = (BBOX_W, BBOX_S, BBOX_E, BBOX_N)  # (left, bottom, right, top)

# Geometric center of the bbox (kept for reference).
BBOX_CENTER_LON = (BBOX_W + BBOX_E) / 2
BBOX_CENTER_LAT = (BBOX_S + BBOX_N) / 2

# Initial MAP view sent to the front end. Deliberately NOT the bbox center: the
# dated anchor buildings cluster in the academic/historic core (north-east of
# bbox-center), so opening there makes the color-coding immediately visible.
# "Fetch extent" (bbox) and "initial view" (core) are intentionally decoupled.
CENTER_LON = -72.2515
CENTER_LAT = 41.8086
DEFAULT_ZOOM = 15.6

# --- Temporal filter -------------------------------------------------------
# The architectural spine: a building is "included" in the historical map if it
# existed at or before the cutoff. A building with construction_year == CUTOFF
# is INCLUDED (<=, not <). Change this to re-target a different era.
CUTOFF_YEAR = 1984

# temporal_status vocabulary emitted into the GeoJSON. Kept as constants so the
# API, tests and front end never disagree on a string literal.
STATUS_PRE = "pre_cutoff"     # construction_year <= CUTOFF_YEAR  -> on the map
STATUS_POST = "post_cutoff"   # construction_year >  CUTOFF_YEAR  -> not yet built
STATUS_UNKNOWN = "unknown"    # no known year -> the work-remaining bucket

# Coordinate reference system we emit. OSM is natively EPSG:4326 and MapLibre
# expects 4326 GeoJSON, so we never reproject in this foundation. See DECISIONS.
OUTPUT_CRS = "EPSG:4326"

# --- OSM fetch -------------------------------------------------------------
# Tags that identify a building footprint in OpenStreetMap.
OSM_TAGS = {"building": True}
