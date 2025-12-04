#!/usr/bin/env python3
"""
Incremental Congress Bills Ingestion
Ingests bills from Congress.gov API with checkpoint tracking and fingerprinting
"""

import os
import sys
import requests
import hashlib
import json
import time
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

from rate_limiter import adaptive_limiters
from env_config import get_optional_env_var, validate_api_keys

class IncrementalCongressBillsIngestor:
    """Incremental bills ingestion for Congress.gov API"""

    def __init__(self):
        # Validate API key
        api_keys = validate_api_keys()
        if not api_keys['congress.gov']:
            raise ValueError("CONGRESS_API_KEY not found in environment variables")

        self.api_key = get_optional_env_var('CONGRESS_API_KEY')
        self.base_url = "https://api.congress.gov/v3"
        self.batch_size = 50
        self.db_conn = self._connect_with_retry()

    def _connect_with_retry(self, max_retries=3, retry_delay=2):
        """Connect to database with retry logic"""
        for attempt in range(max_retries):
            try:
                conn = psycopg2.connect(
                    database='opendiscourse',
                    user='cbwinslow',
                    host='/var/run/postgresql',
                    connect_timeout=10
                )
                return conn
            except psycopg2.OperationalError as e:
                if attempt == max_retries - 1:
                    print(f"❌ Database connection failed after {max_retries} attempts: {e}")
                    raise
                else:
                    print(f"⚠️ Database connection attempt {attempt + 1} failed, retrying...")
                    time.sleep(retry_delay * (2 ** attempt))  # Exponential backoff
            except Exception as e:
                print(f"❌ Unexpected database connection error: {e}")
                raise

    def start_ingestion_session(self, congress: int) -> str:
        """Start ingestion session for tracking"""
        session_id = f"congress_bills_{congress}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        cursor = self.db_conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO incremental.ingestion_sessions (
                    session_id, data_source, data_type, status, started_at
                ) VALUES (%s, %s, %s, %s, %s)
            """, (session_id, 'congress.gov', 'bills', 'running', datetime.now()))

            self.db_conn.commit()
            return session_id
        except Exception as e:
            self.db_conn.rollback()
            raise e
        finally:
            cursor.close()

    def complete_ingestion_session(self, session_id: str, status: str, error_message: str = None):
        """Complete ingestion session"""
        cursor = self.db_conn.cursor()
        try:
            cursor.execute("""
                UPDATE incremental.ingestion_sessions SET
                    status = %s,
                    completed_at = %s,
                    error_summary = %s
                WHERE session_id = %s
            """, (status, datetime.now(), error_message, session_id))

            self.db_conn.commit()
        except Exception as e:
            self.db_conn.rollback()
            raise e
        finally:
            cursor.close()

    def get_next_ingestion_params(self, congress: int) -> Dict[str, Any]:
        """Get next ingestion parameters from checkpoint"""
        cursor = self.db_conn.cursor()
        try:
            cursor.execute("""
                SELECT * FROM incremental.get_next_ingestion_params('congress.gov', 'bills', %s)
            """, (str(congress),))

            result = cursor.fetchone()
            if result:
                return {
                    'next_offset': result[0],
                    'is_completed': result[4],  # Fixed: is_completed is at position 4
                    'total_processed': result[2] if len(result) > 2 else 0,
                    'last_run': result[3] if len(result) > 3 else None
                }
            else:
                return {
                    'next_offset': 0,
                    'is_completed': False,
                    'total_processed': 0,
                    'last_run': None
                }
        finally:
            cursor.close()

    def is_record_processed(self, bill_id: str, bill_data: Dict[str, Any]) -> bool:
        """Check if bill was already processed using fingerprint"""
        cursor = self.db_conn.cursor()
        try:
            cursor.execute("""
                SELECT * FROM incremental.is_record_processed('congress.gov', 'bills', %s, %s)
            """, (bill_id, json.dumps(bill_data, sort_keys=True)))

            result = cursor.fetchone()
            return result[0] if result else False
        finally:
            cursor.close()

    def fetch_bills_page(self, congress: int, offset: int = 0) -> Dict[str, Any]:
        """Fetch a page of bills from Congress.gov API"""
        # Use adaptive rate limiting
        adaptive_limiters['congress.gov'].wait_for_token()

        url = f"{self.base_url}/bill"
        params = {
            'congress': congress,
            'limit': self.batch_size,
            'offset': offset
        }

        if self.api_key:
            params['api_key'] = self.api_key

        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }

        try:
            response = requests.get(url, params=params, headers=headers, timeout=30)

            # Update rate limiter based on response
            adaptive_limiters['congress.gov'].update_from_response(response.headers)
            adaptive_limiters['congress.gov'].handle_error(response.status_code)

            response.raise_for_status()

            # Handle JSON parsing errors with fallback
            try:
                return response.json()
            except json.JSONDecodeError as json_e:
                print(f"⚠️ JSON parsing error, retrying: {json_e}")
                # Retry once for JSON parsing errors
                time.sleep(2)
                response = requests.get(url, params=params, headers=headers, timeout=30)
                response.raise_for_status()
                return response.json()

        except requests.exceptions.RequestException as e:
            # Enhanced error handling with retry logic
            if hasattr(e, 'response') and e.response:
                status_code = e.response.status_code

                if status_code == 429:
                    # Handle rate limit errors with exponential backoff
                    adaptive_limiters['congress.gov'].handle_error(429)
                    print(f"⚠️ Rate limit hit, waiting and retrying...")
                    time.sleep(10)
                    response = requests.get(url, params=params, headers=headers, timeout=30)
                    response.raise_for_status()
                    return response.json()

                elif status_code >= 500:
                    # Handle server errors (HTTP 500+) with retries
                    print(f"⚠️ Server error {status_code}, retrying...")
                    for attempt in range(3):
                        time.sleep(2 ** attempt)  # Exponential backoff
                        try:
                            response = requests.get(url, params=params, headers=headers, timeout=30)
                            response.raise_for_status()
                            return response.json()
                        except requests.exceptions.RequestException:
                            if attempt == 2:  # Last attempt
                                print(f"❌ Server error persisted after 3 attempts")
                                raise

                elif status_code == 404:
                    print(f"⚠️ Resource not found: {url}")
                    return {"bills": [], "pagination": {"count": 0}}

            elif isinstance(e, requests.exceptions.Timeout):
                # Handle timeout errors with retry
                print(f"⚠️ Request timeout, retrying...")
                time.sleep(5)
                response = requests.get(url, params=params, headers=headers, timeout=30)
                response.raise_for_status()
                return response.json()
            elif isinstance(e, requests.exceptions.ConnectionError):
                # Handle connection errors with retry
                print(f"⚠️ Connection error, retrying...")
                time.sleep(3)
                response = requests.get(url, params=params, headers=headers, timeout=30)
                response.raise_for_status()
                return response.json()
            else:
                print(f"❌ API request failed: {e}")
                raise

    def normalize_bill_data(self, bill_data: Dict[str, Any], congress: int) -> Optional[Dict[str, Any]]:
        """Normalize bill data for database insertion"""
        try:
            bill = bill_data.get('bill', bill_data)

            # Extract basic information
            bill_id = bill.get('billId', '')
            bill_type = bill.get('type', '')
            bill_number = bill.get('number', '')

            # Parse bill_id to get components (Congress.gov format: type-number-congress)
            if '-' in bill_id:
                parts = bill_id.split('-')
                if len(parts) >= 2:
                    # For format like "hr-1-118" -> bill_type="hr", bill_number="1"
                    bill_type = parts[0].lower() if parts[0] else bill_type
                    bill_number = parts[1] if parts[1] else bill_number
                else:
                    # Legacy format like "hr1" -> bill_type="hr", bill_number="1"
                    congress_part, type_num = bill_id.split('-', 1)
                    if type_num:
                        bill_type = type_num[0] if type_num[0].isalpha() else bill_type
                        bill_number = type_num[1:] if type_num[0].isalpha() else type_num

            # Get title and summary
            titles = bill.get('titles', [])
            primary_title = titles[0].get('title', '') if titles else ''

            # Get sponsor information
            sponsor = bill.get('sponsor', {})
            sponsor_bioguide = sponsor.get('bioguideId', '')

            # Get introduction date
            introduced_date = bill.get('introducedDate', '')

            # Get latest action
            actions = bill.get('actions', [])
            latest_action = actions[-1] if actions else {}
            latest_action_text = latest_action.get('text', '')
            latest_action_date = latest_action.get('actionDate', '')

            # Get policy areas
            policy_areas = bill.get('policyArea', {})
            policy_area_name = policy_areas.get('name', '')

            # Get subjects
            subjects = bill.get('subjects', [])
            subject_names = [s.get('name', '') for s in subjects if s.get('name')]

            return {
                'bill_id': bill_id,
                'congress': congress,
                'bill_type': bill_type,
                'bill_number': bill_number,
                'title': primary_title,
                'sponsor_bioguide_id': sponsor_bioguide,
                'introduced_date': datetime.fromisoformat(introduced_date.replace('Z', '+00:00')) if introduced_date else None,
                'latest_action_text': latest_action_text,
                'latest_action_date': datetime.fromisoformat(latest_action_date.replace('Z', '+00:00')) if latest_action_date else None,
                'policy_area': policy_area_name,
                'subjects': subject_names,
                'url': bill.get('url', ''),
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }
        except Exception as e:
            print(f"❌ Error normalizing bill data: {e}")
            return None

    def insert_bills_batch(self, bills: List[Dict[str, Any]]) -> int:
        """Insert batch of bills into database"""
        cursor = self.db_conn.cursor()
        try:
            bill_query = """
                INSERT INTO congress.bills (
                    bill_id, congress, bill_type, bill_number, title,
                    sponsor_bioguide_id, introduced_date, latest_action_text,
                    latest_action_date, policy_area, subjects, url,
                    created_at, updated_at
                ) VALUES %s
                ON CONFLICT (bill_id) DO UPDATE SET
                    title = EXCLUDED.title,
                    sponsor_bioguide_id = EXCLUDED.sponsor_bioguide_id,
                    introduced_date = EXCLUDED.introduced_date,
                    latest_action_text = EXCLUDED.latest_action_text,
                    latest_action_date = EXCLUDED.latest_action_date,
                    policy_area = EXCLUDED.policy_area,
                    subjects = EXCLUDED.subjects,
                    url = EXCLUDED.url,
                    updated_at = EXCLUDED.updated_at
            """

            bill_values = [
                (
                    b['bill_id'], b['congress'], b['bill_type'], b['bill_number'],
                    b['title'], b['sponsor_bioguide_id'], b['introduced_date'],
                    b['latest_action_text'], b['latest_action_date'], b['policy_area'],
                    b['subjects'], b['url'], b['created_at'], b['updated_at']
                )
                for b in bills if b
            ]

            if bill_values:
                execute_values(cursor, bill_query, bill_values)
                inserted = len(bill_values)

                # Update subjects table
                self._update_bill_subjects(cursor, bills)

                return inserted
            return 0
        except Exception as e:
            print(f"❌ Error inserting bills batch: {e}")
            return 0
        finally:
            cursor.close()

    def _update_bill_subjects(self, cursor, bills: List[Dict[str, Any]]):
        """Update bill subjects relationship"""
        for bill in bills:
            if bill and bill.get('subjects'):
                bill_id = bill['bill_id']
                for subject in bill['subjects']:
                    if subject.strip():
                        cursor.execute("""
                            INSERT INTO congress.bill_subjects (bill_id, subject_name)
                            VALUES (%s, %s)
                            ON CONFLICT (bill_id, subject_name) DO NOTHING
                        """, (bill_id, subject.strip()))

    def update_checkpoint(self, congress: int, offset: int, batch_size: int):
        """Update checkpoint progress"""
        cursor = self.db_conn.cursor()
        try:
            cursor.execute("""
                SELECT incremental.update_checkpoint_progress(
                    'congress.gov', 'bills', %s, %s, NULL, NULL, NULL, NULL, %s
                )
            """, (str(congress), offset, batch_size))

            self.db_conn.commit()
        except Exception as e:
            self.db_conn.rollback()
            print(f"❌ Error updating checkpoint: {e}")
        finally:
            cursor.close()

    def ingest_congress_bills(self, congress: int) -> Dict[str, Any]:
        """Ingest bills for a specific congress"""
        print(f"🏛️ Starting incremental bills ingestion for Congress {congress}")

        # Get checkpoint info
        params = self.get_next_ingestion_params(congress)

        if params['is_completed']:
            print(f"✅ Congress {congress} bills already completed")
            return {
                'congress': congress,
                'status': 'already_completed',
                'records_processed': 0,
                'records_skipped': 0
            }

        print(f"📍 Starting from offset: {params['next_offset']}")

        session_id = self.start_ingestion_session(congress)

        try:
            offset = params['next_offset']
            total_processed = 0
            total_skipped = 0

            while True:
                # Fetch batch
                batch_data = self.fetch_bills_page(congress, offset)
                bills = batch_data.get('bills', [])

                if not bills:
                    print(f"✅ No more bills found")
                    break

                print(f"📄 Processing {len(bills)} bills from offset {offset}")

                new_bills = []
                skipped_in_batch = 0

                for bill_data in bills:
                    bill_id = bill_data.get('billId', '')

                    if not bill_id:
                        skipped_in_batch += 1
                        continue

                    # Check if already processed
                    if self.is_record_processed(bill_id, bill_data):
                        skipped_in_batch += 1
                        continue

                    # Normalize data
                    normalized = self.normalize_bill_data(bill_data, congress)
                    if normalized and normalized['bill_id']:
                        new_bills.append(normalized)

                # Insert new bills
                if new_bills:
                    inserted = self.insert_bills_batch(new_bills)
                    total_processed += inserted
                    print(f"   ✅ Inserted {inserted} new bills")

                total_skipped += skipped_in_batch

                # Update checkpoint
                self.update_checkpoint(congress, offset, len(bills))

                # Check if we should continue
                if len(bills) < self.batch_size:
                    print(f"✅ Reached end of bills list")
                    break

                offset += self.batch_size

            # Mark checkpoint as completed
            self.update_checkpoint(congress, offset, 0)

            # Complete session
            self.complete_ingestion_session(session_id, 'completed')

            result = {
                'congress': congress,
                'status': 'completed',
                'records_processed': total_processed,
                'records_skipped': total_skipped
            }

            print(f"🎉 Congress {congress} bills ingestion completed!")
            print(f"📊 Processed: {total_processed}, Skipped: {total_skipped}")

            return result

        except Exception as e:
            self.complete_ingestion_session(session_id, 'failed', str(e))
            print(f"❌ Congress {congress} bills failed: {e}")
            return {
                'congress': congress,
                'status': 'failed',
                'error': str(e),
                'records_processed': total_processed,
                'records_skipped': total_skipped
            }

    def ingest_all_congresses(self, start_congress: int = 118, end_congress: int = 118) -> List[Dict[str, Any]]:
        """Ingest bills for multiple congresses"""
        results = []

        for congress in range(start_congress, end_congress + 1):
            result = self.ingest_congress_bills(congress)
            results.append(result)

        # Summary
        completed = sum(1 for r in results if r.get('status') == 'completed')
        total_processed = sum(r.get('records_processed', 0) for r in results)
        total_skipped = sum(r.get('records_skipped', 0) for r in results)

        print(f"\n🎉 All Congress bills ingestion completed!")
        print(f"📊 Summary:")
        print(f"   Congresses completed: {completed}/{len(results)}")
        print(f"   Total bills processed: {total_processed}")
        print(f"   Total bills skipped: {total_skipped}")

        return results

def main():
    """Main function for testing"""
    ingestor = IncrementalCongressBillsIngestor()

    # Test with current congress
    results = ingestor.ingest_all_congresses(118, 118)

    print(f"\n🎯 Bills ingestion test completed!")
    print(f"Results: {results}")

if __name__ == "__main__":
    main()
