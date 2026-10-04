"""Small Open-Meteo adapter used as contextual weather data."""

from __future__ import annotations

from datetime import date, datetime, timedelta

import httpx
from pydantic import BaseModel


class WeatherReading(BaseModel):
    timestamp: datetime
    temperature_c: float | None = None
    relative_humidity_pct: float | None = None
    precipitation_mm: float | None = None
    dew_point_c: float | None = None
    source: str = "open-meteo"


class OpenMeteoService:
    """Fetch and cache one-day historical weather context for Vantaa."""

    url = "https://archive-api.open-meteo.com/v1/archive"
    latitude = 60.2934
    longitude = 25.0378

    def __init__(self) -> None:
        self._cache: dict[date, list[WeatherReading]] = {}

    def fetch_day(self, day: date) -> list[WeatherReading]:
        if day in self._cache:
            return self._cache[day]
        params = {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "start_date": day.isoformat(),
            "end_date": day.isoformat(),
            "hourly": "temperature_2m,relative_humidity_2m,precipitation,dew_point_2m",
            "timezone": "Europe/Helsinki",
        }
        try:
            response = httpx.get(self.url, params=params, timeout=5.0)
            response.raise_for_status()
            payload = response.json()
            hourly = payload["hourly"]
            times = hourly["time"]
            readings = [
                WeatherReading(
                    timestamp=datetime.fromisoformat(timestamp),
                    temperature_c=_value(hourly, "temperature_2m", index),
                    relative_humidity_pct=_value(hourly, "relative_humidity_2m", index),
                    precipitation_mm=_value(hourly, "precipitation", index),
                    dew_point_c=_value(hourly, "dew_point_2m", index),
                )
                for index, timestamp in enumerate(times)
            ]
        except (httpx.HTTPError, KeyError, TypeError, ValueError):
            readings = []
        self._cache[day] = readings
        return readings

    def context_for_timestamp(self, timestamp: datetime) -> WeatherReading | None:
        readings = self.fetch_day(timestamp.date())
        if not readings:
            return None
        nearest = min(readings, key=lambda reading: abs(reading.timestamp - timestamp))
        return nearest if abs(nearest.timestamp - timestamp) <= timedelta(hours=3) else None


def _value(hourly: dict[str, list[float | None]], name: str, index: int) -> float | None:
    values = hourly.get(name, [])
    return values[index] if index < len(values) else None
