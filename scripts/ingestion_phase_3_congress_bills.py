#!/usr/bin/env python3
"""
Phase 3: Congress Bills Data Ingestion

This script handles ingestion of Congress bills data for specified congresses:
- Ingests bills for Congress 117 and 118
- Handles offset-based pagination with proper checkpointing
- Implements duplicate detection via fingerprinting
- Provides real-time progress monitoring and rate limiting

ASSIGNED TO: AI Agent responsible for Congress bills ingestion
DEPENDENCIES: Phase 1 (validation) must complete successfully
"""

import hashlib
import json
import os
import sys
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

class Phase3CongressBillsIngestion:
    """Phase 3: Congress Bills Data Ingestion"""

    def __init__(self):
        self.phase_start = datetime.now()
        self.api_base_url = "https://api.congress.gov/v3"
        self.congress_api_key = os.getenv('CONGRESS_API_KEY')
        self.batch_size = 50
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
        if not self.congress_api_key:
            raise ValueError("CONGRESS_API_KEY not found")

        print("✅ Phase 1 prerequisites validated")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def _make_api_request(self, url: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make API request with retry logic"""
        headers = {
            'X-API-Key': self.congress_api_key,
            'Accept': 'application/json'
        }

        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()

        # Rate limiting - Congress.gov allows 10 requests per second
        time.sleep(0.1)

        return response.json()

    def _generate_fingerprint(self, bill_data: Dict[str, Any]) -> str:
        """Generate SHA-256 fingerprint for bill data"""
        # Create a consistent string representation
        fingerprint_data = {
            'congress': bill_data.get('congress'),
            'bill_type': bill_data.get('billType'),
            'bill_number': bill_data.get('billNumber'),
            'title': bill_data.get('title'),
            'introduced_date': bill_data.get('introducedDate')
        }

        fingerprint_str = json.dumps(fingerprint_data, sort_keys=True)
        return hashlib.sha256(fingerprint_str.encode()).hexdigest()

    def _save_bill_to_database(self, bill_data: Dict[str, Any]) -> bool:
        """Save bill data to database with duplicate detection"""
        fingerprint = self._generate_fingerprint(bill_data)

        try:
            conn = psycopg2.connect(database='cbwinslow', user='cbwinslow')
            cursor = conn.cursor()

            # Check for duplicates
            cursor.execute("""
                SELECT COUNT(*) FROM congress.bills
                WHERE congress_number = %s AND bill_type = %s AND bill_number = %s
            """, (
                bill_data.get('congress'),
                bill_data.get('billType'),
                bill_data.get('billNumber')
            ))

            if cursor.fetchone()[0] > 0:
                cursor.close()
                conn.close()
                return False  # Duplicate, skip

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
                bill_data.get('billId') or str(hash(fingerprint)),
                bill_data.get('congress'),
                bill_data.get('billType'),
                bill_data.get('billNumber'),
                bill_data.get('originChamber'),
                bill_data.get('introducedDate'),
                bill_data.get('latestAction', {}).get('actionDate'),
                bill_data.get('latestAction', {}).get('text'),
                bill_data.get('policyArea', {}).get('name'),
                bill_data.get('summary', {}).get('text'),
                bill_data.get('summary', {}).get('updateDate'),
                bill_data.get('status'),
                bill_data.get('title'),
                bill_data.get('sponsors', [{}])[0].get('bioguideId') if bill_data.get('sponsors') else None,
                bill_data.get('committees', []),
                fingerprint,
                datetime.now(),
                datetime.now()
            ))

            conn.commit()
            cursor.close()
            conn.close()
            return True

        except Exception as e:
            print(f"❌ Error saving bill {bill_data.get('billType')}-{bill_data.get('billNumber')}: {e}")
            return False

    def _update_checkpoint(self, congress: int, offset: int, total_processed: int):
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
                'congress.gov', 'bills', str(congress),
                offset, total_processed, datetime.now(), 'IN_PROGRESS'
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
                WHERE data_source = 'congress.gov' AND data_type = 'bills' AND category = %s
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

    def ingest_congress_bills(self, congress: int) -> Dict[str, Any]:
        """Ingest bills for a specific congress"""
        print(f"\n📜 Ingesting Congress {congress} Bills...")

        start_time = datetime.now()
        offset, total_processed = self._get_checkpoint(congress)

        if total_processed > 0:
            print(f"🔄 Resuming from offset {offset} ({total_processed} already processed)")

        ingested_count = 0
        duplicate_count = 0
        error_count = 0

        while True:
            try:
                # Make API request
                url = f"{self.api_base_url}/bill/{congress}"
                params = {
                    'limit': self.batch_size,
                    'offset': offset
                }

                response_data = self._make_api_request(url, params)
                bills = response_data.get('bills', [])

                if not bills:
                    print("✅ No more bills to ingest")
                    break

                # Process batch
                batch_ingested = 0
                for bill in bills:
                    if self._save_bill_to_database(bill):
                        batch_ingested += 1
                        ingested_count += 1
                    else:
                        duplicate_count += 1

                # Update progress
                offset += self.batch_size
                total_processed += len(bills)

                # Update checkpoint every 5 batches
                if offset % (self.batch_size * 5) == 0:
                    self._update_checkpoint(congress, offset, total_processed)
                    print(f"📊 Progress: {total_processed} processed, {ingested_count} ingested, {duplicate_count} duplicates")

                # Check if we've reached the end
                if len(bills) < self.batch_size:
                    break

            except Exception as e:
                print(f"❌ Error processing batch at offset {offset}: {e}")
                error_count += 1
                break

        # Final checkpoint update
        self._update_checkpoint(congress, offset, total_processed)

        duration = (datetime.now() - start_time).total_seconds()

        stats = {
            'congress': congress,
            'start_time': start_time.isoformat(),
            'end_time': datetime.now().isoformat(),
            'duration_seconds': duration,
            'total_processed': total_processed,
            'newly_ingested': ingested_count,
            'duplicates_skipped': duplicate_count,
            'errors': error_count,
            'final_offset': offset,
            'status': 'COMPLETED'
        }

        print(f"✅ Congress {congress} Bills: {ingested_count} ingested, {duplicate_count} duplicates, {duration:.1f}s")
        return stats

    def run_phase_3_ingestion(self, congresses: List[int] = None) -> Dict[str, Any]:
        """Run complete Phase 3 ingestion"""
        if congresses is None:
            congresses = [117, 118]

        print("\n" + "="*60)
        print("📜 PHASE 3: CONGRESS BILLS INGESTION")
        print("="*60)

        all_stats = []
        total_ingested = 0
        total_duplicates = 0
        total_errors = 0

        for congress in congresses:
            stats = self.ingest_congress_bills(congress)
            all_stats.append(stats)
            total_ingested += stats['newly_ingested']
            total_duplicates += stats['duplicates_skipped']
            total_errors += stats['errors']

        # Generate summary
        summary = {
            'phase': 3,
            'phase_name': 'Congress Bills Ingestion',
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
        print(f"📊 PHASE 3 SUMMARY: {summary['overall_status']}")
        print(f"📜 Congresses: {', '.join(map(str, congresses))}")
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
            filename = f"phase_3_congress_bills_{timestamp}.json"

        summary = self.run_phase_3_ingestion(congresses)

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

    parser = argparse.ArgumentParser(description='Phase 3: Congress Bills Ingestion')
    parser.add_argument('--congresses', '-c', nargs='+', type=int,
                       default=[117, 118], help='Congress numbers to ingest')
    parser.add_argument('--output', '-o', help='Output filename (default: auto-generated)')
    parser.add_argument('--save', action='store_true', help='Save results to file')

    args = parser.parse_args()

    try:
        ingester = Phase3CongressBillsIngestion()

        if args.save:
            ingester.save_ingestion_results(args.output, args.congresses)
        else:
            ingester.run_phase_3_ingestion(args.congresses)

    except Exception as e:
        print(f"❌ Phase 3 ingestion failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
