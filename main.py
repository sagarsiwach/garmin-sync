"""
Garmin Sync - Fetch and analyze data from Garmin Connect
"""

import os
from datetime import date, timedelta
from dotenv import load_dotenv
from garminconnect import Garmin

load_dotenv()


def get_client() -> Garmin:
    """Initialize and login to Garmin Connect"""
    email = os.getenv("GARMIN_EMAIL")
    password = os.getenv("GARMIN_PASSWORD")

    if not email or not password:
        raise ValueError("Set GARMIN_EMAIL and GARMIN_PASSWORD in .env file")

    client = Garmin(email, password)
    client.login()
    return client


def get_today_stats(client: Garmin) -> dict:
    """Get today's activity stats"""
    today = date.today().isoformat()
    return client.get_stats(today)


def get_heart_rate(client: Garmin, day: date = None) -> dict:
    """Get heart rate data for a specific day"""
    day = day or date.today()
    return client.get_heart_rates(day.isoformat())


def get_sleep(client: Garmin, day: date = None) -> dict:
    """Get sleep data for a specific day"""
    day = day or date.today()
    return client.get_sleep_data(day.isoformat())


def get_activities(client: Garmin, limit: int = 10) -> list:
    """Get recent activities"""
    return client.get_activities(0, limit)


def get_steps_weekly(client: Garmin) -> list:
    """Get steps for the last 7 days"""
    results = []
    for i in range(7):
        day = date.today() - timedelta(days=i)
        try:
            stats = client.get_stats(day.isoformat())
            results.append({
                "date": day.isoformat(),
                "steps": stats.get("totalSteps") or 0,
                "calories": stats.get("totalKilocalories") or 0,
                "distance_km": round((stats.get("totalDistanceMeters") or 0) / 1000, 2)
            })
        except Exception as e:
            print(f"Error fetching {day}: {e}")
    return results


if __name__ == "__main__":
    print("Connecting to Garmin...")
    client = get_client()
    print("Connected!\n")

    # Today's stats
    print("=== Today's Stats ===")
    stats = get_today_stats(client)
    print(f"Steps: {stats.get('totalSteps') or 0:,}")
    print(f"Calories: {stats.get('totalKilocalories') or 0:.0f}")
    distance = (stats.get('totalDistanceMeters') or 0) / 1000
    print(f"Distance: {distance:.2f} km")
    active_mins = (stats.get('activeSeconds') or 0) // 60
    print(f"Active Minutes: {active_mins}")
    print(f"Resting HR: {stats.get('restingHeartRate') or 'N/A'} bpm")

    # Recent activities
    print("\n=== Recent Activities ===")
    activities = get_activities(client, 5)
    for act in activities:
        name = act.get("activityName", "Unknown")
        act_type = act.get("activityType", {}).get("typeKey", "unknown")
        duration = (act.get("duration") or 0) / 60
        print(f"- {name} ({act_type}) - {duration:.0f} min")

    # Weekly steps
    print("\n=== Weekly Steps ===")
    weekly = get_steps_weekly(client)
    for day in weekly:
        print(f"{day['date']}: {day['steps']:,} steps, {day['distance_km']} km")
