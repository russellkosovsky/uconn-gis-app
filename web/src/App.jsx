import { useEffect, useRef, useState } from "react";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import {
  baseStyle,
  fillColorExpression,
  STATUS_COLORS,
  STATUS_LABELS,
} from "./mapStyle.js";

// Fallback center if /api/config can't be reached (Storrs campus).
const FALLBACK = { center: [-72.2515, 41.8086], zoom: 15.6, cutoff: 1984 };

export default function App() {
  const mapContainer = useRef(null);
  const mapRef = useRef(null);
  const [counts, setCounts] = useState(null);
  const [cutoff, setCutoff] = useState(FALLBACK.cutoff);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;

    async function init() {
      // Pull spatial config from the API (single source of truth), with a
      // graceful fallback so the map still renders if the API is slow.
      let center = FALLBACK.center;
      let zoom = FALLBACK.zoom;
      try {
        const cfg = await fetch("/api/config").then((r) => r.json());
        center = [cfg.center.lon, cfg.center.lat];
        if (cfg.zoom) zoom = cfg.zoom;
        setCutoff(cfg.cutoff_year);
      } catch {
        /* keep fallback */
      }
      if (cancelled) return;

      const map = new maplibregl.Map({
        container: mapContainer.current,
        style: baseStyle,
        center,
        zoom,
      });
      mapRef.current = map;
      map.addControl(new maplibregl.NavigationControl(), "top-right");
      map.addControl(
        new maplibregl.AttributionControl({ compact: true }),
        "bottom-right"
      );

      map.on("load", async () => {
        let fc;
        try {
          const res = await fetch("/api/buildings");
          if (!res.ok) throw new Error(`API ${res.status}`);
          fc = await res.json();
        } catch (e) {
          setError(
            "Could not load /api/buildings — run `make data` then `make api`."
          );
          return;
        }
        if (cancelled) return;
        if (fc.metadata?.counts) setCounts(fc.metadata.counts);

        map.addSource("buildings", { type: "geojson", data: fc });

        // Filled footprints colored by temporal_status.
        map.addLayer({
          id: "buildings-fill",
          type: "fill",
          source: "buildings",
          paint: {
            "fill-color": fillColorExpression,
            "fill-opacity": 0.65,
          },
        });
        // Crisp outline so adjacent footprints stay legible.
        map.addLayer({
          id: "buildings-outline",
          type: "line",
          source: "buildings",
          paint: { "line-color": "#222", "line-width": 0.4 },
        });

        // Click a footprint -> popup with what we know (and how we matched it).
        map.on("click", "buildings-fill", (e) => {
          const p = e.features[0].properties;
          const year = p.construction_year ?? "—";
          const name = p.name || p.seed_name || "(unnamed footprint)";
          const conf = p.year_confidence
            ? ` · confidence: ${p.year_confidence}`
            : "";
          const src = p.source ? `<br/>source: ${p.source}` : "";
          const method = p.match_method
            ? `<br/>matched: ${p.match_method}`
            : "";
          new maplibregl.Popup({ closeButton: true })
            .setLngLat(e.lngLat)
            .setHTML(
              `<div class="popup-title">${name}</div>` +
                `<div class="popup-meta">status: ${p.temporal_status}<br/>` +
                `year: ${year}${conf}${src}${method}</div>`
            )
            .addTo(map);
        });
        map.on("mouseenter", "buildings-fill", () => {
          map.getCanvas().style.cursor = "pointer";
        });
        map.on("mouseleave", "buildings-fill", () => {
          map.getCanvas().style.cursor = "";
        });
      });
    }

    init();
    return () => {
      cancelled = true;
      mapRef.current?.remove();
    };
  }, []);

  const order = ["pre_cutoff", "post_cutoff", "unknown"];

  return (
    <>
      <div id="map" ref={mapContainer} />
      {error && <div className="banner">{error}</div>}
      <div className="panel">
        <h1>UConn Storrs — Historical Campus</h1>
        <p className="sub">
          Reconstruction target: pre-{cutoff + 1} (cutoff {cutoff}). Footprints
          colored by <code>temporal_status</code>.
        </p>
        {order.map((key) => (
          <div className="legend-row" key={key}>
            <span
              className="swatch"
              style={{ background: STATUS_COLORS[key] }}
            />
            <span>{STATUS_LABELS[key]}</span>
            {counts && <span className="count">{counts[key] ?? 0}</span>}
          </div>
        ))}
        <p className="note">
          “Unknown” = OSM footprints not yet in the construction-year seed table.
          That bucket is the visible measure of dating work remaining. Footprints
          © OpenStreetMap contributors (ODbL).
        </p>
      </div>
    </>
  );
}
