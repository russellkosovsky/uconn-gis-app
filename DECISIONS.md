# Decisions & Assumptions

Every non-obvious choice in this foundation, with the reasoning. Append here
rather than burying decisions in commit messages.

## Environment

- **Python 3.13.4, not 3.11.** The spec asked for 3.11, but pyenv on this machine
  only has 3.13.4 installed (and `system`). Modern geopandas/osmnx/rasterio all
  ship 3.13 wheels, so everything installs and runs cleanly. Compiling 3.11 from
  source would cost minutes for no functional gain. If you need 3.11 for parity,
  `pyenv install 3.11 && pyenv local 3.11` then recreate the venv.
- **Node via nvm.** `node` isn't on the default PATH; it lives at
  `~/.nvm/versions/node/v22.17.0/bin`. The Makefile's `NPM` variable falls back
  to the newest nvm-installed npm if `npm` isn't on PATH.
- **Project-local `web/.npmrc`.** The user's global `~/.npmrc` points npm at a
  private, authenticated Azure DevOps registry (stale creds → install failed).
  `web/.npmrc` forces the **public** npm registry for this repo only, so
  `make setup` is reproducible and doesn't touch global config.

## Pipeline / GIS

- **osmnx pinned to 2.1.0.** `features_from_bbox` changed signature between major
  versions: 1.x took positional `(north, south, east, west, tags)`; 2.x takes a
  single `bbox=(left, bottom, right, top)` tuple. We verified the installed
  signature (`features_from_bbox(bbox, tags)`) and `pipeline/fetch.py`
  introspects it at runtime, adapting to either form so a version bump can't
  silently transpose coordinates.
- **BBOX ordering = (W, S, E, N).** Deliberately matches osmnx 2.x's
  `(left, bottom, right, top)` so we pass it straight through. Stored once in
  `pipeline/config.py`.
- **CRS = EPSG:4326 throughout, no reprojection.** OSM is natively WGS84 and
  MapLibre consumes 4326 GeoJSON, so reprojecting would only add round-trip
  error. `build.py` still reprojects *defensively* if the source CRS ever
  differs. If we later add area/distance analysis, reproject to a projected CRS
  (e.g. EPSG:6433, CT State Plane / NAD83) for that step only.
- **Cutoff is inclusive (`year <= CUTOFF_YEAR`).** A building completed in 1984 is
  ON the map; 1985 is off. Default cutoff 1984 (target era "early 1980s"), set
  once in `config.py`.
- **Three-bucket `temporal_status`: `pre_cutoff` / `post_cutoff` / `unknown`.**
  Footprints with no known year are NEVER silently included or dropped — they go
  to `unknown`. That bucket (currently ~821 of 834 footprints) is the visible
  measure of how much construction-date research remains.

## The join (footprint ↔ construction year)

- **Match on name OR alias, normalized, with a token-subset fallback.** OSM uses
  full official names ("Albert Gurdon Gulley Hall") where the seed table uses
  common names ("Gulley Hall"). The join does two passes:
  1. **Exact** match on normalized (lowercased, depunctuated, whitespace-
     collapsed) `building_name` or any `;`-delimited alias. High precision.
  2. **Token-subset fallback** when exact misses: a seed key matches if *all* of
     its tokens are a subset of the OSM name's tokens, the key has ≥2 tokens, and
     exactly one building wins (most-specific). Ambiguous ties → no match. This
     recovered Gulley, Hawley Armory, Beach, Arjona, and Babbidge.
- **`match_method` is published per feature** (`exact` / `token_subset` / null) so
  every join is auditable — you can see which dates came from a fuzzy match.
- **Why some seed rows still don't match:** Jorgensen, Monteith, and NextGen are
  not named in OSM within the bbox (footprint unnamed or absent). That's correct
  behavior — they stay `unknown` rather than getting guessed coordinates.
- **No invented years.** The seed CSV holds only the 16 anchor buildings the user
  supplied, each with a `source` and `year_confidence`. Filling the `unknown`
  bucket (UConn Archives building files, NRHP historic-district nomination for the
  1906–1942 masonry core) is the real, deferred work. See the TODO in the README.

## Backend

- **FastAPI serves the prebuilt GeoJSON file**, it does not run the pipeline on
  request. `make data` is an explicit build step; the API just reads the artifact
  (and returns 503 with guidance if it's missing).
- **CORS is wide open (`*`)** for the foundation. The Vite dev server also proxies
  `/api`→`:8000`, so in practice requests are same-origin in dev. Tighten CORS
  before any deployment.
- **`/tiles/{z}/{x}/{y}.png` is a deliberate 404 stub.** Route exists, returns 404
  + a TODO pointing at `pipeline/fetch_usgs.py`, so a future tile layer fails
  gracefully today.

## Frontend

- **Basemap = plain OSM raster tiles (keyless), attributed.** Placeholder until
  the USGS historical raster basemap is built. No API key needed; ODbL
  attribution shown in the map. Do NOT embed copyrighted UConn/MAGIC map assets.
- **One fill layer, data-driven color.** A MapLibre `match` expression maps
  `temporal_status` → color, rather than three separate filtered layers. Colors
  and labels live in one file (`web/src/mapStyle.js`).
- **Spatial config comes from `/api/config`** (center/cutoff) with a hardcoded
  Storrs fallback, so the front end has no duplicated bbox constants.

## Stubbed this session (interfaces only)

- `pipeline/fetch_usgs.py` — USGS TNMAccess / Historical Topographic Map
  Collection integration. Documented API + function signature, raises
  `NotImplementedError`.
- `GET /tiles/{z}/{x}/{y}.png` — see above.
- `rasterio` is installed (for the future USGS raster step) but unused this
  session.
