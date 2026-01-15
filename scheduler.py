"""
Scheduler - Runs Garmin sync on a schedule and saves daily health reports.

This module provides a long-running scheduler that:
1. Generates a health report immediately on startup (configurable)
2. Generates a daily report at a specified time
3. Saves reports as Markdown files to the data/ directory

Environment Variables:
    GARMIN_EMAIL: Your Garmin Connect email address
    GARMIN_PASSWORD: Your Garmin Connect password
    REPORT_TIME: Time to generate daily report in 24h format (default: "07:00")
    RUN_ON_STARTUP: Whether to generate report on startup (default: "true")

Usage:
    # Run directly
    python scheduler.py

    # Or via uv
    uv run scheduler.py

    # Or via Docker
    docker-compose up -d
"""

import os
import time
import schedule
from datetime import date, datetime
from main import get_client, get_today_stats, get_activities, get_steps_weekly, get_sleep


def generate_report() -> str:
    """
    Generate a daily health report from Garmin data.

    Fetches today's stats, recent activities, and weekly step summary.
    Saves the report as a Markdown file in data/report_YYYY-MM-DD.md.

    Returns:
        str: The generated report text, or empty string on error
    """
    print(f"\n[{datetime.now().isoformat()}] Generating report...")

    try:
        client = get_client()
        stats = get_today_stats(client)
        activities = get_activities(client, 5)
        weekly = get_steps_weekly(client)

        report = []
        report.append(f"# Garmin Daily Report - {date.today().isoformat()}")
        report.append("")
        report.append("## Today's Stats")
        report.append(f"- Steps: {stats.get('totalSteps') or 0:,}")
        report.append(f"- Calories: {stats.get('totalKilocalories') or 0:.0f}")
        report.append(f"- Distance: {(stats.get('totalDistanceMeters') or 0) / 1000:.2f} km")
        report.append(f"- Resting HR: {stats.get('restingHeartRate') or 'N/A'} bpm")
        report.append("")
        report.append("## Recent Activities")
        for act in activities[:5]:
            name = act.get("activityName", "Unknown")
            duration = (act.get("duration") or 0) / 60
            report.append(f"- {name}: {duration:.0f} min")
        report.append("")
        report.append("## Weekly Steps")
        for day in weekly:
            report.append(f"- {day['date']}: {day['steps']:,} steps")

        report_text = "\n".join(report)
        print(report_text)

        # Save to file
        os.makedirs("data", exist_ok=True)
        filename = f"data/report_{date.today().isoformat()}.md"
        with open(filename, "w") as f:
            f.write(report_text)
        print(f"Saved to {filename}")

        return report_text

    except Exception as e:
        print(f"Error generating report: {e}")
        return ""


def run_scheduler():
    """
    Start the scheduler loop.

    Schedules daily report generation at REPORT_TIME and optionally
    runs an immediate report on startup. Runs indefinitely, checking
    for pending tasks every 60 seconds.
    """
    run_time = os.getenv("REPORT_TIME", "07:00")

    print(f"Garmin Sync Scheduler Started")
    print(f"Will generate reports daily at {run_time}")
    print(f"Timezone: {time.tzname}")
    print("-" * 40)

    # Schedule daily report
    schedule.every().day.at(run_time).do(generate_report)

    # Also run once on startup
    if os.getenv("RUN_ON_STARTUP", "true").lower() == "true":
        generate_report()

    # Keep running
    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    run_scheduler()
