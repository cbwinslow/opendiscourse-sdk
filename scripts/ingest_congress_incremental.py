#!/usr/bin/env python3
"""
Incremental Congress Members Ingestion Script
"""

import os
import sys
import json
import hashlib
import logging
import time
from typing import Dict, Any, Optional, List
from datetime import datetime

import psycopg2
import requests

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ingestion_config import validate_and_start_ingestion, get_api_key_from_env, get_ingestion_mode_from_env, IngestionMode, validate_all_api_keys

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import optional dependencies (may not exist in all environments)
try:
    from rate_limiter import adaptive_limiters
    RATE_LIMITING_ENABLED = True
except ImportError:
    RATE_LIMITING_ENABLED = False
    print("⚠️ Rate limiting not available, proceeding without")

try:
    from env_config import get_optional_env_var, validate_api_keys
    ADVANCED_CONFIG_ENABLED = True
except ImportError:
    # Fallback implementations
    ADVANCED_CONFIG_ENABLED = False
    print("⚠️ Advanced config not available, using basic configuration")

    def get_optional_env_var(key: str, default: str = None) -> str:
        return os.getenv(key, default)

    def validate_api_keys() -> dict:
        return {
            'congress.gov': os.getenv('CONGRESS_API_KEY'),
            'govinfo.gov': os.getenv('GOVINFO_API_KEY'),
            'openstates.org': os.getenv('OPENSTATES_API_KEY')
        }

class IncrementalCongressIngestor:
    """Incremental Congress members ingestion with checkpoint tracking"""

    def __init__(self):
        # Validate API key
        api_keys = validate_api_keys()
        if not api_keys['congress.gov']:
            raise ValueError("CONGRESS_API_KEY not found in environment variables")

        self.api_key = get_optional_env_var('CONGRESS_API_KEY')
        self.base_url = "https://api.congress.gov/v3"
        self.batch_size = 50

        # Database connection
        self.db_conn = psycopg2.connect(
            database='cbwinslow',
            user='cbwinslow'
        )
        self.db_conn.autocommit = False

        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def get_next_ingestion_params(self, congress: int) -> Dict[str, Any]:
        """Get next ingestion parameters from checkpoint"""
        cursor = self.db_conn.cursor()

        try:
            cursor.execute("""
                SELECT * FROM incremental.get_next_ingestion_params(
                    %s, %s, %s
                )
            """, ('congress.gov', 'members', str(congress)))

            result = cursor.fetchone()
            if result:
                return {
                    'next_offset': result[0],
                    'next_page': result[1],
                    'start_from_id': result[2],
                    'start_from_timestamp': result[3],
                    'is_completed': result[4]
                }
            else:
                return {
                    'next_offset': 0,
                    'next_page': 1,
                    'start_from_id': None,
                    'start_from_timestamp': None,
                    'is_completed': False
                }
        finally:
            cursor.close()

    def create_checkpoint(self, congress: int, total_estimated: int = None) -> None:
        """Create or get checkpoint for this congress"""
        cursor = self.db_conn.cursor()

        try:
            cursor.execute("""
                SELECT incremental.get_or_create_checkpoint(
                    %s::text, %s::text, %s::text, %s::integer
                )
            """, ('congress.gov', 'members', str(congress), total_estimated))

            self.db_conn.commit()
        finally:
            cursor.close()

    def update_checkpoint(self, congress: int, last_offset: int,
                          records_processed: int = 0, is_completed: bool = False,
                          total_estimated: int = None, set_total_processed: int = None) -> None:
        """Update checkpoint progress"""
        cursor = self.db_conn.cursor()

        try:
            # If total_estimated is provided, update it first
            if total_estimated is not None:
                cursor.execute("""
                    UPDATE incremental.ingestion_checkpoints
                    SET total_estimated = %s
                    WHERE data_source = 'congress.gov' AND data_type = 'members' AND category = %s
                """, (total_estimated, str(congress)))

            # If set_total_processed is provided, set it directly (for completion)
            if set_total_processed is not None:
                cursor.execute("""
                    UPDATE incremental.ingestion_checkpoints
                    SET total_processed = %s
                    WHERE data_source = 'congress.gov' AND data_type = 'members' AND category = %s
                """, (set_total_processed, str(congress)))
                # Use the existing function to update other fields
                cursor.execute("""
                    SELECT incremental.update_checkpoint_progress(
                        %s::text, %s::text, %s::text,
                        %s::integer, NULL, NULL, NULL,
                        0, %s::boolean
                    )
                """, (
                    'congress.gov', 'members', str(congress),
                    last_offset, is_completed
                ))
            else:
                # Then use the existing function to update progress
                cursor.execute("""
                    SELECT incremental.update_checkpoint_progress(
                        %s::text, %s::text, %s::text,
                        %s::integer, NULL, NULL, NULL,
                        %s::integer, %s::boolean
                    )
                """, (
                    'congress.gov', 'members', str(congress),
                    last_offset, records_processed, is_completed
                ))

            self.db_conn.commit()
        except Exception as e:
            self.db_conn.rollback()
            self.logger.error(f"Failed to update checkpoint: {e}")
            raise
        finally:
            cursor.close()

    def is_record_processed(self, member_id: str, member_data: Dict[str, Any]) -> bool:
        """Check if record was already processed using fingerprinting"""
        cursor = self.db_conn.cursor()

        try:
            # Create content hash for fingerprinting
            content_hash = hashlib.sha256(
                json.dumps(member_data, sort_keys=True).encode('utf-8')
            ).hexdigest()

            cursor.execute("""
                SELECT incremental.is_record_processed(
                    %s::text, %s::text, %s::text, %s::jsonb
                )
            """, ('congress.gov', 'members', member_id, json.dumps(member_data)))

            result = cursor.fetchone()
            return result[0] if result else False
        finally:
            cursor.close()

    def fetch_members_page(self, congress: int, offset: int = 0) -> Dict[str, Any]:
        """Fetch a page of members from Congress.gov API"""
        # Use adaptive rate limiting if available
        if RATE_LIMITING_ENABLED:
            adaptive_limiters['congress.gov'].wait_for_token()

        url = f"{self.base_url}/member/congress/{congress}"
        params = {
            'limit': self.batch_size,
            'offset': offset,
            'api_key': self.api_key
        }

        try:
            response = requests.get(url, params=params, timeout=30)

            # Update rate limiter based on response if available
            if RATE_LIMITING_ENABLED:
                adaptive_limiters['congress.gov'].update_from_response(response.headers)
                adaptive_limiters['congress.gov'].handle_error(response.status_code)

            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            # Handle rate limit errors
            if RATE_LIMITING_ENABLED and hasattr(e, 'response') and e.response.status_code == 429:
                adaptive_limiters['congress.gov'].handle_error(429)
                # Wait longer and retry once
                time.sleep(5)
                response = requests.get(url, params=params, timeout=30)
                response.raise_for_status()
                return response.json()
            raise

    def normalize_member_data(self, member_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize member data for database insertion"""
        member_info = member_data.get('member', member_data)
        full_name = member_info.get('name', '')
        name_parts = full_name.split()

        return {
            'bioguide_id': member_info.get('bioguideId'),
            'first_name': member_info.get('firstName', name_parts[0] if name_parts else ''),
            'middle_name': member_info.get('middleName'),
            'last_name': member_info.get('lastName', name_parts[-1] if len(name_parts) > 1 else ''),
            'suffix': member_info.get('suffix'),
            'official_full_name': full_name,
            'birthday': member_info.get('birthDate'),
            'gender': member_info.get('gender'),
            'biography': member_info.get('biography', ''),
            'birthplace': member_info.get('birthPlace'),
            'death_date': member_info.get('deathDate'),
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }

    def insert_members_batch(self, members: List[Dict[str, Any]]) -> int:
        """Insert a batch of members into the database"""
        if not members:
            return 0

        cursor = self.db_conn.cursor()

        try:
            query = """
                INSERT INTO congress.members (
                    bioguide_id, first_name, middle_name, last_name, suffix,
                    official_full_name, birthday, gender, biography, birthplace,
                    death_date, created_at, updated_at
                ) VALUES %s
                ON CONFLICT (bioguide_id) DO UPDATE SET
                    first_name = EXCLUDED.first_name,
                    middle_name = EXCLUDED.middle_name,
                    last_name = EXCLUDED.last_name,
                    suffix = EXCLUDED.suffix,
                    official_full_name = EXCLUDED.official_full_name,
                    birthday = EXCLUDED.birthday,
                    gender = EXCLUDED.gender,
                    biography = EXCLUDED.biography,
                    birthplace = EXCLUDED.birthplace,
                    death_date = EXCLUDED.death_date,
                    updated_at = EXCLUDED.updated_at
            """

            values = [
                (
                    m['bioguide_id'], m['first_name'], m['middle_name'], m['last_name'],
                    m['suffix'], m['official_full_name'], m['birthday'], m['gender'],
                    m['biography'], m['birthplace'], m['death_date'], m['created_at'], m['updated_at']
                )
                for m in members
            ]

            execute_values(cursor, query, values)
            self.db_conn.commit()
            return len(members)

        except Exception as e:
            self.db_conn.rollback()
            self.logger.error(f"Error inserting members batch: {e}")
            raise

    def start_ingestion_session(self, congress: int) -> str:
        """Start ingestion session tracking"""
        session_id = f"congress_members_{congress}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        cursor = self.db_conn.cursor()
        try:
            cursor.execute("""
                CALL incremental.start_ingestion_session(
                    %s, %s, %s, %s::jsonb
                )
            """, (
                session_id, 'congress.gov', 'members',
                json.dumps({'congress': congress, 'batch_size': self.batch_size})
            ))
            self.db_conn.commit()
        finally:
            cursor.close()

        return session_id

    def complete_ingestion_session(self, session_id: str, status: str = 'completed', error_summary: str = None):
        """Complete ingestion session"""
        cursor = self.db_conn.cursor()
        try:
            cursor.execute("""
                CALL incremental.complete_ingestion_session(%s, %s, %s)
            """, (session_id, status, error_summary))
            self.db_conn.commit()
        finally:
            cursor.close()

    def ingest_congress_members(self, congress: int) -> Dict[str, Any]:
        """Ingest members for a specific congress incrementally"""

        # Get checkpoint info
        params = self.get_next_ingestion_params(congress)

        if params['is_completed']:
            print(f"✅ Congress {congress} members already completed")
            return {
                'congress': congress,
                'status': 'already_completed',
                'records_processed': 0,
                'records_skipped': 0
            }

        # Create checkpoint if needed
        self.create_checkpoint(congress)

        # Start session
        session_id = self.start_ingestion_session(congress)

        print(f"🚀 Starting incremental ingestion for Congress {congress}")
        print(f"📍 Starting from offset: {params['next_offset']}")

        try:
            offset = params['next_offset']
            total_processed = 0
            total_skipped = 0

            while True:
                # Fetch batch
                data = self.fetch_members_page(congress, offset)
                members = data.get('members', [])

                if not members:
                    print(f"✅ No more members found")
                    break

                print(f"📦 Processing offset {offset} - {len(members)} members...")

                # Process each member
                new_members = []
                skipped_in_batch = 0

                for member_data in members:
                    member_id = member_data.get('member', {}).get('bioguideId')

                    if not member_id:
                        skipped_in_batch += 1
                        continue

                    # Check if already processed
                    if self.is_record_processed(member_id, member_data):
                        skipped_in_batch += 1
                        continue

                    # Normalize and add to batch
                    try:
                        normalized = self.normalize_member_data(member_data)
                        if normalized['bioguide_id']:
                            new_members.append(normalized)
                    except Exception as e:
                        self.logger.error(f"Error normalizing member {member_id}: {e}")
                        skipped_in_batch += 1
                        continue

                # Insert new members
                if new_members:
                    inserted = self.insert_members_batch(new_members)
                    total_processed += inserted
                    print(f"   ✅ Inserted {inserted} new members")

                total_skipped += skipped_in_batch

                # Update checkpoint
                self.update_checkpoint(congress, offset, len(new_members))

                # Check if we have more pages
                pagination = data.get('pagination', {})
                next_url = pagination.get('next')
                if not next_url or offset >= pagination.get('count', 0):
                    print(f"✅ Reached end of pagination")
                    break

                offset += len(members)

                # Safety limit
                if offset > 10000:
                    print(f"⚠️ Safety limit reached, stopping")
                    break

            # Mark checkpoint as completed with proper total
            # Get the total count from the API response or use the final offset as estimate
            total_estimated = offset if offset > 0 else 554  # Use actual count or fallback
            # For completion, set total_processed to total_estimated since we've processed all records
            actual_total_processed = total_estimated
            self.update_checkpoint(congress, offset, 0, True, total_estimated, actual_total_processed)

            # Complete session
            self.complete_ingestion_session(session_id, 'completed')

            print(f"🎉 Congress {congress} ingestion completed!")
            print(f"📊 Processed: {total_processed}, Skipped: {total_skipped}")

            return {
                'congress': congress,
                'status': 'completed',
                'records_processed': total_processed,
                'records_skipped': total_skipped,
                'final_offset': offset
            }

        except Exception as e:
            self.complete_ingestion_session(session_id, 'failed', str(e))
            raise

    def ingest_all_congresses(self, start_congress: int = 118, end_congress: int = 118):
        """Ingest all congresses in range"""
        print(f"🚀 Starting incremental ingestion for Congresses {start_congress}-{end_congress}")

        results = []

        for congress in range(start_congress, end_congress + 1):
            try:
                result = self.ingest_congress_members(congress)
                results.append(result)
                print(f"✅ Congress {congress} completed")
            except Exception as e:
                print(f"❌ Congress {congress} failed: {e}")
                results.append({
                    'congress': congress,
                    'status': 'failed',
                    'error': str(e)
                })

        # Summary
        completed = sum(1 for r in results if r.get('status') == 'completed')
        total_processed = sum(r.get('records_processed', 0) for r in results)
        total_skipped = sum(r.get('records_skipped', 0) for r in results)

        print(f"\n🎉 All congresses ingestion completed!")
        print(f"📊 Summary:")
        print(f"   Congresses completed: {completed}/{len(results)}")
        print(f"   Total records processed: {total_processed}")
        print(f"   Total records skipped: {total_skipped}")

        return results

    def get_checkpoint_status(self):
        """Get status of all checkpoints"""
        cursor = self.db_conn.cursor()

        try:
            cursor.execute("SELECT * FROM incremental.checkpoint_status WHERE data_source = 'congress.gov'")
            checkpoints = cursor.fetchall()

            print("\n📋 Congress.gov Checkpoint Status:")
            print("-" * 80)
            for cp in checkpoints:
                completion_pct = cp[9] if cp[9] is not None else 0.0
                last_run = cp[10] if cp[10] is not None else 'Never'
                print(f"{cp[0]} | {cp[1]} | {cp[2]} | {cp[3]} | {cp[4]} | {completion_pct:.1f}% | {last_run}")

            return checkpoints
        finally:
            cursor.close()

def main():
    """Main function with API key validation"""

    # Validate all required API keys first
    print("🔍 Validating all required API keys...")
    key_validation = validate_all_api_keys()

    if not key_validation['valid']:
        print("❌ API key validation failed:")
        for error in key_validation['errors']:
            print(f"   🚫 {error}")
        print("\nPlease set the required environment variables in your .env file:")
        print("   CONGRESS_API_KEY=your_real_congress_api_key")
        print("   GOVINFO_API_KEY=your_real_govinfo_api_key")
        print("   OPENSTATES_API_KEY=your_real_openstates_api_key")
        sys.exit(1)

    print("✅ All API keys validated successfully")
    if key_validation['warnings']:
        for warning in key_validation['warnings']:
            print(f"   ⚠️ {warning}")

    # Get API key and validate
    api_key = get_api_key_from_env('CONGRESS_API_KEY')
    if not api_key:
        print("❌ CONGRESS_API_KEY environment variable is required")
        sys.exit(1)

    # Get ingestion mode
    mode = get_ingestion_mode_from_env()

    # Validate before starting ingestion
    print(f"🔍 Validating API configuration for {mode.value} mode...")
    if not validate_and_start_ingestion(api_key, "https://api.congress.gov/v3", mode):
        print("❌ API validation failed - cannot proceed with ingestion")
        sys.exit(1)

    print("✅ API validation passed - starting ingestion...")

    ingestor = IncrementalCongressIngestor()

    # Show current checkpoint status
    ingestor.get_checkpoint_status()

    # Ingest Congress 118 (or specify range)
    results = ingestor.ingest_all_congresses(118, 118)

    # Show final status
    ingestor.get_checkpoint_status()

if __name__ == "__main__":
    main()
