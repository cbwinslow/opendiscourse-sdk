#!/usr/bin/env python3
"""
Phase 2: Congress Members Data Ingestion

This script handles ingestion of Congress members data for specified congresses:
- Ingests members for Congress 116, 117, and 118
- Handles offset-based pagination with proper checkpointing
- Implements duplicate detection via fingerprinting
- Provides real-time progress monitoring

ASSIGNED TO: AI Agent responsible for Congress members ingestion
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

class Phase2CongressMembersIngestion:
    """Phase 2: Congress Members Data Ingestion"""

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

        # Rate limiting
        time.sleep(0.1)

        return response.json()

    def _generate_fingerprint(self, member_data: Dict[str, Any]) -> str:
        """Generate SHA-256 fingerprint for member data"""
        # Create a consistent string representation
        fingerprint_data = {
            'bioguide_id': member_data.get('bioguideId'),
            'first_name': member_data.get('firstName'),
            'last_name': member_data.get('lastName'),
            'state': member_data.get('state'),
            'party': member_data.get('party'),
            'district': member_data.get('district')
        }

        fingerprint_str = json.dumps(fingerprint_data, sort_keys=True)
        return hashlib.sha256(fingerprint_str.encode()).hexdigest()

    def _save_member_to_database(self, member_data: Dict[str, Any], congress: int) -> bool:
        """Save member data to database with duplicate detection"""
        fingerprint = self._generate_fingerprint(member_data)

        try:
            conn = psycopg2.connect(database='cbwinslow', user='cbwinslow')
            cursor = conn.cursor()

            # Check for duplicates
            cursor.execute("""
                SELECT COUNT(*) FROM congress.members
                WHERE bioguide_id = %s AND fingerprint = %s
            """, (member_data.get('bioguideId'), fingerprint))

            if cursor.fetchone()[0] > 0:
                cursor.close()
                conn.close()
                return False  # Duplicate, skip

            # Insert new member
            cursor.execute("""
                INSERT INTO congress.members (
                    bioguide_id, first_name, middle_name, last_name, suffix,
                    official_full_name, birthday, gender, biography, birthplace,
                    death_date, fingerprint, created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                member_data.get('bioguideId'),
                member_data.get('firstName'),
                member_data.get('middleName'),
                member_data.get('lastName'),
                member_data.get('suffix'),
                member_data.get('officialFullName'),
                member_data.get('birthDate'),
                member_data.get('gender'),
                member_data.get('biography'),
                member_data.get('birthPlace'),
                member_data.get('deathDate'),
                fingerprint,
                datetime.now(),
                datetime.now()
            ))

            conn.commit()
            cursor.close()
            conn.close()
            return True

        except Exception as e:
            print(f"❌ Error saving member {member_data.get('bioguideId')}: {e}")
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
                'congress.gov', 'members', str(congress),
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
                WHERE data_source = 'congress.gov' AND data_type = 'members' AND category = %s
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

    def ingest_congress_members(self, congress: int) -> Dict[str, Any]:
        """Ingest members for a specific congress"""
        print(f"\n🏛️  Ingesting Congress {congress} Members...")

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
                url = f"{self.api_base_url}/member/congress/{congress}"
                params = {
                    'limit': self.batch_size,
                    'offset': offset
                }

                response_data = self._make_api_request(url, params)
                members = response_data.get('members', [])

                if not members:
                    print("✅ No more members to ingest")
                    break

                # Process batch
                batch_ingested = 0
                for member in members:
                    if self._save_member_to_database(member, congress):
                        batch_ingested += 1
                        ingested_count += 1
                    else:
                        duplicate_count += 1

                # Update progress
                offset += self.batch_size
                total_processed += len(members)

                # Update checkpoint every 5 batches
                if offset % (self.batch_size * 5) == 0:
                    self._update_checkpoint(congress, offset, total_processed)
                    print(f"📊 Progress: {total_processed} processed, {ingested_count} ingested, {duplicate_count} duplicates")

                # Check if we've reached the end
                if len(members) < self.batch_size:
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

        print(f"✅ Congress {congress} Members: {ingested_count} ingested, {duplicate_count} duplicates, {duration:.1f}s")
        return stats

    def run_phase_2_ingestion(self, congresses: List[int] = None) -> Dict[str, Any]:
        """Run complete Phase 2 ingestion"""
        if congresses is None:
            congresses = [116, 117, 118]

        print("\n" + "="*60)
        print("🏛️  PHASE 2: CONGRESS MEMBERS INGESTION")
        print("="*60)

        all_stats = []
        total_ingested = 0
        total_duplicates = 0
        total_errors = 0

        for congress in congresses:
            stats = self.ingest_congress_members(congress)
            all_stats.append(stats)
            total_ingested += stats['newly_ingested']
            total_duplicates += stats['duplicates_skipped']
            total_errors += stats['errors']

        # Generate summary
        summary = {
            'phase': 2,
            'phase_name': 'Congress Members Ingestion',
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
        print(f"📊 PHASE 2 SUMMARY: {summary['overall_status']}")
        print(f"🏛️  Congresses: {', '.join(map(str, congresses))}")
        print(f"👥 Members Ingested: {total_ingested:,}")
        print(f"🔄 Duplicates Skipped: {total_duplicates:,}")
        print(f"❌ Errors: {total_errors}")
        print(f"⏱️  Duration: {summary['duration_seconds']:.1f} seconds")
        print("="*60)

        return summary

    def save_ingestion_results(self, filename: str = None, congresses: List[int] = None) -> str:
        """Save ingestion results to file"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"phase_2_congress_members_{timestamp}.json"

        summary = self.run_phase_2_ingestion(congresses)

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

    parser = argparse.ArgumentParser(description='Phase 2: Congress Members Ingestion')
    parser.add_argument('--congresses', '-c', nargs='+', type=int,
                       default=[116, 117, 118], help='Congress numbers to ingest')
    parser.add_argument('--output', '-o', help='Output filename (default: auto-generated)')
    parser.add_argument('--save', action='store_true', help='Save results to file')

    args = parser.parse_args()

    try:
        ingester = Phase2CongressMembersIngestion()

        if args.save:
            ingester.save_ingestion_results(args.output, args.congresses)
        else:
            ingester.run_phase_2_ingestion(args.congresses)

    except Exception as e:
        print(f"❌ Phase 2 ingestion failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
