# Garmin Health API

A FastAPI-based REST API for on-demand access to all Garmin Connect health and fitness data.

**No scheduling, no cron jobs** - just call the endpoints when you need data.

## Features

### Health Data Available

| Category | Data Points |
|----------|-------------|
| **Daily Stats** | Steps, calories (total/active/BMR), distance, floors, active minutes |
| **Heart Rate** | Resting/min/max HR, HR zones, all-day readings count |
| **HRV** | Heart rate variability, weekly average, status |
| **Sleep** | Duration, score, quality, deep/light/REM/awake breakdown, SpO2 |
| **Stress** | Average/max levels, time in each stress zone |
| **Body Battery** | Start/end energy levels |
| **SpO2 & Respiration** | Blood oxygen, breathing rate |
| **Activities** | Full list with distance, pace, HR, training effect |
| **Activity Details** | Per-activity splits, HR zones, weather, gear |
| **Training** | Readiness score, status, load, recovery time |
| **Performance** | VO2 max, fitness age, race predictions |
| **Body Composition** | Weight, BMI, body fat %, muscle mass |
| **Hydration** | Daily intake vs goal |
| **Devices** | Connected Garmin devices |

### API Design

- **RESTful endpoints** with clear naming
- **Pydantic models** for type-safe responses
- **OpenAPI/Swagger docs** at `/docs`
- **Date parameters** for historical data
- **Singleton client** for efficient Garmin connection

## Quick Start

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

Edit `.env`:

```env
GARMIN_EMAIL=your@email.com
GARMIN_PASSWORD=your_password
API_HOST=0.0.0.0
API_PORT=8000
```

### 4. Run the API server

```bash
uv run uvicorn api:app --host 0.0.0.0 --port 8000
```

### 5. Access the API

- **API Root:** http://localhost:8000/
- **Swagger Docs:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

## API Endpoints

### Health Reports

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API info and endpoint directory |
| `/health` | GET | Today's comprehensive health report |
| `/health/{date}` | GET | Health report for specific date |

### Sleep

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/sleep` | GET | Today's sleep data |
| `/sleep/{date}` | GET | Sleep data for specific date |

### Heart Rate & HRV

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/heart-rate` | GET | Today's heart rate and HRV |
| `/heart-rate/{date}` | GET | Heart rate for specific date |

### Stress & Energy

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/stress` | GET | Today's stress and body battery |
| `/stress/{date}` | GET | Stress for specific date |

### Activities

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/activities` | GET | Recent activities (use `?limit=N`, `?days=N`) |
| `/activities/{id}` | GET | Detailed activity with splits, HR zones, weather |

### Training & Performance

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/training` | GET | Training readiness, status, VO2 max, race predictions |

### Body & Hydration

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/body` | GET | Body composition (use `?days=N` for history) |
| `/hydration` | GET | Today's hydration data |
| `/hydration/{date}` | GET | Hydration for specific date |

### Summary & Devices

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/weekly` | GET | 7-day aggregated summary |
| `/devices` | GET | Connected Garmin devices |

### Utility

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/reconnect` | POST | Force re-authentication |

## Usage Examples

### Get Today's Health Report

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "report_date": "2026-01-16",
  "generated_at": "2026-01-16T09:30:00",
  "daily_stats": {
    "date": "2026-01-16",
    "steps": 8234,
    "goal_steps": 7500,
    "calories_total": 2150,
    "distance_km": 6.52
  },
  "sleep": {
    "duration_hours": 7.2,
    "sleep_score": 82,
    "deep_sleep_minutes": 55
  },
  "heart_rate": {
    "resting_hr": 62,
    "min_hr": 52,
    "max_hr": 145
  },
  ...
}
```

### Get Sleep Data for Specific Date

```bash
curl http://localhost:8000/sleep/2026-01-15
```

### Get Last 5 Activities

```bash
curl "http://localhost:8000/activities?limit=5"
```

### Get Activity Details with Splits

```bash
curl http://localhost:8000/activities/12345678
```

Response includes:
- Activity summary (distance, duration, pace, HR)
- Lap/split data with per-lap metrics
- Heart rate zones during activity
- Weather conditions
- Gear used

### Get Weekly Summary

```bash
curl http://localhost:8000/weekly
```

Response:
```json
{
  "period": "2026-01-10 to 2026-01-16",
  "total_steps": 52340,
  "avg_steps": 7477,
  "total_distance_km": 41.23,
  "avg_sleep_hours": 7.1,
  "avg_resting_hr": 61,
  "activity_count": 5,
  "daily_breakdown": [...]
}
```

## Docker Deployment

### Build and Run

```bash
# Create .env file
cat > .env << 'EOF'
GARMIN_EMAIL=your@email.com
GARMIN_PASSWORD=your_password
API_HOST=0.0.0.0
API_PORT=8000
EOF

# Build and start
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

### Docker Commands

```bash
# Rebuild after code changes
docker-compose up -d --build

# View real-time logs
docker-compose logs -f garmin-api

# Restart the service
docker-compose restart

# Check health
curl http://localhost:8000/
```

## Project Structure

```
garmin-sync/
├── api.py              # FastAPI application with all endpoints
├── main.py             # GarminClient class with data fetching methods
├── scheduler.py        # Legacy scheduled runner (optional)
├── pyproject.toml      # Python dependencies
├── uv.lock             # Locked dependency versions
├── Dockerfile          # Container image
├── docker-compose.yml  # Container orchestration
├── .env.example        # Example environment variables
├── .env                # Your credentials (gitignored)
└── data/               # Generated reports (gitignored)
```

## Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `GARMIN_EMAIL` | Garmin Connect email | - | Yes |
| `GARMIN_PASSWORD` | Garmin Connect password | - | Yes |
| `API_HOST` | Host to bind API server | `0.0.0.0` | No |
| `API_PORT` | Port for API server | `8000` | No |

## Response Models

All responses use Pydantic models for type safety. Key models:

### ComprehensiveReport
Complete health report with all data categories.

### SleepData
```python
{
    "date": "2026-01-16",
    "sleep_start": "2026-01-15T23:30:00",
    "sleep_end": "2026-01-16T06:45:00",
    "duration_hours": 7.25,
    "duration_minutes": 435,
    "deep_sleep_minutes": 55,
    "light_sleep_minutes": 210,
    "rem_sleep_minutes": 95,
    "awake_minutes": 15,
    "sleep_score": 82,
    "sleep_quality": "GOOD",
    "avg_spo2": 96.5,
    "avg_respiration": 14.2
}
```

### ActivityDetail
```python
{
    "activity_id": 12345678,
    "summary": {
        "name": "Morning Run",
        "type": "running",
        "duration_mins": 32.5,
        "distance_km": 5.23,
        "avg_pace_min_km": "6:13",
        "avg_hr": 155,
        "training_effect_aerobic": 3.2
    },
    "splits": [
        {"lap_number": 1, "distance_m": 1000, "duration_s": 372, "avg_hr": 148},
        {"lap_number": 2, "distance_m": 1000, "duration_s": 365, "avg_hr": 155}
    ],
    "hr_zones": [...],
    "weather": {"temperature": 24, "condition": "PARTLY_CLOUDY"},
    "gear": [{"name": "Nike Pegasus 40", "uuid": "..."}]
}
```

### WeeklySummary
Aggregated data with daily breakdown for the past 7 days.

## Error Handling

The API returns appropriate HTTP status codes:

| Code | Meaning |
|------|---------|
| 200 | Success |
| 400 | Bad request (e.g., invalid date format) |
| 404 | Resource not found (e.g., activity ID) |
| 500 | Server error |
| 503 | Garmin connection failed |

Error response format:
```json
{
    "detail": "Error message here"
}
```

## Troubleshooting

### Authentication Errors

```bash
# Force reconnect
curl -X POST http://localhost:8000/reconnect
```

### "Login failed"

- Verify email/password in `.env`
- Try logging into Garmin Connect web first
- Check if MFA is required

### Rate Limiting

The API caches the Garmin client connection. If you hit rate limits:
- Wait a few minutes
- Use `/reconnect` to reset the session

### No Data for Today

- Garmin data syncs from your watch periodically
- Today's data may be incomplete until watch syncs
- Sync via Garmin Connect app first

## Security Notes

- Never commit `.env` to git
- Use strong, unique password for Garmin
- Consider running behind a reverse proxy with auth for production
- The API exposes personal health data - secure accordingly

## Development

### Run with auto-reload

```bash
uv run uvicorn api:app --host 0.0.0.0 --port 8000 --reload
```

### Access Swagger UI

Open http://localhost:8000/docs for interactive API documentation.

## License

MIT

## Credits

- [python-garminconnect](https://github.com/cyberjunky/python-garminconnect) - Unofficial Garmin Connect API client
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
