# VILPE Guardian

**"Is my building OK?"** VILPE Guardian turns VILPE Sense moisture data into one clear answer per building area: **Healthy · Attention · Action needed**. Each answer comes with a plain-language reason, a weather-aware forecast and a recommended next step.

Built for the VILPE × Vaasa Hackathon 2026 (Junction).

## The idea

VILPE Sense already measures temperature, humidity, mould index and fan speed inside roofs and crawl spaces. Guardian adds the interpretation:

- **Understand:** compares each area with outdoor air, local weather and its own history. One humid reading is not a problem; a persistent pattern is.
- **Predict:** uses weather forecasts and each area's own drying behaviour to say what happens next.
- **Act:** recommends what to do, and later hands off to a contractor and verifies the repair.

Over time this becomes the building's **Structure Passport**: a trusted moisture-health history.

## Stack

React · TypeScript · Vercel · Postgres · Open-Meteo weather data

## Development

Requires [uv](https://docs.astral.sh/uv/) and Node 20+.

```bash
make install    # Python + web dependencies
make dev-api    # API on http://localhost:8000
make dev-web    # app on http://localhost:5173
make check      # lint, tests and build
```
