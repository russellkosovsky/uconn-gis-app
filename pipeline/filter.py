"""Temporal classification — the architectural spine of the project.

A footprint is bucketed into exactly one ``temporal_status`` based on its known
construction year relative to the cutoff:

    pre_cutoff   year <= cutoff   (existed in the target era -> on the map)
    post_cutoff  year >  cutoff   (built later -> excluded from the era map)
    unknown      no known year    (NOT silently dropped or included)

The ``unknown`` bucket is a first-class output: it is the visible measure of how
much construction-date research remains. See README / DECISIONS.md.
"""
from __future__ import annotations

import math
from typing import Optional

from .config import CUTOFF_YEAR, STATUS_POST, STATUS_PRE, STATUS_UNKNOWN


def _is_missing(year: object) -> bool:
    """True for None, NaN, empty string or otherwise unparseable years."""
    if year is None:
        return True
    if isinstance(year, float) and math.isnan(year):
        return True
    if isinstance(year, str) and year.strip() == "":
        return True
    return False


def classify_temporal_status(year: object, cutoff: int = CUTOFF_YEAR) -> str:
    """Classify a single construction year. Pure function — no I/O, no globals
    beyond the default cutoff.

    Boundary rule: a building completed in the cutoff year is INCLUDED
    (``year <= cutoff``), so 1984 -> pre_cutoff and 1985 -> post_cutoff when
    cutoff == 1984.

    Missing / unparseable years map to ``unknown`` rather than raising, so the
    pipeline never crashes on a footprint that simply has no date yet.
    """
    if _is_missing(year):
        return STATUS_UNKNOWN
    try:
        y = int(float(year))  # tolerate "1984", 1984.0, etc.
    except (TypeError, ValueError):
        return STATUS_UNKNOWN
    return STATUS_PRE if y <= cutoff else STATUS_POST


def apply_temporal_status(gdf, cutoff: int = CUTOFF_YEAR):
    """Add a ``temporal_status`` column to an enriched GeoDataFrame.

    Expects a ``construction_year`` column (may contain NaN). Returns the same
    GeoDataFrame with the new column; does not mutate in place beyond assignment.
    """
    gdf = gdf.copy()
    gdf["temporal_status"] = gdf["construction_year"].apply(
        lambda y: classify_temporal_status(y, cutoff)
    )
    return gdf


def summarize(gdf) -> dict[str, int]:
    """Return a {status: count} summary for logging / sanity checks."""
    counts = gdf["temporal_status"].value_counts().to_dict()
    # Ensure all three keys always appear, even at zero.
    return {
        STATUS_PRE: int(counts.get(STATUS_PRE, 0)),
        STATUS_POST: int(counts.get(STATUS_POST, 0)),
        STATUS_UNKNOWN: int(counts.get(STATUS_UNKNOWN, 0)),
    }
