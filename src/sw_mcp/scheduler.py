"""Optional APScheduler for daily sync"""

import os
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz
from .swarfarm.client import SwarfarmClient
from .swarfarm.sync import sync_all
from .db.repo import SwarfarmRepository
from .db.engine import DB_URL


def run_daily_sync():
    """Run daily sync (called by scheduler)"""
    db_url = os.getenv("SW_MCP_DB_URL", DB_URL)
    rps = float(os.getenv("SW_MCP_HTTP_RPS", "2.0"))
    
    # Create tables if needed
    SwarfarmRepository.create_tables(db_url)
    
    client = SwarfarmClient(rps=rps)
    repo = SwarfarmRepository()
    
    try:
        sync_all(client, repo, enable_changelog=True, verbose=True)
    finally:
        client.close()
        repo.close()


def start_scheduler():
    """Start APScheduler for daily sync"""
    enable = os.getenv("SW_MCP_ENABLE_SCHEDULER", "0")
    if enable != "1":
        print("Scheduler disabled (set SW_MCP_ENABLE_SCHEDULER=1 to enable)")
        return
    
    schedule_hour = int(os.getenv("SW_MCP_SCHEDULE_HOUR", "4"))
    timezone = os.getenv("SW_MCP_SCHEDULE_TIMEZONE", "Asia/Seoul")
    
    scheduler = BlockingScheduler(timezone=pytz.timezone(timezone))
    
    # Daily at specified hour
    scheduler.add_job(
        run_daily_sync,
        trigger=CronTrigger(hour=schedule_hour, minute=0),
        id="swarfarm_daily_sync",
        name="SWARFARM Daily Sync",
    )
    
    print(f"Scheduler started: Daily sync at {schedule_hour}:00 {timezone}")
    print("Press Ctrl+C to stop")
    
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        print("Scheduler stopped")


if __name__ == "__main__":
    start_scheduler()


