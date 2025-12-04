#!/usr/bin/env python3
"""
Parallel Bulk Votes Ingestion with Monitoring
Ingests House and Senate voting data in parallel with comprehensive monitoring
"""

import argparse
import json
import logging
import os
import sys
import time
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import multiprocessing
import psutil
import threading

import psycopg2
import requests
import xml.etree.ElementTree as ET
from psycopg2.extras import execute_values
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class IngestionConfig:
    """Configuration for votes ingestion"""

    def __init__(self):
        self.db_host = os.getenv("DB_HOST", "/var/run/postgresql")
        self.db_port = int(os.getenv("DB_PORT", "5432"))
        self.db_name = os.getenv("DB_NAME", "opendiscourse")
        self.db_user = os.getenv("DB_USER", "cbwinslow")
        self.db_password = os.getenv("DB_PASSWORD", "")
        self.request_timeout = int(os.getenv("REQUEST_TIMEOUT", "30"))
        self.rate_limit_delay = float(os.getenv("RATE_LIMIT_DELAY", "0.5"))
        self.batch_size = int(os.getenv("BATCH_SIZE", "100"))
        self.max_retries = int(os.getenv("MAX_RETRIES", "3"))
        self.max_workers = min(int(os.getenv("MAX_WORKERS", "4")), multiprocessing.cpu_count())


class IngestionMonitor:
    """Monitor and log ingestion runs to database"""

    def __init__(self, config: IngestionConfig):
        self.config = config
        self.conn = None
        self.run_id = None
        self.start_time = None
        self.metrics_lock = threading.Lock()
        self.total_processed = 0
        self.successful = 0
        self.failed = 0
        self.duplicates = 0

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
            logger.error(f"Failed to connect to monitoring database: {e}")
            raise

    def start_run(
        self,
        script_name: str,
        source_type: str,
        target_congress: Optional[int] = None,
        config_params: Optional[Dict] = None,
    ):
        """Start monitoring a new ingestion run"""
        self.connect_db()
        self.run_id = str(uuid.uuid4())
        self.start_time = datetime.now()

        try:
            with self.conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO monitoring.ingestion_runs 
                    (run_id, script_name, source_type, target_congress, start_time, status, config_params)
                    VALUES (%s, %s, %s, %s, %s, 'running', %s)
                """,
                    (
                        self.run_id,
                        script_name,
                        source_type,
                        target_congress,
                        self.start_time,
                        json.dumps(config_params or {}),
                    ),
                )
                self.conn.commit()
            logger.info(f"Started monitoring run {self.run_id}")
        except Exception as e:
            logger.error(f"Failed to start monitoring run: {e}")
            raise

    def log_error(
        self,
        error_type: str,
        error_message: str,
        error_severity: str = "error",
        error_code: Optional[str] = None,
        context_data: Optional[Dict] = None,
    ):
        """Log an error to the monitoring database"""
        if not self.conn or not self.run_id:
            return

        try:
            with self.conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO monitoring.ingestion_errors 
                    (run_id, error_type, error_severity, error_code, error_message, context_data)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """,
                    (
                        self.run_id,
                        error_type,
                        error_severity,
                        error_code,
                        error_message,
                        context_data,
                    ),
                )
                self.conn.commit()
        except Exception as e:
            logger.error(f"Failed to log error to monitoring: {e}")

    def log_metric(
        self,
        metric_type: str,
        metric_name: str,
        metric_value: float,
        metric_unit: Optional[str] = None,
        additional_data: Optional[Dict] = None,
    ):
        """Log a performance metric"""
        if not self.conn or not self.run_id:
            return

        try:
            with self.conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO monitoring.ingestion_metrics 
                    (run_id, metric_type, metric_name, metric_value, metric_unit, additional_data)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """,
                    (
                        self.run_id,
                        metric_type,
                        metric_name,
                        metric_value,
                        metric_unit,
                        additional_data,
                    ),
                )
                self.conn.commit()
        except Exception as e:
            logger.error(f"Failed to log metric to monitoring: {e}")

    def update_progress(self, successful: int, failed: int, duplicates: int = 0):
        """Update ingestion progress"""
        with self.metrics_lock:
            self.successful += successful
            self.failed += failed
            self.duplicates += duplicates
            self.total_processed += successful + failed + duplicates

    def finish_run(self, status: str = "completed", error_summary: Optional[str] = None):
        """Finish the monitoring run"""
        if not self.conn or not self.run_id:
            return

        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()

        # Calculate processing speed
        processing_speed = self.total_processed / duration if duration > 0 else 0

        # Calculate error rate
        error_rate = (self.failed / self.total_processed * 100) if self.total_processed > 0 else 0

        try:
            with self.conn.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE monitoring.ingestion_runs 
                    SET end_time = %s, status = %s, total_records_processed = %s,
                        successful_records = %s, failed_records = %s, duplicate_records = %s,
                        error_rate = %s, processing_speed_records_per_second = %s,
                        memory_usage_mb = %s, cpu_usage_percent = %s, error_summary = %s
                    WHERE run_id = %s
                """,
                    (
                        end_time,
                        status,
                        self.total_processed,
                        self.successful,
                        self.failed,
                        self.duplicates,
                        error_rate,
                        processing_speed,
                        psutil.virtual_memory().used / 1024 / 1024,
                        psutil.cpu_percent(),
                        error_summary,
                        self.run_id,
                    ),
                )
                self.conn.commit()
            logger.info(
                f"Finished monitoring run {self.run_id}: {self.total_processed} records, {processing_speed:.2f} records/sec"
            )
        except Exception as e:
            logger.error(f"Failed to finish monitoring run: {e}")
        finally:
            if self.conn:
                self.conn.close()


class ParallelVotesIngestor:
    """Handles parallel ingestion of congressional roll call votes"""

    def __init__(self, config: IngestionConfig):
        self.config = config
        self.monitor = IngestionMonitor(config)
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        """Create HTTP session with retry strategy"""
        session = requests.Session()
        retry_strategy = Retry(
            total=self.config.max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    def ingest_house_congress(self, congress: int, year: int, roll_range: Tuple[int, int]) -> Dict:
        """Ingest House votes for a specific congress, year, and roll range"""
        results = {"processed": 0, "successful": 0, "failed": 0, "duplicates": 0}
        base_url = "http://clerk.house.gov/cgi-bin/vote.asp"

        start_roll, end_roll = roll_range

        for roll_number in range(start_roll, end_roll + 1):
            try:
                url = f"{base_url}?year={year}&rollnumber={roll_number}"

                response = self.session.get(url, timeout=self.config.request_timeout)
                response.raise_for_status()

                # Parse XML response
                root = ET.fromstring(response.text)
                vote_metadata = root.find("vote-metadata")

                if vote_metadata is None:
                    continue

                congress_num = int(vote_metadata.find("congress").text)
                if congress_num != congress:
                    continue

                # Extract vote data (simplified for parallel processing)
                vote_data = self._extract_vote_data(vote_metadata, congress, roll_number)
                if vote_data:
                    success = self._insert_vote_data(vote_data)
                    if success:
                        results["successful"] += 1
                    else:
                        results["duplicates"] += 1
                else:
                    results["failed"] += 1

                results["processed"] += 1

                # Rate limiting
                time.sleep(self.config.rate_limit_delay)

            except Exception as e:
                results["failed"] += 1
                self.monitor.log_error(
                    "network",
                    f"Error processing roll {roll_number}: {str(e)}",
                    "error",
                    context_data={"roll_number": roll_number, "year": year, "congress": congress},
                )

        return results

    def ingest_senate_congress(self, congress: int, year: int) -> Dict:
        """Ingest Senate votes for a specific congress and year"""
        results = {"processed": 0, "successful": 0, "failed": 0, "duplicates": 0}
        
        logger.info(f"Starting Senate ingestion for {congress}th Congress, {year}")
        
        # Simple Senate ingestion without external dependency
        base_url = "https://www.senate.gov"
        
        # Try different Senate Clerk URL patterns
        urls = [
            f"{base_url}/legislative/votes_roll_call_votes_{congress}.htm",
            f"{base_url}/legislative/votes_{congress}th_congress.htm",
            f"{base_url}/legislative/votes_{congress}th_congress_{year}.htm"
        ]
        
        roll_calls_found = False
        for url in urls:
            try:
                logger.info(f"Fetching Senate roll call list from: {url}")
                response = self.session.get(url, timeout=self.config.request_timeout)
                response.raise_for_status()
                
                # Parse HTML to find roll call links
                import re
                pattern = r'votes_roll_call_vote(\d+)\.htm'
                matches = re.findall(pattern, response.text)
                
                if matches:
                    roll_calls_found = True
                    roll_calls = sorted([(int(match), f"votes_roll_call_vote{match}.htm") for match in matches], reverse=True)
                    break
                    
            except Exception as e:
                logger.warning(f"Failed to fetch from {url}: {e}")
                continue
        
        if not roll_calls_found:
            logger.warning(f"No Senate roll calls found for {congress}th Congress, {year}")
            return results
        
        for roll_number, vote_file in roll_calls:
            try:
                url = f"{base_url}/legislative/votes_roll_call_votes_{congress}/{vote_file}"
                
                logger.debug(f"Fetching Senate roll call {roll_number} from: {url}")
                response = self.session.get(url, timeout=self.config.request_timeout)
                response.raise_for_status()
                
                # Parse XML response (Senate Clerk provides XML)
                import xml.etree.ElementTree as ET
                root = ET.fromstring(response.text)
                
                # Extract vote metadata
                vote_metadata = root.find(".//vote")
                if vote_metadata is None:
                    continue
                
                # Extract basic vote information
                vote_question = self._safe_get_text(vote_metadata, "question")
                vote_result = self._safe_get_text(vote_metadata, "result")
                vote_date = self._safe_get_text(vote_metadata, "date")
                
                # Extract vote totals
                yeas = 0
                nays = 0
                present = 0
                not_voting = 0
                
                vote_totals = vote_metadata.find(".//totals")
                if vote_totals is not None:
                    yeas = int(self._safe_get_text(vote_totals, "yeas") or "0")
                    nays = int(self._safe_get_text(vote_totals, "nays") or "0")
                    present = int(self._safe_get_text(vote_totals, "present") or "0")
                    not_voting = int(self._safe_get_text(vote_totals, "not_voting") or "0")
                
                # Extract bill information
                bill_number = None
                bill_type = None
                bill_elem = vote_metadata.find(".//bill")
                if bill_elem is not None:
                    bill_number = self._safe_get_text(bill_elem, "number")
                    bill_type = self._safe_get_text(bill_elem, "type")
                
                # Create vote data matching our table structure
                vote_data = {
                    "vote_id": f"{congress}-senate-{roll_number}",
                    "congress_number": congress,
                    "chamber": "Senate",
                    "roll_call_number": roll_number,
                    "vote_question": vote_question,
                    "vote_result": vote_result,
                    "vote_date": self._parse_date(vote_date),
                    "vote_time": None,  # Senate may not provide time
                    "vote_description": vote_question,
                    "vote_type": "roll_call",
                    "yeas": yeas,
                    "nays": nays,
                    "present": present,
                    "not_voting": not_voting,
                    "democratic_position": None,  # Would need party analysis
                    "republican_position": None,  # Would need party analysis
                    "bill_id": f"{bill_type}{bill_number}" if bill_type and bill_number else None,
                    "amendment_number": None,
                    "nomination_number": None,
                    "source": "senate-clerk",
                }
                
                success = self._insert_vote_data(vote_data)
                if success:
                    results["successful"] += 1
                else:
                    results["duplicates"] += 1
                    
                results["processed"] += 1
                
                # Rate limiting
                time.sleep(self.config.rate_limit_delay)
                
            except Exception as e:
                results["failed"] += 1
                logger.error(f"Error processing Senate roll call {roll_number}: {e}")
                
        logger.info(f"Senate ingestion completed for {congress}th Congress, {year}: {results}")
        return results

    def _extract_vote_data(self, vote_metadata, congress: int, roll_number: int) -> Optional[Dict]:
        """Extract vote data from XML metadata"""
        try:
            chamber = vote_metadata.find("chamber").text
            vote_question = vote_metadata.find("vote-question").text
            vote_result = vote_metadata.find("vote-result").text

            vote_totals = vote_metadata.find("vote-totals")
            yeas = int(vote_totals.find("totals-by-vote/yea-total").text)
            nays = int(vote_totals.find("totals-by-vote/nay-total").text)

            return {
                "vote_id": f"{congress}-house-{roll_number}",
                "congress_number": congress,
                "chamber": chamber,
                "roll_call_number": roll_number,
                "vote_question": vote_question,
                "vote_result": vote_result,
                "yeas": yeas,
                "nays": nays,
                "source": "house-clerk",
            }
        except Exception as e:
            return None

    def _insert_vote_data(self, vote_data: Dict) -> bool:
        """Insert vote data into database"""
        try:
            conn = psycopg2.connect(
                host=self.config.db_host,
                port=self.config.db_port,
                database=self.config.db_name,
                user=self.config.db_user,
                password=self.config.db_password,
            )

            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO congress.roll_call_votes_bulk 
                    (vote_id, congress_number, chamber, roll_call_number, vote_question, 
                     vote_result, yeas, nays, source)
                    VALUES (%(vote_id)s, %(congress_number)s, %(chamber)s, %(roll_call_number)s,
                            %(vote_question)s, %(vote_result)s, %(yeas)s, %(nays)s, %(source)s)
                    ON CONFLICT (vote_id) DO NOTHING
                """,
                    vote_data,
                )

                success = cursor.rowcount > 0
                conn.commit()
                return success

        except Exception as e:
            logger.error(f"Failed to insert vote data: {e}")
            return False
        finally:
            if "conn" in locals():
                conn.close()

    def run_parallel_ingestion(self, congresses: List[int], source_types: List[str]):
        """Run parallel ingestion for multiple congresses and source types"""
        # Start monitoring
        self.monitor.start_run(
            "parallel_votes_ingestion.py",
            "parallel_bulk",
            congresses[0] if len(congresses) == 1 else None,
            {
                "congresses": congresses,
                "source_types": source_types,
                "max_workers": self.config.max_workers,
            },
        )

        try:
            with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
                futures = []

                # Create tasks for each congress and source type
                for congress in congresses:
                    if "house-clerk" in source_types:
                        # House Clerk data - split by years and roll ranges
                        congress_years = {
                            113: (2013, 2014), 114: (2015, 2016), 115: (2017, 2018),
                            116: (2019, 2020), 117: (2021, 2022), 118: (2023, 2024)
                        }
                        
                        years = congress_years.get(congress, (2024, 2024))
                        for year in years:
                            # Split roll calls into chunks for parallel processing
                            roll_chunks = [(1, 150), (151, 300), (301, 450), (451, 600)]
                            for start_roll, end_roll in roll_chunks:
                                future = executor.submit(
                                    self.ingest_house_congress, congress, year, (start_roll, end_roll)
                                )
                                futures.append(future)
                    
                    if "senate-clerk" in source_types:
                        # Senate Clerk data - split by years
                        congress_years = {
                            113: (2013, 2014), 114: (2015, 2016), 115: (2017, 2018),
                            116: (2019, 2020), 117: (2021, 2022), 118: (2023, 2024)
                        }
                        
                        years = congress_years.get(congress, (2024, 2024))
                        for year in years:
                            future = executor.submit(
                                self.ingest_senate_congress, congress, year)
                            )
                            futures.append(future)

                # Process completed tasks
                for future in as_completed(futures):
                    try:
                        results = future.result()
                        self.monitor.update_progress(
                            results["successful"], results["failed"], results["duplicates"]
                        )

                        # Log progress metrics
                        self.monitor.log_metric(
                            "batch_progress", "records_processed", results["processed"], "records"
                        )

                    except Exception as e:
                        self.monitor.log_error("processing", f"Task failed: {str(e)}", "error")
                        self.monitor.update_progress(0, 1, 0)

            self.monitor.finish_run("completed")

        except KeyboardInterrupt:
            logger.info("Ingestion interrupted by user")
            self.monitor.finish_run("cancelled", "Interrupted by user")
        except Exception as e:
            logger.error(f"Parallel ingestion failed: {e}")
            self.monitor.finish_run("failed", str(e))
            raise


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Parallel bulk votes ingestion with monitoring")
    parser.add_argument(
        "--congresses",
        nargs="+",
        type=int,
        default=[113, 114, 115, 116, 117, 118],
        help="Congress numbers to ingest (default: 113-118)",
    )
    parser.add_argument(
        "--sources",
        nargs="+",
        type=str,
        default=["house-clerk"],
        choices=["house-clerk", "senate-clerk"],
        help="Data sources to ingest (default: house-clerk)",
    )
    parser.add_argument("--workers", type=int, help="Number of parallel workers")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    config = IngestionConfig()
    if args.workers:
        config.max_workers = args.workers

    ingestor = ParallelVotesIngestor(config)

    try:
        start_time = datetime.now()
        logger.info(
            f"Starting parallel ingestion for Congresses {args.congresses} from sources {args.sources}"
        )
        logger.info(f"Using {config.max_workers} parallel workers")

        ingestor.run_parallel_ingestion(args.congresses, args.sources)

        end_time = datetime.now()
        duration = end_time - start_time
        logger.info(f"Parallel ingestion completed in {duration}")

    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
