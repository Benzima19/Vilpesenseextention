# VILPE Guardian API

All timestamps are local Vantaa time in ISO 8601 format. Sensor values are nullable when the source workbook has no reading.

## `GET /api/health`

Returns `{ "status": "ok", "version": "0.1.0" }`.

## `GET /api/buildings/vantaa/overview`

Returns the building summary and all seven monitored areas.

```json
{
  "building": { "id": "vantaa", "name": "VILPE Vantaa", "location": "Vantaa", "area_count": 7 },
  "overall_status": "healthy|attention|action_needed",
  "health_score": 0,
  "updated_at": "2026-09-11T05:32:13",
  "areas": []
}
```

Each area includes `id`, `name`, `kind`, device metadata, `latest_mould_index`, `latest_reading`, `status`, `health_score`, `reasons`, `trend`, `data_quality`, and nullable `weather_context`.

## `GET /api/buildings/vantaa/structure`

Returns the seven areas for the structure map. Each area contains:

```json
{
  "id": "katto-1",
  "name": "VILPE Vantaa, Katto 1",
  "kind": "roof|green_roof|crawl_space|unknown",
  "status": "healthy|attention|action_needed",
  "score": 0,
  "latest_reading": {},
  "device": {
    "serial": "N112741ZDLY",
    "type": "VILPE MCU-2",
    "usage": "Kattorakenteen tuuletus",
    "material": "Betoni",
    "controller_sensors": { "indoor": "...", "outdoor": "..." }
  },
  "reason": "Indoor humidity is high"
}
```

## `GET /api/buildings/vantaa/areas/{area_id}/trends`

Path IDs are the normalized area IDs, for example `katto-1` or `hallin-alapohja`.

Optional query parameters:

- `start_date=YYYY-MM-DD`
- `end_date=YYYY-MM-DD`

The response contains `area`, `from`, `to`, `trend_direction`, nullable `weather_context`, and `readings`. Each reading contains:

```json
{
  "timestamp": "2026-09-11T04:53:42",
  "indoor_temperature_c": 9.4,
  "indoor_relative_humidity_pct": 90.7,
  "indoor_absolute_humidity_g_m3": 9.0,
  "outdoor_temperature_c": 7.8,
  "outdoor_relative_humidity_pct": 97.5,
  "outdoor_absolute_humidity_g_m3": 8.0,
  "fan_rpm": 1725
}
```

`trend_direction` is `improving`, `stable`, or `worsening`. Date ranges with no readings return an empty `readings` array. An unknown area returns `404`; an invalid date range returns `400`.

## Weather context

Open-Meteo historical hourly data is fetched for Vantaa using temperature, relative humidity, precipitation, and dew point. It is returned as nullable `weather_context` and never replaces VILPE outdoor measurements. If Open-Meteo fails, the endpoint still returns VILPE data and `weather_context: null`.

Weather fields use `temperature_c`, `dew_point_c`, `relative_humidity_pct`, and `precipitation_mm`.
