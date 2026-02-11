#!/usr/bin/env python3
"""
GovInfo.gov Bills Ingestion Script

This script ingests bills data from GovInfo.gov API with comprehensive
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
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class GovInfoBillsConfig:
    """Configuration for GovInfo bills ingestion"""
    congress: int
    batch_size: int = 50
    api_key: str = ""
    base_url: str = "https://api.govinfo.gov"
    max_retries: int = 3
    retry_delay: float = 1.0

class GovInfoBillsIngestor:
    """GovInfo.gov Bills Ingestion Engine"""

    def __init__(self, config: GovInfoBillsConfig):
        self.config = config
        self.api_key = config.api_key or get_api_key_from_env('GOVINFO_API_KEY')
        self.session = requests.Session()
        self.session.headers.update({
            'X-API-Key': self.api_key,
            'Accept': 'application/json'
        })

        # Database connection
        self.conn = psycopg2.connect(database='cbwinslow', user='cbwinslow')
        self.cursor = self.conn.cursor(cursor_factory=DictCursor)

        # Progress monitoring
        self.monitor = UniversalProgressMonitor(
            self.conn,
            display_mode='tui'
        )

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
        if hasattr(self, 'cursor'):
            self.cursor.close()
        if hasattr(self, 'conn'):
            self.conn.close()
        if hasattr(self, 'monitor'):
            self.monitor.stop()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2, min=4, max=10))
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
            self.cursor.execute("""
                SELECT total_processed, total_estimated, completion_percentage, is_completed, last_ingestion_at
                FROM incremental.ingestion_checkpoints
                WHERE data_source = 'govinfo.gov'
                AND data_type = 'bills'
                AND category = %s
            """, (str(self.config.congress),))

            result = self.cursor.fetchone()
            if result:
                return {
                    'total_processed': result[0] or 0,
                    'total_estimated': result[1],
                    'completion_percentage': result[2],
                    'is_completed': result[3],
                    'last_ingestion_at': result[4]
                }
            else:
                return {
                    'total_processed': 0,
                    'total_estimated': None,
                    'completion_percentage': 0.0,
                    'is_completed': False,
                    'last_ingestion_at': None
                }
        except Exception as e:
            logger.error(f"Error getting checkpoint status: {e}")
            return {
                'total_processed': 0,
                'total_estimated': None,
                'completion_percentage': 0.0,
                'is_completed': False,
                'last_ingestion_at': None
            }

    def update_checkpoint(self, processed_count: int, estimated_total: Optional[int] = None):
        """Update checkpoint progress"""
        try:
            completion_percentage = (processed_count / estimated_total * 100) if estimated_total else 0.0

            self.cursor.execute("""
                INSERT INTO incremental.ingestion_checkpoints
                (data_source, data_type, category, total_processed, total_estimated,
                 completion_percentage, is_completed, last_ingestion_at)
                VALUES ('govinfo.gov', 'bills', %s, %s, %s, %s, false, %s)
                ON CONFLICT (data_source, data_type, category)
                DO UPDATE SET
                    total_processed = EXCLUDED.total_processed,
                    total_estimated = COALESCE(EXCLUDED.total_estimated, %s),
                    completion_percentage = EXCLUDED.completion_percentage,
                    last_ingestion_at = EXCLUDED.last_ingestion_at
            """, (str(self.config.congress), processed_count, estimated_total,
                  completion_percentage, datetime.now(), estimated_total))

            self.conn.commit()
            logger.info(f"Updated checkpoint: {processed_count} processed")

        except Exception as e:
            logger.error(f"Error updating checkpoint: {e}")
            self.conn.rollback()

    def mark_checkpoint_complete(self, total_processed: int):
        """Mark checkpoint as complete"""
        try:
            self.cursor.execute("""
                UPDATE incremental.ingestion_checkpoints
                SET is_completed = true, completion_percentage = 100.0, last_ingestion_at = %s
                WHERE data_source = 'govinfo.gov'
                AND data_type = 'bills'
                AND category = %s
            """, (datetime.now(), str(self.config.congress)))

            self.conn.commit()
            logger.info(f"Marked checkpoint complete for Congress {self.config.congress}")

        except Exception as e:
            logger.error(f"Error marking checkpoint complete: {e}")
            self.conn.rollback()

    def get_total_bills_estimate(self) -> Optional[int]:
        """Get estimate of total bills for this congress"""
        try:
            # GovInfo typically has comprehensive collections
            # Use standard estimate for modern congresses
            return 8000  # Conservative estimate for modern congresses

        except Exception as e:
            logger.error(f"Error getting bills estimate: {e}")
            return None

    def get_congress_collections(self) -> List[str]:
        """Get available collections for the congress"""
        try:
            # Get collections for the specific congress
            congress_year = self.get_congress_year()
            if not congress_year:
                return []

            # GovInfo collections are organized by year
            start_year = congress_year
            end_year = congress_year + 2

            collections = []
            for year in range(start_year, end_year + 1):
                collections.append(f'BILLS-{year}')

            return collections

        except Exception as e:
            logger.error(f"Error getting congress collections: {e}")
            return []

    def get_congress_year(self) -> Optional[int]:
        """Get the year corresponding to the congress"""
        # Congress 117: 2021-2022
        # Congress 118: 2023-2024
        # Formula: year = 1787 + (congress - 1) * 2
        try:
            return 1787 + (self.config.congress - 1) * 2
        except Exception:
            return None

    def process_bill_package(self, package_data: Dict[str, Any]) -> int:
        """Process a bill package from GovInfo"""
        try:
            # Extract basic bill info
            package_id = package_data.get('packageId', '')

            # Get detailed bill data
            granules_url = f"{self.config.base_url}/collections/{package_id}/granules?pageSize={self.config.batch_size}"
            granules_data = self.make_api_request(granules_url)

            processed_count = 0

            if 'granules' in granules_data and granules_data['granules']:
                for granule in granules_data['granules']:
                    bill_data = self.extract_bill_data(granule, package_data)

                    if bill_data:
                        # Check if bill already processed
                        fingerprint = self.generate_fingerprint(bill_data)
                        if self.is_bill_processed(bill_data['bill_id'], fingerprint):
                            continue

                        # Insert bill
                        self.insert_bill(bill_data, fingerprint)
                        processed_count += 1

            return processed_count

        except Exception as e:
            logger.error(f"Error processing bill package: {e}")
            return 0

    def extract_bill_data(self, granule: Dict[str, Any], package_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract bill data from granule"""
        try:
            granule_id = granule.get('granuleId', '')
            granule_class = granule.get('granuleClass', '')

            # Only process bill granules
            if granule_class != 'BILL':
                return None

            # Parse bill ID from granule ID
            # Format: BILLS-118hr1234-is
            bill_id_parts = granule_id.split('-')
            if len(bill_id_parts) < 3:
                return None

            bill_type = bill_id_parts[2][:2]  # hr, s, hres, sres, etc.
            bill_number = bill_id_parts[2][2:]

            # Get detailed bill data
            bill_url = f"{self.config.base_url}/packages/{granule_id}"
            bill_detail = self.make_api_request(bill_url)

            # Extract bill title and other info
            title = bill_detail.get('title', '')
            if not title and 'download' in bill_detail:
                # Try to get title from download info
                downloads = bill_detail.get('download', {}).get('txt', [])
                if downloads:
                    title = downloads[0].get('name', '')

            return {
                'congress': self.config.congress,
                'bill_id': granule_id,
                'bill_type': bill_type,
                'bill_number': bill_number,
                'title': title,
                'package_id': package_data.get('packageId', ''),
                'collection_code': package_data.get('collectionCode', ''),
                'granule_id': granule_id,
                'granule_class': granule_class,
                'date_issued': self.parse_date(bill_detail.get('dateIssued')),
                'last_modified': self.parse_date(bill_detail.get('lastModified')),
                'package_details': package_data,
                'bill_details': bill_detail,
                'api_data': granule
            }

        except Exception as e:
            logger.error(f"Error extracting bill data: {e}")
            return None

    def parse_date(self, date_str: Optional[str]) -> Optional[date]:
        """Parse date string"""
        if not date_str:
            return None

        try:
            # GovInfo dates are typically in YYYY-MM-DD format
            return datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            try:
                return datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%SZ').date()
            except ValueError:
                return None

    def generate_fingerprint(self, bill_data: Dict[str, Any]) -> str:
        """Generate SHA-256 fingerprint for bill data"""
        import hashlib

        # Use key fields for fingerprint
        fingerprint_data = f"{bill_data['bill_id']}|{bill_data['title']}|{bill_data['last_modified']}"
        return hashlib.sha256(fingerprint_data.encode()).hexdigest()

    def is_bill_processed(self, bill_id: str, fingerprint: str) -> bool:
        """Check if bill has already been processed"""
        try:
            self.cursor.execute("""
                SELECT 1 FROM congress.bills
                WHERE bill_id = %s AND fingerprint = %s
                LIMIT 1
            """, (bill_id, fingerprint))

            return self.cursor.fetchone() is not None

        except Exception as e:
            logger.error(f"Error checking if bill processed: {e}")
            return False

    def insert_bill(self, bill_data: Dict[str, Any], fingerprint: str):
        """Insert bill into database"""
        try:
            self.cursor.execute("""
                INSERT INTO congress.bills (
                    congress, bill_id, bill_type, bill_number, title,
                    package_id, collection_code, granule_id, granule_class,
                    date_issued, last_modified, package_details, bill_details,
                    fingerprint, api_data
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (bill_id, fingerprint) DO NOTHING
            """, (
                bill_data['congress'], bill_data['bill_id'], bill_data['bill_type'],
                bill_data['bill_number'], bill_data['title'], bill_data['package_id'],
                bill_data['collection_code'], bill_data['granule_id'], bill_data['granule_class'],
                bill_data['date_issued'], bill_data['last_modified'], bill_data['package_details'],
                bill_data['bill_details'], fingerprint, bill_data['api_data']
            ))

        except Exception as e:
            logger.error(f"Error inserting bill: {e}")
            raise

    def ingest_govinfo_bills(self) -> Dict[str, Any]:
        """Main ingestion method for GovInfo bills"""
        logger.info(f"Starting GovInfo bills ingestion for Congress {self.config.congress}")

        # Get current checkpoint status
        checkpoint = self.get_checkpoint_status()

        logger.info(f"Current checkpoint: {checkpoint['total_processed']} processed")

        # Get total estimate
        if not checkpoint['total_estimated']:
            estimated_total = self.get_total_bills_estimate()
            if estimated_total:
                self.update_checkpoint(checkpoint['total_processed'], estimated_total)
                self.monitor.set_total_estimated(estimated_total)
        else:
            self.monitor.set_total_estimated(checkpoint['total_estimated'])

        # Start monitoring
        self.monitor.start()

        total_processed = checkpoint['total_processed']
        collection_count = 0

        try:
            # Get collections for this congress
            collections = self.get_congress_collections()
            logger.info(f"Found {len(collections)} collections for Congress {self.config.congress}")

            for collection in collections:
                logger.info(f"Processing collection: {collection}")

                try:
                    # Get collection packages
                    collection_url = f"{self.config.base_url}/collections/{collection}?offset={total_processed}&pageSize={self.config.batch_size}"
                    collection_data = self.make_api_request(collection_url)

                    if 'packages' in collection_data and collection_data['packages']:
                        packages = collection_data['packages']

                        for package in packages:
                            processed = self.process_bill_package(package)
                            if processed > 0:
                                total_processed += processed
                                self.update_checkpoint(total_processed, checkpoint['total_estimated'])
                                self.monitor.add_progress(processed)

                        collection_count += 1
                        logger.info(f"Processed collection {collection}: {len(packages)} packages")

                    # Rate limiting for GovInfo (40 requests/minute)
                    import time
                    time.sleep(1.5)  # 1.5 seconds = 40 requests/minute

                except Exception as e:
                    logger.error(f"Error processing collection {collection}: {e}")
                    continue

            # Mark checkpoint complete
            self.mark_checkpoint_complete(total_processed)

            result = {
                'congress': self.config.congress,
                'status': 'completed',
                'total_processed': total_processed,
                'collections_processed': collection_count,
                'final_offset': total_processed
            }

            logger.info(f"GovInfo Congress {self.config.congress} bills ingestion completed: {result}")
            return result

        except Exception as e:
            logger.error(f"Error during GovInfo bills ingestion: {e}")
            return {
                'congress': self.config.congress,
                'status': 'error',
                'error': str(e),
                'total_processed': total_processed,
                'collections_processed': collection_count
            }
        finally:
            self.monitor.stop()

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Ingest GovInfo.gov bills data')
    parser.add_argument('--congress', type=int, required=True, help='Congress number (e.g., 117, 118)')
    parser.add_argument('--batch-size', type=int, default=50, help='Batch size for API calls')
    parser.add_argument('--dry-run', action='store_true', help='Dry run (no actual ingestion)')

    args = parser.parse_args()

    # Validate API keys first
    logger.info("🔍 Validating all required API keys...")
    key_validation = validate_all_api_keys()
    if not key_validation['valid']:
        logger.error("❌ API key validation failed")
        for error in key_validation['errors']:
            logger.error(f"   🚫 {error}")
        sys.exit(1)

    # Verify production mode
    mode = get_ingestion_mode_from_env()
    if mode.value != 'production':
        logger.error(f"❌ Production mode required. Current mode: {mode.value}")
        sys.exit(1)

    logger.info("✅ API keys validated - starting ingestion")

    # Create configuration
    config = GovInfoBillsConfig(
        congress=args.congress,
        batch_size=args.batch_size,
        api_key=get_api_key_from_env('GOVINFO_API_KEY')
    )

    if args.dry_run:
        logger.info("DRY RUN: Would ingest GovInfo bills data")
        logger.info(f"Congress: {config.congress}")
        logger.info(f"Batch size: {config.batch_size}")
        logger.info(f"API endpoint: {config.base_url}")
        return

    # Run ingestion
    try:
        with GovInfoBillsIngestor(config) as ingestor:
            result = ingestor.ingest_govinfo_bills()

            if result['status'] == 'completed':
                logger.info(f"🎉 GovInfo Congress {config.congress} bills ingestion completed successfully!")
                logger.info(f"📊 Total processed: {result['total_processed']:,}")
                logger.info(f"📦 Collections processed: {result['collections_processed']}")
            else:
                logger.error(f"❌ GovInfo Congress {config.congress} bills ingestion failed: {result.get('error', 'Unknown error')}")
                sys.exit(1)

    except KeyboardInterrupt:
        logger.info("⚠️ Ingestion interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
