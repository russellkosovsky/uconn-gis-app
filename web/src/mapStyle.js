// Single source of truth for temporal_status -> color, and a keyless basemap.
//
// Basemap: plain OpenStreetMap raster tiles. © OpenStreetMap contributors
// (ODbL) — attributed in the map control below. This is the placeholder until
// the USGS historical raster basemap (pipeline/fetch_usgs.py) is built.

export const STATUS_COLORS = {
  pre_cutoff: "#2e7d32", // green  — existed at/before cutoff (on the era map)
  post_cutoff: "#c62828", // red    — built after cutoff (excluded)
  unknown: "#9e9e9e", // gray   — no known construction year (work remaining)
};

export const STATUS_LABELS = {
  pre_cutoff: "Pre-cutoff (≤ 1984) — on the map",
  post_cutoff: "Post-cutoff (> 1984) — excluded",
  unknown: "Unknown year — needs dating",
};

// MapLibre "match" expression driving fill color straight from the feature's
// temporal_status property. One layer, one mapping.
export const fillColorExpression = [
  "match",
  ["get", "temporal_status"],
  "pre_cutoff",
  STATUS_COLORS.pre_cutoff,
  "post_cutoff",
  STATUS_COLORS.post_cutoff,
  STATUS_COLORS.unknown, // default (covers "unknown" and any surprise)
];

// Minimal keyless raster basemap style.
export const baseStyle = {
  version: 8,
  sources: {
    osm: {
      type: "raster",
      tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],
      tileSize: 256,
      attribution:
        '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    },
  },
  layers: [{ id: "osm", type: "raster", source: "osm" }],
};
