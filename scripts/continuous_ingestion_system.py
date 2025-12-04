#!/usr/bin/env python3
"""
Continuous Ingestion System - Never Stop Processing
Continuously ingests data with automatic retry, recovery, and non-stop operation
"""

import os
import sys
import time
import subprocess
import logging
import signal
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import psycopg2
from psycopg2 import pool

# Add project root to path
sys.path.append('/home/cbwinslow/Videos/opendiscourse')

# Configure logging for continuous operation
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/cbwinslow/Videos/opendiscourse/logs/continuous_ingestion.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class ContinuousIngestionSystem:
    """Continuous ingestion system that never stops"""

    def __init__(self):
        self.base_path = "/home/cbwinslow/Videos/opendiscourse"
        self.running = True
        self.start_time = datetime.now()
        self.db_pool = None
        self.ingestion_cycles = 0
        self.total_records = 0
        self.setup_database_pool()

        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def setup_database_pool(self):
        """Setup database connection pool"""
        try:
            self.db_pool = psycopg2.pool.ThreadedConnectionPool(
                minconn=5,
                maxconn=20,
                database="opendiscourse",
                user="cbwinslow",
                host="/var/run/postgresql"
            )
            logger.info("✅ Database connection pool established")
        except Exception as e:
            logger.error(f"❌ Database pool setup failed: {e}")
            self.db_pool = None

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"🛑 Received signal {signum}, but continuous ingestion never stops!")
        # Don't actually stop - this is continuous!

    def run_continuous_ingestion(self):
        """Run continuous ingestion cycles forever"""
        logger.info("🚀 Starting Continuous Ingestion System - NEVER STOPPING!")
        logger.info("=" * 80)

        while self.running:  # This will run forever
            try:
                self.ingestion_cycles += 1
                cycle_start = datetime.now()

                logger.info(f"\n🔄 Starting Ingestion Cycle #{self.ingestion_cycles}")
                logger.info(f"📅 Cycle Start: {cycle_start.strftime('%Y-%m-%d %H:%M:%S')}")

                # Run comprehensive ingestion
                self._run_comprehensive_ingestion()

                # Run parallel ingestion
                self._run_parallel_ingestion()

                # Check database growth
                self._check_database_growth()

                # Short delay before next cycle (but keep running!)
                cycle_end = datetime.now()
                cycle_duration = (cycle_end - cycle_start).total_seconds()

                logger.info(f"✅ Cycle #{self.ingestion_cycles} completed in {cycle_duration:.2f} seconds")
                logger.info(f"📊 Total records ingested: {self.total_records:,}")
                logger.info(f"🚀 Next cycle starting in 30 seconds...")

                # Wait 30 seconds before next cycle (but don't stop!)
                for i in range(30, 0, -1):
                    if not self.running:
                        break
                    time.sleep(1)
                    if i % 5 == 0:
                        logger.info(f"🕒 Next cycle in {i} seconds...")

            except KeyboardInterrupt:
                logger.info("🚫 Keyboard interrupt received, but continuous ingestion NEVER STOPS!")
            except Exception as e:
                logger.error(f"❌ Cycle error, but continuous ingestion continues: {e}")
                time.sleep(10)  # Brief pause then continue

    def _run_comprehensive_ingestion(self):
        """Run comprehensive bulk ingestion"""
        try:
            logger.info("📦 Running comprehensive bulk ingestion...")

            process = subprocess.Popen(
                [sys.executable, "scripts/comprehensive_bulk_ingestion.py"],
                cwd=self.base_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # Monitor process
            while process.poll() is None:
                time.sleep(5)
                logger.info("⏳ Comprehensive ingestion running...")

            return_code = process.returncode
            if return_code == 0:
                logger.info("✅ Comprehensive ingestion completed successfully")
            else:
                logger.error(f"❌ Comprehensive ingestion failed with code {return_code}")
                # But we continue anyway!

        except Exception as e:
            logger.error(f"❌ Comprehensive ingestion error: {e}")
            # Continue regardless

    def _run_parallel_ingestion(self):
        """Run parallel bulk ingestion"""
        try:
            logger.info("🔄 Running parallel bulk ingestion...")

            process = subprocess.Popen(
                [sys.executable, "scripts/parallel_bulk_ingestion.py"],
                cwd=self.base_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # Monitor process
            while process.poll() is None:
                time.sleep(5)
                logger.info("⏳ Parallel ingestion running...")

            return_code = process.returncode
            if return_code == 0:
                logger.info("✅ Parallel ingestion completed successfully")
            else:
                logger.error(f"❌ Parallel ingestion failed with code {return_code}")
                # But we continue anyway!

        except Exception as e:
            logger.error(f"❌ Parallel ingestion error: {e}")
            # Continue regardless

    def _check_database_growth(self):
        """Check database growth and update records count"""
        try:
            if not self.db_pool:
                return

            conn = self.db_pool.getconn()
            try:
                cursor = conn.cursor()

                # Get current counts
                cursor.execute("SELECT COUNT(*) FROM congress.bills")
                bills_count = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM congress.members")
                members_count = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM congress.committees")
                committees_count = cursor.fetchone()[0]

                # Try to get OpenStates counts if available
                try:
                    cursor.execute("SELECT COUNT(*) FROM openstates.people")
                    people_count = cursor.fetchone()[0]
                except:
                    people_count = 0

                try:
                    cursor.execute("SELECT COUNT(*) FROM openstates.bills")
                    bills_openstates_count = cursor.fetchone()[0]
                except:
                    bills_openstates_count = 0

                cursor.close()

                total = bills_count + members_count + committees_count + people_count + bills_openstates_count

                if total > self.total_records:
                    incremental = total - self.total_records
                    self.total_records = total
                    logger.info(f"📈 Database growth detected: +{incremental:,} records")
                    logger.info(f"  🏛️  Congress: {bills_count:,} bills, {members_count:,} members, {committees_count:,} committees")
                    logger.info(f"  🗳️  OpenStates: {people_count:,} people, {bills_openstates_count:,} bills")
                else:
                    logger.info("📊 No new database growth detected this cycle")

            finally:
                self.db_pool.putconn(conn)

        except Exception as e:
            logger.error(f"❌ Database growth check error: {e}")

def main():
    """Main entry point for continuous ingestion"""
    print("🚀 CONTINUOUS INGESTION SYSTEM - NEVER STOPPING!")
    print("=" * 80)
    print("This system will continuously ingest data forever.")
    print("It will automatically retry failed jobs and never stop.")
    print("Press Ctrl+C to attempt stopping (but it won't stop!).")
    print()

    # Start continuous ingestion
    ingestion = ContinuousIngestionSystem()
    ingestion.run_continuous_ingestion()

if __name__ == "__main__":
    main()
