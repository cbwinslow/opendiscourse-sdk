"""
================================================================================
File: bulk_ingest_all.py
Author: OpenDiscourse Contributors
Created: 2025-12-04
Last Modified: 2025-12-04
Version: 2.0.0

Description:
    Comprehensive bulk data ingestion orchestrator for all three data sources.
    Systematically ingests data from Congress.gov, OpenStates, and GovInfo
    using the existing CLI tools with progress tracking, error handling,
    and resume capability.

Dependencies:
    - subprocess: Run CLI commands
    - multiprocessing: Parallel execution
    - logging: Progress tracking
    - datetime: Timestamp tracking
    - json: State persistence

Usage:
    # Run full ingestion (all sources, all time)
    python3 scripts/ingestion/bulk_ingest_all.py --all

    # Run specific sources
    python3 scripts/ingestion/bulk_ingest_all.py --congress --years 5
    python3 scripts/ingestion/bulk_ingest_all.py --states --jurisdictions ca,ny,tx
    python3 scripts/ingestion/bulk_ingest_all.py --govinfo --collections BILLS,CREC

    # Resume from failure
    python3 scripts/ingestion/bulk_ingest_all.py --resume

Parameters:
    --all: Ingest from all sources
    --congress: Ingest Congress.gov data
    --states: Ingest OpenStates data
    --govinfo: Ingest GovInfo data
    --years: Number of years of historical data (default: 10)
    --congresses: Congress numbers to ingest (e.g., 115,116,117,118)
    --jurisdictions: State codes (e.g., ca,ny,tx)
    --collections: GovInfo collections (e.g., BILLS,CREC)
    --parallel: Number of parallel workers (default: 4)
    --resume: Resume from last checkpoint
    --dry-run: Test without making changes

Outputs:
    - Progress logs to logs/bulk_ingestion.log
    - State file at data/ingestion_state.json
    - Summary report when complete

Changelog:
    2025-12-04: Initial creation

Notes:
    - Automatically creates checkpoints for resume capability
    - Runs CLI tools as subprocesses
    - Tracks success/failure for each job
    - Generates comprehensive final report

================================================================================
"""

import argparse
import subprocess
import json
import logging
import sys
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from enum import Enum


# ============================================================================
# Configuration
# ============================================================================

# Congress numbers for historical data (last 10 congresses = ~20 years)
RECENT_CONGRESSES = list(range(109, 119))  # 109th (2005) through 118th (2023-2024)

# All US jurisdictions for OpenStates
ALL_JURISDICTIONS = [
    "al", "ak", "az", "ar", "ca", "co", "ct", "de", "fl", "ga",
    "hi", "id", "il", "in", "ia", "ks", "ky", "la", "me", "md",
    "ma", "mi", "mn", "ms", "mo", "mt", "ne", "nv", "nh", "nj",
    "nm", "ny", "nc", "nd", "oh", "ok", "or", "pa", "ri", "sc",
    "sd", "tn", "tx", "ut", "vt", "va", "wa", "wv", "wi", "wy",
    "dc", "pr"
]

# GovInfo collections to ingest
GOVINFO_COLLECTIONS = [
    "BILLS", "CREC", "FR", "CRPT", "CHRG", "CPRT",
    "PLAW", "STATUTE", "BILLSTATUS"
]

# Congress.gov endpoints to ingest
CONGRESS_ENDPOINTS = [
    "bills", "members", "committees", "votes",
    "bill-actions", "bill-cosponsors", "bill-subjects",
    "bill-titles", "bill-summaries", "related-bills",
    "committee-reports", "committee-prints", "hearings",
    "nominations", "treaties"
]


# ============================================================================
# Data Classes
# ============================================================================

class JobStatus(str, Enum):
    """Job execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class IngestionJob:
    """
    Represents a single ingestion job.

    Attributes:
        source: Data source (congress, openstates, govinfo)
        command: CLI command to execute
        description: Human-readable job description
        status: Current job status
        started_at: Job start timestamp
        completed_at: Job completion timestamp
        error: Error message if failed
        attempts: Number of execution attempts
    """
    source: str
    command: List[str]
    description: str
    status: JobStatus = JobStatus.PENDING
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error: Optional[str] = None
    attempts: int = 0

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


# ============================================================================
# Bulk Ingestion Orchestrator
# ============================================================================

class BulkIngestionOrchestrator:
    """
    Orchestrates bulk data ingestion across all three sources.

    Manages job creation, execution, progress tracking, error handling,
    and state persistence for resume capability.
    """

    def __init__(
        self,
        parallel_workers: int = 4,
        state_file: Path = Path("data/ingestion_state.json"),
        log_file: Path = Path("logs/bulk_ingestion.log"),
        dry_run: bool = False
    ):
        """
        Initialize orchestrator.

        Args:
            parallel_workers: Number of parallel jobs
            state_file: Path to state persistence file
            log_file: Path to log file
            dry_run: If True, don't actually run commands
        """
        self.parallel_workers = parallel_workers
        self.state_file = state_file
        self.log_file = log_file
        self.dry_run = dry_run

        # Ensure directories exist
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

        # Setup logging
        self._setup_logging()

        # Job tracking
        self.jobs: List[IngestionJob] = []
        self.stats = {
            "total": 0,
            "completed": 0,
            "failed": 0,
            "skipped": 0
        }

        self.logger.info("Bulk ingestion orchestrator initialized")

    def _setup_logging(self):
        """Configure logging to file and console."""
        # Create logger
        self.logger = logging.getLogger("BulkIngestion")
        self.logger.setLevel(logging.INFO)

        # File handler
        file_handler = logging.FileHandler(self.log_file)
        file_handler.setLevel(logging.DEBUG)
        file_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_format)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_format = logging.Formatter('%(levelname)s: %(message)s')
        console_handler.setFormatter(console_format)

        # Add handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    # ========================================================================
    # Job Creation
    # ========================================================================

    def create_congress_jobs(self, congresses: List[int]) -> List[IngestionJob]:
        """
        Create jobs for Congress.gov ingestion.

        Args:
            congresses: List of congress numbers to ingest

        Returns:
            List of ingestion jobs
        """
        jobs = []

        for congress in congresses:
            # Bills
            jobs.append(IngestionJob(
                source="congress",
                command=["python3", "scripts/ingestion/congress_cli.py", "ingest-bills", str(congress)],
                description=f"Congress {congress}: Bills"
            ))

            # Members
            jobs.append(IngestionJob(
                source="congress",
                command=["python3", "scripts/ingestion/congress_cli.py", "ingest-members", str(congress)],
                description=f"Congress {congress}: Members"
            ))

            # Committees
            jobs.append(IngestionJob(
                source="congress",
                command=["python3", "scripts/ingestion/congress_cli.py", "ingest-committees", str(congress)],
                description=f"Congress {congress}: Committees"
            ))

            # Votes
            jobs.append(IngestionJob(
                source="congress",
                command=["python3", "scripts/ingestion/congress_cli.py", "ingest-votes", str(congress)],
                description=f"Congress {congress}: Votes"
            ))

            # Bill details (composite jobs - run after bills)
            jobs.append(IngestionJob(
                source="congress",
                command=["python3", "scripts/ingestion/congress_cli.py", "ingest-bill-actions", str(congress)],
                description=f"Congress {congress}: Bill Actions"
            ))

            jobs.append(IngestionJob(
                source="congress",
                command=["python3", "scripts/ingestion/congress_cli.py", "ingest-bill-cosponsors", str(congress)],
                description=f"Congress {congress}: Bill Cosponsors"
            ))

            jobs.append(IngestionJob(
                source="congress",
                command=["python3", "scripts/ingestion/congress_cli.py", "ingest-bill-subjects", str(congress)],
                description=f"Congress {congress}: Bill Subjects"
            ))

            # Committee reports, prints, hearings
            jobs.append(IngestionJob(
                source="congress",
                command=["python3", "scripts/ingestion/congress_cli.py", "ingest-committee-reports", str(congress)],
                description=f"Congress {congress}: Committee Reports"
            ))

            jobs.append(IngestionJob(
                source="congress",
                command=["python3", "scripts/ingestion/congress_cli.py", "ingest-hearings", str(congress)],
                description=f"Congress {congress}: Hearings"
            ))

        self.logger.info(f"Created {len(jobs)} Congress.gov jobs for {len(congresses)} congresses")
        return jobs

    def create_openstates_jobs(self, jurisdictions: List[str], years_back: int = 5) -> List[IngestionJob]:
        """
        Create jobs for OpenStates ingestion.

        Args:
            jurisdictions: List of state codes
            years_back: Years of historical data

        Returns:
            List of ingestion jobs
        """
        jobs = []

        for jurisdiction in jurisdictions:
            # Bills
            jobs.append(IngestionJob(
                source="openstates",
                command=[
                    "python3", "scripts/ingestion/openstates_cli.py",
                    "ingest-bills", jurisdiction,
                    "--years-back", str(years_back)
                ],
                description=f"OpenStates {jurisdiction.upper()}: Bills ({years_back} years)"
            ))

            # People
            jobs.append(IngestionJob(
                source="openstates",
                command=["python3", "scripts/ingestion/openstates_cli.py", "ingest-people", jurisdiction],
                description=f"OpenStates {jurisdiction.upper()}: People"
            ))

            # Votes
            jobs.append(IngestionJob(
                source="openstates",
                command=[
                    "python3", "scripts/ingestion/openstates_cli.py",
                    "ingest-votes", jurisdiction,
                    "--years-back", str(years_back)
                ],
                description=f"OpenStates {jurisdiction.upper()}: Votes ({years_back} years)"
            ))

        self.logger.info(f"Created {len(jobs)} OpenStates jobs for {len(jurisdictions)} jurisdictions")
        return jobs

    def create_govinfo_jobs(self, collections: List[str]) -> List[IngestionJob]:
        """
        Create jobs for GovInfo ingestion.

        Args:
            collections: List of collection codes

        Returns:
            List of ingestion jobs
        """
        jobs = []

        # List collections
        jobs.append(IngestionJob(
            source="govinfo",
            command=["python3", "scripts/ingestion/govinfo_cli.py", "list-collections"],
            description="GovInfo: List Collections"
        ))

        # Ingest each collection
        for collection in collections:
            # Calculate date range (last 2 years for most collections)
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=730)).strftime("%Y-%m-%d")

            jobs.append(IngestionJob(
                source="govinfo",
                command=[
                    "python3", "scripts/ingestion/govinfo_cli.py",
                    "ingest-collection", collection,
                    "--start-date", start_date,
                    "--end-date", end_date
                ],
                description=f"GovInfo: {collection} collection (2 years)"
            ))

        self.logger.info(f"Created {len(jobs)} GovInfo jobs for {len(collections)} collections")
        return jobs

    # ========================================================================
    # Job Execution
    # ========================================================================

    def execute_job(self, job: IngestionJob) -> IngestionJob:
        """
        Execute a single ingestion job.

        Args:
            job: Job to execute

        Returns:
            Updated job with results
        """
        job.attempts += 1
        job.started_at = datetime.now().isoformat()
        job.status = JobStatus.RUNNING

        self.logger.info(f"Starting: {job.description}")

        if self.dry_run:
            self.logger.info(f"DRY RUN: {' '.join(job.command)}")
            time.sleep(1)  # Simulate work
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.now().isoformat()
            return job

        try:
            # Execute command
            result = subprocess.run(
                job.command,
                capture_output=True,
                text=True,
                timeout=3600  # 1 hour timeout
            )

            # Check result
            if result.returncode == 0:
                job.status = JobStatus.COMPLETED
                self.logger.info(f"✅ Completed: {job.description}")
            else:
                job.status = JobStatus.FAILED
                job.error = result.stderr[:500]  # First 500 chars of error
                self.logger.error(f"❌ Failed: {job.description} - {job.error}")

        except subprocess.TimeoutExpired:
            job.status = JobStatus.FAILED
            job.error = "Command timeout (1 hour)"
            self.logger.error(f"⏱️  Timeout: {job.description}")

        except Exception as e:
            job.status = JobStatus.FAILED
            job.error = str(e)
            self.logger.error(f"💥 Exception: {job.description} - {e}")

        finally:
            job.completed_at = datetime.now().isoformat()

        return job

    def run_all_jobs(self):
        """Execute all jobs with parallel execution."""
        if not self.jobs:
            self.logger.warning("No jobs to execute")
            return

        self.logger.info(f"Starting execution of {len(self.jobs)} jobs with {self.parallel_workers} workers")

        # Update stats
        self.stats["total"] = len(self.jobs)

        # Execute jobs in parallel
        with ThreadPoolExecutor(max_workers=self.parallel_workers) as executor:
            # Submit all jobs
            future_to_job = {executor.submit(self.execute_job, job): job for job in self.jobs}

            # Process completed jobs
            for future in as_completed(future_to_job):
                job = future_to_job[future]
                try:
                    updated_job = future.result()

                    # Update job in list
                    idx = self.jobs.index(job)
                    self.jobs[idx] = updated_job

                    # Update stats
                    if updated_job.status == JobStatus.COMPLETED:
                        self.stats["completed"] += 1
                    elif updated_job.status == JobStatus.FAILED:
                        self.stats["failed"] += 1

                    # Save state after each job
                    self.save_state()

                    # Log progress
                    progress = (self.stats["completed"] + self.stats["failed"]) / self.stats["total"] * 100
                    self.logger.info(f"Progress: {progress:.1f}% ({self.stats['completed']} completed, {self.stats['failed']} failed)")

                except Exception as e:
                    self.logger.error(f"Error processing job result: {e}")

        self.logger.info("All jobs completed")

    # ========================================================================
    # State Management
    # ========================================================================

    def save_state(self):
        """Save current state to file for resume capability."""
        state = {
            "timestamp": datetime.now().isoformat(),
            "stats": self.stats,
            "jobs": [job.to_dict() for job in self.jobs]
        }

        with open(self.state_file, 'w') as f:
            json.dump(state, f, indent=2)

    def load_state(self) -> bool:
        """
        Load state from file.

        Returns:
            True if state loaded successfully
        """
        if not self.state_file.exists():
            self.logger.info("No previous state file found")
            return False

        try:
            with open(self.state_file, 'r') as f:
                state = json.load(f)

            # Restore jobs
            self.jobs = [
                IngestionJob(**job_dict) if isinstance(job_dict.get('status'), str)
                else IngestionJob(**{**job_dict, 'status': JobStatus(job_dict['status'])})
                for job_dict in state['jobs']
            ]

            # Restore stats
            self.stats = state['stats']

            self.logger.info(f"Loaded state from {state['timestamp']}")
            self.logger.info(f"Found {len(self.jobs)} jobs ({self.stats['completed']} completed, {self.stats['failed']} failed)")

            return True

        except Exception as e:
            self.logger.error(f"Failed to load state: {e}")
            return False

    def get_pending_jobs(self) -> List[IngestionJob]:
        """Get jobs that haven't completed yet."""
        return [
            job for job in self.jobs
            if job.status in [JobStatus.PENDING, JobStatus.FAILED]
        ]

    # ========================================================================
    # Reporting
    # ========================================================================

    def print_summary(self):
        """Print execution summary."""
        print("\n" + "=" * 80)
        print("BULK INGESTION SUMMARY")
        print("=" * 80)
        print(f"\nTotal Jobs: {self.stats['total']}")
        print(f"✅ Completed: {self.stats['completed']}")
        print(f"❌ Failed: {self.stats['failed']}")
        print(f"⏭️  Skipped: {self.stats['skipped']}")

        # Success rate
        if self.stats['total'] > 0:
            success_rate = (self.stats['completed'] / self.stats['total']) * 100
            print(f"\n📊 Success Rate: {success_rate:.1f}%")

        # Failed jobs
        failed_jobs = [j for j in self.jobs if j.status == JobStatus.FAILED]
        if failed_jobs:
            print(f"\n❌ Failed Jobs ({len(failed_jobs)}):")
            for job in failed_jobs[:10]:  # Show first 10
                print(f"  - {job.description}")
                if job.error:
                    print(f"    Error: {job.error[:100]}")

        print("\n" + "=" * 80)


# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    """Main entry point for bulk ingestion."""
    parser = argparse.ArgumentParser(description="Bulk data ingestion orchestrator")

    # Source selection
    parser.add_argument('--all', action='store_true', help='Ingest from all sources')
    parser.add_argument('--congress', action='store_true', help='Ingest Congress.gov data')
    parser.add_argument('--states', action='store_true', help='Ingest OpenStates data')
    parser.add_argument('--govinfo', action='store_true', help='Ingest GovInfo data')

    # Configuration
    parser.add_argument('--years', type=int, default=10, help='Years of historical data')
    parser.add_argument('--congresses', help='Congress numbers (comma-separated, e.g., 116,117,118)')
    parser.add_argument('--jurisdictions', help='State codes (comma-separated, e.g., ca,ny,tx)')
    parser.add_argument('--collections', help='GovInfo collections (comma-separated)')

    # Execution options
    parser.add_argument('--parallel', type=int, default=4, help='Parallel workers')
    parser.add_argument('--resume', action='store_true', help='Resume from checkpoint')
    parser.add_argument('--dry-run', action='store_true', help='Test without executing')

    args = parser.parse_args()

    # Create orchestrator
    orchestrator = BulkIngestionOrchestrator(
        parallel_workers=args.parallel,
        dry_run=args.dry_run
    )

    # Resume from checkpoint if requested
    if args.resume:
        if orchestrator.load_state():
            pending = orchestrator.get_pending_jobs()
            print(f"Resuming with {len(pending)} pending jobs")
            orchestrator.jobs = pending
        else:
            print("No state to resume from")
            return
    else:
        # Create jobs based on arguments
        if args.all or args.congress:
            # Determine congresses
            if args.congresses:
                congresses = [int(c.strip()) for c in args.congresses.split(',')]
            else:
                # Last N years (2 congresses per year)
                num_congresses = min(args.years * 2, len(RECENT_CONGRESSES))
                congresses = RECENT_CONGRESSES[-num_congresses:]

            orchestrator.jobs.extend(orchestrator.create_congress_jobs(congresses))

        if args.all or args.states:
            # Determine jurisdictions
            if args.jurisdictions:
                jurisdictions = [j.strip().lower() for j in args.jurisdictions.split(',')]
            else:
                jurisdictions = ALL_JURISDICTIONS

            orchestrator.jobs.extend(orchestrator.create_openstates_jobs(jurisdictions, args.years))

        if args.all or args.govinfo:
            # Determine collections
            if args.collections:
                collections = [c.strip().upper() for c in args.collections.split(',')]
            else:
                collections = GOVINFO_COLLECTIONS

            orchestrator.jobs.extend(orchestrator.create_govinfo_jobs(collections))

    # Execute all jobs
    if orchestrator.jobs:
        orchestrator.run_all_jobs()
        orchestrator.print_summary()
    else:
        print("No jobs created. Use --all, --congress, --states, or --govinfo")


if __name__ == "__main__":
    main()
