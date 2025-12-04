#!/usr/bin/env python3
"""
Incremental GovInfo Bills Ingestion
Ingests bills from GovInfo.gov API with checkpoint tracking and fingerprinting
"""

import os
import sys
import requests
import hashlib
import json
import time
import psycopg2
import psycopg2.pool
from psycopg2.extras import execute_values
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

from rate_limiter import adaptive_limiters
from env_config import get_optional_env_var, validate_api_keys

class IncrementalGovInfoBillsIngestor:
    """Incremental bills ingestion for GovInfo.gov API"""

    def __init__(self):
        # Validate API key
        api_keys = validate_api_keys()
        if not api_keys['govinfo.gov']:
            raise ValueError("GOVINFO_API_KEY not found in environment variables")

        self.api_key = get_optional_env_var('GOVINFO_API_KEY')
        self.base_url = "https://api.govinfo.gov"
        self.batch_size = 100
        self.db_pool = None
        self._setup_database_pool()

    def _setup_database_pool(self):
        """Setup database connection pool"""
        try:
            self.db_pool = psycopg2.pool.ThreadedConnectionPool(
                minconn=2,
                maxconn=10,
                database="opendiscourse",
                user="cbwinslow",
                host="/var/run/postgresql"
            )
            print("✅ Database connection pool established")
        except Exception as e:
            print(f"❌ Database pool setup failed: {e}")
            self.db_pool = None

    def start_ingestion_session(self, congress: int) -> str:
        """Start ingestion session for tracking"""
        session_id = f"govinfo_bills_{congress}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        if not self.db_pool:
            print("❌ Database pool not available")
            return None

        conn = self.db_pool.getconn()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO incremental.ingestion_sessions (
                    session_id, data_source, data_type, status, started_at
                ) VALUES (%s, %s, %s, %s, %s)
            """, (session_id, 'govinfo.gov', 'bills', 'running', datetime.now()))

            self.db_pool.putconn(conn)
            return session_id
        except Exception as e:
            self.db_pool.putconn(conn)
            raise e

    def complete_ingestion_session(self, session_id: str, status: str, error_message: str = None):
        """Complete ingestion session"""
        if not self.db_pool:
            print("❌ Database pool not available")
            return

        conn = self.db_pool.getconn()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                UPDATE incremental.ingestion_sessions SET
                    status = %s,
                    completed_at = %s,
                    error_summary = %s
                WHERE session_id = %s
            """, (status, datetime.now(), error_message, session_id))

            self.db_pool.putconn(conn)
        except Exception as e:
            self.db_pool.putconn(conn)
            raise e

    def get_next_ingestion_params(self, congress: int) -> Dict[str, Any]:
        """Get next ingestion parameters from checkpoint"""
        if not self.db_pool:
            print("❌ Database pool not available")
            return {}

        conn = self.db_pool.getconn()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT * FROM incremental.get_next_ingestion_params('govinfo.gov', 'bills', %s)
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
            self.db_pool.putconn(conn)
            cursor.close()

    def is_record_processed(self, bill_id: str, bill_data: Dict[str, Any]) -> bool:
        """Check if bill was already processed using fingerprint"""
        if not self.db_pool:
            print("❌ Database pool not available")
            return False

        # Generate content hash
        content_str = json.dumps(bill_data, sort_keys=True, separators=(',', ':'))
        content_hash = hashlib.sha256(content_str.encode()).hexdigest()

        conn = self.db_pool.getconn()
        cursor = conn.cursor()
        try:
            # Check if record fingerprint exists
            cursor.execute("""
                SELECT 1 FROM incremental.record_fingerprints
                WHERE data_source = %s AND data_type = %s AND record_id = %s
            """, ('govinfo.gov', 'bills', bill_id))

            exists = cursor.fetchone() is not None

            if not exists:
                # Insert new fingerprint
                cursor.execute("""
                    INSERT INTO incremental.record_fingerprints (
                        data_source, data_type, record_id, record_hash,
                        record_timestamp, first_seen_at, last_updated_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    'govinfo.gov', 'bills', bill_id, content_hash,
                    datetime.now(), datetime.now(), datetime.now()
                ))

            self.db_pool.putconn(conn)
            return exists

        except Exception as e:
            self.db_pool.putconn(conn)
            print(f"❌ Error checking record fingerprint: {e}")
            return False

    def fetch_bill_packages(self, congress: int, offset: int = 0) -> Dict[str, Any]:
        """Fetch bill packages from GovInfo.gov API"""
        # Use adaptive rate limiting
        adaptive_limiters['govinfo.gov'].wait_for_token()

        # Calculate date range for the congress
        start_year = 1789 + (congress - 1) * 2
        end_year = start_year + 2
        start_date = f"{start_year}-01-01T00:00:00Z"
        end_date = f"{end_year}-01-01T00:00:00Z"

        url = f"{self.base_url}/collections/BILLS/{start_date}"
        params = {
            'congress': congress,
            'offset': offset,
            'pageSize': self.batch_size
        }

        if self.api_key:
            params['api_key'] = self.api_key

        headers = {
            'Accept': 'application/json'
        }

        try:
            response = requests.get(url, params=params, headers=headers, timeout=30)

            # Update rate limiter based on response
            adaptive_limiters['govinfo.gov'].update_from_response(response.headers)
            adaptive_limiters['govinfo.gov'].handle_error(response.status_code)

            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            # Handle rate limit errors
            if hasattr(e, 'response') and e.response.status_code == 429:
                adaptive_limiters['govinfo.gov'].handle_error(429)
                print(f"⚠️ Rate limit hit, waiting and retrying...")
                time.sleep(5)
                response = requests.get(url, params=params, headers=headers, timeout=30)
                response.raise_for_status()
                return response.json()
            else:
                print(f"❌ API request failed: {e}")
                raise

    def fetch_bill_package_details(self, package_id: str) -> Dict[str, Any]:
        """Fetch detailed information about a specific bill package"""
        # Use adaptive rate limiting
        adaptive_limiters['govinfo.gov'].wait_for_token()

        url = f"{self.base_url}/packages/{package_id}"
        params = {}

        if self.api_key:
            params['api_key'] = self.api_key

        headers = {
            'Accept': 'application/json'
        }

        try:
            response = requests.get(url, params=params, headers=headers, timeout=30)

            # Update rate limiter based on response
            adaptive_limiters['govinfo.gov'].update_from_response(response.headers)
            adaptive_limiters['govinfo.gov'].handle_error(response.status_code)

            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            # Handle rate limit errors
            if hasattr(e, 'response') and e.response.status_code == 429:
                adaptive_limiters['govinfo.gov'].handle_error(429)
                print(f"⚠️ Rate limit hit on package details, waiting...")
                time.sleep(5)
                response = requests.get(url, params=params, headers=headers, timeout=30)
                response.raise_for_status()
                return response.json()
            else:
                print(f"❌ Package details request failed: {e}")
                return {}

    def fetch_bill_text(self, package_id: str) -> Optional[str]:
        """Fetch full text of a bill"""
        # Use adaptive rate limiting
        adaptive_limiters['govinfo.gov'].wait_for_token()

        url = f"{self.base_url}/packages/{package_id}/htm"
        params = {}

        if self.api_key:
            params['api_key'] = self.api_key

        headers = {
            'Accept': 'text/html'
        }

        try:
            response = requests.get(url, params=params, headers=headers, timeout=30)

            # Update rate limiter based on response
            adaptive_limiters['govinfo.gov'].update_from_response(response.headers)
            adaptive_limiters['govinfo.gov'].handle_error(response.status_code)

            response.raise_for_status()
            return response.text

        except requests.exceptions.RequestException as e:
            # Handle rate limit errors
            if hasattr(e, 'response') and e.response.status_code == 429:
                adaptive_limiters['govinfo.gov'].handle_error(429)
                print(f"⚠️ Rate limit hit on bill text, waiting...")
                time.sleep(5)
                response = requests.get(url, params=params, headers=headers, timeout=30)
                response.raise_for_status()
                return response.text
            else:
                print(f"⚠️ Could not fetch bill text: {e}")
                return None

    def normalize_bill_data(self, package_data: Dict[str, Any], bill_text: str = None) -> Optional[Dict[str, Any]]:
        """Normalize bill data for database insertion"""
        try:
            package_id = package_data.get('packageId', '')

            # Extract bill information from package ID
            # Format: BILLS-118hr1234-2023-05-15
            if '-' in package_id:
                parts = package_id.split('-')
                if len(parts) >= 3:
                    congress_part = parts[1] if len(parts) > 1 else ''
                    bill_number_part = parts[2] if len(parts) > 2 else ''

                    # Parse congress
                    congress = None
                    if congress_part.isdigit():
                        congress = int(congress_part)

                    # Parse bill number
                    bill_type = ''
                    bill_number = ''
                    if bill_number_part:
                        if bill_number_part[0].isalpha():
                            bill_type = bill_number_part[0]
                            bill_number = bill_number_part[1:]
                        else:
                            bill_number = bill_number_part

            # If we couldn't parse congress from package_id, set a default
            if congress is None:
                congress = 118  # Default to current congress

            # Get title from package metadata
            title = package_data.get('title', '')

            # Get date information
            date_issued = package_data.get('dateIssued', '')
            last_modified = package_data.get('lastModified', '')

            # Get download information
            downloads = package_data.get('download', [])
            pdf_url = ''
            xml_url = ''

            for download in downloads:
                if download.get('format') == 'pdf':
                    pdf_url = download.get('url', '')
                elif download.get('format') == 'xml':
                    xml_url = download.get('url', '')

            # Get summary from package metadata
            summary = package_data.get('summary', '')

            return {
                'package_id': package_id,
                'congress': congress,
                'bill_type': bill_type,
                'bill_number': bill_number,
                'title': title,
                'summary': summary,
                'bill_text': bill_text,
                'date_issued': datetime.fromisoformat(date_issued.replace('Z', '+00:00')) if date_issued else None,
                'last_modified': datetime.fromisoformat(last_modified.replace('Z', '+00:00')) if last_modified else None,
                'pdf_url': pdf_url,
                'xml_url': xml_url,
                'govinfo_url': f"https://www.govinfo.gov/content/pkg/{package_id}",
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }
        except Exception as e:
            print(f"❌ Error normalizing bill data: {e}")
            return None

    def insert_bills_batch(self, bills: List[Dict[str, Any]]) -> int:
        """Insert batch of bills into database"""
        if not self.db_pool:
            print("❌ Database pool not available")
            return 0

        conn = self.db_pool.getconn()
        cursor = conn.cursor()
        try:
            bill_query = """
                INSERT INTO govinfo.bills (
                    package_id, congress, bill_type, bill_number, title, summary,
                    bill_text, date_issued, last_modified, pdf_url, xml_url,
                    govinfo_url, created_at, updated_at
                ) VALUES %s
                ON CONFLICT (package_id) DO UPDATE SET
                    title = EXCLUDED.title,
                    summary = EXCLUDED.summary,
                    bill_text = EXCLUDED.bill_text,
                    date_issued = EXCLUDED.date_issued,
                    last_modified = EXCLUDED.last_modified,
                    pdf_url = EXCLUDED.pdf_url,
                    xml_url = EXCLUDED.xml_url,
                    govinfo_url = EXCLUDED.govinfo_url,
                    updated_at = EXCLUDED.updated_at
            """

            bill_values = [
                (
                    b['package_id'], b['congress'], b['bill_type'], b['bill_number'],
                    b['title'], b['summary'], b['bill_text'], b['date_issued'],
                    b['last_modified'], b['pdf_url'], b['xml_url'], b['govinfo_url'],
                    b['created_at'], b['updated_at']
                )
                for b in bills if b and b.get('package_id')
            ]

            if bill_values:
                execute_values(cursor, bill_query, bill_values)
                inserted = len(bill_values)

                # Update bill versions table
                self._update_bill_versions(cursor, bills)

                self.db_pool.putconn(conn)
                return inserted
            self.db_pool.putconn(conn)
            return 0
        except Exception as e:
            print(f"❌ Error inserting bills batch: {e}")
            self.db_pool.putconn(conn)
            return 0
        finally:
            cursor.close()

    def _update_bill_versions(self, cursor, bills: List[Dict[str, Any]]):
        """Update bill versions with text content"""
        for bill in bills:
            if bill and bill.get('package_id') and bill.get('bill_text'):
                cursor.execute("""
                    INSERT INTO govinfo.bill_versions (
                        package_id, version_type, content_text, content_url
                    ) VALUES (%s, %s, %s, %s)
                    ON CONFLICT (package_id, version_type) DO UPDATE SET
                        content_text = EXCLUDED.content_text,
                        content_url = EXCLUDED.content_url
                """, (bill['package_id'], 'htm', bill['bill_text'], bill['govinfo_url']))

    def update_checkpoint(self, congress: int, offset: int, batch_size: int):
        """Update checkpoint progress"""
        if not self.db_pool:
            print("❌ Database pool not available")
            return

        conn = self.db_pool.getconn()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                CALL incremental.update_checkpoint_progress(
                    'govinfo.gov', 'bills', %s, %s, %s, %s
                )
            """, (str(congress), offset, batch_size, True))

            self.db_pool.putconn(conn)
        except Exception as e:
            self.db_pool.putconn(conn)
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
                # Fetch batch of packages
                batch_data = self.fetch_bill_packages(congress, offset)
                packages = batch_data.get('packages', [])

                if not packages:
                    print(f"✅ No more bill packages found")
                    break

                print(f"📄 Processing {len(packages)} bill packages from offset {offset}")

                new_bills = []
                skipped_in_batch = 0

                for package_data in packages:
                    package_id = package_data.get('packageId', '')

                    if not package_id:
                        skipped_in_batch += 1
                        continue

                    # Check if already processed
                    if self.is_record_processed(package_id, package_data):
                        skipped_in_batch += 1
                        continue

                    # Fetch detailed package information
                    package_details = self.fetch_bill_package_details(package_id)

                    # Fetch bill text (optional, can be skipped for performance)
                    bill_text = None
                    # Uncomment the following line if you want to fetch full text
                    # bill_text = self.fetch_bill_text(package_id)

                    # Normalize data
                    normalized = self.normalize_bill_data(package_details or package_data, bill_text)
                    if normalized and normalized['package_id']:
                        new_bills.append(normalized)

                # Insert new bills
                if new_bills:
                    inserted = self.insert_bills_batch(new_bills)
                    total_processed += inserted
                    print(f"   ✅ Inserted {inserted} new bills")

                total_skipped += skipped_in_batch

                # Update checkpoint
                self.update_checkpoint(congress, offset, len(packages))

                # Check if we should continue
                if len(packages) < self.batch_size:
                    print(f"✅ Reached end of bill packages list")
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
    ingestor = IncrementalGovInfoBillsIngestor()

    # Test with current congress
    results = ingestor.ingest_all_congresses(118, 118)

    print(f"\n🎯 Bills ingestion test completed!")
    print(f"Results: {results}")

if __name__ == "__main__":
    main()
