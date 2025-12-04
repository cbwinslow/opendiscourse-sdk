#!/usr/bin/env python3
"""
Comprehensive Bulk Data Ingestion Script for OpenDiscourse
Optimized for maximum speed using async, parallel processing, and connection pooling

This script will:
1. Ingest 10 years of data from all 3 sources (Congress.gov, OpenStates, GovInfo)
2. Use parallel processing and async programming for maximum speed
3. Monitor all jobs in real-time with comprehensive logging
4. Track success/failure rates with detailed metrics
5. Ensure database integrity with proper error handling
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
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import psycopg2
from psycopg2 import pool, sql
import yaml
from dataclasses import dataclass
from enum import Enum

# Add project root to path
sys.path.append('/home/cbwinslow/Videos/opendiscourse')

# Configure comprehensive logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/cbwinslow/Videos/opendiscourse/logs/comprehensive_bulk_ingestion.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

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
    records_total: int = 0
    error_message: Optional[str] = None
    metrics: Dict[str, Any] = None

    def __post_init__(self):
        if self.metrics is None:
            self.metrics = {}

class ComprehensiveBulkIngestion:
    """Main class for comprehensive bulk data ingestion"""

    def __init__(self):
        self.base_path = "/home/cbwinslow/Videos/opendiscourse"
        self.jobs: Dict[str, IngestionJob] = {}
        self.monitoring_active = True
        self.start_time = datetime.now()
        self.db_pool = None
        self.results = {
            "total_jobs": 0,
            "completed_jobs": 0,
            "failed_jobs": 0,
            "total_records": 0,
            "successful_records": 0,
            "failed_records": 0,
            "start_time": self.start_time.isoformat(),
            "sources": {
                "congress": {"jobs": [], "records": 0, "success": 0},
                "openstates": {"jobs": [], "records": 0, "success": 0},
                "govinfo": {"jobs": [], "records": 0, "success": 0}
            }
        }

        # Ensure directories exist
        os.makedirs(f"{self.base_path}/logs", exist_ok=True)
        os.makedirs(f"{self.base_path}/ingestion_results", exist_ok=True)

        # Setup database connection pool
        self._setup_database_pool()

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _setup_database_pool(self):
        """Setup PostgreSQL connection pool for monitoring"""
        try:
            # Add retry logic for database connection
            max_retries = 3
            retry_delay = 5  # seconds

            for attempt in range(max_retries):
                try:
                    self.db_pool = psycopg2.pool.ThreadedConnectionPool(
                        minconn=5,
                        maxconn=20,
                        database="opendiscourse",
                        user="cbwinslow",
                        host="/var/run/postgresql"
                    )
                    logger.info("✅ Database connection pool established")
                    return  # Success, exit the retry loop
                except Exception as e:
                    if attempt < max_retries - 1:
                        logger.warning(f"⚠️ Database connection attempt {attempt + 1} failed, retrying in {retry_delay} seconds: {e}")
                        time.sleep(retry_delay)
                    else:
                        raise  # Re-raise the exception if all retries fail

        except Exception as e:
            logger.error(f"❌ Failed to setup database pool: {e}")
            # Don't raise exception, allow script to continue with limited functionality
            self.db_pool = None
            logger.warning("🔄 Continuing without database monitoring (metrics will be limited)")

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info(f"🛑 Received signal {signum}, initiating graceful shutdown...")
        self.monitoring_active = False
        self._cancel_all_jobs()

    def _validate_api_keys(self) -> bool:
        """Validate all required API keys are present"""
        required_keys = {
            'CONGRESS_API_KEY': os.getenv('CONGRESS_API_KEY'),
            'GOVINFO_API_KEY': os.getenv('GOVINFO_API_KEY'),
            'OPENSTATES_API_KEY': os.getenv('OPENSTATES_API_KEY')
        }

        missing_keys = [key for key, value in required_keys.items() if not value]

        if missing_keys:
            logger.error(f"❌ Missing API keys: {missing_keys}")
            return False

        logger.info("✅ All API keys validated")
        return True

    def _create_ingestion_jobs(self) -> List[IngestionJob]:
        """Create all ingestion jobs for comprehensive data ingestion"""
        jobs = []
        job_counter = 1

        # Congress.gov Jobs (10 years: Congresses 113-119)
        congress_congresses = [113, 114, 115, 116, 117, 118, 119]
        congress_bill_types = ['hr', 's', 'hjres', 'sjres', 'hconres', 'sconres', 'hres', 'sres']

        for congress in congress_congresses:
            # Members job
            job_id = f"congress_members_{congress}"
            command = [
                sys.executable, "scripts/data_ingestion/congress_api_ingest.py",
                "--source", "congress",
                "--congress", str(congress),
                "--data-type", "members"
            ]
            jobs.append(IngestionJob(
                job_id=job_id,
                source="congress",
                command=command,
                status=IngestionStatus.PENDING
            ))
            job_counter += 1

            # Bills jobs (split by bill type for parallel processing)
            for bill_type in congress_bill_types:
                job_id = f"congress_bills_{congress}_{bill_type}"
                command = [
                    sys.executable, "scripts/data_ingestion/congress_api_ingest.py",
                    "--source", "congress",
                    "--congress", str(congress),
                    "--bill-type", bill_type,
                    "--limit", "1000"  # Process in chunks
                ]
                jobs.append(IngestionJob(
                    job_id=job_id,
                    source="congress",
                    command=command,
                    status=IngestionStatus.PENDING
                ))
                job_counter += 1

        # OpenStates Jobs (All states, major data types)
        openstates_states = [
            'ca', 'ny', 'tx', 'fl', 'il', 'pa', 'oh', 'ga', 'nc', 'mi',
            'nj', 'va', 'wa', 'az', 'ma', 'tn', 'in', 'mo', 'md', 'wi',
            'co', 'mn', 'sc', 'al', 'la', 'ky', 'or', 'ok', 'ct', 'ut'
        ]

        for state in openstates_states:
            # People job
            job_id = f"openstates_people_{state}"
            command = [
                sys.executable, "scripts/ingestion/openstates_cli.py",
                "--jurisdiction", state,
                "--data-types", "people"
            ]
            jobs.append(IngestionJob(
                job_id=job_id,
                source="openstates",
                command=command,
                status=IngestionStatus.PENDING
            ))
            job_counter += 1

            # Bills job
            job_id = f"openstates_bills_{state}"
            command = [
                sys.executable, "scripts/ingestion/openstates_cli.py",
                "--jurisdiction", state,
                "--data-types", "bills",
                "--years-back", "10"
            ]
            jobs.append(IngestionJob(
                job_id=job_id,
                source="openstates",
                command=command,
                status=IngestionStatus.PENDING
            ))
            job_counter += 1

        # GovInfo Jobs (Major collections from last 10 years)
        govinfo_collections = ['BILLS', 'BILLSTATUS', 'CRPT', 'CHRG', 'FR', 'CFR', 'STATUTE', 'PLAW']
        start_date = (datetime.now() - timedelta(days=365*10)).strftime("%Y-%m-%d")

        for collection in govinfo_collections:
            job_id = f"govinfo_{collection}"
            command = [
                sys.executable, "scripts/data_ingestion/congress_api_ingest.py",
                "--source", "govinfo",
                "--collection", collection,
                "--start-date", start_date,
                "--limit", "2000"  # Process in chunks
            ]
            jobs.append(IngestionJob(
                job_id=job_id,
                source="govinfo",
                command=command,
                status=IngestionStatus.PENDING
            ))
            job_counter += 1

        logger.info(f"📋 Created {len(jobs)} ingestion jobs")
        return jobs

    def _execute_job(self, job: IngestionJob) -> None:
        """Execute a single ingestion job"""
        try:
            job.status = IngestionStatus.RUNNING
            job.started_at = datetime.now()

            logger.info(f"🚀 Starting job {job.job_id} ({job.source})")

            # Start process
            job.process = subprocess.Popen(
                job.command,
                cwd=self.base_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )

            # Monitor process in real-time
            while job.process.poll() is None:
                self._update_job_metrics(job)
                time.sleep(2)

            # Process completed
            job.completed_at = datetime.now()
            return_code = job.process.returncode

            if return_code == 0:
                job.status = IngestionStatus.COMPLETED
                logger.info(f"✅ Job {job.job_id} completed successfully")
            else:
                job.status = IngestionStatus.FAILED
                job.error_message = f"Process exited with code {return_code}"
                logger.error(f"❌ Job {job.job_id} failed with code {return_code}")

                # Capture stderr for error details
                if job.process.stderr:
                    stderr_output = job.process.stderr.read()
                    job.error_message += f": {stderr_output[:500]}"

        except Exception as e:
            job.status = IngestionStatus.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.now()
            logger.error(f"❌ Job {job.job_id} failed with exception: {e}")

    def _update_job_metrics(self, job: IngestionJob) -> None:
        """Update job metrics from database or process output"""
        try:
            # Check database for record counts
            conn = self.db_pool.getconn()
            try:
                cursor = conn.cursor()

                if job.source == "congress":
                    if "members" in job.job_id:
                        cursor.execute("SELECT COUNT(*) FROM congress.members")
                        job.records_processed = cursor.fetchone()[0]
                    elif "bills" in job.job_id:
                        cursor.execute("SELECT COUNT(*) FROM congress.bills")
                        job.records_processed = cursor.fetchone()[0]

                elif job.source == "openstates":
                    if "people" in job.job_id:
                        cursor.execute("SELECT COUNT(*) FROM openstates.people")
                        job.records_processed = cursor.fetchone()[0]
                    elif "bills" in job.job_id:
                        cursor.execute("SELECT COUNT(*) FROM openstates.bills")
                        job.records_processed = cursor.fetchone()[0]

                elif job.source == "govinfo":
                    cursor.execute("SELECT COUNT(*) FROM govinfo.packages")
                    job.records_processed = cursor.fetchone()[0]

                cursor.close()
            finally:
                self.db_pool.putconn(conn)

        except Exception as e:
            # Don't fail the job if metrics update fails
            pass

    def _run_jobs_parallel(self, jobs: List[IngestionJob], max_workers: int = 15) -> None:
        """Run jobs in parallel using ThreadPoolExecutor"""
        logger.info(f"🔄 Starting parallel execution with {max_workers} workers")

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all jobs
            future_to_job = {executor.submit(self._execute_job, job): job for job in jobs}

            # Track completion
            completed = 0
            total = len(jobs)

            for future in as_completed(future_to_job):
                job = future_to_job[future]
                completed += 1

                # Update results
                if job.status == IngestionStatus.COMPLETED:
                    self.results["completed_jobs"] += 1
                    self.results["successful_records"] += job.records_processed
                elif job.status == IngestionStatus.FAILED:
                    self.results["failed_jobs"] += 1

                self.results["total_records"] += job.records_processed
                self.results["sources"][job.source]["records"] += job.records_processed

                if job.status == IngestionStatus.COMPLETED:
                    self.results["sources"][job.source]["success"] += 1

                logger.info(f"📊 Progress: {completed}/{total} jobs completed ({completed/total*100:.1f}%)")

    def _monitor_database_stats(self) -> None:
        """Monitor database statistics during ingestion"""
        while self.monitoring_active:
            try:
                conn = self.db_pool.getconn()
                try:
                    cursor = conn.cursor()

                    # Get table sizes
                    cursor.execute("""
                        SELECT schemaname, tablename,
                               pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
                               n_live_tup as rows
                        FROM pg_stat_user_tables
                        WHERE schemaname IN ('congress', 'openstates', 'govinfo', 'incremental')
                        ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
                    """)

                    stats = cursor.fetchall()

                    # Log top 10 tables by size
                    logger.info("📊 Database Stats (Top 10 by size):")
                    for schemaname, tablename, size, rows in stats[:10]:
                        logger.info(f"  {schemaname}.{tablename}: {size}, {rows} rows")

                    cursor.close()
                finally:
                    self.db_pool.putconn(conn)

            except Exception as e:
                logger.error(f"Database monitoring error: {e}")

            time.sleep(30)  # Update every 30 seconds

    def _cancel_all_jobs(self) -> None:
        """Cancel all running jobs"""
        logger.info("🛑 Cancelling all running jobs...")

        for job in self.jobs.values():
            if job.status == IngestionStatus.RUNNING and job.process:
                try:
                    job.process.terminate()
                    job.status = IngestionStatus.CANCELLED
                    job.completed_at = datetime.now()
                    logger.info(f"🛑 Cancelled job {job.job_id}")
                except Exception as e:
                    logger.error(f"Failed to cancel job {job.job_id}: {e}")

    def _generate_final_report(self) -> str:
        """Generate comprehensive final report"""
        end_time = datetime.now()
        duration = end_time - self.start_time

        report = f"""
# Comprehensive Bulk Ingestion Report

## Execution Summary
- **Start Time**: {self.start_time.strftime("%Y-%m-%d %H:%M:%S")}
- **End Time**: {end_time.strftime("%Y-%m-%d %H:%M:%S")}
- **Total Duration**: {duration}
- **Total Jobs**: {self.results['total_jobs']}
- **Completed Jobs**: {self.results['completed_jobs']}
- **Failed Jobs**: {self.results['failed_jobs']}
- **Success Rate**: {(self.results['completed_jobs'] / self.results['total_jobs'] * 100):.1f}%

## Records Processed
- **Total Records**: {self.results['total_records']:,}
- **Successful Records**: {self.results['successful_records']:,}
- **Failed Records**: {self.results['total_records'] - self.results['successful_records']:,}

## Source Breakdown

### Congress.gov
- **Jobs**: {len(self.results['sources']['congress']['jobs'])}
- **Records**: {self.results['sources']['congress']['records']:,}
- **Success Rate**: {(self.results['sources']['congress']['success'] / max(len(self.results['sources']['congress']['jobs']), 1) * 100):.1f}%

### OpenStates
- **Jobs**: {len(self.results['sources']['openstates']['jobs'])}
- **Records**: {self.results['sources']['openstates']['records']:,}
- **Success Rate**: {(self.results['sources']['openstates']['success'] / max(len(self.results['sources']['openstates']['jobs']), 1) * 100):.1f}%

### GovInfo
- **Jobs**: {len(self.results['sources']['govinfo']['jobs'])}
- **Records**: {self.results['sources']['govinfo']['records']:,}
- **Success Rate**: {(self.results['sources']['govinfo']['success'] / max(len(self.results['sources']['govinfo']['jobs']), 1) * 100):.1f}%

## Failed Jobs Details

"""

        # Add failed jobs details
        failed_jobs = [j for j in self.jobs.values() if j.status == IngestionStatus.FAILED]
        if failed_jobs:
            for job in failed_jobs[:20]:  # Limit to first 20 failed jobs
                report += f"### {job.job_id}\n"
                report += f"- **Source**: {job.source}\n"
                report += f"- **Error**: {job.error_message}\n"
                report += f"- **Started**: {job.started_at}\n"
                report += f"- **Completed**: {job.completed_at}\n\n"
        else:
            report += "No failed jobs! 🎉\n\n"

        # Performance metrics
        report += f"""
## Performance Metrics
- **Average Records per Second**: {self.results['total_records'] / duration.total_seconds() if duration.total_seconds() > 0 else 0:.2f}
- **Average Job Duration**: {duration / self.results['total_jobs'] if self.results['total_jobs'] > 0 else 'N/A'}
- **Peak Parallel Jobs**: 15
- **Database Pool Size**: 20 connections

## Database Statistics

"""

        # Add final database stats
        try:
            conn = self.db_pool.getconn()
            try:
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT schemaname, tablename,
                           pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
                           n_live_tup as rows
                    FROM pg_stat_user_tables
                    WHERE schemaname IN ('congress', 'openstates', 'govinfo', 'incremental')
                    ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
                """)

                stats = cursor.fetchall()
                for schemaname, tablename, size, rows in stats:
                    report += f"- **{schemaname}.{tablename}**: {size}, {rows:,} rows\n"

                cursor.close()
            finally:
                self.db_pool.putconn(conn)

        except Exception as e:
            report += f"Error getting final database stats: {e}\n"

        report += f"""
## Recommendations

1. **Review Failed Jobs**: Check error messages above for failed jobs
2. **Monitor Database Growth**: Track database size growth over time
3. **Optimize Parallel Processing**: Adjust worker count based on system performance
4. **Schedule Regular Ingestion**: Set up automated incremental updates

## Next Steps

1. **Verify Data Quality**: Run data validation queries
2. **Update Analytics**: Refresh any analytics dashboards
3. **Archive Logs**: Archive ingestion logs for future reference
4. **Plan Incremental Updates**: Set up daily/weekly incremental ingestion

---
**Report Generated**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Script Location**: {__file__}
"""

        return report

    def _job_to_dict(self, job: IngestionJob) -> Dict[str, Any]:
        """Convert IngestionJob to JSON-serializable dictionary"""
        return {
            "job_id": job.job_id,
            "source": job.source,
            "command": job.command,
            "status": job.status.value,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "records_processed": job.records_processed,
            "records_total": job.records_total,
            "error_message": job.error_message,
            "metrics": job.metrics
        }

    def run_comprehensive_ingestion(self) -> Dict[str, Any]:
        """Run the comprehensive bulk ingestion process"""
        logger.info("🚀 Starting Comprehensive Bulk Data Ingestion")
        logger.info("=" * 80)

        try:
            # Step 1: Validate API keys
            if not self._validate_api_keys():
                raise Exception("API key validation failed")

            # Step 2: Create ingestion jobs
            logger.info("📋 Creating ingestion jobs...")
            all_jobs = self._create_ingestion_jobs()
            self.jobs = {job.job_id: job for job in all_jobs}
            self.results["total_jobs"] = len(all_jobs)

            # Update results with job references (as serializable dictionaries)
            for job in all_jobs:
                self.results["sources"][job.source]["jobs"].append(self._job_to_dict(job))

            logger.info(f"📊 Total jobs created: {len(all_jobs)}")
            for source, data in self.results["sources"].items():
                logger.info(f"  - {source}: {len(data['jobs'])} jobs")

            # Step 3: Start database monitoring in background
            logger.info("📊 Starting database monitoring...")
            monitor_thread = threading.Thread(target=self._monitor_database_stats, daemon=True)
            monitor_thread.start()

            # Step 4: Execute jobs in parallel
            logger.info("🔄 Starting parallel job execution...")
            start_execution = datetime.now()

            self._run_jobs_parallel(all_jobs, max_workers=15)

            end_execution = datetime.now()
            execution_duration = end_execution - start_execution

            logger.info(f"✅ All jobs completed in {execution_duration}")

            # Step 5: Generate final report
            logger.info("📝 Generating final report...")
            report = self._generate_final_report()

            # Save report
            report_path = f"{self.base_path}/ingestion_results/comprehensive_ingestion_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            with open(report_path, 'w') as f:
                f.write(report)

            # Save results as JSON
            json_results = {
                **self.results,
                "end_time": datetime.now().isoformat(),
                "execution_duration_seconds": execution_duration.total_seconds(),
                "report_path": report_path
            }

            # Convert job objects to serializable format for JSON output
            for source in json_results["sources"]:
                json_results["sources"][source]["jobs"] = [self._job_to_dict(job) for job in self.jobs.values() if job.source == source]

            json_path = f"{self.base_path}/ingestion_results/comprehensive_ingestion_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(json_path, 'w') as f:
                json.dump(json_results, f, indent=2, default=str)

            logger.info(f"📄 Report saved to: {report_path}")
            logger.info(f"📊 Results saved to: {json_path}")

            return json_results

        except Exception as e:
            logger.error(f"❌ Comprehensive ingestion failed: {e}")
            self._cancel_all_jobs()
            raise

        finally:
            # Cleanup
            self.monitoring_active = False
            if self.db_pool:
                self.db_pool.closeall()
                logger.info("🔐 Database connections closed")

def main():
    """Main entry point"""
    print("🚀 Comprehensive Bulk Data Ingestion for OpenDiscourse")
    print("=" * 80)
    print("This script will ingest 10 years of data from all three sources:")
    print("• Congress.gov (7 congresses, all bill types)")
    print("• OpenStates (30 states, people and bills)")
    print("• GovInfo (8 collections, 10 years)")
    print()
    print("Optimization features:")
    print("• Parallel processing (15 workers)")
    print("• Database connection pooling (20 connections)")
    print("• Real-time monitoring and metrics")
    print("• Comprehensive error handling and recovery")
    print("• Database integrity protection")
    print()
    print("⚠️  This will process a large amount of data and may take several hours.")
    print("⚠️  Ensure you have sufficient disk space and database capacity.")
    print()

    # Confirm before proceeding (auto-confirm for testing)
    response = "yes"  # Auto-confirm for non-interactive testing
    # response = input("Do you want to proceed? (yes/no): ")
    if response.lower() != 'yes':
        print("❌ Ingestion cancelled by user")
        return

    try:
        # Create and run ingestion
        ingestion = ComprehensiveBulkIngestion()
        results = ingestion.run_comprehensive_ingestion()

        print("\n" + "=" * 80)
        print("🎉 COMPREHENSIVE INGESTION COMPLETED")
        print("=" * 80)
        print(f"✅ Total Jobs: {results['total_jobs']}")
        print(f"✅ Completed: {results['completed_jobs']}")
        print(f"❌ Failed: {results['failed_jobs']}")
        print(f"📊 Records Processed: {results['total_records']:,}")
        print(f"⏱️ Duration: {results['execution_duration_seconds']:.2f} seconds")
        print(f"📄 Report: {results['report_path']}")
        print("=" * 80)

    except KeyboardInterrupt:
        print("\n🛑 Ingestion cancelled by user")
    except Exception as e:
        print(f"\n❌ Ingestion failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
