"""
Scheduler - Runs comprehensive Garmin sync on a schedule.

This module provides a long-running scheduler that:
1. Generates a comprehensive health report immediately on startup (configurable)
2. Generates a daily report at a specified time
3. Saves reports as both Markdown and JSON files to the data/ directory

Environment Variables:
    GARMIN_EMAIL: Your Garmin Connect email address
    GARMIN_PASSWORD: Your Garmin Connect password
    REPORT_TIME: Time to generate daily report in 24h format (default: "07:00")
    RUN_ON_STARTUP: Whether to generate report on startup (default: "true")
    INCLUDE_ACTIVITY_DETAILS: Whether to fetch detailed activity data (default: "true")

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
from main import GarminClient, format_report_markdown, export_report_json


def generate_comprehensive_report() -> str:
    """
    Generate a comprehensive daily health report from Garmin data.

    Fetches ALL available Garmin data including:
    - Daily stats (steps, calories, distance, floors)
    - Heart rate and HRV data
    - Sleep analysis
    - Stress and Body Battery
    - SpO2 and respiration
    - Detailed activity data with splits and HR zones
    - Training readiness and status
    - Race predictions and VO2 max
    - Body composition

    Saves the report as both Markdown and JSON files in data/ directory.

    Returns:
        str: The generated report text, or empty string on error
    """
    print(f"\n{'='*60}")
    print(f"[{datetime.now().isoformat()}] Generating comprehensive Garmin report...")
    print('='*60)

    try:
        # Initialize client
        client = GarminClient()

        # Check if we should include detailed activity data
        include_details = os.getenv("INCLUDE_ACTIVITY_DETAILS", "true").lower() == "true"

        # Get comprehensive report
        report = client.get_comprehensive_report(
            day=date.today(),
            include_activity_details=include_details
        )

        # Format as Markdown
        markdown = format_report_markdown(report)

        # Print to console
        print("\n" + markdown)

        # Save files
        os.makedirs("data", exist_ok=True)
        today = date.today().isoformat()

        # Save Markdown
        md_file = f"data/report_{today}.md"
        with open(md_file, "w") as f:
            f.write(markdown)
        print(f"\nMarkdown report saved to: {md_file}")

        # Save JSON (full data including detailed readings)
        json_file = export_report_json(report)
        print(f"JSON report saved to: {json_file}")

        print(f"\n[{datetime.now().isoformat()}] Report generation complete!")
        print('='*60)

        return markdown

    except Exception as e:
        print(f"Error generating report: {e}")
        import traceback
        traceback.print_exc()
        return ""


def run_scheduler():
    """
    Start the scheduler loop.

    Schedules comprehensive daily report generation at REPORT_TIME and optionally
    runs an immediate report on startup. Runs indefinitely, checking
    for pending tasks every 60 seconds.
    """
    run_time = os.getenv("REPORT_TIME", "07:00")
    run_on_startup = os.getenv("RUN_ON_STARTUP", "true").lower() == "true"

    print("="*60)
    print("GARMIN COMPREHENSIVE SYNC SCHEDULER")
    print("="*60)
    print(f"Report time: {run_time}")
    print(f"Run on startup: {run_on_startup}")
    print(f"Timezone: {time.tzname}")
    print(f"Include activity details: {os.getenv('INCLUDE_ACTIVITY_DETAILS', 'true')}")
    print("-" * 60)

    # Schedule daily report
    schedule.every().day.at(run_time).do(generate_comprehensive_report)

    # Run on startup if enabled
    if run_on_startup:
        generate_comprehensive_report()

    print(f"\nScheduler running. Next report at {run_time} daily.")
    print("Press Ctrl+C to stop.\n")

    # Keep running
    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    run_scheduler()
