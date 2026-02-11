#!/usr/bin/env python3
"""
Congress.gov Bills Ingestion Script

This script ingests bills data from congress.gov API with comprehensive
offset-based pagination, checkpoint tracking, and API key enforcement.
"""

import argparse
import logging
import os
import sys
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Dict, List, Optional

import psycopg2
import requests
from psycopg2.extras import DictCursor
from tenacity import retry, stop_after_attempt, wait_exponential

# Import monitoring and configuration components
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# Load environment variables
from dotenv import load_dotenv
from ingestion_config import (
    get_api_key_from_env,
    get_ingestion_mode_from_env,
    validate_all_api_keys,
)

from monitoring.delegates import setup_all_delegates
from monitoring.progress_monitor import UniversalProgressMonitor

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class CongressBillsConfig:
    """Configuration for Congress bills ingestion"""

    congress: int
    batch_size: int = 50
    api_key: str = ""
    base_url: str = "https://api.congress.gov/v3"
    max_retries: int = 3
    retry_delay: float = 1.0


class CongressBillsIngestor:
    """Congress.gov Bills Ingestion Engine"""

    def __init__(self, config: CongressBillsConfig):
        self.config = config
        self.api_key = config.api_key or get_api_key_from_env("CONGRESS_API_KEY")
        self.session = requests.Session()
        self.session.headers.update(
            {"X-API-Key": self.api_key, "Accept": "application/json"}
        )

        # Database connection (env-driven with sensible defaults)
        db_host = os.getenv("DB_HOST", "localhost")
        db_port = os.getenv("DB_PORT", "5432")
        db_name = os.getenv("DB_NAME", "cbwinslow")
        db_user = os.getenv("DB_USER", "cbwinslow")
        db_password = os.getenv("DB_PASSWORD", None)
        self.conn = psycopg2.connect(
            dbname=db_name,
            user=db_user,
            password=db_password,
            host=db_host,
            port=db_port,
        )
        self.cursor = self.conn.cursor(cursor_factory=DictCursor)

        # Progress monitoring
        self.monitor = UniversalProgressMonitor(self.conn, display_mode="tui")

        # Setup monitoring delegates
        self.delegates = setup_all_delegates()
        for delegate in self.delegates:
            self.monitor.add_delegate(delegate)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()

    def cleanup(self):
        """Clean up resources"""
        if hasattr(self, "cursor"):
            self.cursor.close()
        if hasattr(self, "conn"):
            self.conn.close()
        if hasattr(self, "monitor"):
            self.monitor.stop()

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2, min=4, max=10)
    )
    def make_api_request(self, url: str) -> Dict[str, Any]:
        """Make API request with retry logic"""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed for {url}: {e}")
            raise

    def get_checkpoint_status(self) -> Dict[str, Any]:
        """Get current checkpoint status"""
        try:
            self.cursor.execute(
                """
                SELECT total_processed, total_estimated, completion_percentage, is_completed, last_ingestion_at
                FROM incremental.ingestion_checkpoints
                WHERE data_source = 'congress.gov'
                AND data_type = 'bills'
                AND category = %s
            """,
                (str(self.config.congress),),
            )

            result = self.cursor.fetchone()
            if result:
                return {
                    "total_processed": result[0] or 0,
                    "total_estimated": result[1],
                    "completion_percentage": result[2],
                    "is_completed": result[3],
                    "last_ingestion_at": result[4],
                }
            else:
                return {
                    "total_processed": 0,
                    "total_estimated": None,
                    "completion_percentage": 0.0,
                    "is_completed": False,
                    "last_ingestion_at": None,
                }
        except Exception as e:
            logger.error(f"Error getting checkpoint status: {e}")
            return {
                "total_processed": 0,
                "total_estimated": None,
                "completion_percentage": 0.0,
                "is_completed": False,
                "last_ingestion_at": None,
            }

    def update_checkpoint(
        self, processed_count: int, estimated_total: Optional[int] = None
    ):
        """Update checkpoint progress"""
        try:
            completion_percentage = (
                (processed_count / estimated_total * 100) if estimated_total else 0.0
            )

            self.cursor.execute(
                """
                INSERT INTO incremental.ingestion_checkpoints
                (data_source, data_type, category, total_processed, total_estimated,
                 completion_percentage, is_completed, last_ingestion_at)
                VALUES ('congress.gov', 'bills', %s, %s, %s, %s, false, %s)
                ON CONFLICT (data_source, data_type, category)
                DO UPDATE SET
                    total_processed = EXCLUDED.total_processed,
                    total_estimated = COALESCE(EXCLUDED.total_estimated, %s),
                    completion_percentage = EXCLUDED.completion_percentage,
                    last_ingestion_at = EXCLUDED.last_ingestion_at
            """,
                (
                    str(self.config.congress),
                    processed_count,
                    estimated_total,
                    completion_percentage,
                    datetime.now(),
                    estimated_total,
                ),
            )

            self.conn.commit()
            logger.info(f"Updated checkpoint: {processed_count} processed")

        except Exception as e:
            logger.error(f"Error updating checkpoint: {e}")
            self.conn.rollback()

    def mark_checkpoint_complete(self, total_processed: int):
        """Mark checkpoint as complete"""
        try:
            self.cursor.execute(
                """
                UPDATE incremental.ingestion_checkpoints
                SET is_completed = true, completion_percentage = 100.0, last_ingestion_at = %s
                WHERE data_source = 'congress.gov'
                AND data_type = 'bills'
                AND category = %s
            """,
                (datetime.now(), str(self.config.congress)),
            )

            self.conn.commit()
            logger.info(
                f"Marked checkpoint complete for Congress {self.config.congress}"
            )

        except Exception as e:
            logger.error(f"Error marking checkpoint complete: {e}")
            self.conn.rollback()

    def get_total_bills_estimate(self) -> Optional[int]:
        """Get estimate of total bills for this congress"""
        try:
            # First, try to get a small sample to estimate
            url = f"{self.config.base_url}/bill/{self.config.congress}?limit=1"
            data = self.make_api_request(url)

            if "bills" in data and data["bills"]:
                # Use pagination info to estimate total
                # Congress typically has 4,000-10,000 bills per session
                # We'll use a conservative estimate
                return 8000  # Conservative estimate for modern congresses

            return None

        except Exception as e:
            logger.error(f"Error getting bills estimate: {e}")
            return None

    def process_bill_batch(self, bills: List[Dict[str, Any]]) -> int:
        """Process a batch of bills and store in database"""
        if not bills:
            return 0

        processed_count = 0

        try:
            for bill in bills:
                # Extract bill data
                bill_data = {
                    "congress": self.config.congress,
                    "bill_id": bill.get("bill_id", ""),
                    "bill_type": bill.get("bill_type", ""),
                    "bill_number": bill.get("bill_number", ""),
                    "title": bill.get("title", ""),
                    "introduced_date": self.parse_date(bill.get("introduced_date")),
                    "update_date": self.parse_date(bill.get("update_date")),
                    "latest_action": bill.get("latest_action", {}).get("text", ""),
                    "latest_action_date": self.parse_date(
                        bill.get("latest_action", {}).get("actionDate")
                    ),
                    "sponsor_id": bill.get("sponsor", {}).get("bioguideId", ""),
                    "sponsor_name": bill.get("sponsor", {}).get("fullName", ""),
                    "sponsor_party": bill.get("sponsor", {}).get("party", ""),
                    "sponsor_state": bill.get("sponsor", {}).get("state", ""),
                    "policy_area": bill.get("policy_area", {}).get("name", ""),
                    "subjects": [s.get("name", "") for s in bill.get("subjects", [])],
                    "summaries": bill.get("summaries", []),
                    "text_versions": bill.get("textVersions", []),
                    "cosponsors": bill.get("cosponsors", []),
                    "related_bills": bill.get("related_bills", []),
                    "committees": bill.get("committees", []),
                    "api_data": bill,  # Store full API response
                }

                # Check if bill already exists (using fingerprinting)
                fingerprint = self.generate_fingerprint(bill_data)
                if self.is_bill_processed(bill_data["bill_id"], fingerprint):
                    continue

                # Insert bill
                self.insert_bill(bill_data, fingerprint)
                processed_count += 1

            self.conn.commit()
            return processed_count

        except Exception as e:
            logger.error(f"Error processing bill batch: {e}")
            self.conn.rollback()
            return 0

    def parse_date(self, date_str: Optional[str]) -> Optional[date]:
        """Parse date string"""
        if not date_str:
            return None

        try:
            return datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            try:
                return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ").date()
            except ValueError:
                return None

    def generate_fingerprint(self, bill_data: Dict[str, Any]) -> str:
        """Generate SHA-256 fingerprint for bill data"""
        import hashlib

        # Use key fields for fingerprint
        fingerprint_data = f"{bill_data['bill_id']}|{bill_data['title']}|{bill_data['latest_action']}|{bill_data['update_date']}"
        return hashlib.sha256(fingerprint_data.encode()).hexdigest()

    def is_bill_processed(self, bill_id: str, fingerprint: str) -> bool:
        """Check if bill has already been processed"""
        try:
            self.cursor.execute(
                """
                SELECT 1 FROM congress.bills
                WHERE bill_id = %s AND fingerprint = %s
                LIMIT 1
            """,
                (bill_id, fingerprint),
            )

            return self.cursor.fetchone() is not None

        except Exception as e:
            logger.error(f"Error checking if bill processed: {e}")
            return False

    def insert_bill(self, bill_data: Dict[str, Any], fingerprint: str):
        """Insert bill into database"""
        try:
            self.cursor.execute(
                """
                INSERT INTO congress.bills (
                    congress, bill_id, bill_type, bill_number, title,
                    introduced_date, update_date, latest_action, latest_action_date,
                    sponsor_id, sponsor_name, sponsor_party, sponsor_state,
                    policy_area, subjects, summaries, text_versions,
                    cosponsors, related_bills, committees, fingerprint, api_data
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (bill_id, fingerprint) DO NOTHING
            """,
                (
                    bill_data["congress"],
                    bill_data["bill_id"],
                    bill_data["bill_type"],
                    bill_data["bill_number"],
                    bill_data["title"],
                    bill_data["introduced_date"],
                    bill_data["update_date"],
                    bill_data["latest_action"],
                    bill_data["latest_action_date"],
                    bill_data["sponsor_id"],
                    bill_data["sponsor_name"],
                    bill_data["sponsor_party"],
                    bill_data["sponsor_state"],
                    bill_data["policy_area"],
                    bill_data["subjects"],
                    bill_data["summaries"],
                    bill_data["text_versions"],
                    bill_data["cosponsors"],
                    bill_data["related_bills"],
                    bill_data["committees"],
                    fingerprint,
                    bill_data["api_data"],
                ),
            )

        except Exception as e:
            logger.error(f"Error inserting bill: {e}")
            raise

    def ingest_congress_bills(self) -> Dict[str, Any]:
        """Main ingestion method for Congress bills"""
        logger.info(f"Starting bills ingestion for Congress {self.config.congress}")

        # Get current checkpoint status
        checkpoint = self.get_checkpoint_status()
        start_offset = checkpoint["total_processed"]

        logger.info(f"Resuming from offset: {start_offset}")

        # Get total estimate
        if not checkpoint["total_estimated"]:
            estimated_total = self.get_total_bills_estimate()
            if estimated_total:
                self.update_checkpoint(start_offset, estimated_total)
                self.monitor.set_total_estimated(estimated_total)
        else:
            self.monitor.set_total_estimated(checkpoint["total_estimated"])

        # Start monitoring
        self.monitor.start()

        total_processed = start_offset
        batch_count = 0

        try:
            while True:
                # Fetch batch of bills
                url = f"{self.config.base_url}/bill/{self.config.congress}?offset={total_processed}&limit={self.config.batch_size}"

                logger.info(
                    f"Fetching bills batch {batch_count + 1} (offset: {total_processed})"
                )

                try:
                    data = self.make_api_request(url)

                    if "bills" not in data or not data["bills"]:
                        logger.info("No more bills available")
                        break

                    bills = data["bills"]
                    batch_processed = self.process_bill_batch(bills)

                    if batch_processed > 0:
                        total_processed += batch_processed
                        self.update_checkpoint(
                            total_processed, checkpoint["total_estimated"]
                        )

                        # Update monitor
                        self.monitor.add_progress(batch_processed)
                        batch_count += 1

                        logger.info(
                            f"Processed batch {batch_count}: {batch_processed} bills (total: {total_processed})"
                        )

                    # Check if we've reached the end
                    if len(bills) < self.config.batch_size:
                        logger.info("Reached end of available bills")
                        break

                    # Small delay to respect rate limits
                    import time

                    time.sleep(0.1)  # 100ms delay = 10 requests/second max

                except Exception as e:
                    logger.error(f"Error processing batch {batch_count + 1}: {e}")
                    break

            # Mark checkpoint complete
            self.mark_checkpoint_complete(total_processed)

            result = {
                "congress": self.config.congress,
                "status": "completed",
                "total_processed": total_processed,
                "batches_processed": batch_count,
                "final_offset": total_processed,
            }

            logger.info(
                f"Congress {self.config.congress} bills ingestion completed: {result}"
            )
            return result

        except Exception as e:
            logger.error(f"Error during bills ingestion: {e}")
            return {
                "congress": self.config.congress,
                "status": "error",
                "error": str(e),
                "total_processed": total_processed,
                "batches_processed": batch_count,
            }
        finally:
            self.monitor.stop()


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Ingest Congress.gov bills data")
    parser.add_argument(
        "--congress", type=int, required=True, help="Congress number (e.g., 117, 118)"
    )
    parser.add_argument(
        "--batch-size", type=int, default=50, help="Batch size for API calls"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Dry run (no actual ingestion)"
    )

    args = parser.parse_args()

    # Validate API keys first
    logger.info("🔍 Validating all required API keys...")
    key_validation = validate_all_api_keys()
    if not key_validation["valid"]:
        logger.error("❌ API key validation failed")
        for error in key_validation["errors"]:
            logger.error(f"   🚫 {error}")
        sys.exit(1)

    # Verify production mode
    mode = get_ingestion_mode_from_env()
    if mode.value != "production":
        logger.error(f"❌ Production mode required. Current mode: {mode.value}")
        sys.exit(1)

    logger.info("✅ API keys validated - starting ingestion")

    # Create configuration
    config = CongressBillsConfig(
        congress=args.congress,
        batch_size=args.batch_size,
        api_key=get_api_key_from_env("CONGRESS_API_KEY"),
    )

    if args.dry_run:
        logger.info("DRY RUN: Would ingest Congress bills data")
        logger.info(f"Congress: {config.congress}")
        logger.info(f"Batch size: {config.batch_size}")
        logger.info(f"API endpoint: {config.base_url}")
        return

    # Run ingestion
    try:
        with CongressBillsIngestor(config) as ingestor:
            result = ingestor.ingest_congress_bills()

            if result["status"] == "completed":
                logger.info(
                    f"🎉 Congress {config.congress} bills ingestion completed successfully!"
                )
                logger.info(f"📊 Total processed: {result['total_processed']:,}")
                logger.info(f"📦 Batches processed: {result['batches_processed']}")
            else:
                logger.error(
                    f"❌ Congress {config.congress} bills ingestion failed: {result.get('error', 'Unknown error')}"
                )
                sys.exit(1)

    except KeyboardInterrupt:
        logger.info("⚠️ Ingestion interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
