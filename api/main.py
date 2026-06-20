"""FastAPI app serving the processed footprints GeoJSON and a tile-route stub.

Run with:  uvicorn api.main:app --reload --port 8000   (or `make api`)

Endpoints:
    GET /                       health + metadata
    GET /api/buildings          the processed FeatureCollection (temporal_status)
    GET /api/config             bbox / center / cutoff for the front end
    GET /tiles/{z}/{x}/{y}.png  STUB historical-raster tile route (404 + TODO)
"""
from __future__ import annotations

import json

from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from pipeline.config import (
    BBOX,
    CENTER_LAT,
    CENTER_LON,
    CUTOFF_YEAR,
    DEFAULT_ZOOM,
    OUT_GEOJSON,
    STATUS_POST,
    STATUS_PRE,
    STATUS_UNKNOWN,
)

app = FastAPI(title="UConn Storrs Historical Map API", version="0.1.0")

# The Vite dev server runs on a different origin (5173); allow it to fetch us.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # foundation only; tighten before any deployment
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/")
def root() -> dict:
    """Health check + whether the data has been built yet."""
    return {
        "service": "uconn-storrs-historical-map",
        "status": "ok",
        "data_built": OUT_GEOJSON.exists(),
        "cutoff_year": CUTOFF_YEAR,
        "hint": "run `make data` if data_built is false",
    }


@app.get("/api/config")
def config() -> dict:
    """Spatial/temporal config so the front end has a single source of truth."""
    return {
        "bbox": {"w": BBOX[0], "s": BBOX[1], "e": BBOX[2], "n": BBOX[3]},
        "center": {"lon": CENTER_LON, "lat": CENTER_LAT},
        "zoom": DEFAULT_ZOOM,
        "cutoff_year": CUTOFF_YEAR,
        "statuses": [STATUS_PRE, STATUS_POST, STATUS_UNKNOWN],
    }


@app.get("/api/buildings")
def buildings() -> Response:
    """Serve the processed footprints FeatureCollection.

    Returns 503 with guidance if the pipeline hasn't been run yet, so the front
    end can show a useful message instead of failing to parse.
    """
    if not OUT_GEOJSON.exists():
        return JSONResponse(
            status_code=503,
            content={
                "error": "data not built",
                "detail": "run `make data` (python -m pipeline.build) first",
            },
        )
    with open(OUT_GEOJSON) as f:
        data = json.load(f)
    return JSONResponse(content=data)


@app.get("/tiles/{z}/{x}/{y}.png")
def historical_tile(z: int, x: int, y: int) -> Response:
    """STUB — XYZ tile route for the USGS historical raster basemap.

    NOT IMPLEMENTED THIS SESSION. Returns 404 so a tile layer pointed here fails
    gracefully (the map uses a plain OSM basemap for now). When pipeline/
    fetch_usgs.py is built, serve the tiled HTMC quad PNGs from here.
    """
    return JSONResponse(
        status_code=404,
        content={
            "error": "historical tiles not implemented",
            "requested": {"z": z, "x": x, "y": y},
            "todo": "see pipeline/fetch_usgs.py — USGS HTMC basemap tiling",
        },
    )
