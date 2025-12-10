#!/usr/bin/env python3
"""
Simple Bulk Ingestion Script for OpenDiscourse
Uses the working data_ingestion scripts to ingest data from all three sources
"""

import os
import sys
import subprocess
import json
import time
import logging
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class SimpleBulkIngestion:
    def __init__(self):
        self.base_path = Path("/home/cbwinslow/Videos/opendiscourse")
        self.venv_python = "./venv/bin/python3"
        self.results = {
            "start_time": datetime.now().isoformat(),
            "jobs": [],
            "completed": 0,
            "failed": 0,
            "total": 0,
        }

        # Set API keys from .env file
        self._setup_api_keys()

    def _setup_api_keys(self):
        """Setup API keys from .env file"""
        try:
            with open(".env", "r") as f:
                for line in f:
                    if line.strip() and not line.startswith("#"):
                        if "=" in line:
                            key, value = line.split("=", 1)
                            key = key.strip()
                            value = value.strip().strip("\"'")
                            os.environ[key] = value

            logger.info("✅ API keys loaded from .env file")

        except Exception as e:
            logger.error(f"❌ Failed to load API keys: {e}")
            sys.exit(1)

    def run_job(self, job_name: str, command: List[str]) -> Dict[str, Any]:
        """Run a single job and return results"""
        logger.info(f"🚀 Starting: {job_name}")

        start_time = datetime.now()

        try:
            # Run the command
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=3600,  # 1 hour timeout
                cwd=str(self.base_path),
            )

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            success = result.returncode == 0

            job_result = {
                "job_name": job_name,
                "command": " ".join(command),
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "duration_seconds": duration,
                "success": success,
                "return_code": result.returncode,
                "stdout": result.stdout[-1000:] if result.stdout else "",  # Last 1000 chars
                "stderr": result.stderr[-1000:] if result.stderr else "",  # Last 1000 chars
            }

            if success:
                logger.info(f"✅ Completed: {job_name} in {duration:.1f}s")
                self.results["completed"] += 1
            else:
                logger.error(f"❌ Failed: {job_name} in {duration:.1f}s")
                logger.error(
                    f"   Error: {result.stderr[:500] if result.stderr else 'Unknown error'}"
                )
                self.results["failed"] += 1

            return job_result

        except subprocess.TimeoutExpired:
            logger.error(f"⏱️ Timeout: {job_name} after 1 hour")
            self.results["failed"] += 1
            return {
                "job_name": job_name,
                "command": " ".join(command),
                "success": False,
                "timeout": True,
                "error": "Command timed out after 1 hour",
            }

        except Exception as e:
            logger.error(f"💥 Exception: {job_name} - {e}")
            self.results["failed"] += 1
            return {
                "job_name": job_name,
                "command": " ".join(command),
                "success": False,
                "error": str(e),
            }

    def run_congress_ingestion(self):
        """Run Congress.gov ingestion for recent congresses"""
        logger.info("🏛️ Starting Congress.gov ingestion")

        jobs = [
            (
                "Congress 117 - Bills",
                [
                    self.venv_python,
                    "scripts/data_ingestion/congress_api_ingest.py",
                    "--source",
                    "congress",
                    "--congress",
                    "117",
                    "--limit",
                    "200",
                ],
            ),
            (
                "Congress 118 - Bills",
                [
                    self.venv_python,
                    "scripts/data_ingestion/congress_api_ingest.py",
                    "--source",
                    "congress",
                    "--congress",
                    "118",
                    "--limit",
                    "200",
                ],
            ),
            (
                "Congress 117 - Members",
                [
                    self.venv_python,
                    "scripts/data_ingestion/congress_api_ingest.py",
                    "--source",
                    "congress",
                    "--congress",
                    "117",
                    "--data-type",
                    "members",
                ],
            ),
            (
                "Congress 118 - Members",
                [
                    self.venv_python,
                    "scripts/data_ingestion/congress_api_ingest.py",
                    "--source",
                    "congress",
                    "--congress",
                    "118",
                    "--data-type",
                    "members",
                ],
            ),
        ]

        for job_name, command in jobs:
            result = self.run_job(job_name, command)
            self.results["jobs"].append(result)
            self.results["total"] += 1

    def run_govinfo_ingestion(self):
        """Run GovInfo ingestion for major collections"""
        logger.info("📄 Starting GovInfo ingestion")

        jobs = [
            (
                "GovInfo - BILLS Collection",
                [
                    self.venv_python,
                    "scripts/data_ingestion/congress_api_ingest.py",
                    "--source",
                    "govinfo",
                    "--collection",
                    "BILLS",
                    "--limit",
                    "100",
                ],
            ),
            (
                "GovInfo - CRPT Collection",
                [
                    self.venv_python,
                    "scripts/data_ingestion/congress_api_ingest.py",
                    "--source",
                    "govinfo",
                    "--collection",
                    "CRPT",
                    "--limit",
                    "100",
                ],
            ),
            (
                "GovInfo - CHRG Collection",
                [
                    self.venv_python,
                    "scripts/data_ingestion/congress_api_ingest.py",
                    "--source",
                    "govinfo",
                    "--collection",
                    "CHRG",
                    "--limit",
                    "100",
                ],
            ),
        ]

        for job_name, command in jobs:
            result = self.run_job(job_name, command)
            self.results["jobs"].append(result)
            self.results["total"] += 1

    def run_openstates_ingestion(self):
        """Run OpenStates ingestion for major states"""
        logger.info("🏢 Starting OpenStates ingestion")

        # Focus on major states for testing
        major_states = ["ca", "ny", "tx", "fl", "il"]

        jobs = []
        for state in major_states:
            jobs.append(
                (
                    f"OpenStates {state.upper()} - People",
                    [
                        self.venv_python,
                        "scripts/data_ingestion/congress_api_ingest.py",
                        "--source",
                        "openstates",
                        "--jurisdiction",
                        state,
                        "--data-type",
                        "people",
                    ],
                )
            )
            jobs.append(
                (
                    f"OpenStates {state.upper()} - Bills",
                    [
                        self.venv_python,
                        "scripts/data_ingestion/congress_api_ingest.py",
                        "--source",
                        "openstates",
                        "--jurisdiction",
                        state,
                        "--data-type",
                        "bills",
                        "--limit",
                        "50",
                    ],
                )
            )

        for job_name, command in jobs:
            result = self.run_job(job_name, command)
            self.results["jobs"].append(result)
            self.results["total"] += 1

    def run_all_ingestion(self):
        """Run ingestion for all three sources"""
        logger.info("🚀 Starting comprehensive bulk ingestion")
        logger.info("=" * 60)

        start_time = datetime.now()

        try:
            # Run each source
            self.run_congress_ingestion()
            self.run_govinfo_ingestion()
            self.run_openstates_ingestion()

        except KeyboardInterrupt:
            logger.info("⚠️ Ingestion interrupted by user")
        except Exception as e:
            logger.error(f"❌ Ingestion failed: {e}")

        finally:
            # Generate final report
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            self.results["end_time"] = end_time.isoformat()
            self.results["total_duration_seconds"] = duration

            self._generate_report()

    def _generate_report(self):
        """Generate final report"""
        logger.info("\n" + "=" * 60)
        logger.info("📊 BULK INGESTION SUMMARY")
        logger.info("=" * 60)

        logger.info(
            f"⏰ Duration: {self.results['total_duration_seconds']:.1f} seconds ({self.results['total_duration_seconds'] / 60:.1f} minutes)"
        )
        logger.info(f"📋 Total Jobs: {self.results['total']}")
        logger.info(f"✅ Completed: {self.results['completed']}")
        logger.info(f"❌ Failed: {self.results['failed']}")

        if self.results["total"] > 0:
            success_rate = (self.results["completed"] / self.results["total"]) * 100
            logger.info(f"📈 Success Rate: {success_rate:.1f}%")

        # Show failed jobs
        failed_jobs = [job for job in self.results["jobs"] if not job.get("success", False)]
        if failed_jobs:
            logger.info(f"\n❌ Failed Jobs ({len(failed_jobs)}):")
            for job in failed_jobs:
                error = job.get("error", job.get("stderr", "Unknown error"))[:100]
                logger.info(f"  - {job['job_name']}: {error}")

        logger.info("=" * 60)

        # Save results to file
        results_file = f"bulk_ingestion_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        try:
            with open(results_file, "w") as f:
                json.dump(self.results, f, indent=2, default=str)
            logger.info(f"📄 Results saved to: {results_file}")
        except Exception as e:
            logger.error(f"Error saving results: {e}")


def main():
    """Main entry point"""
    print("🚀 Simple Bulk Data Ingestion for OpenDiscourse")
    print("=" * 60)
    print("This script will ingest data from:")
    print("• Congress.gov (Recent congresses)")
    print("• GovInfo (Major collections)")
    print("• OpenStates (Major states)")
    print()

    # Confirm before proceeding
    try:
        response = input("Do you want to proceed? (yes/no): ")
        if response.lower() != "yes":
            print("❌ Ingestion cancelled by user")
            return
    except KeyboardInterrupt:
        print("\n❌ Ingestion cancelled by user")
        return

    # Run ingestion
    ingestion = SimpleBulkIngestion()
    ingestion.run_all_ingestion()


if __name__ == "__main__":
    main()
