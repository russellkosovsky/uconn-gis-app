"""Orchestrate the pipeline: fetch -> enrich -> filter -> emit GeoJSON.

Run with ``python -m pipeline.build`` (or ``make data``). Output lands at
``data/processed/buildings.geojson`` in EPSG:4326, ready for the API / MapLibre.
"""
from __future__ import annotations

import json

from .config import OUT_GEOJSON, OUTPUT_CRS, CUTOFF_YEAR
from .enrich import enrich_footprints
from .fetch import fetch_footprints
from .filter import apply_temporal_status, summarize

# Properties we publish per footprint. Anything else from OSM is dropped to keep
# the payload small and predictable for the front end.
PUBLISH_COLS = [
    "osm_id",
    "name",
    "seed_name",
    "building_code",
    "construction_year",
    "year_confidence",
    "source",
    "match_method",
    "temporal_status",
]


def run(force_fetch: bool = False) -> dict[str, int]:
    """Execute the full pipeline and write the processed GeoJSON.

    Returns the {status: count} summary.
    """
    footprints = fetch_footprints(force=force_fetch)
    enriched = enrich_footprints(footprints)
    classified = apply_temporal_status(enriched, cutoff=CUTOFF_YEAR)

    # Reproject defensively (OSM is already 4326, so this is usually a no-op).
    if classified.crs is not None and classified.crs.to_string() != OUTPUT_CRS:
        classified = classified.to_crs(OUTPUT_CRS)

    cols = [c for c in PUBLISH_COLS if c in classified.columns] + ["geometry"]
    out = classified[cols].copy()

    # construction_year is float (NaN for unknowns) after the pandas join; emit
    # it as a nullable int so the front end gets 1990 not 1990.0 / null.
    out["construction_year"] = out["construction_year"].astype("Int64")

    OUT_GEOJSON.parent.mkdir(parents=True, exist_ok=True)
    out.to_file(OUT_GEOJSON, driver="GeoJSON")

    summary = summarize(classified)
    _stamp_metadata(summary, total=len(out))
    return summary


def _stamp_metadata(summary: dict[str, int], total: int) -> None:
    """Fold a small ``metadata`` block into the GeoJSON FeatureCollection so the
    API / front end can show counts and attribution without recomputing.
    """
    with open(OUT_GEOJSON) as f:
        fc = json.load(f)
    fc["metadata"] = {
        "cutoff_year": CUTOFF_YEAR,
        "counts": summary,
        "total_features": total,
        "attribution": "Building footprints © OpenStreetMap contributors (ODbL)",
        "note": (
            "temporal_status is derived from data/seed/"
            "buildings_construction_years.csv; the 'unknown' bucket is the "
            "research-remaining measure, not an error."
        ),
    }
    with open(OUT_GEOJSON, "w") as f:
        json.dump(fc, f)


if __name__ == "__main__":
    s = run()
    print("Wrote", OUT_GEOJSON)
    print("temporal_status counts:", s)
