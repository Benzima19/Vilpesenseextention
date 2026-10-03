"""FastAPI application. Served on Vercel via api/index.py, locally via uvicorn."""

from fastapi import FastAPI

from guardian import __version__

app = FastAPI(title="VILPE Guardian API", version=__version__)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "version": __version__}
