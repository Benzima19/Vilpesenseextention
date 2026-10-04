"""FastAPI application. Served on Vercel via api/index.py, locally via uvicorn."""

from datetime import date
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from guardian import __version__
from guardian.data import Area, Building, Reading, load_vantaa_building
from guardian.health import assess_area
from guardian.weather import OpenMeteoService, WeatherReading

app = FastAPI(title="VILPE Guardian API", version=__version__)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "version": __version__}


class LatestAreaReading(BaseModel):
    timestamp: str
    indoor_temperature_c: float | None = None
    indoor_relative_humidity_pct: float | None = None
    indoor_absolute_humidity_g_m3: float | None = None
    outdoor_temperature_c: float | None = None
    outdoor_relative_humidity_pct: float | None = None
    outdoor_absolute_humidity_g_m3: float | None = None
    fan_rpm: float | None = None


DATA_DIR = Path(__file__).resolve().parents[2] / "data"
weather_service = OpenMeteoService()


def _latest(reading: Reading) -> LatestAreaReading:
    return LatestAreaReading(
        timestamp=reading.timestamp.isoformat(),
        **reading.model_dump(exclude={"timestamp"}),
    )


def _weather(area: Area) -> WeatherReading | None:
    if not area.readings:
        return None
    return weather_service.context_for_timestamp(area.readings[-1].timestamp)


def _weather_payload(weather: WeatherReading | None) -> dict | None:
    return weather.model_dump(mode="json") if weather else None


def _area_payload(area: Area, weather: WeatherReading | None = None) -> dict:
    assessment = assess_area(area, weather)
    latest = _latest(area.readings[-1]) if area.readings else None
    return {
        "id": area.id,
        "name": area.name,
        "kind": area.kind,
        "usage": area.usage,
        "material": area.material,
        "device_serial": area.device_serial,
        "device_type": area.device_type,
        "controller_sensors": area.controller_sensors,
        "latest_mould_index": area.latest_mould_index,
        "latest_reading": latest.model_dump() if latest else None,
        "status": assessment.status,
        "health_score": assessment.score,
        "reasons": assessment.reasons,
        "trend": assessment.trend,
        "data_quality": area.data_quality.model_dump() if area.data_quality else None,
        "weather_context": _weather_payload(weather),
    }


@app.get("/api/buildings/vantaa/overview")
def building_overview() -> dict:
    building: Building = load_vantaa_building(DATA_DIR)
    areas = []
    for area in building.areas:
        areas.append(_area_payload(area, _weather(area)))

    scores = [area["health_score"] for area in areas]
    if any(area["status"] == "action_needed" for area in areas):
        overall_status = "action_needed"
    elif any(area["status"] == "attention" for area in areas):
        overall_status = "attention"
    else:
        overall_status = "healthy"
    timestamps = [
        area["latest_reading"]["timestamp"] for area in areas if area["latest_reading"] is not None
    ]
    return {
        "building": {
            "id": building.id,
            "name": building.name,
            "location": building.location,
            "area_count": len(building.areas),
        },
        "overall_status": overall_status,
        "health_score": round(sum(scores) / len(scores)) if scores else None,
        "updated_at": max(timestamps) if timestamps else None,
        "areas": areas,
    }


@app.get("/api/buildings/vantaa/structure")
def building_structure() -> dict:
    building = load_vantaa_building(DATA_DIR)
    areas = []
    for area in building.areas:
        payload = _area_payload(area, _weather(area))
        areas.append(
            {
                "id": payload["id"],
                "name": payload["name"],
                "kind": payload["kind"],
                "status": payload["status"],
                "score": payload["health_score"],
                "latest_reading": payload["latest_reading"],
                "device": {
                    "serial": payload["device_serial"],
                    "type": payload["device_type"],
                    "usage": payload["usage"],
                    "material": payload["material"],
                    "controller_sensors": payload["controller_sensors"],
                },
                "reason": payload["reasons"][0]
                if payload["reasons"]
                else "No current warning signals",
            }
        )
    return {
        "building": {"id": building.id, "name": building.name, "location": building.location},
        "areas": areas,
    }


@app.get("/api/buildings/vantaa/areas/{area_id}/trends")
def area_trends(
    area_id: str,
    start_date: date | None = None,
    end_date: date | None = None,
) -> dict:
    if start_date and end_date and start_date > end_date:
        raise HTTPException(status_code=400, detail="start_date must be before end_date")
    building = load_vantaa_building(DATA_DIR)
    area = next((candidate for candidate in building.areas if candidate.id == area_id), None)
    if area is None:
        raise HTTPException(status_code=404, detail=f"Unknown area: {area_id}")
    readings = [
        reading
        for reading in area.readings
        if (start_date is None or reading.timestamp.date() >= start_date)
        and (end_date is None or reading.timestamp.date() <= end_date)
    ]
    filtered_area = area.model_copy(update={"readings": readings})
    weather = _weather(filtered_area)
    assessment = assess_area(filtered_area, weather)
    return {
        "area": {"id": area.id, "name": area.name, "kind": area.kind},
        "from": readings[0].timestamp.isoformat() if readings else None,
        "to": readings[-1].timestamp.isoformat() if readings else None,
        "trend_direction": assessment.trend,
        "weather_context": _weather_payload(weather),
        "readings": [reading.model_dump(mode="json") for reading in readings],
    }
