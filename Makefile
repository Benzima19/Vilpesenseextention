# VILPE Guardian – common tasks. Requires uv (Python) and npm (Node 20+).

.PHONY: install dev-api dev-web test lint check

install:            ## install backend and web dependencies
	uv sync
	npm --prefix web install

dev-api:            ## run the Python API on http://localhost:8000
	uv run guardian serve

dev-web:            ## run the web app on http://localhost:5173 (proxies /api to :8000)
	npm --prefix web run dev

test:               ## run all tests
	uv run pytest -q
	npm --prefix web test

lint:               ## lint and format checks
	uv run ruff check .
	uv run ruff format --check .
	npm --prefix web run lint

check: lint test    ## everything CI runs
	npm --prefix web run build
