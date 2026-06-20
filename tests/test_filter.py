"""Unit tests for the temporal-filter spine.

These test the PURE classification logic and the name/alias enrichment join —
no network, no osmnx. That is the whole point of keeping `classify_temporal_status`
dependency-free.
"""
import math

import pandas as pd
import pytest

from pipeline.config import (
    CUTOFF_YEAR,
    STATUS_POST,
    STATUS_PRE,
    STATUS_UNKNOWN,
)
from pipeline.enrich import (
    build_token_index,
    build_year_lookup,
    match_row,
    match_token_subset,
    normalize_name,
)
from pipeline.filter import classify_temporal_status


# --- bucketing -------------------------------------------------------------

@pytest.mark.parametrize(
    "year,expected",
    [
        (1906, STATUS_PRE),    # NRHP historic-district core
        (1978, STATUS_PRE),    # Babbidge Library
        (1990, STATUS_POST),   # Gampel Pavilion
        (2016, STATUS_POST),   # NextGen
    ],
)
def test_known_years_bucket_correctly(year, expected):
    assert classify_temporal_status(year, CUTOFF_YEAR) == expected


# --- cutoff boundary (the load-bearing case) -------------------------------

def test_cutoff_boundary_inclusive():
    # A building completed in the cutoff year is INCLUDED (<=).
    assert classify_temporal_status(1984, 1984) == STATUS_PRE
    # The very next year flips to post.
    assert classify_temporal_status(1985, 1984) == STATUS_POST


def test_default_cutoff_is_1984():
    assert CUTOFF_YEAR == 1984
    assert classify_temporal_status(1984) == STATUS_PRE
    assert classify_temporal_status(1985) == STATUS_POST


# --- missing / malformed years map to unknown, never crash -----------------

@pytest.mark.parametrize("missing", [None, float("nan"), "", "   ", "n/a", "circa"])
def test_missing_year_is_unknown(missing):
    assert classify_temporal_status(missing, CUTOFF_YEAR) == STATUS_UNKNOWN


def test_string_and_float_years_are_tolerated():
    assert classify_temporal_status("1978") == STATUS_PRE
    assert classify_temporal_status(1990.0) == STATUS_POST


# --- name/alias enrichment join --------------------------------------------

@pytest.fixture
def seed():
    return pd.DataFrame(
        [
            {
                "building_name": "Homer Babbidge Library",
                "aliases": "Babbidge Library;HBL",
                "building_code": "HBL",
                "construction_year": 1978,
                "year_confidence": "high",
                "source": "en.wikipedia.org",
            },
            {
                "building_name": "Harry A. Gampel Pavilion",
                "aliases": "Gampel Pavilion;Gampel",
                "building_code": pd.NA,
                "construction_year": 1990,
                "year_confidence": "high",
                "source": "en.wikipedia.org",
            },
        ]
    )


def test_normalize_name_collapses_noise():
    assert normalize_name("  Koons   Hall! ") == "koons hall"
    assert normalize_name(None) == ""


def test_match_on_canonical_name(seed):
    lookup = build_year_lookup(seed)
    rec = match_row("Homer Babbidge Library", lookup)
    assert rec is not None and rec["construction_year"] == 1978


def test_match_on_alias(seed):
    lookup = build_year_lookup(seed)
    # OSM might label it just "Gampel" — alias match must still resolve.
    rec = match_row("gampel", lookup)
    assert rec is not None and rec["construction_year"] == 1990


def test_unmatched_name_returns_none(seed):
    lookup = build_year_lookup(seed)
    assert match_row("Some Unlisted Dorm", lookup) is None


# --- token-subset fallback (recovers OSM's full honorific names) -----------

def test_token_subset_recovers_full_osm_name(seed):
    # OSM labels it "Homer D. Babbidge Library"; exact match misses the "D.".
    idx = build_token_index(seed)
    lookup = build_year_lookup(seed)
    assert match_row("Homer D. Babbidge Library", lookup) is None  # exact miss
    rec = match_token_subset("Homer D. Babbidge Library", idx)     # fuzzy hit
    assert rec is not None and rec["construction_year"] == 1978


def test_token_subset_requires_all_seed_tokens(seed):
    idx = build_token_index(seed)
    # "Library" alone shares a token but is not a full seed key -> no match.
    assert match_token_subset("Some Other Library", idx) is None


# --- end-to-end on the seed records (no OSM needed) ------------------------

def test_seed_records_produce_all_three_buckets(seed):
    # Build a tiny stand-in with one of each status to prove the pipeline's
    # classification covers pre/post/unknown together.
    years = [1978, 1990, None]
    statuses = [classify_temporal_status(y, CUTOFF_YEAR) for y in years]
    assert set(statuses) == {STATUS_PRE, STATUS_POST, STATUS_UNKNOWN}
