from fastapi.testclient import TestClient

from guardian import __version__
from guardian.api.app import app


def test_health() -> None:
    res = TestClient(app).get("/api/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok", "version": __version__}
