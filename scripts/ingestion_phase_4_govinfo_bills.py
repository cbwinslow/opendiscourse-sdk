#!/usr/bin/env python3
"""
Phase 4: GovInfo Bills Data Ingestion

This script handles ingestion of GovInfo bills data for specified congresses:
- Ingests bills for Congress 117 and 118 from GovInfo.gov
- Handles collection-based processing with granule extraction
- Implements rate limiting (40 requests per minute)
- Provides real-time progress monitoring and checkpointing

ASSIGNED TO: AI Agent responsible for GovInfo bills ingestion
DEPENDENCIES: Phase 1 (validation) must complete successfully
"""

import hashlib
import json
import os
import sys
import time
from datetime import datetime
from typing import Any, Dict, List, Tuple

import psycopg2
import requests
from tenacity import retry, stop_after_attempt, wait_exponential

# Add project path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# Load environment variables
from dotenv import load_dotenv
from ingestion_config import get_ingestion_mode_from_env, validate_all_api_keys

load_dotenv()

class Phase4GovInfoBillsIngestion:
    """Phase 4: GovInfo Bills Data Ingestion"""

    def __init__(self):
        self.phase_start = datetime.now()
        self.api_base_url = "https://api.govinfo.gov"
        self.govinfo_api_key = os.getenv('GOVINFO_API_KEY')
        self.rate_limit_delay = 1.5  # 40 requests per minute = 1.5 seconds between requests
        self.ingestion_stats = {}

        # Validate prerequisites
        self._validate_prerequisites()

    def _validate_prerequisites(self):
        """Validate Phase 1 prerequisites"""
        print("🔍 Validating Phase 1 prerequisites...")

        # Check API keys
        key_validation = validate_all_api_keys()
        if not key_validation['valid']:
            raise ValueError("Phase 1 validation failed - API keys invalid")

        # Check production mode
        mode = get_ingestion_mode_from_env()
        if mode.value != 'production':
            raise ValueError("Phase 1 validation failed - not in production mode")

        # Check specific key
        if not self.govinfo_api_key:
            raise ValueError("GOVINFO_API_KEY not found")

        print("✅ Phase 1 prerequisites validated")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def _make_api_request(self, url: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make API request with retry logic and rate limiting"""
        headers = {
            'X-Api-Key': self.govinfo_api_key,
            'Accept': 'application/json'
        }

        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()

        # Rate limiting - GovInfo.gov allows 40 requests per minute
        time.sleep(self.rate_limit_delay)

        return response.json()

    def _get_collections_for_congress(self, congress: int) -> List[Dict[str, Any]]:
        """Get bill collections for a specific congress"""
        print(f"🔍 Getting bill collections for Congress {congress}...")

        collections = []
        offset = 0
        page_size = 100

        while True:
            try:
                url = f"{self.api_base_url}/collections"
                params = {
                    'api_key': self.govinfo_api_key,
                    'congress': congress,
                    'collection': 'BILLS',
                    'pageSize': page_size,
                    'offset': offset
                }

                response_data = self._make_api_request(url, params)
                packages = response_data.get('packages', [])

                if not packages:
                    break

                collections.extend(packages)
                offset += page_size

                if len(packages) < page_size:
                    break

            except Exception as e:
                print(f"❌ Error getting collections: {e}")
                break

        print(f"📊 Found {len(collections)} bill collections for Congress {congress}")
        return collections

    def _generate_fingerprint(self, bill_data: Dict[str, Any]) -> str:
        """Generate SHA-256 fingerprint for bill data"""
        fingerprint_data = {
            'package_id': bill_data.get('packageId'),
            'title': bill_data.get('title'),
            'congress': bill_data.get('congress'),
            'bill_type': bill_data.get('billType'),
            'bill_number': bill_data.get('billNumber')
        }

        fingerprint_str = json.dumps(fingerprint_data, sort_keys=True)
        return hashlib.sha256(fingerprint_str.encode()).hexdigest()

    def _save_bill_to_database(self, bill_data: Dict[str, Any], granules: List[Dict[str, Any]]) -> bool:
        """Save bill data to database with duplicate detection"""
        fingerprint = self._generate_fingerprint(bill_data)

        try:
            conn = psycopg2.connect(database='cbwinslow', user='cbwinslow')
            cursor = conn.cursor()

            # Check for duplicates
            cursor.execute("""
                SELECT COUNT(*) FROM congress.bills
                WHERE bill_id = %s OR fingerprint = %s
            """, (bill_data.get('packageId'), fingerprint))

            if cursor.fetchone()[0] > 0:
                cursor.close()
                conn.close()
                return False  # Duplicate, skip

            # Parse bill info from packageId (format: BILLS-118s1234is)
            package_id = bill_data.get('packageId', '')
            bill_parts = package_id.split('-')
            if len(bill_parts) >= 2:
                bill_code = bill_parts[1]
                # Extract congress and bill info
                congress = int(bill_code[:3]) if bill_code[:3].isdigit() else None
                bill_type = bill_code[3] if len(bill_code) > 3 else None
                bill_number = bill_code[4:] if len(bill_code) > 4 else None
            else:
                congress = bill_data.get('congress')
                bill_type = None
                bill_number = None

            # Insert new bill
            cursor.execute("""
                INSERT INTO congress.bills (
                    bill_id, congress_number, bill_type, bill_number, origin_chamber,
                    introduced_date, latest_action_date, latest_action_text,
                    policy_area, summary_text, summary_last_updated, status,
                    official_title, sponsor_bioguide_id, committee_ids,
                    fingerprint, created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                bill_data.get('packageId'),
                congress,
                bill_type,
                bill_number,
                bill_data.get('originChamber'),
                bill_data.get('dateIssued'),
                bill_data.get('dateIssued'),
                None,  # Latest action text
                None,  # Policy area
                bill_data.get('summary'),
                bill_data.get('lastModified'),
                bill_data.get('status', 'ACTIVE'),
                bill_data.get('title'),
                None,  # Sponsor bioguide_id
                [],  # Committee IDs
                fingerprint,
                datetime.now(),
                datetime.now()
            ))

            conn.commit()
            cursor.close()
            conn.close()
            return True

        except Exception as e:
            print(f"❌ Error saving bill {bill_data.get('packageId')}: {e}")
            return False

    def _update_checkpoint(self, congress: int, processed: int, total: int):
        """Update checkpoint progress"""
        try:
            conn = psycopg2.connect(database='cbwinslow', user='cbwinslow')
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO incremental.ingestion_checkpoints (
                    data_source, data_type, category, offset, total_processed,
                    last_ingestion_at, status
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (data_source, data_type, category)
                DO UPDATE SET
                    offset = EXCLUDED.offset,
                    total_processed = EXCLUDED.total_processed,
                    last_ingestion_at = EXCLUDED.last_ingestion_at,
                    status = EXCLUDED.status
            """, (
                'govinfo.gov', 'bills', str(congress),
                processed, total, datetime.now(), 'IN_PROGRESS'
            ))

            conn.commit()
            cursor.close()
            conn.close()

        except Exception as e:
            print(f"❌ Error updating checkpoint: {e}")

    def _get_checkpoint(self, congress: int) -> Tuple[int, int]:
        """Get checkpoint progress for a congress"""
        try:
            conn = psycopg2.connect(database='cbwinslow', user='cbwinslow')
            cursor = conn.cursor()

            cursor.execute("""
                SELECT offset, total_processed FROM incremental.ingestion_checkpoints
                WHERE data_source = 'govinfo.gov' AND data_type = 'bills' AND category = %s
            """, (str(congress),))

            result = cursor.fetchone()
            cursor.close()
            conn.close()

            if result:
                return result[0], result[1]
            else:
                return 0, 0

        except Exception as e:
            print(f"❌ Error getting checkpoint: {e}")
            return 0, 0

    def ingest_govinfo_bills(self, congress: int) -> Dict[str, Any]:
        """Ingest bills for a specific congress from GovInfo"""
        print(f"\n🏛️  Ingesting GovInfo Congress {congress} Bills...")

        start_time = datetime.now()
        processed, total_processed = self._get_checkpoint(congress)

        if total_processed > 0:
            print(f"🔄 Resuming from {processed} packages processed")

        # Get all collections for this congress
        collections = self.get_collections_for_congress(congress)

        # Skip already processed collections
        if processed > 0 and processed < len(collections):
            collections = collections[processed:]
            print(f"📊 Resuming from collection {processed}")

        ingested_count = 0
        duplicate_count = 0
        error_count = 0

        for i, collection in enumerate(collections):
            try:
                # Get package details
                package_id = collection.get('packageId')
                url = f"{self.api_base_url}/packages/{package_id}"

                package_data = self._make_api_request(url)

                # Get granules (bill versions, amendments, etc.)
                granules_url = f"{self.api_base_url}/collections/{package_id}/granules"
                granules_response = self._make_api_request(granules_url)
                granules = granules_response.get('granules', [])

                # Save to database
                if self._save_bill_to_database(package_data, granules):
                    ingested_count += 1
                else:
                    duplicate_count += 1

                # Update progress
                processed = i + 1
                total_processed += 1

                # Update checkpoint every 10 packages
                if processed % 10 == 0:
                    self._update_checkpoint(congress, processed, total_processed)
                    print(f"📊 Progress: {processed}/{len(collections)} packages, {ingested_count} ingested, {duplicate_count} duplicates")

            except Exception as e:
                print(f"❌ Error processing package {collection.get('packageId')}: {e}")
                error_count += 1
                continue

        # Final checkpoint update
        self._update_checkpoint(congress, processed, total_processed)

        duration = (datetime.now() - start_time).total_seconds()

        stats = {
            'congress': congress,
            'start_time': start_time.isoformat(),
            'end_time': datetime.now().isoformat(),
            'duration_seconds': duration,
            'total_packages': len(collections),
            'packages_processed': processed,
            'newly_ingested': ingested_count,
            'duplicates_skipped': duplicate_count,
            'errors': error_count,
            'status': 'COMPLETED'
        }

        print(f"✅ GovInfo Congress {congress} Bills: {ingested_count} ingested, {duplicate_count} duplicates, {duration:.1f}s")
        return stats

    def run_phase_4_ingestion(self, congresses: List[int] = None) -> Dict[str, Any]:
        """Run complete Phase 4 ingestion"""
        if congresses is None:
            congresses = [117, 118]

        print("\n" + "="*60)
        print("🏛️  PHASE 4: GOVINFO BILLS INGESTION")
        print("="*60)

        all_stats = []
        total_ingested = 0
        total_duplicates = 0
        total_errors = 0

        for congress in congresses:
            stats = self.ingest_govinfo_bills(congress)
            all_stats.append(stats)
            total_ingested += stats['newly_ingested']
            total_duplicates += stats['duplicates_skipped']
            total_errors += stats['errors']

        # Generate summary
        summary = {
            'phase': 4,
            'phase_name': 'GovInfo Bills Ingestion',
            'start_time': self.phase_start.isoformat(),
            'end_time': datetime.now().isoformat(),
            'duration_seconds': (datetime.now() - self.phase_start).total_seconds(),
            'congresses_processed': congresses,
            'total_newly_ingested': total_ingested,
            'total_duplicates_skipped': total_duplicates,
            'total_errors': total_errors,
            'individual_stats': all_stats,
            'overall_status': 'COMPLETED' if total_errors == 0 else 'COMPLETED_WITH_ERRORS'
        }

        print("\n" + "="*60)
        print(f"📊 PHASE 4 SUMMARY: {summary['overall_status']}")
        print(f"🏛️  Congresses: {', '.join(map(str, congresses))}")
        print(f"📄 Bills Ingested: {total_ingested:,}")
        print(f"🔄 Duplicates Skipped: {total_duplicates:,}")
        print(f"❌ Errors: {total_errors}")
        print(f"⏱️  Duration: {summary['duration_seconds']:.1f} seconds")
        print("="*60)

        return summary

    def save_ingestion_results(self, filename: str = None, congresses: List[int] = None) -> str:
        """Save ingestion results to file"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"phase_4_govinfo_bills_{timestamp}.json"

        summary = self.run_phase_4_ingestion(congresses)

        try:
            with open(filename, 'w') as f:
                json.dump(summary, f, indent=2, default=str)

            print(f"📄 Ingestion results saved to: {filename}")
            return filename

        except Exception as e:
            print(f"❌ Error saving ingestion results: {e}")
            return ""

def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(description='Phase 4: GovInfo Bills Ingestion')
    parser.add_argument('--congresses', '-c', nargs='+', type=int,
                       default=[117, 118], help='Congress numbers to ingest')
    parser.add_argument('--output', '-o', help='Output filename (default: auto-generated)')
    parser.add_argument('--save', action='store_true', help='Save results to file')

    args = parser.parse_args()

    try:
        ingester = Phase4GovInfoBillsIngestion()

        if args.save:
            ingester.save_ingestion_results(args.output, args.congresses)
        else:
            ingester.run_phase_4_ingestion(args.congresses)

    except Exception as e:
        print(f"❌ Phase 4 ingestion failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
