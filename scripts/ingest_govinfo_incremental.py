#!/usr/bin/env python3
"""
Incremental GovInfo Members Ingestion Script
Uses checkpoint tracking to avoid re-downloading and re-processing data
"""

import os
import sys
import requests
import hashlib
import json
import time
import logging
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

from rate_limiter import adaptive_limiters
from env_config import get_optional_env_var, validate_api_keys
from psycopg2.extras import execute_values, Json

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class IncrementalGovInfoIngestor:
    """Incremental GovInfo members ingestion with checkpoint tracking"""

    def __init__(self):
        # Validate API key
        api_keys = validate_api_keys()
        if not api_keys['govinfo.gov']:
            raise ValueError("GOVINFO_API_KEY not found in environment variables")

        self.api_key = get_optional_env_var('GOVINFO_API_KEY')
        self.base_url = "https://api.govinfo.gov"
        self.batch_size = 100
        self.max_retries = 3

        # Database connection
        self.db_conn = psycopg2.connect(
            database='cbwinslow',
            user='cbwinslow'
        )
        self.db_conn.autocommit = False

        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def get_next_ingestion_params(self, congress: int = None, data_type: str = 'members') -> Dict[str, Any]:
        """Get next ingestion parameters from checkpoint"""
        cursor = self.db_conn.cursor()

        try:
            category = str(congress) if congress else 'all'

            cursor.execute("""
                SELECT * FROM incremental.get_next_ingestion_params(
                    %s, %s, %s
                )
            """, ('govinfo.gov', data_type, category))

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

    def create_checkpoint(self, congress: int = None, data_type: str = 'members', total_estimated: int = None) -> None:
        """Create or get checkpoint for this data type"""
        cursor = self.db_conn.cursor()

        try:
            category = str(congress) if congress else 'all'

            cursor.execute("""
                SELECT incremental.get_or_create_checkpoint(
                    %s, %s, %s, %s
                )
            """, ('govinfo.gov', data_type, category, total_estimated))

            self.db_conn.commit()
        finally:
            cursor.close()

    def update_checkpoint(self, congress: int = None, data_type: str = 'members',
                         last_offset: int = None, records_processed: int = 0, is_completed: bool = False) -> None:
        """Update checkpoint progress"""
        cursor = self.db_conn.cursor()

        try:
            category = str(congress) if congress else 'all'

            cursor.execute("""
                SELECT incremental.update_checkpoint_progress(
                    %s, %s, %s,
                    %s, NULL, NULL, NULL,
                    %s, %s
                )
            """, (
                'govinfo.gov', data_type, category,
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
                    %s, %s, %s, %s::jsonb
                )
            """, ('govinfo.gov', 'members', member_id, json.dumps(member_data)))

            result = cursor.fetchone()
            return result[0] if result else False
        finally:
            cursor.close()

    def fetch_congressional_directories(self, congress: int) -> List[Dict[str, Any]]:
        """Fetch Congressional Directory packages for a congress"""
        # Use adaptive rate limiting
        adaptive_limiters['govinfo.gov'].wait_for_token()

        url = f"{self.base_url}/collections/CDIR/2023-01-01T00:00:00Z"
        params = {
            'api_key': self.api_key,
            'congress': congress,
            'offset': 0,
            'pageSize': 100
        }

        for attempt in range(self.max_retries):
            try:
                response = requests.get(url, params=params, timeout=30)

                # Update rate limiter based on response
                adaptive_limiters['govinfo.gov'].update_from_response(response.headers)
                adaptive_limiters['govinfo.gov'].handle_error(response.status_code)

                response.raise_for_status()

                data = response.json()
                packages = data.get('packages', [])

                # Filter for the most recent directory
                if packages:
                    return packages

                return []

            except requests.exceptions.RequestException as e:
                # Handle rate limit errors
                if hasattr(e, 'response') and e.response.status_code == 429:
                    adaptive_limiters['govinfo.gov'].handle_error(429)
                    self.logger.warning(f"Rate limit hit on attempt {attempt + 1}, waiting...")
                    time.sleep(5 * (attempt + 1))
                    continue

                if attempt == self.max_retries - 1:
                    raise
                self.logger.warning(f"Attempt {attempt + 1} failed: {e}")
                time.sleep(2 ** attempt)

        return []

    def fetch_directory_content(self, package_id: str) -> str:
        """Fetch the text content of a Congressional Directory"""
        summary_url = f"{self.base_url}/packages/{package_id}/summary"
        params = {'api_key': self.api_key}

        for attempt in range(self.max_retries):
            try:
                # Fetch package summary to discover available download links
                response = requests.get(summary_url, params=params, timeout=30)
                response.raise_for_status()

                data = response.json()
                download_links = data.get('download', {})

                txt_link = download_links.get('txtLink')
                if txt_link:
                    txt_response = requests.get(f"{txt_link}?api_key={self.api_key}", timeout=60)
                    txt_response.raise_for_status()
                    return txt_response.text

                pdf_link = download_links.get('pdfLink')
                if pdf_link:
                    self.logger.warning(f"No TXT link for {package_id}; PDF link available at {pdf_link}")

                return ""

            except requests.exceptions.RequestException as e:
                if attempt == self.max_retries - 1:
                    raise
                self.logger.warning(f"Attempt {attempt + 1} failed: {e}")
                time.sleep(2 ** attempt)

        return ""

    def parse_members_from_directory(self, content: str) -> List[Dict[str, Any]]:
        """Parse member information from Congressional Directory text"""
        members = []
        lines = content.split('\n')

        current_member = {}
        current_section = None

        for line in lines:
            line = line.strip()

            if not line:
                continue

            # Detect section headers
            if line.upper() in ['SENATE', 'HOUSE OF REPRESENTATIVES', 'HOUSE']:
                current_section = 'SENATE' if 'SENATE' in line.upper() else 'HOUSE'
                continue

            # Parse member lines (simplified pattern matching)
            # This is a basic parser - you'd need to enhance this based on actual format
            if ', ' in line and any(char.isdigit() for char in line):
                parts = line.split(', ')
                if len(parts) >= 2:
                    name = parts[0].strip()
                    state_info = parts[1].strip()

                    # Extract state (simplified)
                    state = state_info.split()[0] if state_info else ''

                    # Create basic member record
                    member = {
                        'memberId': f"govinfo_{name.replace(' ', '_').lower()}_{state.lower()}",
                        'bioguideId': None,  # Would need to match with other sources
                        'name': {
                            'first': name.split()[0] if name.split() else '',
                            'last': name.split()[-1] if name.split() else '',
                            'fullName': name
                        },
                        'party': 'Unknown',  # Would need to parse from text
                        'state': state,
                        'chamber': current_section,
                        'sourceText': line
                    }

                    members.append(member)

        return members

    def normalize_member_data(self, member_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize member data for database insertion"""
        name_info = member_data.get('name', {})
        party_code = member_data.get('party', None)
        if party_code in ('Unknown', '', None):
            party_code = None

        return {
            'member_id': member_data.get('memberId'),
            'bioguide_id': member_data.get('bioguideId'),
            'first_name': name_info.get('first', ''),
            'middle_name': None,
            'last_name': name_info.get('last', ''),
            'suffix': None,
            'full_name': name_info.get('fullName', ''),
            'preferred_name': None,
            'birthday': None,
            'gender': None,
            'party_code': party_code,
            'state': member_data.get('state', ''),
            'district': None,
            'url': None,
            'twitter_handle': None,
            'youtube_handle': None,
            'facebook_handle': None,
            'biography_text': member_data.get('sourceText', ''),
            'photo_url': None,
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
                INSERT INTO govinfo.members (
                    member_id, bioguide_id, first_name, middle_name, last_name, suffix,
                    full_name, preferred_name, birthday, gender, party_code, state,
                    district, url, twitter_handle, youtube_handle, facebook_handle,
                    biography_text, photo_url, created_at, updated_at
                ) VALUES %s
                ON CONFLICT (member_id) DO NOTHING
            """

            values = [
                (
                    m['member_id'], m['bioguide_id'], m['first_name'], m['middle_name'],
                    m['last_name'], m['suffix'], m['full_name'], m['preferred_name'],
                    m['birthday'], m['gender'], m['party_code'], m['state'],
                    m['district'], m['url'], m['twitter_handle'], m['youtube_handle'],
                    m['facebook_handle'], m['biography_text'], m['photo_url'],
                    m['created_at'], m['updated_at']
                )
                for m in members
            ]

            execute_values(cursor, query, values)
            self.db_conn.commit()
            return cursor.rowcount if cursor.rowcount != -1 else len(members)

        except Exception as e:
            self.db_conn.rollback()
            self.logger.error(f"Error inserting members batch: {e}")
            raise

    def start_ingestion_session(self, congress: int = None, data_type: str = 'members') -> str:
        """Start ingestion session tracking"""
        category = str(congress) if congress else 'all'
        session_id = f"govinfo_{data_type}_{category}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        cursor = self.db_conn.cursor()
        try:
            cursor.execute("""
                CALL incremental.start_ingestion_session(
                    %s, %s, %s, %s::jsonb
                )
            """, (
                session_id, 'govinfo.gov', data_type,
                json.dumps({'congress': congress, 'data_type': data_type})
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
        params = self.get_next_ingestion_params(congress, 'members')

        if params['is_completed']:
            print(f"✅ GovInfo Congress {congress} members already completed")
            return {
                'congress': congress,
                'status': 'already_completed',
                'records_processed': 0,
                'records_skipped': 0
            }

        # Create checkpoint if needed
        self.create_checkpoint(congress, 'members')

        # Start session
        session_id = self.start_ingestion_session(congress, 'members')

        print(f"🚀 Starting incremental GovInfo ingestion for Congress {congress}")

        try:
            # Fetch Congressional Directory packages
            packages = self.fetch_congressional_directories(congress)

            if not packages:
                print(f"❌ No Congressional Directory found for Congress {congress}")
                self.complete_ingestion_session(session_id, 'failed', 'No directory found')
                return {
                    'congress': congress,
                    'status': 'failed',
                    'error': 'No directory found'
                }

            # Use the most recent directory
            latest_package = packages[0]
            package_id = latest_package.get('packageId')

            print(f"📄 Found directory package: {package_id}")

            # Fetch and parse content
            content = self.fetch_directory_content(package_id)

            if not content:
                print(f"❌ No content found for package {package_id}")
                self.complete_ingestion_session(session_id, 'failed', 'No content found')
                return {
                    'congress': congress,
                    'status': 'failed',
                    'error': 'No content found'
                }

            # Parse members from content
            all_members = self.parse_members_from_directory(content)

            if not all_members:
                print(f"❌ No members parsed from content")
                self.complete_ingestion_session(session_id, 'failed', 'No members parsed')
                return {
                    'congress': congress,
                    'status': 'failed',
                    'error': 'No members parsed'
                }

            print(f"👥 Parsed {len(all_members)} members from directory")

            # Process members with deduplication
            new_members = []
            skipped_count = 0
            seen_member_ids = set()

            for member_data in all_members:
                member_id = member_data.get('memberId')

                if not member_id:
                    skipped_count += 1
                    continue

                if member_id in seen_member_ids:
                    skipped_count += 1
                    continue
                seen_member_ids.add(member_id)

                # Check if already processed
                if self.is_record_processed(member_id, member_data):
                    skipped_count += 1
                    continue

                # Normalize and add to batch
                try:
                    normalized = self.normalize_member_data(member_data)
                    if normalized['member_id']:
                        new_members.append(normalized)
                except Exception as e:
                    self.logger.error(f"Error normalizing member {member_id}: {e}")
                    skipped_count += 1
                    continue

            # Insert new members
            total_inserted = 0
            if new_members:
                # Process in batches
                for i in range(0, len(new_members), self.batch_size):
                    batch = new_members[i:i + self.batch_size]
                    inserted = self.insert_members_batch(batch)
                    total_inserted += inserted
                    print(f"   ✅ Inserted batch {i//self.batch_size + 1}: {inserted} members")

            # Update checkpoint
            processed_count = total_inserted + skipped_count
            self.update_checkpoint(congress, 'members', len(all_members), processed_count, True)

            # Complete session
            self.complete_ingestion_session(session_id, 'completed')

            print(f"🎉 GovInfo Congress {congress} ingestion completed!")
            print(f"📊 Processed: {processed_count}, Skipped: {skipped_count}, Inserted: {total_inserted}")

            return {
                'congress': congress,
                'status': 'completed',
                'records_processed': processed_count,
                'records_skipped': skipped_count,
                'total_found': len(all_members)
            }

        except Exception as e:
            self.complete_ingestion_session(session_id, 'failed', str(e))
            raise

    def ingest_all_congresses(self, start_congress: int = 118, end_congress: int = 118):
        """Ingest all congresses in range"""
        print(f"🚀 Starting incremental GovInfo ingestion for Congresses {start_congress}-{end_congress}")

        results = []

        for congress in range(start_congress, end_congress + 1):
            try:
                result = self.ingest_congress_members(congress)
                results.append(result)
                print(f"✅ Congress {congress} completed")
                time.sleep(2)  # Rate limiting between congresses
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

        print(f"\n🎉 All GovInfo congresses ingestion completed!")
        print(f"📊 Summary:")
        print(f"   Congresses completed: {completed}/{len(results)}")
        print(f"   Total records processed: {total_processed}")
        print(f"   Total records skipped: {total_skipped}")

        return results

    def get_checkpoint_status(self):
        """Get status of all checkpoints"""
        cursor = self.db_conn.cursor()

        try:
            cursor.execute("SELECT * FROM incremental.checkpoint_status WHERE data_source = 'govinfo.gov'")
            checkpoints = cursor.fetchall()

            print("\n📋 GovInfo.gov Checkpoint Status:")
            print("-" * 80)
            for cp in checkpoints:
                progress = f"{cp[8]:.1f}%" if cp[8] is not None else "N/A"
                last_run = cp[9] if cp[9] is not None else "Never"
                print(f"{cp[0]} | {cp[1]} | {cp[2]} | {cp[11]} | {progress} | {last_run}")

            return checkpoints
        finally:
            cursor.close()

def main():
    """Main function"""
    ingestor = IncrementalGovInfoIngestor()

    # Show current checkpoint status
    ingestor.get_checkpoint_status()

    # Ingest Congress 118 (or specify range)
    results = ingestor.ingest_all_congresses(118, 118)

    # Show final status
    ingestor.get_checkpoint_status()

if __name__ == "__main__":
    main()
