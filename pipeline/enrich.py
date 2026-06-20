"""Join OSM footprints to the seed construction-year table.

Matching strategy (see DECISIONS.md): OSM building names are messy and some
buildings were renamed, so we match on **name OR alias**, not exact name. The
seed CSV carries a semicolon-delimited ``aliases`` column for exactly this.

Names are normalized (lowercased, whitespace-collapsed, punctuation-trimmed)
before comparison so "Koons Hall" matches "koons  hall".
"""
from __future__ import annotations

import re
from typing import Optional

import pandas as pd

from .config import SEED_CSV


def normalize_name(name: object) -> str:
    """Lowercase, strip surrounding punctuation, collapse internal whitespace.

    Returns "" for missing names so unnamed footprints never accidentally match
    a blank key.
    """
    if name is None or (isinstance(name, float)):
        return ""
    s = str(name).strip().lower()
    s = re.sub(r"[^\w\s]", " ", s)   # drop punctuation
    s = re.sub(r"\s+", " ", s).strip()
    return s


def load_seed(path=SEED_CSV) -> pd.DataFrame:
    """Load the construction-year seed table."""
    return pd.read_csv(path, dtype={"building_code": "string"})


def _record_from_row(row) -> dict:
    return {
        "construction_year": row.get("construction_year"),
        "year_confidence": row.get("year_confidence"),
        "source": row.get("source"),
        "building_code": row.get("building_code"),
        "seed_name": row.get("building_name"),
    }


def _keys_for_row(row) -> list[str]:
    keys = [row.get("building_name")]
    aliases = row.get("aliases")
    if isinstance(aliases, str) and aliases.strip():
        keys.extend(aliases.split(";"))
    return keys


def build_year_lookup(seed: pd.DataFrame) -> dict[str, dict]:
    """Build {normalized_name_or_alias -> seed_row_dict}.

    Both the canonical ``building_name`` and every entry in ``aliases`` map to
    the same row, so the enrich step can match on either.
    """
    lookup: dict[str, dict] = {}
    for _, row in seed.iterrows():
        record = _record_from_row(row)
        for key in _keys_for_row(row):
            norm = normalize_name(key)
            if norm:
                lookup[norm] = record
    return lookup


def build_token_index(seed: pd.DataFrame) -> list[dict]:
    """Build a token-subset index for the fuzzy fallback pass.

    Each entry is {tokens: frozenset, n: int, record: dict}. Only keys with >= 2
    tokens are indexed, because a single common token ("hall", "gampel") is too
    weak to match safely.
    """
    index: list[dict] = []
    for _, row in seed.iterrows():
        record = _record_from_row(row)
        for key in _keys_for_row(row):
            toks = frozenset(normalize_name(key).split())
            if len(toks) >= 2:
                index.append({"tokens": toks, "n": len(toks), "record": record})
    return index


def match_row(osm_name: object, lookup: dict[str, dict]) -> Optional[dict]:
    """Exact match: return the seed record for an OSM name (name or alias)."""
    return lookup.get(normalize_name(osm_name))


def match_token_subset(
    osm_name: object, token_index: list[dict]
) -> Optional[dict]:
    """Fallback: match if ALL tokens of a seed key are present in the OSM name.

    Picks the most specific (most tokens) candidate. If two *different*
    buildings tie for most-specific, returns None — an ambiguous match is worse
    than no match (we'd be assigning a possibly-wrong construction year).
    """
    osm_tokens = set(normalize_name(osm_name).split())
    if not osm_tokens:
        return None
    candidates = [e for e in token_index if e["tokens"] <= osm_tokens]
    if not candidates:
        return None
    best_n = max(e["n"] for e in candidates)
    winners = [e for e in candidates if e["n"] == best_n]
    distinct = {w["record"]["seed_name"] for w in winners}
    if len(distinct) != 1:
        return None  # ambiguous -> leave as unknown
    return winners[0]["record"]


def enrich_footprints(gdf, seed: Optional[pd.DataFrame] = None):
    """Attach construction_year / year_confidence / source / building_code to
    each footprint by name-or-alias match. Unmatched footprints keep NaN year
    (which the filter will later classify as ``unknown``).
    """
    if seed is None:
        seed = load_seed()
    lookup = build_year_lookup(seed)
    token_index = build_token_index(seed)

    gdf = gdf.copy()
    # OSM stores the human name under "name".
    names = gdf["name"] if "name" in gdf.columns else [None] * len(gdf)

    years, confs, sources, codes, seed_names, methods = [], [], [], [], [], []
    for nm in names:
        rec = match_row(nm, lookup)
        method = "exact" if rec is not None else None
        if rec is None:
            rec = match_token_subset(nm, token_index)
            method = "token_subset" if rec is not None else None
        if rec is None:
            years.append(None)
            confs.append(None)
            sources.append(None)
            codes.append(None)
            seed_names.append(None)
            methods.append(None)
        else:
            years.append(rec["construction_year"])
            confs.append(rec["year_confidence"])
            sources.append(rec["source"])
            codes.append(rec["building_code"])
            seed_names.append(rec["seed_name"])
            methods.append(method)

    gdf["construction_year"] = years
    gdf["year_confidence"] = confs
    gdf["source"] = sources
    gdf["building_code"] = codes
    gdf["seed_name"] = seed_names
    gdf["match_method"] = methods
    return gdf
