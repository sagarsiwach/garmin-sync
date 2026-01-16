"""
Garmin Health API - On-Demand Health Data Access

A FastAPI application that provides instant access to all Garmin Connect health data.
No scheduling - just call the endpoints when you need data.

Endpoints:
    GET /                   - API info and available endpoints
    GET /health             - Today's comprehensive health report
    GET /health/{date}      - Health report for specific date
    GET /sleep              - Today's sleep data
    GET /sleep/{date}       - Sleep data for specific date
    GET /heart-rate         - Today's heart rate + HRV
    GET /heart-rate/{date}  - Heart rate for specific date
    GET /stress             - Today's stress + body battery
    GET /stress/{date}      - Stress for specific date
    GET /activities         - Recent activities list
    GET /activities/{id}    - Detailed activity data
    GET /training           - Training readiness and status
    GET /body               - Body composition data
    GET /weekly             - 7-day summary
    GET /devices            - Connected Garmin devices

Usage:
    # Run locally
    uv run uvicorn api:app --host 0.0.0.0 --port 8000

    # Or via Docker
    docker-compose up -d

    # Then call endpoints
    curl http://localhost:8000/health
    curl http://localhost:8000/sleep/2026-01-15
    curl http://localhost:8000/activities/12345678

Environment Variables:
    GARMIN_EMAIL: Your Garmin Connect email
    GARMIN_PASSWORD: Your Garmin Connect password
    API_HOST: Host to bind to (default: 0.0.0.0)
    API_PORT: Port to bind to (default: 8000)
"""

import os
from datetime import date, datetime, timedelta
from typing import Optional, List, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query, Path
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from main import GarminClient, format_report_markdown

load_dotenv()


# =============================================================================
# PYDANTIC MODELS - Response schemas for type safety and documentation
# =============================================================================

class APIInfo(BaseModel):
    """API information and available endpoints."""
    name: str = "Garmin Health API"
    version: str = "1.0.0"
    description: str = "On-demand access to Garmin Connect health data"
    endpoints: dict = Field(default_factory=dict)


class DailyStats(BaseModel):
    """Daily activity statistics."""
    date: str
    steps: int = 0
    goal_steps: int = 0
    calories_total: int = 0
    calories_active: int = 0
    calories_bmr: int = 0
    distance_meters: float = 0
    distance_km: float = 0
    active_minutes: int = 0
    intensity_minutes: int = 0
    floors_climbed: int = 0
    floors_goal: int = 0


class HeartRateData(BaseModel):
    """Heart rate metrics."""
    date: str
    resting_hr: Optional[int] = None
    min_hr: Optional[int] = None
    max_hr: Optional[int] = None
    avg_hr: Optional[int] = None
    hr_zones: List[dict] = Field(default_factory=list)
    hr_readings_count: int = 0


class HRVData(BaseModel):
    """Heart rate variability data."""
    date: str
    weekly_avg: Optional[float] = None
    last_night: Optional[float] = None
    status: Optional[str] = None
    baseline: Optional[str] = None


class SleepData(BaseModel):
    """Sleep analysis data."""
    date: str
    sleep_start: Optional[str] = None
    sleep_end: Optional[str] = None
    duration_hours: float = 0
    duration_minutes: int = 0
    deep_sleep_minutes: int = 0
    light_sleep_minutes: int = 0
    rem_sleep_minutes: int = 0
    awake_minutes: int = 0
    sleep_score: Optional[int] = None
    sleep_quality: Optional[str] = None
    avg_spo2: Optional[float] = None
    avg_respiration: Optional[float] = None
    hrv_status: Optional[str] = None


class StressData(BaseModel):
    """Stress metrics."""
    date: str
    avg_stress: Optional[int] = None
    max_stress: Optional[int] = None
    stress_duration_mins: int = 0
    rest_duration_mins: int = 0
    low_stress_mins: int = 0
    medium_stress_mins: int = 0
    high_stress_mins: int = 0


class BodyBatteryData(BaseModel):
    """Body battery / energy levels."""
    date: str
    start_level: Optional[int] = None
    end_level: Optional[int] = None
    current_level: Optional[int] = None
    charged: Optional[int] = None
    drained: Optional[int] = None


class StressAndEnergy(BaseModel):
    """Combined stress and body battery data."""
    stress: StressData
    body_battery: BodyBatteryData


class RespirationData(BaseModel):
    """Respiration / breathing data."""
    date: str
    avg_waking: Optional[float] = None
    highest: Optional[float] = None
    lowest: Optional[float] = None


class SpO2Data(BaseModel):
    """Blood oxygen data."""
    date: str
    avg_spo2: Optional[float] = None
    min_spo2: Optional[float] = None
    max_spo2: Optional[float] = None


class ActivitySummary(BaseModel):
    """Summary of a single activity."""
    id: Optional[int] = None
    name: Optional[str] = None
    type: Optional[str] = None
    start_time: Optional[str] = None
    duration_mins: float = 0
    distance_km: float = 0
    calories: Optional[int] = None
    avg_hr: Optional[int] = None
    max_hr: Optional[int] = None
    avg_speed_kmh: float = 0
    max_speed_kmh: float = 0
    avg_pace_min_km: Optional[str] = None
    elevation_gain_m: Optional[float] = None
    elevation_loss_m: Optional[float] = None
    avg_cadence: Optional[float] = None
    training_effect_aerobic: Optional[float] = None
    training_effect_anaerobic: Optional[float] = None
    vo2max: Optional[float] = None


class ActivityDetail(BaseModel):
    """Detailed activity data including splits and HR zones."""
    activity_id: int
    summary: ActivitySummary
    splits: List[dict] = Field(default_factory=list)
    split_summaries: dict = Field(default_factory=dict)
    hr_zones: List[dict] = Field(default_factory=list)
    weather: dict = Field(default_factory=dict)
    gear: List[dict] = Field(default_factory=list)


class TrainingReadiness(BaseModel):
    """Training readiness score."""
    date: str
    score: Optional[int] = None
    level: Optional[str] = None
    recovery_time_hrs: Optional[int] = None
    hrv_feedback: Optional[str] = None
    sleep_feedback: Optional[str] = None


class TrainingStatus(BaseModel):
    """Training status and load."""
    date: str
    training_status: Optional[str] = None
    training_status_message: Optional[str] = None
    load: Optional[float] = None
    load_focus: Optional[str] = None


class MaxMetrics(BaseModel):
    """VO2 Max and performance metrics."""
    date: str
    vo2max_running: Optional[float] = None
    vo2max_cycling: Optional[float] = None
    fitness_age: Optional[int] = None


class RacePredictions(BaseModel):
    """Race time predictions."""
    five_k: Optional[str] = Field(None, alias="5k")
    ten_k: Optional[str] = Field(None, alias="10k")
    half_marathon: Optional[str] = None
    marathon: Optional[str] = None

    class Config:
        populate_by_name = True


class EnduranceScore(BaseModel):
    """Endurance score."""
    date: str
    score: Optional[int] = None
    classification: Optional[str] = None


class TrainingData(BaseModel):
    """Combined training metrics."""
    readiness: TrainingReadiness
    status: TrainingStatus
    max_metrics: MaxMetrics
    race_predictions: RacePredictions
    endurance: EnduranceScore


class BodyComposition(BaseModel):
    """Body composition data."""
    period: str
    weight_kg: Optional[float] = None
    bmi: Optional[float] = None
    body_fat_pct: Optional[float] = None
    muscle_mass_kg: Optional[float] = None
    bone_mass_kg: Optional[float] = None
    body_water_pct: Optional[float] = None
    recent_measurements: List[dict] = Field(default_factory=list)


class HydrationData(BaseModel):
    """Hydration / water intake data."""
    date: str
    intake_ml: Optional[int] = None
    goal_ml: Optional[int] = None
    sweat_loss_ml: Optional[int] = None
    percentage_of_goal: Optional[float] = None


class DeviceInfo(BaseModel):
    """Garmin device information."""
    device_id: Optional[int] = None
    display_name: Optional[str] = None
    device_type: Optional[str] = None
    firmware_version: Optional[str] = None
    last_sync: Optional[str] = None


class ComprehensiveReport(BaseModel):
    """Complete health report with all data."""
    report_date: str
    generated_at: str
    daily_stats: DailyStats
    heart_rate: HeartRateData
    hrv: HRVData
    sleep: SleepData
    stress: StressData
    body_battery: BodyBatteryData
    respiration: RespirationData
    spo2: SpO2Data
    training_readiness: TrainingReadiness
    training_status: TrainingStatus
    max_metrics: MaxMetrics
    race_predictions: RacePredictions
    endurance: EnduranceScore
    body_composition: BodyComposition
    hydration: HydrationData
    activities: List[ActivitySummary] = Field(default_factory=list)
    devices: List[DeviceInfo] = Field(default_factory=list)
    markdown_report: str = ""


class WeeklySummary(BaseModel):
    """7-day summary."""
    period: str
    total_steps: int = 0
    avg_steps: int = 0
    total_distance_km: float = 0
    total_calories: int = 0
    avg_sleep_hours: float = 0
    avg_resting_hr: Optional[int] = None
    activity_count: int = 0
    daily_breakdown: List[dict] = Field(default_factory=list)


# =============================================================================
# GLOBAL CLIENT - Singleton pattern for Garmin connection
# =============================================================================

_garmin_client: Optional[GarminClient] = None


def get_client() -> GarminClient:
    """Get or create Garmin client singleton."""
    global _garmin_client
    if _garmin_client is None:
        try:
            _garmin_client = GarminClient()
        except Exception as e:
            raise HTTPException(
                status_code=503,
                detail=f"Failed to connect to Garmin: {str(e)}"
            )
    return _garmin_client


def reset_client():
    """Reset client (for re-authentication)."""
    global _garmin_client
    _garmin_client = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - initialize client on startup."""
    print("=" * 60)
    print("GARMIN HEALTH API")
    print("=" * 60)
    print(f"Starting at {datetime.now().isoformat()}")
    print(f"Email: {os.getenv('GARMIN_EMAIL', 'NOT SET')}")
    print("-" * 60)

    # Pre-initialize client on startup
    try:
        get_client()
        print("Garmin client initialized successfully")
    except Exception as e:
        print(f"Warning: Could not initialize Garmin client: {e}")
        print("Client will be initialized on first request")

    print("=" * 60)
    print("API ready. Available at http://0.0.0.0:8000")
    print("=" * 60)

    yield

    print("Shutting down Garmin Health API")


# =============================================================================
# FASTAPI APPLICATION
# =============================================================================

app = FastAPI(
    title="Garmin Health API",
    description="""
    On-demand access to all Garmin Connect health and fitness data.

    ## Features
    - Comprehensive health reports
    - Sleep analysis
    - Heart rate and HRV data
    - Stress and Body Battery
    - Activity tracking with detailed splits
    - Training metrics and race predictions
    - Body composition

    ## Usage
    Simply call any endpoint to get current data. Use date parameters (YYYY-MM-DD)
    for historical data.
    """,
    version="1.0.0",
    lifespan=lifespan,
)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def parse_date(date_str: str) -> date:
    """Parse date string (YYYY-MM-DD) to date object."""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid date format: {date_str}. Use YYYY-MM-DD"
        )


def safe_divide(a: Optional[float], b: Optional[float]) -> Optional[float]:
    """Safely divide two numbers."""
    if a is None or b is None or b == 0:
        return None
    return round(a / b, 2)


# =============================================================================
# API ENDPOINTS
# =============================================================================

@app.get("/", response_model=APIInfo, tags=["Info"])
async def root():
    """
    Get API information and list of available endpoints.

    Returns basic API info and a directory of all available endpoints
    with their descriptions.
    """
    return APIInfo(
        name="Garmin Health API",
        version="1.0.0",
        description="On-demand access to Garmin Connect health data",
        endpoints={
            "GET /": "This endpoint - API info",
            "GET /health": "Today's comprehensive health report",
            "GET /health/{date}": "Health report for specific date (YYYY-MM-DD)",
            "GET /sleep": "Today's sleep data",
            "GET /sleep/{date}": "Sleep data for specific date",
            "GET /heart-rate": "Today's heart rate and HRV",
            "GET /heart-rate/{date}": "Heart rate for specific date",
            "GET /stress": "Today's stress and body battery",
            "GET /stress/{date}": "Stress for specific date",
            "GET /activities": "Recent activities (use ?limit=N)",
            "GET /activities/{id}": "Detailed activity with splits, HR zones, weather",
            "GET /training": "Training readiness, status, VO2 max, race predictions",
            "GET /body": "Body composition (weight, BMI, body fat)",
            "GET /hydration": "Today's hydration data",
            "GET /hydration/{date}": "Hydration for specific date",
            "GET /weekly": "7-day summary",
            "GET /devices": "Connected Garmin devices",
            "POST /reconnect": "Force re-authentication with Garmin",
        }
    )


# -----------------------------------------------------------------------------
# COMPREHENSIVE HEALTH REPORT
# -----------------------------------------------------------------------------

@app.get("/health", response_model=ComprehensiveReport, tags=["Health"])
async def get_health_today(
    include_markdown: bool = Query(True, description="Include markdown-formatted report")
):
    """
    Get today's comprehensive health report.

    Returns ALL available health data for today including:
    - Daily stats (steps, calories, distance)
    - Heart rate and HRV
    - Sleep analysis
    - Stress and body battery
    - Recent activities
    - Training metrics
    - Body composition
    """
    return await get_health_by_date(date.today().isoformat(), include_markdown)


@app.get("/health/{report_date}", response_model=ComprehensiveReport, tags=["Health"])
async def get_health_by_date(
    report_date: str = Path(..., description="Date in YYYY-MM-DD format"),
    include_markdown: bool = Query(True, description="Include markdown-formatted report")
):
    """
    Get comprehensive health report for a specific date.

    Fetches all available health data for the specified date.
    """
    day = parse_date(report_date)
    client = get_client()

    try:
        # Fetch all data
        raw_report = client.get_comprehensive_report(day=day, include_activity_details=False)

        # Transform to response models
        stats = raw_report.get("daily_stats", {})
        hr = raw_report.get("heart_rate", {})
        hrv_raw = raw_report.get("hrv", {})
        hrv_summary = hrv_raw.get("hrv_summary", {})
        sleep_raw = raw_report.get("sleep", {})
        stress_raw = raw_report.get("stress", {})
        battery_raw = raw_report.get("body_battery", {})
        resp_raw = raw_report.get("respiration", {})
        spo2_raw = raw_report.get("spo2", {})
        readiness_raw = raw_report.get("training_readiness", {})
        status_raw = raw_report.get("training_status", {})
        metrics_raw = raw_report.get("max_metrics", {})
        predictions_raw = raw_report.get("race_predictions", {})
        endurance_raw = raw_report.get("endurance_score", {})
        body_raw = raw_report.get("body_composition", {})
        hydration_raw = raw_report.get("hydration", {})

        # Build response
        response = ComprehensiveReport(
            report_date=day.isoformat(),
            generated_at=datetime.now().isoformat(),

            daily_stats=DailyStats(
                date=day.isoformat(),
                steps=stats.get("steps", 0),
                goal_steps=stats.get("goal_steps", 0),
                calories_total=stats.get("calories_total", 0),
                calories_active=stats.get("calories_active", 0),
                calories_bmr=stats.get("calories_bmr", 0),
                distance_meters=stats.get("distance_meters", 0),
                distance_km=round(stats.get("distance_meters", 0) / 1000, 2),
                active_minutes=stats.get("active_minutes", 0),
                intensity_minutes=stats.get("intensity_minutes", 0),
                floors_climbed=stats.get("floors_climbed", 0),
                floors_goal=stats.get("floors_goal", 0),
            ),

            heart_rate=HeartRateData(
                date=day.isoformat(),
                resting_hr=hr.get("resting_hr"),
                min_hr=hr.get("min_hr"),
                max_hr=hr.get("max_hr"),
                avg_hr=hr.get("avg_hr"),
                hr_zones=hr.get("hr_zones", []),
                hr_readings_count=len(hr.get("hr_readings", [])),
            ),

            hrv=HRVData(
                date=day.isoformat(),
                weekly_avg=hrv_summary.get("weeklyAvg"),
                last_night=hrv_summary.get("lastNight"),
                status=hrv_summary.get("status"),
                baseline=hrv_raw.get("baseline"),
            ),

            sleep=SleepData(
                date=day.isoformat(),
                sleep_start=sleep_raw.get("sleep_start"),
                sleep_end=sleep_raw.get("sleep_end"),
                duration_hours=sleep_raw.get("duration_hours", 0),
                duration_minutes=int(sleep_raw.get("duration_hours", 0) * 60),
                deep_sleep_minutes=(sleep_raw.get("deep_sleep_seconds", 0) or 0) // 60,
                light_sleep_minutes=(sleep_raw.get("light_sleep_seconds", 0) or 0) // 60,
                rem_sleep_minutes=(sleep_raw.get("rem_sleep_seconds", 0) or 0) // 60,
                awake_minutes=(sleep_raw.get("awake_seconds", 0) or 0) // 60,
                sleep_score=sleep_raw.get("sleep_score"),
                sleep_quality=sleep_raw.get("sleep_quality"),
                avg_spo2=sleep_raw.get("avg_spo2"),
                avg_respiration=sleep_raw.get("avg_respiration"),
                hrv_status=sleep_raw.get("hrv_status"),
            ),

            stress=StressData(
                date=day.isoformat(),
                avg_stress=stress_raw.get("avg_stress"),
                max_stress=stress_raw.get("max_stress"),
                stress_duration_mins=stress_raw.get("stress_duration_mins", 0),
                rest_duration_mins=stress_raw.get("rest_duration_mins", 0),
                low_stress_mins=stress_raw.get("low_stress_mins", 0),
                medium_stress_mins=stress_raw.get("medium_stress_mins", 0),
                high_stress_mins=stress_raw.get("high_stress_mins", 0),
            ),

            body_battery=BodyBatteryData(
                date=day.isoformat(),
                start_level=battery_raw.get("start_level"),
                end_level=battery_raw.get("end_level"),
                current_level=battery_raw.get("end_level"),  # Use end as current
            ),

            respiration=RespirationData(
                date=day.isoformat(),
                avg_waking=resp_raw.get("avg_waking"),
                highest=resp_raw.get("highest"),
                lowest=resp_raw.get("lowest"),
            ),

            spo2=SpO2Data(
                date=day.isoformat(),
                avg_spo2=spo2_raw.get("avg_spo2"),
                min_spo2=spo2_raw.get("min_spo2"),
                max_spo2=spo2_raw.get("max_spo2"),
            ),

            training_readiness=TrainingReadiness(
                date=day.isoformat(),
                score=readiness_raw.get("score"),
                level=readiness_raw.get("level"),
                recovery_time_hrs=readiness_raw.get("recovery_time_hrs"),
                hrv_feedback=readiness_raw.get("hrv_feedback"),
                sleep_feedback=readiness_raw.get("sleep_feedback"),
            ),

            training_status=TrainingStatus(
                date=day.isoformat(),
                training_status=status_raw.get("training_status"),
                training_status_message=status_raw.get("training_status_message"),
                load=status_raw.get("load"),
                load_focus=status_raw.get("load_focus"),
            ),

            max_metrics=MaxMetrics(
                date=day.isoformat(),
                vo2max_running=metrics_raw.get("vo2max_running"),
                vo2max_cycling=metrics_raw.get("vo2max_cycling"),
                fitness_age=metrics_raw.get("fitness_age"),
            ),

            race_predictions=RacePredictions(
                five_k=predictions_raw.get("5k"),
                ten_k=predictions_raw.get("10k"),
                half_marathon=predictions_raw.get("half_marathon"),
                marathon=predictions_raw.get("marathon"),
            ),

            endurance=EnduranceScore(
                date=day.isoformat(),
                score=endurance_raw.get("score"),
                classification=endurance_raw.get("classification"),
            ),

            body_composition=BodyComposition(
                period=body_raw.get("period", ""),
                weight_kg=safe_divide(body_raw.get("weight_kg"), 1000),  # Convert g to kg
                bmi=body_raw.get("bmi"),
                body_fat_pct=body_raw.get("body_fat_pct"),
                muscle_mass_kg=safe_divide(body_raw.get("muscle_mass_kg"), 1000),
                bone_mass_kg=safe_divide(body_raw.get("bone_mass_kg"), 1000),
                body_water_pct=body_raw.get("body_water_pct"),
                recent_measurements=body_raw.get("measurements", [])[:5],
            ),

            hydration=HydrationData(
                date=day.isoformat(),
                intake_ml=hydration_raw.get("intake_ml"),
                goal_ml=hydration_raw.get("goal_ml"),
                sweat_loss_ml=hydration_raw.get("sweat_loss_ml"),
                percentage_of_goal=safe_divide(
                    hydration_raw.get("intake_ml"),
                    hydration_raw.get("goal_ml")
                ) * 100 if hydration_raw.get("intake_ml") and hydration_raw.get("goal_ml") else None,
            ),

            activities=[
                ActivitySummary(**act) for act in raw_report.get("activities", [])
            ],

            devices=[
                DeviceInfo(
                    device_id=d.get("deviceId"),
                    display_name=d.get("displayName"),
                    device_type=d.get("deviceTypeName"),
                    firmware_version=d.get("softwareVersion"),
                    last_sync=d.get("lastSyncTime"),
                )
                for d in raw_report.get("devices", [])
            ],

            markdown_report=format_report_markdown(raw_report) if include_markdown else "",
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch health data: {str(e)}")


# -----------------------------------------------------------------------------
# SLEEP
# -----------------------------------------------------------------------------

@app.get("/sleep", response_model=SleepData, tags=["Sleep"])
async def get_sleep_today():
    """Get today's sleep data."""
    return await get_sleep_by_date(date.today().isoformat())


@app.get("/sleep/{sleep_date}", response_model=SleepData, tags=["Sleep"])
async def get_sleep_by_date(
    sleep_date: str = Path(..., description="Date in YYYY-MM-DD format")
):
    """
    Get sleep data for a specific date.

    Returns detailed sleep analysis including:
    - Sleep duration and timing
    - Sleep stages (deep, light, REM, awake)
    - Sleep score and quality
    - SpO2 and respiration during sleep
    """
    day = parse_date(sleep_date)
    client = get_client()

    try:
        sleep_raw = client.get_sleep_data(day)

        return SleepData(
            date=day.isoformat(),
            sleep_start=sleep_raw.get("sleep_start"),
            sleep_end=sleep_raw.get("sleep_end"),
            duration_hours=sleep_raw.get("duration_hours", 0),
            duration_minutes=int(sleep_raw.get("duration_hours", 0) * 60),
            deep_sleep_minutes=(sleep_raw.get("deep_sleep_seconds", 0) or 0) // 60,
            light_sleep_minutes=(sleep_raw.get("light_sleep_seconds", 0) or 0) // 60,
            rem_sleep_minutes=(sleep_raw.get("rem_sleep_seconds", 0) or 0) // 60,
            awake_minutes=(sleep_raw.get("awake_seconds", 0) or 0) // 60,
            sleep_score=sleep_raw.get("sleep_score"),
            sleep_quality=sleep_raw.get("sleep_quality"),
            avg_spo2=sleep_raw.get("avg_spo2"),
            avg_respiration=sleep_raw.get("avg_respiration"),
            hrv_status=sleep_raw.get("hrv_status"),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch sleep data: {str(e)}")


# -----------------------------------------------------------------------------
# HEART RATE
# -----------------------------------------------------------------------------

class HeartRateResponse(BaseModel):
    """Combined heart rate and HRV response."""
    heart_rate: HeartRateData
    hrv: HRVData


@app.get("/heart-rate", response_model=HeartRateResponse, tags=["Heart"])
async def get_heart_rate_today():
    """Get today's heart rate and HRV data."""
    return await get_heart_rate_by_date(date.today().isoformat())


@app.get("/heart-rate/{hr_date}", response_model=HeartRateResponse, tags=["Heart"])
async def get_heart_rate_by_date(
    hr_date: str = Path(..., description="Date in YYYY-MM-DD format")
):
    """
    Get heart rate and HRV data for a specific date.

    Returns:
    - Resting, min, max heart rate
    - Heart rate zones
    - HRV (heart rate variability) metrics
    """
    day = parse_date(hr_date)
    client = get_client()

    try:
        hr_raw = client.get_heart_rate_data(day)
        hrv_raw = client.get_hrv_data(day)
        hrv_summary = hrv_raw.get("hrv_summary", {})

        return HeartRateResponse(
            heart_rate=HeartRateData(
                date=day.isoformat(),
                resting_hr=hr_raw.get("resting_hr"),
                min_hr=hr_raw.get("min_hr"),
                max_hr=hr_raw.get("max_hr"),
                avg_hr=hr_raw.get("avg_hr"),
                hr_zones=hr_raw.get("hr_zones", []),
                hr_readings_count=len(hr_raw.get("hr_readings", [])),
            ),
            hrv=HRVData(
                date=day.isoformat(),
                weekly_avg=hrv_summary.get("weeklyAvg"),
                last_night=hrv_summary.get("lastNight"),
                status=hrv_summary.get("status"),
                baseline=hrv_raw.get("baseline"),
            ),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch heart rate data: {str(e)}")


# -----------------------------------------------------------------------------
# STRESS & BODY BATTERY
# -----------------------------------------------------------------------------

@app.get("/stress", response_model=StressAndEnergy, tags=["Stress"])
async def get_stress_today():
    """Get today's stress and body battery data."""
    return await get_stress_by_date(date.today().isoformat())


@app.get("/stress/{stress_date}", response_model=StressAndEnergy, tags=["Stress"])
async def get_stress_by_date(
    stress_date: str = Path(..., description="Date in YYYY-MM-DD format")
):
    """
    Get stress and body battery data for a specific date.

    Returns:
    - Average and max stress levels
    - Time spent in each stress zone
    - Body battery levels throughout the day
    """
    day = parse_date(stress_date)
    client = get_client()

    try:
        stress_raw = client.get_stress_data(day)
        battery_raw = client.get_body_battery(day)

        return StressAndEnergy(
            stress=StressData(
                date=day.isoformat(),
                avg_stress=stress_raw.get("avg_stress"),
                max_stress=stress_raw.get("max_stress"),
                stress_duration_mins=stress_raw.get("stress_duration_mins", 0),
                rest_duration_mins=stress_raw.get("rest_duration_mins", 0),
                low_stress_mins=stress_raw.get("low_stress_mins", 0),
                medium_stress_mins=stress_raw.get("medium_stress_mins", 0),
                high_stress_mins=stress_raw.get("high_stress_mins", 0),
            ),
            body_battery=BodyBatteryData(
                date=day.isoformat(),
                start_level=battery_raw.get("start_level"),
                end_level=battery_raw.get("end_level"),
                current_level=battery_raw.get("end_level"),
            ),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch stress data: {str(e)}")


# -----------------------------------------------------------------------------
# ACTIVITIES
# -----------------------------------------------------------------------------

class ActivitiesResponse(BaseModel):
    """List of activities."""
    count: int
    activities: List[ActivitySummary]


@app.get("/activities", response_model=ActivitiesResponse, tags=["Activities"])
async def get_activities(
    limit: int = Query(10, ge=1, le=100, description="Number of activities to return"),
    days: Optional[int] = Query(None, ge=1, le=365, description="Filter to last N days")
):
    """
    Get list of recent activities.

    Returns activity summaries including:
    - Activity name and type
    - Duration, distance, pace
    - Heart rate stats
    - Training effect
    """
    client = get_client()

    try:
        if days:
            start = date.today() - timedelta(days=days)
            activities_raw = client.get_activities_by_date(start, date.today())
            activities_raw = activities_raw[:limit]
        else:
            activities_raw = client.get_activities(limit=limit)

        activities = [
            ActivitySummary(**client.get_activity_summary(act))
            for act in activities_raw
        ]

        return ActivitiesResponse(
            count=len(activities),
            activities=activities,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch activities: {str(e)}")


@app.get("/activities/{activity_id}", response_model=ActivityDetail, tags=["Activities"])
async def get_activity_detail(
    activity_id: int = Path(..., description="Activity ID")
):
    """
    Get detailed data for a specific activity.

    Returns comprehensive activity data including:
    - Activity summary (distance, duration, pace, HR)
    - Lap/split data with per-lap metrics
    - Heart rate zones during activity
    - Weather conditions
    - Gear used
    """
    client = get_client()

    try:
        # First get the activity to create summary
        activities = client.get_activities(limit=100)
        activity_raw = next(
            (a for a in activities if a.get("activityId") == activity_id),
            None
        )

        if not activity_raw:
            raise HTTPException(status_code=404, detail=f"Activity {activity_id} not found")

        summary = client.get_activity_summary(activity_raw)
        details = client.get_activity_details(activity_id)

        # Extract splits from details
        splits_data = details.get("splits", {})
        splits = []
        if isinstance(splits_data, dict):
            lap_list = splits_data.get("lapDTOs", [])
            for lap in lap_list:
                splits.append({
                    "lap_number": lap.get("lapIndex", 0) + 1,
                    "distance_m": lap.get("distance"),
                    "duration_s": lap.get("duration"),
                    "avg_hr": lap.get("averageHR"),
                    "max_hr": lap.get("maxHR"),
                    "avg_pace": lap.get("averageSpeed"),
                    "calories": lap.get("calories"),
                    "elevation_gain": lap.get("elevationGain"),
                })

        # Extract HR zones
        hr_zones = []
        hr_zones_data = details.get("hr_zones", {})
        if isinstance(hr_zones_data, list):
            hr_zones = hr_zones_data
        elif isinstance(hr_zones_data, dict):
            hr_zones = hr_zones_data.get("heartRateZones", [])

        return ActivityDetail(
            activity_id=activity_id,
            summary=ActivitySummary(**summary),
            splits=splits,
            split_summaries=details.get("split_summaries", {}),
            hr_zones=hr_zones,
            weather=details.get("weather", {}),
            gear=details.get("gear", []),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch activity details: {str(e)}")


# -----------------------------------------------------------------------------
# TRAINING
# -----------------------------------------------------------------------------

@app.get("/training", response_model=TrainingData, tags=["Training"])
async def get_training_data():
    """
    Get training metrics for today.

    Returns:
    - Training readiness score
    - Training status and load
    - VO2 max and fitness age
    - Race predictions (5K, 10K, half marathon, marathon)
    - Endurance score
    """
    day = date.today()
    client = get_client()

    try:
        readiness_raw = client.get_training_readiness(day)
        status_raw = client.get_training_status(day)
        metrics_raw = client.get_max_metrics(day)
        predictions_raw = client.get_race_predictions()
        endurance_raw = client.get_endurance_score(day)

        return TrainingData(
            readiness=TrainingReadiness(
                date=day.isoformat(),
                score=readiness_raw.get("score"),
                level=readiness_raw.get("level"),
                recovery_time_hrs=readiness_raw.get("recovery_time_hrs"),
                hrv_feedback=readiness_raw.get("hrv_feedback"),
                sleep_feedback=readiness_raw.get("sleep_feedback"),
            ),
            status=TrainingStatus(
                date=day.isoformat(),
                training_status=status_raw.get("training_status"),
                training_status_message=status_raw.get("training_status_message"),
                load=status_raw.get("load"),
                load_focus=status_raw.get("load_focus"),
            ),
            max_metrics=MaxMetrics(
                date=day.isoformat(),
                vo2max_running=metrics_raw.get("vo2max_running"),
                vo2max_cycling=metrics_raw.get("vo2max_cycling"),
                fitness_age=metrics_raw.get("fitness_age"),
            ),
            race_predictions=RacePredictions(
                five_k=predictions_raw.get("5k"),
                ten_k=predictions_raw.get("10k"),
                half_marathon=predictions_raw.get("half_marathon"),
                marathon=predictions_raw.get("marathon"),
            ),
            endurance=EnduranceScore(
                date=day.isoformat(),
                score=endurance_raw.get("score"),
                classification=endurance_raw.get("classification"),
            ),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch training data: {str(e)}")


# -----------------------------------------------------------------------------
# BODY COMPOSITION
# -----------------------------------------------------------------------------

@app.get("/body", response_model=BodyComposition, tags=["Body"])
async def get_body_composition(
    days: int = Query(30, ge=1, le=365, description="Number of days of history")
):
    """
    Get body composition data.

    Returns:
    - Current weight
    - BMI
    - Body fat percentage
    - Muscle mass
    - Bone mass
    - Body water percentage
    - Recent measurements history
    """
    client = get_client()

    try:
        body_raw = client.get_body_composition(days=days)

        return BodyComposition(
            period=body_raw.get("period", ""),
            weight_kg=safe_divide(body_raw.get("weight_kg"), 1000),
            bmi=body_raw.get("bmi"),
            body_fat_pct=body_raw.get("body_fat_pct"),
            muscle_mass_kg=safe_divide(body_raw.get("muscle_mass_kg"), 1000),
            bone_mass_kg=safe_divide(body_raw.get("bone_mass_kg"), 1000),
            body_water_pct=body_raw.get("body_water_pct"),
            recent_measurements=body_raw.get("measurements", [])[:10],
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch body composition: {str(e)}")


# -----------------------------------------------------------------------------
# HYDRATION
# -----------------------------------------------------------------------------

@app.get("/hydration", response_model=HydrationData, tags=["Hydration"])
async def get_hydration_today():
    """Get today's hydration data."""
    return await get_hydration_by_date(date.today().isoformat())


@app.get("/hydration/{hydration_date}", response_model=HydrationData, tags=["Hydration"])
async def get_hydration_by_date(
    hydration_date: str = Path(..., description="Date in YYYY-MM-DD format")
):
    """
    Get hydration data for a specific date.

    Returns:
    - Water intake
    - Daily goal
    - Sweat loss (if tracked)
    - Percentage of goal achieved
    """
    day = parse_date(hydration_date)
    client = get_client()

    try:
        hydration_raw = client.get_hydration(day)

        intake = hydration_raw.get("intake_ml")
        goal = hydration_raw.get("goal_ml")

        return HydrationData(
            date=day.isoformat(),
            intake_ml=intake,
            goal_ml=goal,
            sweat_loss_ml=hydration_raw.get("sweat_loss_ml"),
            percentage_of_goal=round((intake / goal) * 100, 1) if intake and goal else None,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch hydration data: {str(e)}")


# -----------------------------------------------------------------------------
# WEEKLY SUMMARY
# -----------------------------------------------------------------------------

@app.get("/weekly", response_model=WeeklySummary, tags=["Summary"])
async def get_weekly_summary():
    """
    Get 7-day health summary.

    Returns aggregated data for the past week:
    - Total and average steps
    - Total distance and calories
    - Average sleep duration
    - Average resting heart rate
    - Activity count
    - Daily breakdown
    """
    client = get_client()

    try:
        total_steps = 0
        total_distance = 0
        total_calories = 0
        total_sleep_hours = 0
        resting_hrs = []
        daily_breakdown = []

        for i in range(7):
            day = date.today() - timedelta(days=i)
            stats = client.get_daily_stats(day)
            sleep = client.get_sleep_data(day)
            hr = client.get_heart_rate_data(day)

            steps = stats.get("steps", 0)
            distance = stats.get("distance_meters", 0) / 1000
            calories = stats.get("calories_total", 0)
            sleep_hours = sleep.get("duration_hours", 0)
            resting_hr = hr.get("resting_hr")

            total_steps += steps
            total_distance += distance
            total_calories += calories
            total_sleep_hours += sleep_hours
            if resting_hr:
                resting_hrs.append(resting_hr)

            daily_breakdown.append({
                "date": day.isoformat(),
                "steps": steps,
                "distance_km": round(distance, 2),
                "calories": calories,
                "sleep_hours": round(sleep_hours, 1),
                "resting_hr": resting_hr,
            })

        # Get activity count for the week
        start = date.today() - timedelta(days=6)
        activities = client.get_activities_by_date(start, date.today())

        return WeeklySummary(
            period=f"{(date.today() - timedelta(days=6)).isoformat()} to {date.today().isoformat()}",
            total_steps=total_steps,
            avg_steps=total_steps // 7,
            total_distance_km=round(total_distance, 2),
            total_calories=total_calories,
            avg_sleep_hours=round(total_sleep_hours / 7, 1),
            avg_resting_hr=round(sum(resting_hrs) / len(resting_hrs)) if resting_hrs else None,
            activity_count=len(activities),
            daily_breakdown=daily_breakdown,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch weekly summary: {str(e)}")


# -----------------------------------------------------------------------------
# DEVICES
# -----------------------------------------------------------------------------

@app.get("/devices", response_model=List[DeviceInfo], tags=["Devices"])
async def get_devices():
    """
    Get list of connected Garmin devices.

    Returns information about all Garmin devices linked to your account.
    """
    client = get_client()

    try:
        devices_raw = client.get_devices()

        return [
            DeviceInfo(
                device_id=d.get("deviceId"),
                display_name=d.get("displayName"),
                device_type=d.get("deviceTypeName"),
                firmware_version=d.get("softwareVersion"),
                last_sync=d.get("lastSyncTime"),
            )
            for d in devices_raw
        ]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch devices: {str(e)}")


# -----------------------------------------------------------------------------
# UTILITY ENDPOINTS
# -----------------------------------------------------------------------------

@app.post("/reconnect", tags=["Utility"])
async def reconnect():
    """
    Force re-authentication with Garmin Connect.

    Use this if you're getting authentication errors or after changing credentials.
    """
    reset_client()
    try:
        get_client()
        return {"status": "success", "message": "Reconnected to Garmin Connect"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Failed to reconnect: {str(e)}")


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    import uvicorn

    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))

    print(f"Starting Garmin Health API on {host}:{port}")
    uvicorn.run(app, host=host, port=port)
