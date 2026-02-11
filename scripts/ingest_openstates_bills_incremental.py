#!/usr/bin/env python3
"""
Incremental OpenStates Bills Ingestion
Ingests bills from OpenStates.org API with checkpoint tracking and fingerprinting
"""

import hashlib
import json
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import psycopg2
import requests
from env_config import get_optional_env_var, validate_api_keys
from psycopg2.extras import execute_values
from rate_limiter import adaptive_limiters


class IncrementalOpenStatesBillsIngestor:
    """Incremental bills ingestion for OpenStates.org API"""

    def __init__(self):
        # Validate API key
        api_keys = validate_api_keys()
        if not api_keys['openstates.org']:
            raise ValueError("OPENSTATES_API_KEY not found in environment variables")

        self.api_key = get_optional_env_var('OPENSTATES_API_KEY')
        self.base_url = "https://v3.openstates.org"
        self.batch_size = 50
        self.db_conn = psycopg2.connect(
            database='cbwinslow',
            user='cbwinslow'
        )

    def start_ingestion_session(self, jurisdiction: str) -> str:
        """Start ingestion session for tracking"""
        session_id = f"openstates_bills_{jurisdiction}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        cursor = self.db_conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO incremental.ingestion_sessions (
                    session_id, data_source, data_type, status, started_at
                ) VALUES (%s, %s, %s, %s, %s)
            """, (session_id, 'openstates.org', 'bills', 'running', datetime.now()))

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
                    error_message = %s
                WHERE session_id = %s
            """, (status, datetime.now(), error_message, session_id))

            self.db_conn.commit()
        except Exception as e:
            self.db_conn.rollback()
            raise e
        finally:
            cursor.close()

    def get_next_ingestion_params(self, jurisdiction: str) -> Dict[str, Any]:
        """Get next ingestion parameters from checkpoint"""
        cursor = self.db_conn.cursor()
        try:
            cursor.execute("""
                SELECT * FROM incremental.get_next_ingestion_params('openstates.org', 'bills', %s)
            """, (jurisdiction,))

            result = cursor.fetchone()
            if result:
                return {
                    'next_page': result[1],  # For OpenStates, we use page-based pagination
                    'is_completed': result[4],  # Fixed: is_completed is at position 4
                    'total_processed': result[2] if len(result) > 2 else 0,
                    'last_run': result[3] if len(result) > 3 else None
                }
            else:
                return {
                    'next_page': 1,
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
            # Generate content hash
            content_str = json.dumps(bill_data, sort_keys=True, separators=(',', ':'))
            content_hash = hashlib.sha256(content_str.encode()).hexdigest()

            cursor.execute("""
                SELECT * FROM incremental.is_record_processed('openstates.org', 'bills', %s, %s, %s)
            """, (bill_id, content_hash, datetime.now()))

            result = cursor.fetchone()
            return result[0] if result else False
        finally:
            cursor.close()

    def fetch_bills_batch(self, jurisdiction: str, page: int = 1) -> Dict[str, Any]:
        """Fetch a batch of bills from OpenStates.org API"""
        # Use adaptive rate limiting
        adaptive_limiters['openstates.org'].wait_for_token()

        url = f"{self.base_url}/bills"
        params = {
            'jurisdiction': jurisdiction,
            'page': page,
            'per_page': self.batch_size,
            'sort': 'updated_desc',
            'include': 'sponsorships,actions,subjects'
        }

        if self.api_key:
            headers = {'X-API-KEY': self.api_key}
        else:
            headers = {}

        headers.update({
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })

        try:
            response = requests.get(url, params=params, headers=headers, timeout=30)

            # Update rate limiter based on response
            adaptive_limiters['openstates.org'].update_from_response(response.headers)
            adaptive_limiters['openstates.org'].handle_error(response.status_code)

            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            # Handle rate limit errors
            if hasattr(e, 'response') and e.response.status_code == 429:
                adaptive_limiters['openstates.org'].handle_error(429)
                print("⚠️ Rate limit hit, waiting and retrying...")
                time.sleep(5)
                response = requests.get(url, params=params, headers=headers, timeout=30)
                response.raise_for_status()
                return response.json()
            else:
                print(f"❌ API request failed: {e}")
                raise

    def normalize_bill_data(self, bill_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Normalize bill data for database insertion"""
        try:
            # Extract basic information
            bill_id = bill_data.get('id', '')
            identifier = bill_data.get('identifier', '')

            # Get title
            title = bill_data.get('title', '')

            # Parse classification
            classification = bill_data.get('classification', [''])[0] if bill_data.get('classification') else ''

            # Get session information
            session = bill_data.get('session', {})
            session_name = session.get('name', '')

            # Get jurisdiction
            jurisdiction = bill_data.get('jurisdiction', {})
            jurisdiction_name = jurisdiction.get('name', '')
            jurisdiction_id = jurisdiction.get('id', '')

            # Get sponsor information
            sponsorships = bill_data.get('sponsorships', [])
            primary_sponsor = None
            for sponsorship in sponsorships:
                if sponsorship.get('primary', False):
                    primary_sponsor = sponsorship.get('person', {})
                    break

            sponsor_name = primary_sponsor.get('name', '') if primary_sponsor else ''
            sponsor_id = primary_sponsor.get('id', '') if primary_sponsor else ''

            # Get actions
            actions = bill_data.get('actions', [])
            latest_action = actions[-1] if actions else {}
            latest_action_description = latest_action.get('description', '')
            latest_action_date = latest_action.get('date', '')

            # Get subjects
            subjects = bill_data.get('subjects', [])

            # Get dates
            created_date = bill_data.get('created_at', '')
            updated_date = bill_data.get('updated_at', '')

            return {
                'bill_id': bill_id,
                'identifier': identifier,
                'title': title,
                'classification': classification,
                'session': session_name,
                'jurisdiction_name': jurisdiction_name,
                'jurisdiction_id': jurisdiction_id,
                'sponsor_name': sponsor_name,
                'sponsor_id': sponsor_id,
                'latest_action_description': latest_action_description,
                'latest_action_date': datetime.fromisoformat(latest_action_date.replace('Z', '+00:00')) if latest_action_date else None,
                'subjects': subjects,
                'created_date': datetime.fromisoformat(created_date.replace('Z', '+00:00')) if created_date else None,
                'updated_date': datetime.fromisoformat(updated_date.replace('Z', '+00:00')) if updated_date else None,
                'openstates_url': bill_data.get('openstates_url', ''),
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
                INSERT INTO openstates.bills (
                    bill_id, identifier, title, classification, session,
                    jurisdiction_name, jurisdiction_id, sponsor_name, sponsor_id,
                    latest_action_description, latest_action_date, subjects,
                    created_date, updated_date, openstates_url, created_at, updated_at
                ) VALUES %s
                ON CONFLICT (bill_id) DO UPDATE SET
                    title = EXCLUDED.title,
                    classification = EXCLUDED.classification,
                    session = EXCLUDED.session,
                    jurisdiction_name = EXCLUDED.jurisdiction_name,
                    jurisdiction_id = EXCLUDED.jurisdiction_id,
                    sponsor_name = EXCLUDED.sponsor_name,
                    sponsor_id = EXCLUDED.sponsor_id,
                    latest_action_description = EXCLUDED.latest_action_description,
                    latest_action_date = EXCLUDED.latest_action_date,
                    subjects = EXCLUDED.subjects,
                    created_date = EXCLUDED.created_date,
                    updated_date = EXCLUDED.updated_date,
                    openstates_url = EXCLUDED.openstates_url,
                    updated_at = EXCLUDED.updated_at
            """

            bill_values = [
                (
                    b['bill_id'], b['identifier'], b['title'], b['classification'],
                    b['session'], b['jurisdiction_name'], b['jurisdiction_id'],
                    b['sponsor_name'], b['sponsor_id'], b['latest_action_description'],
                    b['latest_action_date'], b['subjects'], b['created_date'],
                    b['updated_date'], b['openstates_url'], b['created_at'], b['updated_at']
                )
                for b in bills if b
            ]

            if bill_values:
                execute_values(cursor, bill_query, bill_values)
                inserted = len(bill_values)

                # Update sponsorships table
                self._update_bill_sponsorships(cursor, bills)

                # Update actions table
                self._update_bill_actions(cursor, bills)

                return inserted
            return 0
        except Exception as e:
            print(f"❌ Error inserting bills batch: {e}")
            return 0
        finally:
            cursor.close()

    def _update_bill_sponsorships(self, cursor, bills: List[Dict[str, Any]]):
        """Update bill sponsorships relationship"""
        for bill in bills:
            if bill and bill.get('sponsor_id'):
                cursor.execute("""
                    INSERT INTO openstates.bill_sponsorships (
                        bill_id, sponsor_name, sponsor_id, is_primary
                    ) VALUES (%s, %s, %s, %s)
                    ON CONFLICT (bill_id, sponsor_id) DO UPDATE SET
                        sponsor_name = EXCLUDED.sponsor_name,
                        is_primary = EXCLUDED.is_primary
                """, (bill['bill_id'], bill['sponsor_name'], bill['sponsor_id'], True))

    def _update_bill_actions(self, cursor, bills: List[Dict[str, Any]]):
        """Update bill actions"""
        for bill in bills:
            if bill and bill.get('latest_action_description'):
                cursor.execute("""
                    INSERT INTO openstates.bill_actions (
                        bill_id, action_description, action_date, is_latest
                    ) VALUES (%s, %s, %s, %s)
                    ON CONFLICT (bill_id, action_date) DO UPDATE SET
                        action_description = EXCLUDED.action_description,
                        is_latest = EXCLUDED.is_latest
                """, (bill['bill_id'], bill['latest_action_description'],
                      bill['latest_action_date'], True))

    def update_checkpoint(self, jurisdiction: str, page: int, batch_size: int):
        """Update checkpoint progress"""
        cursor = self.db_conn.cursor()
        try:
            cursor.execute("""
                CALL incremental.update_checkpoint_progress(
                    'openstates.org', 'bills', %s, %s, %s, %s
                )
            """, (jurisdiction, page, batch_size, True))

            self.db_conn.commit()
        except Exception as e:
            self.db_conn.rollback()
            print(f"❌ Error updating checkpoint: {e}")
        finally:
            cursor.close()

    def ingest_jurisdiction_bills(self, jurisdiction: str) -> Dict[str, Any]:
        """Ingest bills for a specific jurisdiction"""
        print(f"🏛️ Starting incremental bills ingestion for {jurisdiction}")

        # Get checkpoint info
        params = self.get_next_ingestion_params(jurisdiction)

        if params['is_completed']:
            print(f"✅ {jurisdiction} bills already completed")
            return {
                'jurisdiction': jurisdiction,
                'status': 'already_completed',
                'records_processed': 0,
                'records_skipped': 0
            }

        print(f"📍 Starting from page: {params['next_page']}")

        session_id = self.start_ingestion_session(jurisdiction)

        try:
            page = params['next_page']
            total_processed = 0
            total_skipped = 0

            while True:
                # Fetch batch
                batch_data = self.fetch_bills_batch(jurisdiction, page)
                bills = batch_data.get('results', [])

                if not bills:
                    print("✅ No more bills found")
                    break

                print(f"📄 Processing {len(bills)} bills from page {page}")

                new_bills = []
                skipped_in_batch = 0

                for bill_data in bills:
                    bill_id = bill_data.get('id', '')

                    if not bill_id:
                        skipped_in_batch += 1
                        continue

                    # Check if already processed
                    if self.is_record_processed(bill_id, bill_data):
                        skipped_in_batch += 1
                        continue

                    # Normalize data
                    normalized = self.normalize_bill_data(bill_data)
                    if normalized and normalized['bill_id']:
                        new_bills.append(normalized)

                # Insert new bills
                if new_bills:
                    inserted = self.insert_bills_batch(new_bills)
                    total_processed += inserted
                    print(f"   ✅ Inserted {inserted} new bills")

                total_skipped += skipped_in_batch

                # Update checkpoint
                self.update_checkpoint(jurisdiction, page, len(bills))

                # Check if we should continue
                if len(bills) < self.batch_size:
                    print("✅ Reached end of bills list")
                    break

                page += 1

            # Mark checkpoint as completed
            self.update_checkpoint(jurisdiction, page, 0)

            # Complete session
            self.complete_ingestion_session(session_id, 'completed')

            result = {
                'jurisdiction': jurisdiction,
                'status': 'completed',
                'records_processed': total_processed,
                'records_skipped': total_skipped
            }

            print(f"🎉 {jurisdiction} bills ingestion completed!")
            print(f"📊 Processed: {total_processed}, Skipped: {total_skipped}")

            return result

        except Exception as e:
            self.complete_ingestion_session(session_id, 'failed', str(e))
            print(f"❌ {jurisdiction} bills failed: {e}")
            return {
                'jurisdiction': jurisdiction,
                'status': 'failed',
                'error': str(e),
                'records_processed': total_processed,
                'records_skipped': total_skipped
            }

    def ingest_all_jurisdictions(self, jurisdictions: List[str] = None) -> List[Dict[str, Any]]:
        """Ingest bills for multiple jurisdictions"""
        if jurisdictions is None:
            jurisdictions = ['ca', 'tx', 'fl', 'ny', 'pa']  # Default to major states

        results = []

        for jurisdiction in jurisdictions:
            result = self.ingest_jurisdiction_bills(jurisdiction)
            results.append(result)

        # Summary
        completed = sum(1 for r in results if r.get('status') == 'completed')
        total_processed = sum(r.get('records_processed', 0) for r in results)
        total_skipped = sum(r.get('records_skipped', 0) for r in results)

        print("\n🎉 All jurisdiction bills ingestion completed!")
        print("📊 Summary:")
        print(f"   Jurisdictions completed: {completed}/{len(results)}")
        print(f"   Total bills processed: {total_processed}")
        print(f"   Total bills skipped: {total_skipped}")

        return results

def main():
    """Main function for testing"""
    ingestor = IncrementalOpenStatesBillsIngestor()

    # Test with California
    results = ingestor.ingest_all_jurisdictions(['ca'])

    print("\n🎯 Bills ingestion test completed!")
    print(f"Results: {results}")

if __name__ == "__main__":
    main()
