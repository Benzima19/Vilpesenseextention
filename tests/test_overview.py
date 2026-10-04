from pathlib import Path

from fastapi.testclient import TestClient

from guardian.api import app as api_module
from guardian.api.app import app


def test_vantaa_overview_returns_all_area_workbooks(monkeypatch) -> None:
    data_dir = Path(__file__).parents[1] / "data"
    monkeypatch.setattr(api_module, "DATA_DIR", data_dir)
    monkeypatch.setattr(api_module.weather_service, "context_for_timestamp", lambda _: None)

    response = TestClient(app).get("/api/buildings/vantaa/overview")

    assert response.status_code == 200
    body = response.json()
    assert body["building"]["id"] == "vantaa"
    assert body["building"]["area_count"] == 7
    assert len(body["areas"]) == 7
    assert {area["kind"] for area in body["areas"]} == {"roof", "green_roof", "crawl_space"}
    assert all("latest_reading" in area for area in body["areas"])
    assert all("data_quality" in area for area in body["areas"])


def test_structure_returns_map_areas_and_weather_context(monkeypatch) -> None:
    data_dir = Path(__file__).parents[1] / "data"
    monkeypatch.setattr(api_module, "DATA_DIR", data_dir)
    weather = {
        "timestamp": "2026-09-11T04:00:00",
        "temperature_c": 8.0,
        "relative_humidity_pct": 96.0,
        "precipitation_mm": 0.2,
        "dew_point_c": 7.4,
        "source": "open-meteo",
    }
    monkeypatch.setattr(
        api_module.weather_service,
        "context_for_timestamp",
        lambda _: api_module.WeatherReading.model_validate(weather),
    )

    response = TestClient(app).get("/api/buildings/vantaa/structure")

    assert response.status_code == 200
    body = response.json()
    assert len(body["areas"]) == 7
    assert {"id", "name", "kind", "status", "score", "latest_reading", "device", "reason"} <= set(
        body["areas"][0]
    )


def test_trends_returns_filtered_normalized_readings(monkeypatch) -> None:
    data_dir = Path(__file__).parents[1] / "data"
    monkeypatch.setattr(api_module, "DATA_DIR", data_dir)
    monkeypatch.setattr(api_module.weather_service, "context_for_timestamp", lambda _: None)

    response = TestClient(app).get(
        "/api/buildings/vantaa/areas/katto-1/trends",
        params={"start_date": "2026-09-10", "end_date": "2026-09-11"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["area"]["id"] == "katto-1"
    assert body["readings"]
    assert {
        "timestamp",
        "indoor_temperature_c",
        "indoor_relative_humidity_pct",
        "indoor_absolute_humidity_g_m3",
        "outdoor_temperature_c",
        "outdoor_relative_humidity_pct",
        "outdoor_absolute_humidity_g_m3",
        "fan_rpm",
    } <= set(body["readings"][0])
    assert body["trend_direction"] in {"improving", "stable", "worsening"}
