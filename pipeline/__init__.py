"""Temporal-GIS pipeline for the historical UConn Storrs campus map.

Stages (each a small, importable module):
    fetch   -> pull modern OSM building footprints for the Storrs bbox (cached)
    enrich  -> join footprints to the seed construction-year table (name/alias)
    filter  -> classify each footprint as pre_cutoff / post_cutoff / unknown
    build   -> orchestrate the above and emit data/processed/buildings.geojson
"""
