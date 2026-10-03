# VILPE Guardian

**"Is my building OK?"** VILPE Guardian turns VILPE Sense moisture data into one clear answer per building area: **Healthy · Monitor · Action needed**. Each answer comes with a plain-language reason, a weather-aware forecast and a recommended next step.

Built for the VILPE × Vaasa Hackathon 2026 (Junction).

## The idea

VILPE Sense already measures temperature, humidity, mould index and fan speed inside roofs and crawl spaces. Guardian adds the interpretation:

- **Understand:** compares each area with outdoor air, local weather and its own history. One humid reading is not a problem; a persistent pattern is.
- **Predict:** uses weather forecasts and each area's own drying behaviour to say what happens next.
- **Act:** recommends what to do, and later hands off to a contractor and verifies the repair.

Over time this becomes the building's **Structure Passport**: a trusted moisture-health history.

## Pilot site

VILPE Express Store, Vantaa: flat roof (Katto 1–4), green roof (Viherkatto 1–2), crawl space (Hallin alapohja), and 51 roof leak sensors.

## Docs

- [ARCHITECTURE.md](ARCHITECTURE.md): system design, data model, rules, API, UI
- [TASKS.md](TASKS.md): task-driven backlog and progress
- [brand/](brand/): VILPE logo and design tokens

## Stack

Vite · React · TypeScript · Tailwind · Recharts | Vercel Functions + Cron | Neon Postgres (Vercel Marketplace) | Open-Meteo | VILPE Sense public API
