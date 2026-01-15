"""
Garmin Sync - Comprehensive Garmin Connect Data Fetcher

This module provides functions to authenticate with Garmin Connect
and retrieve ALL available health/fitness data including:
- Daily stats (steps, calories, distance, heart rate)
- Detailed activity data (runs, workouts with splits, HR zones, pace)
- Heart rate and HRV data
- Sleep data and sleep scores
- Body composition and weight
- Stress and Body Battery
- Respiration and SpO2
- Training readiness and status
- Race predictions and endurance scores

Usage:
    from main import GarminClient

    client = GarminClient()
    report = client.get_comprehensive_report()
    print(report)

Environment Variables:
    GARMIN_EMAIL: Your Garmin Connect email address
    GARMIN_PASSWORD: Your Garmin Connect password
"""

import os
import json
from datetime import date, timedelta
from typing import Optional, Any
from dotenv import load_dotenv
from garminconnect import Garmin

load_dotenv()


class GarminClient:
    """Wrapper for Garmin Connect with comprehensive data fetching."""

    def __init__(self):
        """Initialize and login to Garmin Connect."""
        self.email = os.getenv("GARMIN_EMAIL")
        self.password = os.getenv("GARMIN_PASSWORD")

        if not self.email or not self.password:
            raise ValueError("Set GARMIN_EMAIL and GARMIN_PASSWORD in .env file")

        self.client = Garmin(self.email, self.password)
        self.client.login()

    def _safe_get(self, func, *args, **kwargs) -> Optional[Any]:
        """Safely call a Garmin API method, returning None on error."""
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(f"Warning: {func.__name__} failed: {e}")
            return None

    # ==================== DAILY STATS ====================

    def get_daily_stats(self, day: date = None) -> dict:
        """Get comprehensive daily statistics."""
        day = day or date.today()
        day_str = day.isoformat()

        stats = self._safe_get(self.client.get_stats, day_str) or {}
        steps_data = self._safe_get(self.client.get_steps_data, day_str) or []

        return {
            "date": day_str,
            "steps": stats.get("totalSteps") or 0,
            "goal_steps": stats.get("dailyStepGoal") or 0,
            "calories_total": stats.get("totalKilocalories") or 0,
            "calories_active": stats.get("activeKilocalories") or 0,
            "calories_bmr": stats.get("bmrKilocalories") or 0,
            "distance_meters": stats.get("totalDistanceMeters") or 0,
            "active_minutes": (stats.get("activeSeconds") or 0) // 60,
            "intensity_minutes": stats.get("intensityMinutesGoal") or 0,
            "floors_climbed": stats.get("floorsAscended") or 0,
            "floors_goal": stats.get("floorsGoal") or 0,
            "steps_data": steps_data,  # Detailed per-interval steps
        }

    def get_heart_rate_data(self, day: date = None) -> dict:
        """Get detailed heart rate data for a day."""
        day = day or date.today()
        day_str = day.isoformat()

        hr_data = self._safe_get(self.client.get_heart_rates, day_str) or {}
        rhr = self._safe_get(self.client.get_rhr_day, day_str) or {}

        return {
            "date": day_str,
            "resting_hr": hr_data.get("restingHeartRate"),
            "min_hr": hr_data.get("minHeartRate"),
            "max_hr": hr_data.get("maxHeartRate"),
            "avg_hr": rhr.get("value") if isinstance(rhr, dict) else None,
            "hr_zones": hr_data.get("heartRateZones", []),
            "hr_readings": hr_data.get("heartRateValues", []),  # Detailed HR over time
        }

    def get_hrv_data(self, day: date = None) -> dict:
        """Get Heart Rate Variability data."""
        day = day or date.today()
        hrv = self._safe_get(self.client.get_hrv_data, day.isoformat()) or {}
        return {
            "date": day.isoformat(),
            "hrv_summary": hrv.get("hrvSummary", {}),
            "hrv_values": hrv.get("hrvValues", []),
            "baseline": hrv.get("startTimestampLocal"),
        }

    # ==================== SLEEP ====================

    def get_sleep_data(self, day: date = None) -> dict:
        """Get comprehensive sleep data."""
        day = day or date.today()
        sleep = self._safe_get(self.client.get_sleep_data, day.isoformat()) or {}

        daily_sleep = sleep.get("dailySleepDTO", {})

        return {
            "date": day.isoformat(),
            "sleep_start": daily_sleep.get("sleepStartTimestampLocal"),
            "sleep_end": daily_sleep.get("sleepEndTimestampLocal"),
            "duration_seconds": daily_sleep.get("sleepTimeSeconds") or 0,
            "duration_hours": round((daily_sleep.get("sleepTimeSeconds") or 0) / 3600, 2),
            "deep_sleep_seconds": daily_sleep.get("deepSleepSeconds") or 0,
            "light_sleep_seconds": daily_sleep.get("lightSleepSeconds") or 0,
            "rem_sleep_seconds": daily_sleep.get("remSleepSeconds") or 0,
            "awake_seconds": daily_sleep.get("awakeSleepSeconds") or 0,
            "sleep_score": daily_sleep.get("sleepScores", {}).get("overall", {}).get("value"),
            "sleep_quality": daily_sleep.get("sleepScores", {}).get("qualityOfSleep", {}).get("qualifierKey"),
            "avg_spo2": daily_sleep.get("avgOxygenPercentage"),
            "avg_respiration": daily_sleep.get("avgRespirationValue"),
            "hrv_status": daily_sleep.get("hrvStatus"),
            "sleep_levels": sleep.get("sleepLevels", []),  # Detailed sleep stages over time
        }

    # ==================== STRESS & BODY BATTERY ====================

    def get_stress_data(self, day: date = None) -> dict:
        """Get stress data throughout the day."""
        day = day or date.today()
        day_str = day.isoformat()

        stress = self._safe_get(self.client.get_stress_data, day_str) or {}
        all_day_stress = self._safe_get(self.client.get_all_day_stress, day_str) or {}

        return {
            "date": day_str,
            "avg_stress": stress.get("avgStressLevel"),
            "max_stress": stress.get("maxStressLevel"),
            "stress_duration_mins": stress.get("stressDurationMinutes") or 0,
            "rest_duration_mins": stress.get("restDurationMinutes") or 0,
            "low_stress_mins": stress.get("lowStressDurationMinutes") or 0,
            "medium_stress_mins": stress.get("mediumStressDurationMinutes") or 0,
            "high_stress_mins": stress.get("highStressDurationMinutes") or 0,
            "stress_readings": all_day_stress,  # Detailed stress over time
        }

    def get_body_battery(self, day: date = None) -> dict:
        """Get Body Battery data."""
        day = day or date.today()
        battery = self._safe_get(self.client.get_body_battery, day.isoformat()) or []

        if battery and len(battery) > 0:
            return {
                "date": day.isoformat(),
                "readings": battery,
                "start_level": battery[0].get("bodyBatteryLevel") if battery else None,
                "end_level": battery[-1].get("bodyBatteryLevel") if battery else None,
            }
        return {"date": day.isoformat(), "readings": [], "start_level": None, "end_level": None}

    # ==================== RESPIRATION & SPO2 ====================

    def get_respiration_data(self, day: date = None) -> dict:
        """Get respiration data."""
        day = day or date.today()
        resp = self._safe_get(self.client.get_respiration_data, day.isoformat()) or {}
        return {
            "date": day.isoformat(),
            "avg_waking": resp.get("avgWakingRespirationValue"),
            "highest": resp.get("highestRespirationValue"),
            "lowest": resp.get("lowestRespirationValue"),
            "readings": resp.get("respirationValuesArray", []),
        }

    def get_spo2_data(self, day: date = None) -> dict:
        """Get SpO2 (blood oxygen) data."""
        day = day or date.today()
        spo2 = self._safe_get(self.client.get_spo2_data, day.isoformat()) or {}
        return {
            "date": day.isoformat(),
            "avg_spo2": spo2.get("avgValue"),
            "min_spo2": spo2.get("minValue"),
            "max_spo2": spo2.get("maxValue"),
            "readings": spo2.get("spo2Values", []),
        }

    # ==================== BODY COMPOSITION ====================

    def get_body_composition(self, days: int = 30) -> dict:
        """Get body composition data."""
        end = date.today()
        start = end - timedelta(days=days)

        body = self._safe_get(
            self.client.get_body_composition,
            start.isoformat(),
            end.isoformat()
        ) or {}

        return {
            "period": f"{start.isoformat()} to {end.isoformat()}",
            "weight_kg": body.get("weight"),
            "bmi": body.get("bmi"),
            "body_fat_pct": body.get("bodyFat"),
            "muscle_mass_kg": body.get("muscleMass"),
            "bone_mass_kg": body.get("boneMass"),
            "body_water_pct": body.get("bodyWater"),
            "measurements": body.get("dateWeightList", []),
        }

    def get_weigh_ins(self, days: int = 30) -> list:
        """Get weight entries."""
        end = date.today()
        start = end - timedelta(days=days)
        weigh_ins = self._safe_get(
            self.client.get_weigh_ins,
            start.isoformat(),
            end.isoformat()
        ) or {}
        return weigh_ins.get("dailyWeightSummaries", [])

    # ==================== ACTIVITIES ====================

    def get_activities(self, limit: int = 10) -> list:
        """Get list of recent activities."""
        return self._safe_get(self.client.get_activities, 0, limit) or []

    def get_activities_by_date(self, start: date, end: date = None) -> list:
        """Get activities within a date range."""
        end = end or date.today()
        return self._safe_get(
            self.client.get_activities_by_date,
            start.isoformat(),
            end.isoformat()
        ) or []

    def get_activity_details(self, activity_id: int) -> dict:
        """Get comprehensive details for a specific activity."""
        details = self._safe_get(self.client.get_activity_details, activity_id) or {}
        splits = self._safe_get(self.client.get_activity_splits, activity_id) or {}
        split_summaries = self._safe_get(self.client.get_activity_split_summaries, activity_id) or {}
        hr_zones = self._safe_get(self.client.get_activity_hr_in_timezones, activity_id) or {}
        weather = self._safe_get(self.client.get_activity_weather, activity_id) or {}
        gear = self._safe_get(self.client.get_activity_gear, activity_id) or []

        return {
            "activity_id": activity_id,
            "details": details,
            "splits": splits,
            "split_summaries": split_summaries,
            "hr_zones": hr_zones,
            "weather": weather,
            "gear": gear,
        }

    def get_activity_summary(self, activity: dict) -> dict:
        """Extract key metrics from an activity."""
        return {
            "id": activity.get("activityId"),
            "name": activity.get("activityName"),
            "type": activity.get("activityType", {}).get("typeKey"),
            "start_time": activity.get("startTimeLocal"),
            "duration_mins": round((activity.get("duration") or 0) / 60, 2),
            "distance_km": round((activity.get("distance") or 0) / 1000, 2),
            "calories": activity.get("calories"),
            "avg_hr": activity.get("averageHR"),
            "max_hr": activity.get("maxHR"),
            "avg_speed_kmh": round((activity.get("averageSpeed") or 0) * 3.6, 2),
            "max_speed_kmh": round((activity.get("maxSpeed") or 0) * 3.6, 2),
            "avg_pace_min_km": self._speed_to_pace(activity.get("averageSpeed")),
            "elevation_gain_m": activity.get("elevationGain"),
            "elevation_loss_m": activity.get("elevationLoss"),
            "avg_cadence": activity.get("averageRunningCadenceInStepsPerMinute"),
            "training_effect_aerobic": activity.get("aerobicTrainingEffect"),
            "training_effect_anaerobic": activity.get("anaerobicTrainingEffect"),
            "vo2max": activity.get("vO2MaxValue"),
        }

    def _speed_to_pace(self, speed_mps: float) -> Optional[str]:
        """Convert speed (m/s) to pace (min/km)."""
        if not speed_mps or speed_mps <= 0:
            return None
        pace_seconds = 1000 / speed_mps
        mins = int(pace_seconds // 60)
        secs = int(pace_seconds % 60)
        return f"{mins}:{secs:02d}"

    # ==================== TRAINING & PERFORMANCE ====================

    def get_training_readiness(self, day: date = None) -> dict:
        """Get training readiness score."""
        day = day or date.today()
        readiness = self._safe_get(self.client.get_training_readiness, day.isoformat()) or {}
        return {
            "date": day.isoformat(),
            "score": readiness.get("score"),
            "level": readiness.get("level"),
            "recovery_time_hrs": readiness.get("recoveryTime"),
            "hrv_feedback": readiness.get("hrvFeedback"),
            "sleep_feedback": readiness.get("sleepFeedback"),
        }

    def get_training_status(self, day: date = None) -> dict:
        """Get training status."""
        day = day or date.today()
        status = self._safe_get(self.client.get_training_status, day.isoformat()) or {}
        return {
            "date": day.isoformat(),
            "training_status": status.get("trainingStatus"),
            "training_status_message": status.get("trainingStatusMessage"),
            "load": status.get("load"),
            "load_focus": status.get("loadFocus"),
        }

    def get_endurance_score(self, day: date = None) -> dict:
        """Get endurance score."""
        day = day or date.today()
        score = self._safe_get(self.client.get_endurance_score, day.isoformat()) or {}
        return {
            "date": day.isoformat(),
            "score": score.get("overallScore"),
            "classification": score.get("classification"),
        }

    def get_race_predictions(self) -> dict:
        """Get race time predictions."""
        predictions = self._safe_get(self.client.get_race_predictions) or {}
        return {
            "5k": predictions.get("5k"),
            "10k": predictions.get("10k"),
            "half_marathon": predictions.get("halfMarathon"),
            "marathon": predictions.get("marathon"),
        }

    def get_max_metrics(self, day: date = None) -> dict:
        """Get VO2 Max and other max metrics."""
        day = day or date.today()
        metrics = self._safe_get(self.client.get_max_metrics, day.isoformat()) or {}
        return {
            "date": day.isoformat(),
            "vo2max_running": metrics.get("generic", {}).get("vo2MaxValue"),
            "vo2max_cycling": metrics.get("cycling", {}).get("vo2MaxValue"),
            "fitness_age": metrics.get("generic", {}).get("fitnessAge"),
        }

    def get_personal_records(self) -> dict:
        """Get personal records."""
        records = self._safe_get(self.client.get_personal_record) or {}
        return records

    # ==================== DEVICE INFO ====================

    def get_devices(self) -> list:
        """Get connected Garmin devices."""
        return self._safe_get(self.client.get_devices) or []

    def get_device_last_used(self) -> dict:
        """Get last used device info."""
        return self._safe_get(self.client.get_device_last_used) or {}

    # ==================== GOALS ====================

    def get_goals(self) -> dict:
        """Get user goals."""
        return self._safe_get(self.client.get_goals) or {}

    def get_hydration(self, day: date = None) -> dict:
        """Get hydration data."""
        day = day or date.today()
        hydration = self._safe_get(self.client.get_hydration_data, day.isoformat()) or {}
        return {
            "date": day.isoformat(),
            "intake_ml": hydration.get("valueInML"),
            "goal_ml": hydration.get("goalInML"),
            "sweat_loss_ml": hydration.get("sweatLossInML"),
        }

    # ==================== COMPREHENSIVE REPORT ====================

    def get_comprehensive_report(self, day: date = None, include_activity_details: bool = True) -> dict:
        """
        Get a comprehensive report with ALL available Garmin data.

        Args:
            day: Date to fetch data for (defaults to today)
            include_activity_details: Whether to fetch detailed splits/HR for activities

        Returns:
            dict: Comprehensive health and fitness report
        """
        day = day or date.today()

        print(f"Fetching comprehensive Garmin data for {day.isoformat()}...")

        # Get today's activities
        print("  - Fetching activities...")
        activities = self.get_activities(limit=10)
        activity_summaries = [self.get_activity_summary(a) for a in activities]

        # Get detailed activity data for today's activities if requested
        detailed_activities = []
        if include_activity_details:
            today_activities = [a for a in activities if a.get("startTimeLocal", "").startswith(day.isoformat())]
            for act in today_activities[:5]:  # Limit to 5 to avoid rate limits
                print(f"  - Fetching details for: {act.get('activityName')}...")
                detailed_activities.append(self.get_activity_details(act.get("activityId")))

        print("  - Fetching daily stats...")
        print("  - Fetching heart rate data...")
        print("  - Fetching sleep data...")
        print("  - Fetching stress & body battery...")
        print("  - Fetching training metrics...")

        report = {
            "report_date": day.isoformat(),
            "generated_at": date.today().isoformat(),

            # Daily Stats
            "daily_stats": self.get_daily_stats(day),

            # Heart Rate
            "heart_rate": self.get_heart_rate_data(day),
            "hrv": self.get_hrv_data(day),

            # Sleep
            "sleep": self.get_sleep_data(day),

            # Stress & Energy
            "stress": self.get_stress_data(day),
            "body_battery": self.get_body_battery(day),

            # Respiration & SpO2
            "respiration": self.get_respiration_data(day),
            "spo2": self.get_spo2_data(day),

            # Body Composition
            "body_composition": self.get_body_composition(days=30),

            # Activities
            "activities": activity_summaries,
            "activity_details": detailed_activities,

            # Training & Performance
            "training_readiness": self.get_training_readiness(day),
            "training_status": self.get_training_status(day),
            "endurance_score": self.get_endurance_score(day),
            "max_metrics": self.get_max_metrics(day),
            "race_predictions": self.get_race_predictions(),

            # Hydration
            "hydration": self.get_hydration(day),

            # Device Info
            "devices": self.get_devices(),
        }

        print("Done!")
        return report

    def get_weekly_summary(self) -> dict:
        """Get a summary of the past 7 days."""
        summaries = []
        for i in range(7):
            day = date.today() - timedelta(days=i)
            summaries.append({
                "date": day.isoformat(),
                "stats": self.get_daily_stats(day),
                "sleep": self.get_sleep_data(day),
            })

        return {
            "period": f"{(date.today() - timedelta(days=6)).isoformat()} to {date.today().isoformat()}",
            "daily_summaries": summaries,
        }


def format_report_markdown(report: dict) -> str:
    """Format a comprehensive report as Markdown."""
    lines = []

    lines.append(f"# Garmin Health Report - {report['report_date']}")
    lines.append("")

    # Daily Stats
    stats = report.get("daily_stats", {})
    lines.append("## Daily Activity")
    lines.append(f"- **Steps:** {stats.get('steps', 0):,} / {stats.get('goal_steps', 0):,} goal")
    lines.append(f"- **Distance:** {stats.get('distance_meters', 0) / 1000:.2f} km")
    lines.append(f"- **Calories:** {stats.get('calories_total', 0):,} total ({stats.get('calories_active', 0):,} active)")
    lines.append(f"- **Active Minutes:** {stats.get('active_minutes', 0)}")
    lines.append(f"- **Floors Climbed:** {stats.get('floors_climbed', 0)} / {stats.get('floors_goal', 0)} goal")
    lines.append("")

    # Heart Rate
    hr = report.get("heart_rate", {})
    lines.append("## Heart Rate")
    lines.append(f"- **Resting HR:** {hr.get('resting_hr') or 'N/A'} bpm")
    lines.append(f"- **Min HR:** {hr.get('min_hr') or 'N/A'} bpm")
    lines.append(f"- **Max HR:** {hr.get('max_hr') or 'N/A'} bpm")
    lines.append("")

    # HRV
    hrv = report.get("hrv", {})
    hrv_summary = hrv.get("hrv_summary", {})
    if hrv_summary:
        lines.append("## Heart Rate Variability")
        lines.append(f"- **Weekly Average:** {hrv_summary.get('weeklyAvg') or 'N/A'} ms")
        lines.append(f"- **Last Night:** {hrv_summary.get('lastNight') or 'N/A'} ms")
        lines.append(f"- **Status:** {hrv_summary.get('status') or 'N/A'}")
        lines.append("")

    # Sleep
    sleep = report.get("sleep", {})
    lines.append("## Sleep")
    lines.append(f"- **Duration:** {sleep.get('duration_hours', 0):.1f} hours")
    lines.append(f"- **Sleep Score:** {sleep.get('sleep_score') or 'N/A'}")
    lines.append(f"- **Quality:** {sleep.get('sleep_quality') or 'N/A'}")
    deep_mins = (sleep.get('deep_sleep_seconds', 0) or 0) // 60
    light_mins = (sleep.get('light_sleep_seconds', 0) or 0) // 60
    rem_mins = (sleep.get('rem_sleep_seconds', 0) or 0) // 60
    awake_mins = (sleep.get('awake_seconds', 0) or 0) // 60
    lines.append(f"- **Deep:** {deep_mins} min | **Light:** {light_mins} min | **REM:** {rem_mins} min | **Awake:** {awake_mins} min")
    lines.append("")

    # Stress & Body Battery
    stress = report.get("stress", {})
    battery = report.get("body_battery", {})
    lines.append("## Stress & Energy")
    lines.append(f"- **Avg Stress:** {stress.get('avg_stress') or 'N/A'}")
    lines.append(f"- **Rest Duration:** {stress.get('rest_duration_mins', 0)} min")
    lines.append(f"- **Body Battery:** {battery.get('start_level') or 'N/A'} → {battery.get('end_level') or 'N/A'}")
    lines.append("")

    # SpO2 & Respiration
    spo2 = report.get("spo2", {})
    resp = report.get("respiration", {})
    lines.append("## Respiration & Blood Oxygen")
    lines.append(f"- **SpO2:** {spo2.get('avg_spo2') or 'N/A'}% (min: {spo2.get('min_spo2') or 'N/A'}%, max: {spo2.get('max_spo2') or 'N/A'}%)")
    lines.append(f"- **Respiration:** {resp.get('avg_waking') or 'N/A'} breaths/min")
    lines.append("")

    # Training Readiness
    readiness = report.get("training_readiness", {})
    training = report.get("training_status", {})
    lines.append("## Training Status")
    lines.append(f"- **Readiness Score:** {readiness.get('score') or 'N/A'} ({readiness.get('level') or 'N/A'})")
    lines.append(f"- **Training Status:** {training.get('training_status') or 'N/A'}")
    lines.append(f"- **Recovery Time:** {readiness.get('recovery_time_hrs') or 'N/A'} hours")
    lines.append("")

    # Max Metrics
    metrics = report.get("max_metrics", {})
    predictions = report.get("race_predictions", {})
    lines.append("## Performance Metrics")
    lines.append(f"- **VO2 Max (Running):** {metrics.get('vo2max_running') or 'N/A'}")
    lines.append(f"- **Fitness Age:** {metrics.get('fitness_age') or 'N/A'}")
    if any(predictions.values()):
        lines.append("- **Race Predictions:**")
        if predictions.get("5k"):
            lines.append(f"  - 5K: {predictions['5k']}")
        if predictions.get("10k"):
            lines.append(f"  - 10K: {predictions['10k']}")
        if predictions.get("half_marathon"):
            lines.append(f"  - Half Marathon: {predictions['half_marathon']}")
        if predictions.get("marathon"):
            lines.append(f"  - Marathon: {predictions['marathon']}")
    lines.append("")

    # Activities
    activities = report.get("activities", [])
    if activities:
        lines.append("## Recent Activities")
        for act in activities[:10]:
            name = act.get("name", "Unknown")
            act_type = act.get("type", "unknown")
            duration = act.get("duration_mins", 0)
            distance = act.get("distance_km", 0)
            pace = act.get("avg_pace_min_km")
            hr = act.get("avg_hr")

            activity_line = f"- **{name}** ({act_type})"
            details = []
            if duration:
                details.append(f"{duration:.0f} min")
            if distance:
                details.append(f"{distance:.2f} km")
            if pace:
                details.append(f"pace: {pace}/km")
            if hr:
                details.append(f"HR: {hr} bpm")
            if details:
                activity_line += " - " + ", ".join(details)
            lines.append(activity_line)
        lines.append("")

    # Body Composition
    body = report.get("body_composition", {})
    if body.get("weight_kg"):
        lines.append("## Body Composition")
        lines.append(f"- **Weight:** {body.get('weight_kg', 0) / 1000:.1f} kg")
        if body.get("body_fat_pct"):
            lines.append(f"- **Body Fat:** {body.get('body_fat_pct'):.1f}%")
        if body.get("muscle_mass_kg"):
            lines.append(f"- **Muscle Mass:** {body.get('muscle_mass_kg') / 1000:.1f} kg")
        lines.append("")

    # Hydration
    hydration = report.get("hydration", {})
    if hydration.get("intake_ml"):
        lines.append("## Hydration")
        lines.append(f"- **Intake:** {hydration.get('intake_ml', 0)} ml / {hydration.get('goal_ml', 0)} ml goal")
        lines.append("")

    return "\n".join(lines)


def export_report_json(report: dict, filename: str = None) -> str:
    """Export report to JSON file."""
    if not filename:
        filename = f"data/report_{report['report_date']}.json"

    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, "w") as f:
        json.dump(report, f, indent=2, default=str)

    return filename


if __name__ == "__main__":
    print("=" * 60)
    print("GARMIN COMPREHENSIVE HEALTH REPORT")
    print("=" * 60)
    print()

    client = GarminClient()

    # Get comprehensive report
    report = client.get_comprehensive_report()

    # Format and print as Markdown
    markdown = format_report_markdown(report)
    print(markdown)

    # Save reports
    os.makedirs("data", exist_ok=True)

    # Save Markdown
    md_file = f"data/report_{date.today().isoformat()}.md"
    with open(md_file, "w") as f:
        f.write(markdown)
    print(f"\nMarkdown report saved to: {md_file}")

    # Save JSON (full data)
    json_file = export_report_json(report)
    print(f"JSON report saved to: {json_file}")
