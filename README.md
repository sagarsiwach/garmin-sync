# Garmin Sync

A Python application to fetch health and fitness data from Garmin Connect. Designed for self-hosting with Docker, runs on a schedule and saves daily health reports.

## Features

- Fetches daily stats (steps, calories, distance, heart rate)
- Retrieves recent activities with duration
- Generates weekly step summaries
- Scheduled daily reports
- Docker-ready for server deployment
- Saves reports as Markdown files

## Requirements

- Python 3.9+
- [uv](https://github.com/astral-sh/uv) package manager
- Docker & Docker Compose (for server deployment)
- Garmin Connect account

## Project Structure

```
garmin-sync/
├── main.py           # Core functions to fetch Garmin data
├── scheduler.py      # Scheduled runner for daily reports
├── Dockerfile        # Container image definition
├── docker-compose.yml# Container orchestration
├── pyproject.toml    # Python dependencies
├── uv.lock           # Locked dependency versions
├── .env.example      # Example environment variables
└── data/             # Generated reports (gitignored)
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
```

### 4. Run once (manual fetch)

```bash
uv run main.py
```

Example output:

```
Connecting to Garmin...
Connected!

=== Today's Stats ===
Steps: 14,361
Calories: 2,150
Distance: 11.50 km
Active Minutes: 45
Resting HR: 79 bpm

=== Recent Activities ===
- Morning Walk (walking) - 22 min
- Evening Run (running) - 21 min

=== Weekly Steps ===
2025-01-14: 14,361 steps, 11.5 km
2025-01-13: 12,376 steps, 9.86 km
...
```

### 5. Run scheduler (continuous)

```bash
uv run scheduler.py
```

This will:
- Generate a report immediately (if `RUN_ON_STARTUP=true`)
- Generate reports daily at the configured `REPORT_TIME`
- Save reports to `data/report_YYYY-MM-DD.md`

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
docker-compose run --rm garmin-sync uv run main.py
```

## Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `GARMIN_EMAIL` | Your Garmin Connect email | - | Yes |
| `GARMIN_PASSWORD` | Your Garmin Connect password | - | Yes |
| `REPORT_TIME` | Time to generate daily report (24h format) | `07:00` | No |
| `RUN_ON_STARTUP` | Generate report when container starts | `true` | No |

## Data Fetched

### Daily Stats
- Total steps
- Total calories burned
- Total distance (km)
- Active minutes
- Resting heart rate

### Activities
- Activity name
- Activity type (running, walking, cycling, etc.)
- Duration

### Weekly Summary
- Steps per day for the last 7 days
- Distance per day
- Calorie trends

## Report Format

Reports are saved as Markdown files in `data/report_YYYY-MM-DD.md`:

```markdown
# Garmin Daily Report - 2025-01-14

## Today's Stats
- Steps: 14,361
- Calories: 2,150
- Distance: 11.50 km
- Resting HR: 79 bpm

## Recent Activities
- Morning Walk: 22 min
- Evening Run: 21 min

## Weekly Steps
- 2025-01-14: 14,361 steps
- 2025-01-13: 12,376 steps
...
```

## API Functions (main.py)

```python
from main import get_client, get_today_stats, get_activities, get_heart_rate, get_sleep

# Initialize client
client = get_client()

# Get today's stats
stats = get_today_stats(client)

# Get recent activities
activities = get_activities(client, limit=10)

# Get heart rate data
hr_data = get_heart_rate(client)

# Get sleep data
sleep_data = get_sleep(client)

# Get weekly steps summary
weekly = get_steps_weekly(client)
```

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

## Security Notes

- Never commit `.env` to git (it's in `.gitignore`)
- Use strong, unique password for Garmin
- Consider using Docker secrets for production deployments

## License

MIT

## Credits

- [python-garminconnect](https://github.com/cyberjunky/python-garminconnect) - Unofficial Garmin Connect API client
