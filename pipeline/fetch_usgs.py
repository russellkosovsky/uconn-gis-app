"""STUB — USGS historical topographic raster basemap.

NOT IMPLEMENTED THIS SESSION. The map currently works against a plain OSM raster
basemap (see web/). This module documents the interface for a future session
that adds a period-accurate historical basemap underneath the footprints.

------------------------------------------------------------------------------
Data source (public domain):
    USGS The National Map — TNMAccess API
        https://tnmaccess.nationalmap.gov/api/v1/
    Specifically the **Historical Topographic Map Collection (HTMC)**, which
    contains georeferenced scans of historical USGS quadrangles. For Storrs the
    relevant quad is "Spring Hill, CT" (7.5-minute series); pick an edition
    printed close to the target era (early 1980s) for visual accuracy.

USGS-produced maps are in the public domain — no license key required, but
credit "USGS The National Map: Historical Topographic Map Collection".

------------------------------------------------------------------------------
Implementation sketch (TODO):
    1. Query TNMAccess for HTMC items intersecting the Storrs bbox:
         GET {API}/products
           ?datasets=Historical Topographic Maps
           &bbox={W},{S},{E},{N}
           &prodFormats=GeoPDF
           &outputFormat=JSON
       Response items carry a `downloadURL` (GeoPDF) and `dateCreated`.
    2. Choose the edition nearest CUTOFF_YEAR, download the GeoPDF to data/raw/.
    3. Convert GeoPDF -> GeoTIFF (gdal_translate) and reproject to web mercator.
    4. Tile it into XYZ PNGs (e.g. rio-tiler / gdal2tiles) under data/processed/,
       and wire the FastAPI /tiles/{z}/{x}/{y}.png route to serve them.
       rasterio is already a dependency for exactly this step.
"""
from __future__ import annotations

from .config import BBOX, CUTOFF_YEAR

TNM_ACCESS_API = "https://tnmaccess.nationalmap.gov/api/v1/"
HTMC_DATASET = "Historical Topographic Maps"


def fetch_usgs_historical_quad(
    bbox: tuple[float, float, float, float] = BBOX,
    target_year: int = CUTOFF_YEAR,
    out_dir=None,
) -> None:
    """TODO: download the HTMC quad nearest ``target_year`` for ``bbox``.

    Args:
        bbox: (W, S, E, N) in EPSG:4326.
        target_year: prefer the map edition printed closest to this year.
        out_dir: where to cache the downloaded GeoPDF/GeoTIFF (defaults raw/).

    Returns:
        Eventually: path to a tiled XYZ directory or a single GeoTIFF.

    Raises:
        NotImplementedError: this is a documented stub for a future session.
    """
    raise NotImplementedError(
        "USGS historical basemap is stubbed. See module docstring for the "
        "TNMAccess HTMC integration plan. The map works on a plain basemap "
        "until this is built."
    )
