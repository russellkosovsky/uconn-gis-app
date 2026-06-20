# Task runner for the UConn Storrs historical-map foundation.
#
#   make setup   one-time: create venv, install python + web deps
#   make data    run the pipeline -> data/processed/buildings.geojson
#   make api     serve the GeoJSON + tile stub on :8000 (foreground)
#   make web     run the Vite/React/MapLibre dev server on :5173 (foreground)
#   make test    pytest (filter spine)
#   make all     setup + data, then prints how to start api + web
#   make clean   remove venv, node_modules, generated data
#
# `api` and `web` are long-running servers — run them in two separate terminals.

PYTHON := .venv/bin/python
PIP := .venv/bin/pip
# Prefer npm on PATH; otherwise fall back to the newest nvm-installed node.
NPM := $(shell command -v npm 2>/dev/null || ls -d $(HOME)/.nvm/versions/node/*/bin/npm 2>/dev/null | tail -1)

.PHONY: setup data api web test all clean

setup:
	python3 -m venv .venv
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	cd web && $(NPM) install --no-fund --no-audit
	@echo "✓ setup complete. Next: make data"

data:
	$(PYTHON) -m pipeline.build

api:
	$(PYTHON) -m uvicorn api.main:app --reload --port 8000

web:
	cd web && $(NPM) run dev

test:
	$(PYTHON) -m pytest -q

all: setup data
	@echo ""
	@echo "✓ Data built. Now start the two servers in separate terminals:"
	@echo "    make api   # http://localhost:8000"
	@echo "    make web   # http://localhost:5173"

clean:
	rm -rf .venv web/node_modules web/dist data/raw/* data/processed/*
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
	@echo "✓ cleaned (seed CSV preserved)"
