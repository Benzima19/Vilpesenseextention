from datetime import date, datetime

import httpx

from guardian.weather import OpenMeteoService


def test_open_meteo_response_is_normalized(monkeypatch) -> None:
    payload = {
        "hourly": {
            "time": ["2026-09-11T04:00"],
            "temperature_2m": [8.0],
            "relative_humidity_2m": [96.0],
            "precipitation": [0.2],
            "dew_point_2m": [7.4],
        }
    }

    monkeypatch.setattr(
        "guardian.weather.httpx.get",
        lambda *args, **kwargs: httpx.Response(
            200,
            json=payload,
            request=httpx.Request("GET", "https://example.test"),
        ),
    )
    service = OpenMeteoService()

    readings = service.fetch_day(date(2026, 9, 11))

    assert readings[0].temperature_c == 8.0
    assert readings[0].relative_humidity_pct == 96.0
    assert readings[0].precipitation_mm == 0.2
    assert readings[0].dew_point_c == 7.4


def test_open_meteo_failure_returns_no_context(monkeypatch) -> None:
    def unavailable(*args, **kwargs):
        raise httpx.ConnectError("offline")

    monkeypatch.setattr("guardian.weather.httpx.get", unavailable)
    service = OpenMeteoService()

    assert service.fetch_day(date(2026, 9, 11)) == []
    assert service.context_for_timestamp(datetime(2026, 9, 11, 4, 0)) is None
