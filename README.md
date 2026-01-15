# Garmin Sync

Fetch and sync health data from Garmin Connect. Runs on a schedule and saves daily reports.

## Quick Start (Local)

```bash
# Install dependencies
uv sync

# Set up credentials
cp .env.example .env
# Edit .env with your Garmin email/password

# Run once
uv run main.py

# Run scheduler (continuous)
uv run scheduler.py
```

## Docker Deployment

```bash
# Build and run
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GARMIN_EMAIL` | Your Garmin Connect email | required |
| `GARMIN_PASSWORD` | Your Garmin Connect password | required |
| `REPORT_TIME` | Time to generate daily report (24h) | `07:00` |
| `RUN_ON_STARTUP` | Generate report on container start | `true` |

## Data

Reports are saved to `./data/report_YYYY-MM-DD.md`

## What it fetches

- Daily steps, calories, distance
- Resting heart rate
- Recent activities
- Weekly step summary
