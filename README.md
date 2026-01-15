# Garmin Sync

A comprehensive Python application to fetch **all** health and fitness data from Garmin Connect. Designed for self-hosting with Docker, runs on a schedule and saves detailed daily health reports in both Markdown and JSON formats.

## Features

### Comprehensive Data Fetching
- **Daily Stats**: Steps, calories (total/active/BMR), distance, floors, active minutes
- **Heart Rate**: Resting, min, max HR + HR zones + all-day readings
- **HRV**: Heart rate variability with weekly average and status
- **Sleep**: Duration, sleep score, quality, deep/light/REM/awake breakdown
- **Stress**: Average/max stress levels, rest duration, stress timeline
- **Body Battery**: Energy levels throughout the day
- **SpO2 & Respiration**: Blood oxygen and breathing rate
- **Activities**: Full details including distance, pace, HR, elevation, cadence, training effect
- **Activity Details**: Splits, HR zones during activity, weather conditions, gear used
- **Training Status**: Readiness score, training load, recovery time
- **Performance**: VO2 max, fitness age, race predictions (5K, 10K, half marathon, marathon)
- **Body Composition**: Weight, BMI, body fat %, muscle mass
- **Hydration**: Daily intake vs goal

### Output Formats
- **Markdown reports** for human reading
- **JSON reports** with complete data for further processing/analysis

### Deployment Options
- Run locally with `uv`
- Schedule with Docker for automated daily reports

## Requirements

- Python 3.9+
- [uv](https://github.com/astral-sh/uv) package manager
- Docker & Docker Compose (for server deployment)
- Garmin Connect account

## Project Structure

```
garmin-sync/
├── main.py           # GarminClient class with comprehensive data fetching
├── scheduler.py      # Scheduled runner for daily reports
├── Dockerfile        # Container image definition
├── docker-compose.yml# Container orchestration
├── pyproject.toml    # Python dependencies
├── uv.lock           # Locked dependency versions
├── .env.example      # Example environment variables
└── data/             # Generated reports (gitignored)
    ├── report_YYYY-MM-DD.md   # Human-readable report
    └── report_YYYY-MM-DD.json # Full data export
```

## Quick Start (Local Development)

### 1. Clone the repository

```bash
git clone https://github.com/sagarsiwach/garmin-sync.git
cd garmin-sync
```

### 2. Install dependencies

```bash
uv sync
```

### 3. Configure credentials

```bash
cp .env.example .env
```

Edit `.env` with your Garmin Connect credentials:

```env
GARMIN_EMAIL=your@email.com
GARMIN_PASSWORD=your_password
REPORT_TIME=07:00
RUN_ON_STARTUP=true
INCLUDE_ACTIVITY_DETAILS=true
```

### 4. Run once (comprehensive report)

```bash
uv run python main.py
```

Example output:

```
============================================================
GARMIN COMPREHENSIVE HEALTH REPORT
============================================================

Fetching comprehensive Garmin data for 2025-01-15...
  - Fetching activities...
  - Fetching daily stats...
  - Fetching heart rate data...
  - Fetching sleep data...
  - Fetching stress & body battery...
  - Fetching training metrics...
Done!

# Garmin Health Report - 2025-01-15

## Daily Activity
- **Steps:** 8,234 / 7,500 goal
- **Distance:** 6.52 km
- **Calories:** 2,150 total (450 active)
- **Active Minutes:** 45
- **Floors Climbed:** 12 / 10 goal

## Heart Rate
- **Resting HR:** 62 bpm
- **Min HR:** 52 bpm
- **Max HR:** 165 bpm

## Sleep
- **Duration:** 7.2 hours
- **Sleep Score:** 82
- **Quality:** GOOD
- **Deep:** 55 min | **Light:** 210 min | **REM:** 95 min | **Awake:** 15 min

## Recent Activities
- **Morning Run** (running) - 21 min, 3.23 km, pace: 6:35/km, HR: 157 bpm
- **Evening Walk** (walking) - 22 min, 1.37 km, pace: 16:07/km, HR: 115 bpm

...

Markdown report saved to: data/report_2025-01-15.md
JSON report saved to: data/report_2025-01-15.json
```

### 5. Run scheduler (continuous)

```bash
uv run python scheduler.py
```

This will:
- Generate a comprehensive report immediately (if `RUN_ON_STARTUP=true`)
- Generate reports daily at the configured `REPORT_TIME`
- Save reports to `data/` as both `.md` and `.json` files

## Docker Deployment (Server)

### 1. Clone and configure

```bash
git clone https://github.com/sagarsiwach/garmin-sync.git
cd garmin-sync

# Create environment file
cat > .env << 'EOF'
GARMIN_EMAIL=your@email.com
GARMIN_PASSWORD=your_password
REPORT_TIME=07:00
RUN_ON_STARTUP=true
INCLUDE_ACTIVITY_DETAILS=true
EOF
```

### 2. Build and run

```bash
docker-compose up -d
```

### 3. Verify it's running

```bash
# Check container status
docker-compose ps

# View logs
docker-compose logs -f

# Check generated reports
ls -la data/
```

### 4. Management commands

```bash
# Stop the container
docker-compose down

# Restart
docker-compose restart

# Rebuild after code changes
docker-compose up -d --build

# Run a one-time fetch (without scheduler)
docker-compose run --rm garmin-sync uv run python main.py
```

## Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `GARMIN_EMAIL` | Your Garmin Connect email | - | Yes |
| `GARMIN_PASSWORD` | Your Garmin Connect password | - | Yes |
| `REPORT_TIME` | Time to generate daily report (24h format) | `07:00` | No |
| `RUN_ON_STARTUP` | Generate report when container starts | `true` | No |
| `INCLUDE_ACTIVITY_DETAILS` | Fetch detailed splits/HR zones for activities | `true` | No |

## API Usage (main.py)

```python
from main import GarminClient, format_report_markdown, export_report_json
from datetime import date

# Initialize client (logs in automatically)
client = GarminClient()

# Get comprehensive report with ALL data
report = client.get_comprehensive_report()
print(format_report_markdown(report))

# Or fetch specific data
stats = client.get_daily_stats()
hr = client.get_heart_rate_data()
sleep = client.get_sleep_data()
stress = client.get_stress_data()
battery = client.get_body_battery()
activities = client.get_activities(limit=10)

# Get detailed activity data (splits, HR zones, weather)
activity_details = client.get_activity_details(activity_id=12345678)

# Training metrics
readiness = client.get_training_readiness()
status = client.get_training_status()
predictions = client.get_race_predictions()
vo2max = client.get_max_metrics()

# Body composition
body = client.get_body_composition(days=30)
hydration = client.get_hydration()

# Weekly summary
weekly = client.get_weekly_summary()

# Export to JSON
export_report_json(report, "my_report.json")
```

## Available Data Methods

| Method | Description |
|--------|-------------|
| `get_daily_stats(day)` | Steps, calories, distance, floors, active minutes |
| `get_heart_rate_data(day)` | Resting/min/max HR, HR zones, all readings |
| `get_hrv_data(day)` | Heart rate variability |
| `get_sleep_data(day)` | Sleep duration, score, stages breakdown |
| `get_stress_data(day)` | Stress levels throughout the day |
| `get_body_battery(day)` | Energy levels |
| `get_respiration_data(day)` | Breathing rate |
| `get_spo2_data(day)` | Blood oxygen levels |
| `get_body_composition(days)` | Weight, BMI, body fat, muscle mass |
| `get_hydration(day)` | Water intake |
| `get_activities(limit)` | Recent activities list |
| `get_activity_details(id)` | Detailed activity with splits, HR zones, weather |
| `get_training_readiness(day)` | Training readiness score |
| `get_training_status(day)` | Training load and status |
| `get_endurance_score(day)` | Endurance score |
| `get_race_predictions()` | Predicted race times |
| `get_max_metrics(day)` | VO2 max, fitness age |
| `get_personal_records()` | Personal bests |
| `get_devices()` | Connected Garmin devices |
| `get_comprehensive_report(day)` | All data in one call |
| `get_weekly_summary()` | 7-day summary |

## Data Writing (Limited)

The Garmin API supports limited write operations:

| Data Type | Can Write? | Notes |
|-----------|------------|-------|
| Weight | Yes | Use `client.client.add_weigh_in()` |
| Activities | Yes | Upload FIT/GPX files |
| Hydration | No | Read-only |
| Diet/Nutrition | No | Not exposed by API |

## Troubleshooting

### "Login failed" or authentication errors

- Verify your email and password in `.env`
- Garmin may require MFA - try logging in via browser first
- The library may break if Garmin changes their auth flow - check [garminconnect issues](https://github.com/cyberjunky/python-garminconnect/issues)

### Container keeps restarting

```bash
# Check logs for errors
docker-compose logs garmin-sync
```

### No data for today

- Garmin syncs data from your watch periodically
- Today's data may be incomplete until your watch syncs
- Try syncing your watch via the Garmin Connect app

### Rate limiting

- The app limits detailed activity fetches to 5 per run
- If you see errors, Garmin may be rate-limiting requests
- Set `INCLUDE_ACTIVITY_DETAILS=false` for faster, simpler reports

## Security Notes

- Never commit `.env` to git (it's in `.gitignore`)
- Use strong, unique password for Garmin
- Consider using Docker secrets for production deployments

## License

MIT

## Credits

- [python-garminconnect](https://github.com/cyberjunky/python-garminconnect) - Unofficial Garmin Connect API client
