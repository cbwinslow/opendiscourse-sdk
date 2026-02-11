#!/usr/bin/env python3
"""
Phase 5: OpenStates Data Ingestion

This script handles ingestion of OpenStates data for all states:
- Ingests people data (legislators) for all states
- Ingests bills data for all states
- Handles state-based processing with proper checkpointing
- Implements rate limiting and progress monitoring

ASSIGNED TO: AI Agent responsible for OpenStates ingestion
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

class Phase5OpenStatesIngestion:
    """Phase 5: OpenStates Data Ingestion"""

    def __init__(self):
        self.phase_start = datetime.now()
        self.api_base_url = "https://v3.openstates.org"
        self.openstates_api_key = os.getenv('OPENSTATES_API_KEY')
        self.rate_limit_delay = 0.2  # Conservative rate limiting
        self.batch_size = 50
        self.ingestion_stats = {}

        # List of all US states and territories
        self.all_states = [
            'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
            'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
            'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
            'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
            'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY',
            'DC', 'PR', 'VI', 'GU', 'AS', 'MP'
        ]

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
        if not self.openstates_api_key:
            raise ValueError("OPENSTATES_API_KEY not found")

        print("✅ Phase 1 prerequisites validated")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def _make_api_request(self, url: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make API request with retry logic and rate limiting"""
        headers = {
            'X-API-Key': self.openstates_api_key,
            'Accept': 'application/json'
        }

        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()

        # Rate limiting
        time.sleep(self.rate_limit_delay)

        return response.json()

    def _generate_fingerprint(self, data: Dict[str, Any], data_type: str) -> str:
        """Generate SHA-256 fingerprint for data"""
        if data_type == 'people':
            fingerprint_data = {
                'id': data.get('id'),
                'name': data.get('name'),
                'state': data.get('state'),
                'party': data.get('party')
            }
        else:  # bills
            fingerprint_data = {
                'id': data.get('id'),
                'identifier': data.get('identifier'),
                'title': data.get('title'),
                'state': data.get('state')
            }

        fingerprint_str = json.dumps(fingerprint_data, sort_keys=True)
        return hashlib.sha256(fingerprint_str.encode()).hexdigest()

    def _save_person_to_database(self, person_data: Dict[str, Any]) -> bool:
        """Save person data to database with duplicate detection"""
        fingerprint = self._generate_fingerprint(person_data, 'people')

        try:
            conn = psycopg2.connect(database='cbwinslow', user='cbwinslow')
            cursor = conn.cursor()

            # Check for duplicates
            cursor.execute("""
                SELECT COUNT(*) FROM openstates.people
                WHERE id = %s OR fingerprint = %s
            """, (person_data.get('id'), fingerprint))

            if cursor.fetchone()[0] > 0:
                cursor.close()
                conn.close()
                return False  # Duplicate, skip

            # Insert new person
            cursor.execute("""
                INSERT INTO openstates.people (
                    id, name, state, party, chamber, district, email, image,
                    created_at, updated_at, fingerprint
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                person_data.get('id'),
                person_data.get('name'),
                person_data.get('state'),
                person_data.get('party'),
                person_data.get('current_role', {}).get('chamber'),
                person_data.get('current_role', {}).get('district'),
                person_data.get('email'),
                person_data.get('image'),
                datetime.now(),
                datetime.now(),
                fingerprint
            ))

            conn.commit()
            cursor.close()
            conn.close()
            return True

        except Exception as e:
            print(f"❌ Error saving person {person_data.get('id')}: {e}")
            return False

    def _save_bill_to_database(self, bill_data: Dict[str, Any]) -> bool:
        """Save bill data to database with duplicate detection"""
        fingerprint = self._generate_fingerprint(bill_data, 'bills')

        try:
            conn = psycopg2.connect(database='cbwinslow', user='cbwinslow')
            cursor = conn.cursor()

            # Check for duplicates
            cursor.execute("""
                SELECT COUNT(*) FROM openstates.bills
                WHERE id = %s OR fingerprint = %s
            """, (bill_data.get('id'), fingerprint))

            if cursor.fetchone()[0] > 0:
                cursor.close()
                conn.close()
                return False  # Duplicate, skip

            # Insert new bill
            cursor.execute("""
                INSERT INTO openstates.bills (
                    id, identifier, title, state, chamber, classification,
                    created_at, updated_at, fingerprint
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                bill_data.get('id'),
                bill_data.get('identifier'),
                bill_data.get('title'),
                bill_data.get('state'),
                bill_data.get('from_organization', {}).get('classification'),
                bill_data.get('classification'),
                datetime.now(),
                datetime.now(),
                fingerprint
            ))

            conn.commit()
            cursor.close()
            conn.close()
            return True

        except Exception as e:
            print(f"❌ Error saving bill {bill_data.get('id')}: {e}")
            return False

    def _update_checkpoint(self, data_type: str, state: str, processed: int, total: int):
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
                'openstates.org', data_type, state,
                processed, total, datetime.now(), 'IN_PROGRESS'
            ))

            conn.commit()
            cursor.close()
            conn.close()

        except Exception as e:
            print(f"❌ Error updating checkpoint: {e}")

    def _get_checkpoint(self, data_type: str, state: str) -> Tuple[int, int]:
        """Get checkpoint progress for a data type and state"""
        try:
            conn = psycopg2.connect(database='cbwinslow', user='cbwinslow')
            cursor = conn.cursor()

            cursor.execute("""
                SELECT offset, total_processed FROM incremental.ingestion_checkpoints
                WHERE data_source = 'openstates.org' AND data_type = %s AND category = %s
            """, (data_type, state))

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

    def ingest_openstates_people(self, states: List[str] = None) -> Dict[str, Any]:
        """Ingest people data from OpenStates"""
        if states is None:
            states = self.all_states

        print(f"\n👥 Ingesting OpenStates People for {len(states)} states...")

        start_time = datetime.now()
        all_stats = []
        total_ingested = 0
        total_duplicates = 0
        total_errors = 0

        for state in states:
            state_start = datetime.now()
            offset, total_processed = self._get_checkpoint('people', state)

            if total_processed > 0:
                print(f"🔄 Resuming {state} people from offset {offset}")

            ingested_count = 0
            duplicate_count = 0
            error_count = 0

            try:
                while True:
                    url = f"{self.api_base_url}/people"
                    params = {
                        'state': state,
                        'page': offset // self.batch_size + 1,
                        'per_page': self.batch_size
                    }

                    response_data = self._make_api_request(url, params)
                    people = response_data.get('results', [])

                    if not people:
                        break

                    for person in people:
                        if self._save_person_to_database(person):
                            ingested_count += 1
                        else:
                            duplicate_count += 1

                    offset += self.batch_size
                    total_processed += len(people)

                    if len(people) < self.batch_size:
                        break

                    # Update checkpoint every 5 pages
                    if offset % (self.batch_size * 5) == 0:
                        self._update_checkpoint('people', state, offset, total_processed)
                        print(f"📊 {state} People: {total_processed} processed, {ingested_count} ingested")

                # Final checkpoint update
                self._update_checkpoint('people', state, offset, total_processed)

            except Exception as e:
                print(f"❌ Error processing {state} people: {e}")
                error_count += 1

            state_stats = {
                'state': state,
                'start_time': state_start.isoformat(),
                'end_time': datetime.now().isoformat(),
                'total_processed': total_processed,
                'newly_ingested': ingested_count,
                'duplicates_skipped': duplicate_count,
                'errors': error_count,
                'status': 'COMPLETED'
            }

            all_stats.append(state_stats)
            total_ingested += ingested_count
            total_duplicates += duplicate_count
            total_errors += error_count

            print(f"✅ {state} People: {ingested_count} ingested, {duplicate_count} duplicates")

        duration = (datetime.now() - start_time).total_seconds()

        summary = {
            'data_type': 'people',
            'states_processed': states,
            'start_time': start_time.isoformat(),
            'end_time': datetime.now().isoformat(),
            'duration_seconds': duration,
            'total_newly_ingested': total_ingested,
            'total_duplicates_skipped': total_duplicates,
            'total_errors': total_errors,
            'individual_stats': all_stats,
            'overall_status': 'COMPLETED' if total_errors == 0 else 'COMPLETED_WITH_ERRORS'
        }

        print(f"✅ OpenStates People: {total_ingested} ingested, {total_duplicates} duplicates, {duration:.1f}s")
        return summary

    def ingest_openstates_bills(self, states: List[str] = None) -> Dict[str, Any]:
        """Ingest bills data from OpenStates"""
        if states is None:
            states = self.all_states

        print(f"\n📜 Ingesting OpenStates Bills for {len(states)} states...")

        start_time = datetime.now()
        all_stats = []
        total_ingested = 0
        total_duplicates = 0
        total_errors = 0

        for state in states:
            state_start = datetime.now()
            offset, total_processed = self._get_checkpoint('bills', state)

            if total_processed > 0:
                print(f"🔄 Resuming {state} bills from offset {offset}")

            ingested_count = 0
            duplicate_count = 0
            error_count = 0

            try:
                while True:
                    url = f"{self.api_base_url}/bills"
                    params = {
                        'state': state,
                        'page': offset // self.batch_size + 1,
                        'per_page': self.batch_size
                    }

                    response_data = self._make_api_request(url, params)
                    bills = response_data.get('results', [])

                    if not bills:
                        break

                    for bill in bills:
                        if self._save_bill_to_database(bill):
                            ingested_count += 1
                        else:
                            duplicate_count += 1

                    offset += self.batch_size
                    total_processed += len(bills)

                    if len(bills) < self.batch_size:
                        break

                    # Update checkpoint every 5 pages
                    if offset % (self.batch_size * 5) == 0:
                        self._update_checkpoint('bills', state, offset, total_processed)
                        print(f"📊 {state} Bills: {total_processed} processed, {ingested_count} ingested")

                # Final checkpoint update
                self._update_checkpoint('bills', state, offset, total_processed)

            except Exception as e:
                print(f"❌ Error processing {state} bills: {e}")
                error_count += 1

            state_stats = {
                'state': state,
                'start_time': state_start.isoformat(),
                'end_time': datetime.now().isoformat(),
                'total_processed': total_processed,
                'newly_ingested': ingested_count,
                'duplicates_skipped': duplicate_count,
                'errors': error_count,
                'status': 'COMPLETED'
            }

            all_stats.append(state_stats)
            total_ingested += ingested_count
            total_duplicates += duplicate_count
            total_errors += error_count

            print(f"✅ {state} Bills: {ingested_count} ingested, {duplicate_count} duplicates")

        duration = (datetime.now() - start_time).total_seconds()

        summary = {
            'data_type': 'bills',
            'states_processed': states,
            'start_time': start_time.isoformat(),
            'end_time': datetime.now().isoformat(),
            'duration_seconds': duration,
            'total_newly_ingested': total_ingested,
            'total_duplicates_skipped': total_duplicates,
            'total_errors': total_errors,
            'individual_stats': all_stats,
            'overall_status': 'COMPLETED' if total_errors == 0 else 'COMPLETED_WITH_ERRORS'
        }

        print(f"✅ OpenStates Bills: {total_ingested} ingested, {total_duplicates} duplicates, {duration:.1f}s")
        return summary

    def run_phase_5_ingestion(self, states: List[str] = None, data_types: List[str] = None) -> Dict[str, Any]:
        """Run complete Phase 5 ingestion"""
        if states is None:
            states = self.all_states
        if data_types is None:
            data_types = ['people', 'bills']

        print("\n" + "="*60)
        print("🗺️  PHASE 5: OPENSTATES INGESTION")
        print("="*60)

        all_results = {}
        total_ingested = 0
        total_duplicates = 0
        total_errors = 0

        for data_type in data_types:
            if data_type == 'people':
                result = self.ingest_openstates_people(states)
            else:  # bills
                result = self.ingest_openstates_bills(states)

            all_results[data_type] = result
            total_ingested += result['total_newly_ingested']
            total_duplicates += result['total_duplicates_skipped']
            total_errors += result['total_errors']

        # Generate summary
        summary = {
            'phase': 5,
            'phase_name': 'OpenStates Ingestion',
            'start_time': self.phase_start.isoformat(),
            'end_time': datetime.now().isoformat(),
            'duration_seconds': (datetime.now() - self.phase_start).total_seconds(),
            'states_processed': states,
            'data_types_processed': data_types,
            'total_newly_ingested': total_ingested,
            'total_duplicates_skipped': total_duplicates,
            'total_errors': total_errors,
            'individual_results': all_results,
            'overall_status': 'COMPLETED' if total_errors == 0 else 'COMPLETED_WITH_ERRORS'
        }

        print("\n" + "="*60)
        print(f"📊 PHASE 5 SUMMARY: {summary['overall_status']}")
        print(f"🗺️  States: {len(states)} processed")
        print(f"📊 Data Types: {', '.join(data_types)}")
        print(f"📄 Records Ingested: {total_ingested:,}")
        print(f"🔄 Duplicates Skipped: {total_duplicates:,}")
        print(f"❌ Errors: {total_errors}")
        print(f"⏱️  Duration: {summary['duration_seconds']:.1f} seconds")
        print("="*60)

        return summary

    def save_ingestion_results(self, filename: str = None, states: List[str] = None, data_types: List[str] = None) -> str:
        """Save ingestion results to file"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"phase_5_openstates_{timestamp}.json"

        summary = self.run_phase_5_ingestion(states, data_types)

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

    parser = argparse.ArgumentParser(description='Phase 5: OpenStates Ingestion')
    parser.add_argument('--states', '-s', nargs='+', help='States to ingest (default: all states)')
    parser.add_argument('--data-types', '-t', nargs='+', choices=['people', 'bills'],
                       default=['people', 'bills'], help='Data types to ingest')
    parser.add_argument('--output', '-o', help='Output filename (default: auto-generated)')
    parser.add_argument('--save', action='store_true', help='Save results to file')

    args = parser.parse_args()

    try:
        ingester = Phase5OpenStatesIngestion()

        if args.save:
            ingester.save_ingestion_results(args.output, args.states, args.data_types)
        else:
            ingester.run_phase_5_ingestion(args.states, args.data_types)

    except Exception as e:
        print(f"❌ Phase 5 ingestion failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
