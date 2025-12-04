#!/usr/bin/env python3
"""
Comprehensive Voting Data Ingestion Scheduler
Schedules and runs ingestion for all House and Senate voting data
"""

import argparse
import logging
import os
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, List

import psycopg2
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

# Import our ingestion scripts
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from parallel_votes_ingestion import ParallelVotesIngestor, IngestionConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class VotingDataScheduler:
    """Scheduler for comprehensive voting data ingestion"""

    def __init__(self, config: IngestionConfig):
        self.config = config
        self.scheduler = BackgroundScheduler()
        self.ingestor = ParallelVotesIngestor(config)
        self.conn = None

    def connect_db(self):
        """Establish database connection"""
        try:
            self.conn = psycopg2.connect(
                host=self.config.db_host,
                port=self.config.db_port,
                database=self.config.db_name,
                user=self.config.db_user,
                password=self.config.db_password,
            )
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise

    def setup_schedules(self):
        """Setup ingestion schedules"""

        # House Clerk - Daily at 2 AM for recent data
        self.scheduler.add_job(
            func=self.run_house_recent,
            trigger=CronTrigger(hour=2, minute=0),
            id="house_recent_daily",
            name="House Recent Votes Daily",
            replace_existing=True,
        )

        # House Clerk - Weekly historical data (Sundays at 3 AM)
        self.scheduler.add_job(
            func=self.run_house_historical,
            trigger=CronTrigger(day_of_week="sun", hour=3, minute=0),
            id="house_historical_weekly",
            name="House Historical Votes Weekly",
            replace_existing=True,
        )

        # Senate Clerk - Daily at 4 AM for recent data
        self.scheduler.add_job(
            func=self.run_senate_recent,
            trigger=CronTrigger(hour=4, minute=0),
            id="senate_recent_daily",
            name="Senate Recent Votes Daily",
            replace_existing=True,
        )

        # Senate Clerk - Weekly historical data (Sundays at 5 AM)
        self.scheduler.add_job(
            func=self.run_senate_historical,
            trigger=CronTrigger(day_of_week="sun", hour=5, minute=0),
            id="senate_historical_weekly",
            name="Senate Historical Votes Weekly",
            replace_existing=True,
        )

        # Full sync - Monthly on 1st at 1 AM
        self.scheduler.add_job(
            func=self.run_full_sync,
            trigger=CronTrigger(day=1, hour=1, minute=0),
            id="full_sync_monthly",
            name="Full Monthly Sync",
            replace_existing=True,
        )

        logger.info("Scheduled jobs configured:")
        for job in self.scheduler.get_jobs():
            logger.info(f"  - {job.name}: {job.trigger}")

    def run_house_recent(self):
        """Run recent House votes ingestion"""
        logger.info("Starting scheduled House recent votes ingestion")
        try:
            # Get current congress (118th as of 2024)
            current_congress = 118

            self.ingestor.run_parallel_ingestion(
                congresses=[current_congress], source_types=["house-clerk"]
            )

            self.log_schedule_run("house_recent_daily", "completed")

        except Exception as e:
            logger.error(f"House recent ingestion failed: {e}")
            self.log_schedule_run("house_recent_daily", "failed", str(e))

    def run_house_historical(self):
        """Run historical House votes ingestion"""
        logger.info("Starting scheduled House historical votes ingestion")
        try:
            # Ingest all historical congresses (113th-117th)
            historical_congresses = [113, 114, 115, 116, 117]

            self.ingestor.run_parallel_ingestion(
                congresses=historical_congresses, source_types=["house-clerk"]
            )

            self.log_schedule_run("house_historical_weekly", "completed")

        except Exception as e:
            logger.error(f"House historical ingestion failed: {e}")
            self.log_schedule_run("house_historical_weekly", "failed", str(e))

    def run_senate_recent(self):
        """Run recent Senate votes ingestion"""
        logger.info("Starting scheduled Senate recent votes ingestion")
        try:
            # Get current congress (118th as of 2024)
            current_congress = 118

            self.ingestor.run_parallel_ingestion(
                congresses=[current_congress], source_types=["senate-clerk"]
            )

            self.log_schedule_run("senate_recent_daily", "completed")

        except Exception as e:
            logger.error(f"Senate recent ingestion failed: {e}")
            self.log_schedule_run("senate_recent_daily", "failed", str(e))

    def run_senate_historical(self):
        """Run historical Senate votes ingestion"""
        logger.info("Starting scheduled Senate historical votes ingestion")
        try:
            # Ingest all historical congresses (113th-117th)
            historical_congresses = [113, 114, 115, 116, 117]

            self.ingestor.run_parallel_ingestion(
                congresses=historical_congresses, source_types=["senate-clerk"]
            )

            self.log_schedule_run("senate_historical_weekly", "completed")

        except Exception as e:
            logger.error(f"Senate historical ingestion failed: {e}")
            self.log_schedule_run("senate_historical_weekly", "failed", str(e))

    def run_full_sync(self):
        """Run full sync of all voting data"""
        logger.info("Starting scheduled full sync of all voting data")
        try:
            # All congresses (113th-118th)
            all_congresses = [113, 114, 115, 116, 117, 118]
            all_sources = ["house-clerk", "senate-clerk"]

            self.ingestor.run_parallel_ingestion(
                congresses=all_congresses, source_types=all_sources
            )

            self.log_schedule_run("full_sync_monthly", "completed")

        except Exception as e:
            logger.error(f"Full sync failed: {e}")
            self.log_schedule_run("full_sync_monthly", "failed", str(e))

    def log_schedule_run(self, schedule_name: str, status: str, error_message: str = None):
        """Log schedule run to database"""
        if not self.conn:
            self.connect_db()

        try:
            with self.conn.cursor() as cursor:
                # Update schedule record
                cursor.execute(
                    """
                    INSERT INTO monitoring.ingestion_schedules 
                    (schedule_name, script_name, source_type, schedule_pattern, is_active, 
                     last_run_time, run_count, success_count, failure_count)
                    VALUES (%s, %s, %s, %s, %s, %s, 1, %s, %s)
                    ON CONFLICT (schedule_name) DO UPDATE SET
                        last_run_time = EXCLUDED.last_run_time,
                        run_count = ingestion_schedules.run_count + 1,
                        success_count = CASE WHEN %s = 'completed' 
                                      THEN ingestion_schedules.success_count + 1 
                                      ELSE ingestion_schedules.success_count END,
                        failure_count = CASE WHEN %s = 'failed' 
                                      THEN ingestion_schedules.failure_count + 1 
                                      ELSE ingestion_schedules.failure_count END,
                        updated_at = NOW()
                """,
                    (
                        schedule_name,
                        "voting_scheduler.py",
                        "all",
                        self.get_schedule_pattern(schedule_name),
                        True,
                        datetime.now(),
                        1 if status == "completed" else 0,
                        1 if status == "failed" else 0,
                        status,
                        status,
                    ),
                )

                self.conn.commit()

        except Exception as e:
            logger.error(f"Failed to log schedule run: {e}")

    def get_schedule_pattern(self, schedule_name: str) -> str:
        """Get cron pattern for schedule name"""
        patterns = {
            "house_recent_daily": "0 2 * * *",
            "house_historical_weekly": "0 3 * * 0",
            "senate_recent_daily": "0 4 * * *",
            "senate_historical_weekly": "0 5 * * 0",
            "full_sync_monthly": "0 1 1 * *",
        }
        return patterns.get(schedule_name, "0 2 * * *")

    def start(self):
        """Start the scheduler"""
        self.setup_schedules()
        self.scheduler.start()
        logger.info("Voting data scheduler started")

    def stop(self):
        """Stop the scheduler"""
        self.scheduler.shutdown()
        logger.info("Voting data scheduler stopped")

    def run_immediate(self, job_type: str):
        """Run a specific job immediately"""
        logger.info(f"Running immediate job: {job_type}")

        jobs = {
            "house-recent": self.run_house_recent,
            "house-historical": self.run_house_historical,
            "senate-recent": self.run_senate_recent,
            "senate-historical": self.run_senate_historical,
            "full-sync": self.run_full_sync,
        }

        if job_type in jobs:
            jobs[job_type]()
        else:
            logger.error(f"Unknown job type: {job_type}")
            logger.info(f"Available job types: {list(jobs.keys())}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Voting data ingestion scheduler")
    parser.add_argument("--daemon", action="store_true", help="Run as daemon (continuous)")
    parser.add_argument(
        "--run",
        type=str,
        choices=[
            "house-recent",
            "house-historical",
            "senate-recent",
            "senate-historical",
            "full-sync",
        ],
        help="Run specific job immediately",
    )
    parser.add_argument("--workers", type=int, help="Number of parallel workers")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    config = IngestionConfig()
    if args.workers:
        config.max_workers = args.workers

    scheduler = VotingDataScheduler(config)

    try:
        if args.run:
            # Run specific job immediately
            scheduler.run_immediate(args.run)
        elif args.daemon:
            # Run as daemon
            scheduler.start()
            logger.info("Scheduler running in daemon mode. Press Ctrl+C to stop.")

            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                logger.info("Shutting down scheduler...")
                scheduler.stop()
        else:
            # Show available jobs
            logger.info("Available job types:")
            logger.info("  house-recent      - Recent House votes (current Congress)")
            logger.info("  house-historical  - Historical House votes (113th-117th Congress)")
            logger.info("  senate-recent      - Recent Senate votes (current Congress)")
            logger.info("  senate-historical  - Historical Senate votes (113th-117th Congress)")
            logger.info("  full-sync          - Full sync of all voting data")
            logger.info("")
            logger.info("Usage examples:")
            logger.info("  python3 voting_scheduler.py --run house-recent")
            logger.info("  python3 voting_scheduler.py --daemon")
            logger.info("  python3 voting_scheduler.py --run full-sync --workers 8")

    except Exception as e:
        logger.error(f"Scheduler failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
