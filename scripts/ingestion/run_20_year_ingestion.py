#!/usr/bin/env python3
"""
20-Year Bulk Data Ingestion Script for OpenDiscourse
Ingests data from 2005 to Present (Congresses 109-119)
Optimized for maximum speed using parallel processing and connection pooling.
"""

import os
import sys
import asyncio
import json
import time
import logging
import subprocess
import signal
import threading
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Any, Optional
from pathlib import Path
import psycopg2
from psycopg2 import pool
from dataclasses import dataclass
from enum import Enum

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

# Import resource manager for DB connection and env vars
try:
    from scripts.utils.resource_manager import get_db_connection, close_db_connection
except ImportError:
    # Fallback if running from a different context
    sys.path.append(str(PROJECT_ROOT / "scripts"))
    from utils.resource_manager import get_db_connection, close_db_connection

# Configure logging
LOG_DIR = PROJECT_ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / '20_year_ingestion.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("20YearIngestion")

class IngestionStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class IngestionJob:
    """Represents a single ingestion job"""
    job_id: str
    source: str
    command: List[str]
    status: IngestionStatus
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    process: Optional[subprocess.Popen] = None
    records_processed: int = 0
    error_message: Optional[str] = None

class BulkIngestionRunner:
    """Runner for 20-year bulk ingestion"""

    def __init__(self):
        self.base_path = str(PROJECT_ROOT)
        self.jobs: Dict[str, IngestionJob] = {}
        self.start_time = datetime.now()
        self.results = {
            "total_jobs": 0,
            "completed_jobs": 0,
            "failed_jobs": 0,
            "start_time": self.start_time.isoformat(),
            "sources": {
                "congress": {"jobs": [], "success": 0},
                "openstates": {"jobs": [], "success": 0},
                "govinfo": {"jobs": [], "success": 0}
            }
        }

        # Ensure results directory exists
        (PROJECT_ROOT / "ingestion_results").mkdir(exist_ok=True)

    def _create_jobs(self) -> List[IngestionJob]:
        """Create ingestion jobs for the 20-year period"""
        jobs = []

        # 1. Congress.gov Jobs (Congresses 109-119, approx 2005-2025)
        # Note: Congress 109 started Jan 2005
        congresses = range(109, 120)
        bill_types = ['hr', 's', 'hjres', 'sjres', 'hconres', 'sconres', 'hres', 'sres']

        for congress in congresses:
            # Members
            jobs.append(IngestionJob(
                job_id=f"congress_members_{congress}",
                source="congress",
                command=[
                    sys.executable, "scripts/ingestion/congress_cli.py",
                    "ingest-members",
                    "--congress", str(congress)
                ],
                status=IngestionStatus.PENDING
            ))

            # Bills (by type)
            for bill_type in bill_types:
                jobs.append(IngestionJob(
                    job_id=f"congress_bills_{congress}_{bill_type}",
                    source="congress",
                    command=[
                        sys.executable, "scripts/ingestion/congress_cli.py",
                        "ingest-bills",
                        "--congress", str(congress),
                        "--bill-type", bill_type
                    ],
                    status=IngestionStatus.PENDING
                ))

        # 2. OpenStates Jobs (20 years back)
        # We'll use the CLI's --years-back feature
        # For better parallelism, we can split by jurisdiction if needed,
        # but the CLI handles bulk ingestion well. Let's split by jurisdiction for robustness.
        states = [
            'al', 'ak', 'az', 'ar', 'ca', 'co', 'ct', 'de', 'fl', 'ga',
            'hi', 'id', 'il', 'in', 'ia', 'ks', 'ky', 'la', 'me', 'md',
            'ma', 'mi', 'mn', 'ms', 'mo', 'mt', 'ne', 'nv', 'nh', 'nj',
            'nm', 'ny', 'nc', 'nd', 'oh', 'ok', 'or', 'pa', 'ri', 'sc',
            'sd', 'tn', 'tx', 'ut', 'vt', 'va', 'wa', 'wv', 'wi', 'wy',
            'dc', 'pr'
        ]

        for state in states:
            # People/Legislators
            jobs.append(IngestionJob(
                job_id=f"openstates_people_{state}",
                source="openstates",
                command=[
                    sys.executable, "scripts/ingestion/openstates_cli.py",
                    "ingest-people",
                    "--jurisdiction", state
                ],
                status=IngestionStatus.PENDING
            ))

            # Bills (20 years)
            jobs.append(IngestionJob(
                job_id=f"openstates_bills_{state}",
                source="openstates",
                command=[
                    sys.executable, "scripts/ingestion/openstates_cli.py",
                    "ingest-bills",
                    "--jurisdiction", state,
                    "--years-back", "20"
                ],
                status=IngestionStatus.PENDING
            ))

        # 3. GovInfo Jobs (2005-Present)
        # Collections: BILLS, BILLSTATUS, CRPT, CHRG, FR, PLAW
        collections = ['BILLS', 'BILLSTATUS', 'CRPT', 'CHRG', 'FR', 'PLAW']
        start_date = "2005-01-01T00:00:00Z"

        for collection in collections:
            jobs.append(IngestionJob(
                job_id=f"govinfo_{collection}",
                source="govinfo",
                command=[
                    sys.executable, "scripts/ingestion/govinfo_cli.py",
                    "ingest-collection",
                    "--collection", collection,
                    "--start-date", start_date
                ],
                status=IngestionStatus.PENDING
            ))

        return jobs

    def _execute_job(self, job: IngestionJob) -> None:
        """Execute a single job"""
        try:
            job.status = IngestionStatus.RUNNING
            job.started_at = datetime.now()
            logger.info(f"🚀 Starting {job.job_id}")

            # Run process
            process = subprocess.run(
                job.command,
                cwd=self.base_path,
                capture_output=True,
                text=True
            )

            job.completed_at = datetime.now()

            if process.returncode == 0:
                job.status = IngestionStatus.COMPLETED
                logger.info(f"✅ Completed {job.job_id}")
            else:
                job.status = IngestionStatus.FAILED
                job.error_message = process.stderr[:1000] # Capture first 1000 chars of error
                logger.error(f"❌ Failed {job.job_id}: {job.error_message}")

        except Exception as e:
            job.status = IngestionStatus.FAILED
            job.error_message = str(e)
            logger.error(f"❌ Exception in {job.job_id}: {e}")

    def run(self, max_workers: int = 20):
        """Run all jobs in parallel"""
        logger.info(f"🚀 Starting 20-Year Bulk Ingestion with {max_workers} workers")

        all_jobs = self._create_jobs()
        self.jobs = {job.job_id: job for job in all_jobs}
        self.results["total_jobs"] = len(all_jobs)

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_job = {executor.submit(self._execute_job, job): job for job in all_jobs}

            completed_count = 0
            for future in as_completed(future_to_job):
                job = future_to_job[future]
                completed_count += 1

                if job.status == IngestionStatus.COMPLETED:
                    self.results["completed_jobs"] += 1
                    self.results["sources"][job.source]["success"] += 1
                else:
                    self.results["failed_jobs"] += 1

                progress = (completed_count / len(all_jobs)) * 100
                logger.info(f"📊 Progress: {progress:.1f}% ({completed_count}/{len(all_jobs)})")

        self._save_report()

    def _save_report(self):
        """Save final report"""
        end_time = datetime.now()
        duration = end_time - self.start_time

        report = f"""
# 20-Year Bulk Ingestion Report
Generated: {end_time}

## Summary
- Duration: {duration}
- Total Jobs: {self.results['total_jobs']}
- Completed: {self.results['completed_jobs']}
- Failed: {self.results['failed_jobs']}

## Source Breakdown
- Congress: {self.results['sources']['congress']['success']} successful jobs
- OpenStates: {self.results['sources']['openstates']['success']} successful jobs
- GovInfo: {self.results['sources']['govinfo']['success']} successful jobs

## Failed Jobs
"""
        for job in self.jobs.values():
            if job.status == IngestionStatus.FAILED:
                report += f"- {job.job_id}: {job.error_message}\n"

        report_path = PROJECT_ROOT / "ingestion_results" / f"20_year_report_{end_time.strftime('%Y%m%d_%H%M%S')}.md"
        with open(report_path, "w") as f:
            f.write(report)
        logger.info(f"📝 Report saved to {report_path}")

if __name__ == "__main__":
    runner = BulkIngestionRunner()
    runner.run()
