#!/usr/bin/env python3
"""
Fixed GovInfo Ingestion Process
Comprehensive solution for ingesting votes, bills, and members with proper offset handling
"""

import os
import sys
import requests
import json
import time
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple, Generator
from dataclasses import dataclass
from enum import Enum

import psycopg2
from psycopg2.extras import execute_values, DictCursor
from psycopg2.pool import ThreadedConnectionPool

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rate_limiter import adaptive_limiters
from env_config import get_optional_env_var, validate_api_keys


class DataType(Enum):
    """Enumeration for different data types"""
    BILLS = "bills"
    VOTES = "votes"
    MEMBERS = "members"
    COMMITTEES = "committees"


@dataclass
class IngestionConfig:
    """Configuration for ingestion process"""
    data_type: DataType
    congress: int
    batch_size: int = 100
    max_retries: int = 3
    request_delay: float = 0.1
    enable_checkpoint: bool = True
    resume_from_checkpoint: bool = True


@dataclass
class IngestionStats:
    """Statistics for ingestion process"""
    total_processed: int = 0
    total_inserted: int = 0
    total_skipped: int = 0
    total_failed: int = 0
    current_offset: int = 0
    api_calls_made: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


class FixedGovInfoIngestor:
    """Fixed GovInfo ingestion with proper offset handling for all data types"""

    def __init__(self, db_connection_params: Dict[str, Any] = None):
        # Validate API key
        api_keys = validate_api_keys()
        if not api_keys.get('govinfo.gov'):
            raise ValueError("GOVINFO_API_KEY not found in environment variables")

        self.api_key = get_optional_env_var('GOVINFO_API_KEY')
        self.base_url = "https://api.govinfo.gov"

        # Default database connection parameters
        if db_connection_params is None:
            db_connection_params = {
                'database': os.getenv('DB_NAME', 'cbwinslow'),
                'user': os.getenv('DB_USER', 'cbwinslow'),
                'host': os.getenv('DB_HOST', '/var/run/postgresql')
            }

        self.db_params = db_connection_params
        self.db_pool = None
        self._setup_database_pool()

        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def _setup_database_pool(self):
        """Setup database connection pool"""
        try:
            self.db_pool = ThreadedConnectionPool(
                minconn=2,
                maxconn=10,
                **self.db_params
            )
            self.logger.info("✅ Database connection pool established")
        except Exception as e:
            self.logger.error(f"❌ Database pool setup failed: {e}")
            self.db_pool = None

    def get_db_connection(self):
        """Get database connection from pool"""
        if not self.db_pool:
            return psycopg2.connect(**self.db_params)
        return self.db_pool.getconn()

    def return_db_connection(self, conn):
        """Return database connection to pool"""
        if self.db_pool:
            self.db_pool.putconn(conn)
        else:
            conn.close()

    def get_checkpoint(self, config: IngestionConfig) -> Tuple[int, bool]:
        """Get current checkpoint offset and completion status"""
        if not config.enable_checkpoint:
            return 0, False

        conn = self.get_db_connection()
        cursor = conn.cursor()
        try:
            # Get checkpoint from database
            cursor.execute("""
                SELECT last_offset, is_completed
                FROM incremental.checkpoint_status
                WHERE data_source = 'govinfo.gov'
                AND data_type = %s
                AND category = %s
                ORDER BY last_updated_at DESC
                LIMIT 1
            """, (config.data_type.value, str(config.congress)))

            result = cursor.fetchone()
            if result:
                offset, is_completed = result
                return offset or 0, bool(is_completed)
            else:
                return 0, False
        except Exception as e:
            self.logger.warning(f"Could not get checkpoint: {e}")
            return 0, False
        finally:
            cursor.close()
            self.return_db_connection(conn)

    def update_checkpoint(self, config: IngestionConfig, offset: int, is_completed: bool = False):
        """Update checkpoint offset"""
        if not config.enable_checkpoint:
            return

        conn = self.get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO incremental.checkpoint_status (
                    data_source, data_type, category, last_offset,
                    is_completed, total_expected, progress_percentage,
                    last_run, last_updated_at
                ) VALUES (
                    'govinfo.gov', %s, %s, %s, %s, %s, %s, %s, %s
                )
                ON CONFLICT (data_source, data_type, category)
                DO UPDATE SET
                    last_offset = EXCLUDED.last_offset,
                    is_completed = EXCLUDED.is_completed,
                    progress_percentage = EXCLUDED.progress_percentage,
                    last_run = EXCLUDED.last_run,
                    last_updated_at = EXCLUDED.last_updated_at
            """, (
                config.data_type.value,
                str(config.congress),
                offset,
                is_completed,
                None,  # total_expected
                None,  # progress_percentage
                datetime.now(),
                datetime.now()
            ))
            conn.commit()
        except Exception as e:
            self.logger.warning(f"Could not update checkpoint: {e}")
            conn.rollback()
        finally:
            cursor.close()
            self.return_db_connection(conn)

    def start_ingestion_session(self, config: IngestionConfig) -> str:
        """Start ingestion session for tracking"""
        session_id = f"govinfo_{config.data_type.value}_{config.congress}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        conn = self.get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO incremental.ingestion_sessions (
                    session_id, data_source, data_type, category,
                    status, started_at, metadata
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                session_id,
                'govinfo.gov',
                config.data_type.value,
                str(config.congress),
                'running',
                datetime.now(),
                json.dumps({
                    'batch_size': config.batch_size,
                    'congress': config.congress,
                    'data_type': config.data_type.value
                })
            ))
            conn.commit()
            return session_id
        except Exception as e:
            self.logger.warning(f"Could not start session: {e}")
            return session_id  # Return session ID anyway for tracking
        finally:
            cursor.close()
            self.return_db_connection(conn)

    def complete_ingestion_session(self, session_id: str, status: str, stats: IngestionStats, error_message: str = None):
        """Complete ingestion session"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                UPDATE incremental.ingestion_sessions SET
                    status = %s,
                    completed_at = %s,
                    records_processed = %s,
                    records_succeeded = %s,
                    records_failed = %s,
                    error_summary = %s
                WHERE session_id = %s
            """, (
                status,
                datetime.now(),
                stats.total_processed,
                stats.total_inserted,
                stats.total_failed,
                error_message,
                session_id
            ))
            conn.commit()
        except Exception as e:
            self.logger.warning(f"Could not complete session: {e}")
        finally:
            cursor.close()
            self.return_db_connection(conn)

    def make_api_request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make API request with proper rate limiting and retry logic"""
        # Use adaptive rate limiting
        if 'govinfo.gov' in adaptive_limiters:
            adaptive_limiters['govinfo.gov'].wait_for_token()

        url = f"{self.base_url}{endpoint}"
        if self.api_key:
            params['api_key'] = self.api_key

        headers = {
            'Accept': 'application/json'
        }

        for attempt in range(3):  # max_retries
            try:
                response = requests.get(url, params=params, headers=headers, timeout=30)

                # Update rate limiter based on response
                if 'govinfo.gov' in adaptive_limiters:
                    adaptive_limiters['govinfo.gov'].update_from_response(response.headers)
                    adaptive_limiters['govinfo.gov'].handle_error(response.status_code)

                response.raise_for_status()
                data = response.json()

                # Add metadata to response
                data['_api_metadata'] = {
                    'url': str(response.url),
                    'status_code': response.status_code,
                    'headers': dict(response.headers),
                    'response_time': response.elapsed.total_seconds()
                }

                return data

            except requests.exceptions.RequestException as e:
                self.logger.warning(f"API request failed (attempt {attempt + 1}): {e}")

                # Handle rate limiting
                if hasattr(e, 'response') and e.response and e.response.status_code == 429:
                    if 'govinfo.gov' in adaptive_limiters:
                        adaptive_limiters['govinfo.gov'].handle_error(429)
                    wait_time = 5 * (attempt + 1)
                    self.logger.warning(f"Rate limited, waiting {wait_time}s...")
                    time.sleep(wait_time)
                elif attempt == 2:  # Last attempt
                    raise
                else:
                    time.sleep(2 ** attempt)

        raise Exception("All retry attempts failed")

    def fetch_bills_batch(self, congress: int, offset: int = 0, page_size: int = 100) -> Dict[str, Any]:
        """Fetch bills batch with proper offset handling"""
        self.logger.debug(f"Fetching bills batch - Congress: {congress}, Offset: {offset}, PageSize: {page_size}")

        # Calculate date range for the congress
        start_year = 1789 + (congress - 1) * 2
        end_year = start_year + 2
        start_date = f"{start_year}-01-01T00:00:00Z"

        params = {
            'congress': congress,
            'offset': offset,
            'pageSize': min(page_size, 100)  # GovInfo max is 100
        }

        return self.make_api_request(f"/collections/BILLS/{start_date}", params)

    def fetch_votes_batch(self, congress: int, offset: int = 0, page_size: int = 100) -> Dict[str, Any]:
        """Fetch votes batch with proper offset handling"""
        self.logger.debug(f"Fetching votes batch - Congress: {congress}, Offset: {offset}, PageSize: {page_size}")

        params = {
            'congress': congress,
            'offset': offset,
            'pageSize': min(page_size, 100)  # GovInfo max is 100
        }

        return self.make_api_request("/collections/rolls", params)

    def fetch_members_batch(self, congress: int, offset: int = 0, page_size: int = 100) -> Dict[str, Any]:
        """Fetch members batch with proper offset handling"""
        self.logger.debug(f"Fetching members batch - Congress: {congress}, Offset: {offset}, PageSize: {page_size}")

        params = {
            'congress': congress,
            'offset': offset,
            'pageSize': min(page_size, 100)  # GovInfo max is 100
        }

        return self.make_api_request("/members", params)

    def paginate_api_response(self, config: IngestionConfig, start_offset: int = 0) -> Generator[List[Dict[str, Any]], None, None]:
        """Generator that handles API pagination properly"""
        offset = start_offset
        batch_size = min(config.batch_size, 100)  # GovInfo max is 100

        while True:
            self.logger.info(f"📄 Fetching batch at offset {offset} (batch size: {batch_size})")

            # Fetch appropriate data type
            if config.data_type == DataType.BILLS:
                response = self.fetch_bills_batch(config.congress, offset, batch_size)
            elif config.data_type == DataType.VOTES:
                response = self.fetch_votes_batch(config.congress, offset, batch_size)
            elif config.data_type == DataType.MEMBERS:
                response = self.fetch_members_batch(config.congress, offset, batch_size)
            else:
                raise ValueError(f"Unsupported data type: {config.data_type}")

            # Extract data from response
            data_key = self._get_data_key(config.data_type)
            items = response.get(data_key, [])

            if not items:
                self.logger.info(f"✅ No more data found at offset {offset}")
                break

            self.logger.info(f"📦 Received {len(items)} items")
            yield items

            # Check if this is the last batch
            if len(items) < batch_size:
                self.logger.info(f"✅ Reached end of data (received {len(items)} < {batch_size})")
                break

            # Increment offset for next batch
            offset += len(items)

            # Rate limiting
            if config.request_delay > 0:
                time.sleep(config.request_delay)

    def _get_data_key(self, data_type: DataType) -> str:
        """Get the appropriate data key for each data type"""
        data_keys = {
            DataType.BILLS: 'packages',
            DataType.VOTES: 'rolls',
            DataType.MEMBERS: 'members',
            DataType.COMMITTEES: 'committees'
        }
        return data_keys.get(data_type, 'items')

    def normalize_bill_data(self, package_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Normalize bill data for database insertion"""
        try:
            package_id = package_data.get('packageId', '')
            if not package_id:
                return None

            # Parse package ID to extract bill information
            # Format: BILLS-118hr1234-2023-05-15
            parts = package_id.split('-')
            congress = None
            bill_type = ''
            bill_number = ''

            if len(parts) >= 3:
                congress_part = parts[1] if len(parts) > 1 else ''
                bill_number_part = parts[2] if len(parts) > 2 else ''

                # Parse congress
                if congress_part.isdigit():
                    congress = int(congress_part)

                # Parse bill number and type
                if bill_number_part:
                    if bill_number_part[0].isalpha():
                        bill_type = bill_number_part[0]
                        bill_number = bill_number_part[1:]
                    else:
                        bill_number = bill_number_part

            if not congress:
                congress = self.congress  # Use instance congress

            return {
                'package_id': package_id,
                'congress': congress,
                'bill_type': bill_type,
                'bill_number': bill_number,
                'title': package_data.get('title', ''),
                'date_issued': self._parse_date(package_data.get('dateIssued')),
                'last_modified': self._parse_date(package_data.get('lastModified')),
                'downloads': json.dumps(package_data.get('download', [])),
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }
        except Exception as e:
            self.logger.error(f"Error normalizing bill data: {e}")
            return None

    def normalize_vote_data(self, vote_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Normalize vote data for database insertion"""
        try:
            roll_id = vote_data.get('rollId', '')
            if not roll_id:
                return None

            # Extract information from roll ID
            # Format typically includes congress and roll number
            parts = roll_id.split('-')
            congress = self.congress  # Use instance congress

            # Parse date if available
            date = self._parse_date(vote_data.get('date'))

            return {
                'roll_id': roll_id,
                'congress': congress,
                'date': date,
                'chamber': vote_data.get('chamber', ''),
                'session': vote_data.get('session', ''),
                'roll_number': vote_data.get('rollNumber', ''),
                'question': vote_data.get('question', ''),
                'question_text': vote_data.get('questionText', ''),
                'type': vote_data.get('type', ''),
                'subject': vote_data.get('subject', ''),
                'by_member': json.dumps(vote_data.get('byMember', [])),
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }
        except Exception as e:
            self.logger.error(f"Error normalizing vote data: {e}")
            return None

    def normalize_member_data(self, member_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Normalize member data for database insertion"""
        try:
            member_id = member_data.get('memberId', '')
            if not member_id:
                return None

            # Handle name parsing
            name_info = member_data.get('name', {})
            if isinstance(name_info, str):
                name_info = {'fullName': name_info}

            first_name = name_info.get('first', name_info.get('givenName', ''))
            last_name = name_info.get('last', name_info.get('familyName', ''))
            middle_name = name_info.get('middle', '')
            suffix = name_info.get('suffix', '')
            full_name = name_info.get('fullName', f"{first_name} {last_name}".strip())

            # Parse dates
            birthday = self._parse_date(member_data.get('birthDate'))
            death_date = self._parse_date(member_data.get('deathDate'))

            # Handle party and state
            party_code = member_data.get('party', member_data.get('partyCode', ''))
            state = member_data.get('state', member_data.get('stateCode', ''))
            district = member_data.get('district', '')

            return {
                'member_id': member_id,
                'bioguide_id': member_data.get('bioguideId', ''),
                'first_name': first_name,
                'middle_name': middle_name,
                'last_name': last_name,
                'suffix': suffix,
                'full_name': full_name,
                'preferred_name': name_info.get('preferredName', ''),
                'birthday': birthday,
                'death_date': death_date,
                'gender': member_data.get('gender', ''),
                'party_code': party_code,
                'state': state,
                'district': str(district) if district else '',
                'url': member_data.get('url', ''),
                'twitter_handle': member_data.get('twitter', ''),
                'youtube_handle': member_data.get('youtube', ''),
                'facebook_handle': member_data.get('facebook', ''),
                'biography_text': member_data.get('biography', member_data.get('bio', '')),
                'photo_url': member_data.get('photoUrl', ''),
                'congress': self.congress,
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }
        except Exception as e:
            self.logger.error(f"Error normalizing member data: {e}")
            return None

    def _parse_date(self, date_str: Optional[str]) -> Optional[str]:
        """Parse date string in various formats"""
        if not date_str:
            return None

        try:
            # Try ISO format first
            if date_str.endswith('Z'):
                return datetime.fromisoformat(date_str.replace('Z', '+00:00')).strftime('%Y-%m-%d')

            # Try other common formats
            for fmt in ['%Y-%m-%d', '%Y/%m/%d', '%m/%d/%Y']:
                try:
                    parsed_date = datetime.strptime(date_str, fmt)
                    return parsed_date.strftime('%Y-%m-%d')
                except ValueError:
                    continue

            self.logger.warning(f"Could not parse date: {date_str}")
            return None
        except Exception as e:
            self.logger.warning(f"Error parsing date '{date_str}': {e}")
            return None

    def insert_batch(self, config: IngestionConfig, items: List[Dict[str, Any]]) -> int:
        """Insert a batch of items into the database"""
        if not items:
            return 0

        conn = self.get_db_connection()
        cursor = conn.cursor()
        try:
            if config.data_type == DataType.BILLS:
                return self._insert_bills_batch(cursor, items)
            elif config.data_type == DataType.VOTES:
                return self._insert_votes_batch(cursor, items)
            elif config.data_type == DataType.MEMBERS:
                return self._insert_members_batch(cursor, items)
            else:
                self.logger.warning(f"Unsupported data type for insertion: {config.data_type}")
                return 0
        except Exception as e:
            self.logger.error(f"Error inserting batch: {e}")
            conn.rollback()
            return 0
        finally:
            cursor.close()
            self.return_db_connection(conn)

    def _insert_bills_batch(self, cursor, bills: List[Dict[str, Any]]) -> int:
        """Insert bills batch into database"""
        if not bills:
            return 0

        # Normalize data
        normalized_bills = []
        for bill_data in bills:
            normalized = self.normalize_bill_data(bill_data)
            if normalized:
                normalized_bills.append(normalized)

        if not normalized_bills:
            return 0

        query = """
            INSERT INTO govinfo.bills (
                package_id, congress, bill_type, bill_number, title,
                date_issued, last_modified, downloads, created_at, updated_at
            ) VALUES %s
            ON CONFLICT (package_id) DO UPDATE SET
                title = EXCLUDED.title,
                date_issued = EXCLUDED.date_issued,
                last_modified = EXCLUDED.last_modified,
                downloads = EXCLUDED.downloads,
                updated_at = EXCLUDED.updated_at
        """

        values = [
            (
                b['package_id'], b['congress'], b['bill_type'], b['bill_number'],
                b['title'], b['date_issued'], b['last_modified'], b['downloads'],
                b['created_at'], b['updated_at']
            )
            for b in normalized_bills
        ]

        execute_values(cursor, query, values)
        return len(normalized_bills)

    def _insert_votes_batch(self, cursor, votes: List[Dict[str, Any]]) -> int:
        """Insert votes batch into database"""
        if not votes:
            return 0

        # Normalize data
        normalized_votes = []
        for vote_data in votes:
            normalized = self.normalize_vote_data(vote_data)
            if normalized:
                normalized_votes.append(normalized)

        if not normalized_votes:
            return 0

        query = """
            INSERT INTO govinfo.votes (
                roll_id, congress, date, chamber, session, roll_number,
                question, question_text, type, subject, by_member,
                created_at, updated_at
            ) VALUES %s
            ON CONFLICT (roll_id) DO UPDATE SET
                date = EXCLUDED.date,
                question = EXCLUDED.question,
                question_text = EXCLUDED.question_text,
                subject = EXCLUDED.subject,
                by_member = EXCLUDED.by_member,
                updated_at = EXCLUDED.updated_at
        """

        values = [
            (
                v['roll_id'], v['congress'], v['date'], v['chamber'], v['session'],
                v['roll_number'], v['question'], v['question_text'], v['type'],
                v['subject'], v['by_member'], v['created_at'], v['updated_at']
            )
            for v in normalized_votes
        ]

        execute_values(cursor, query, values)
        return len(normalized_votes)

    def _insert_members_batch(self, cursor, members: List[Dict[str, Any]]) -> int:
        """Insert members batch into database"""
        if not members:
            return 0

        # Normalize data
        normalized_members = []
        for member_data in members:
            normalized = self.normalize_member_data(member_data)
            if normalized:
                normalized_members.append(normalized)

        if not normalized_members:
            return 0

        query = """
            INSERT INTO govinfo.members (
                member_id, bioguide_id, first_name, middle_name, last_name, suffix,
                full_name, preferred_name, birthday, death_date, gender, party_code,
                state, district, url, twitter_handle, youtube_handle, facebook_handle,
                biography_text, photo_url, congress, created_at, updated_at
            ) VALUES %s
            ON CONFLICT (member_id) DO UPDATE SET
                bioguide_id = EXCLUDED.bioguide_id,
                first_name = EXCLUDED.first_name,
                last_name = EXCLUDED.last_name,
                full_name = EXCLUDED.full_name,
                party_code = EXCLUDED.party_code,
                state = EXCLUDED.state,
                district = EXCLUDED.district,
                updated_at = EXCLUDED.updated_at
        """

        values = [
            (
                m['member_id'], m['bioguide_id'], m['first_name'], m['middle_name'],
                m['last_name'], m['suffix'], m['full_name'], m['preferred_name'],
                m['birthday'], m['death_date'], m['gender'], m['party_code'],
                m['state'], m['district'], m['url'], m['twitter_handle'],
                m['youtube_handle'], m['facebook_handle'], m['biography_text'],
                m['photo_url'], m['congress'], m['created_at'], m['updated_at']
            )
            for m in normalized_members
        ]

        execute_values(cursor, query, values)
        return len(normalized_members)

    def ingest_data_type(self, config: IngestionConfig) -> IngestionStats:
        """Main ingestion method for a specific data type and congress"""
        self.congress = config.congress
        stats = IngestionStats(start_time=datetime.now())

        # Get checkpoint
        start_offset, is_completed = self.get_checkpoint(config)
        if is_completed and config.resume_from_checkpoint:
            self.logger.info(f"✅ {config.data_type.value.title()} for Congress {config.congress} already completed")
            stats.end_time = datetime.now()
            return stats

        self.logger.info(f"🚀 Starting {config.data_type.value} ingestion for Congress {config.congress}")
        self.logger.info(f"📍 Starting from offset: {start_offset}")

        # Start session
        session_id = self.start_ingestion_session(config)

        try:
            batch_count = 0
            for items_batch in self.paginate_api_response(config, start_offset):
                batch_count += 1
                batch_start_time = time.time()

                self.logger.info(f"📦 Processing batch {batch_count} ({len(items_batch)} items)")

                # Insert batch
                inserted = self.insert_batch(config, items_batch)

                # Update statistics
                stats.total_processed += len(items_batch)
                stats.total_inserted += inserted
                stats.total_skipped += len(items_batch) - inserted
                stats.current_offset += len(items_batch)

                # Show progress
                batch_duration = time.time() - batch_start_time
                throughput = len(items_batch) / batch_duration if batch_duration > 0 else 0

                self.logger.info(f"   ✅ Inserted: {inserted}, Skipped: {len(items_batch) - inserted}")
                self.logger.info(f"   ⚡ Throughput: {throughput:.1f} items/sec")

                # Update checkpoint
                self.update_checkpoint(config, stats.current_offset)

                # Rate limiting
                if config.request_delay > 0:
                    time.sleep(config.request_delay)

            # Mark as completed
            self.update_checkpoint(config, stats.current_offset, True)

            # Complete session
            stats.end_time = datetime.now()
            self.complete_ingestion_session(session_id, 'completed', stats)

            self.logger.info(f"🎉 {config.data_type.value.title()} ingestion completed!")
            self.logger.info(f"📊 Stats: Processed: {stats.total_processed}, Inserted: {stats.total_inserted}, Skipped: {stats.total_skipped}")

            return stats

        except Exception as e:
            stats.end_time = datetime.now()
            self.logger.error(f"❌ {config.data_type.value.title()} ingestion failed: {e}")
            self.complete_ingestion_session(session_id, 'failed', stats, str(e))
            raise

    def ingest_all_data_types(self, congress: int, data_types: List[DataType] = None) -> Dict[str, IngestionStats]:
        """Ingest all or specified data types for a congress"""
        if data_types is None:
            data_types = [DataType.BILLS, DataType.VOTES, DataType.MEMBERS]

        results = {}

        for data_type in data_types:
            config = IngestionConfig(
                data_type=data_type,
                congress=congress,
                batch_size=100,
                request_delay=0.1,
                enable_checkpoint=True,
                resume_from_checkpoint=True
            )

            try:
                stats = self.ingest_data_type(config)
                results[data_type.value] = stats
                self.logger.info(f"✅ {data_type.value.title()} completed")
            except Exception as e:
                self.logger.error(f"❌ {data_type.value.title()} failed: {e}")
                results[data_type.value] = IngestionStats(end_time=datetime.now())

            # Brief pause between data types
            time.sleep(2)

        return results


def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(description="Fixed GovInfo Ingestion Process")
    parser.add_argument('--congress', type=int, default=118, help='Congress number')
    parser.add_argument('--data-type', choices=['bills', 'votes', 'members', 'all'],
                       default='all', help='Data type to ingest')
    parser.add_argument('--batch-size', type=int, default=100, help='Batch size')
    parser.add_argument('--request-delay', type=float, default=0.1, help='Delay between requests (seconds)')
    parser.add_argument('--no-checkpoint', action='store_true', help='Disable checkpointing')
    parser.add_argument('--no-resume', action='store_true', help='Do not resume from checkpoint')

    args = parser.parse_args()

    # Determine data types
    if args.data_type == 'all':
        data_types = [DataType.BILLS, DataType.VOTES, DataType.MEMBERS]
    else:
        data_types = [DataType(args.data_type)]

    # Create ingestor
    ingestor = FixedGovInfoIngestor()

    # Configure ingestion
    for data_type in data_types:
        config = IngestionConfig(
            data_type=data_type,
            congress=args.congress,
            batch_size=args.batch_size,
            request_delay=args.request_delay,
            enable_checkpoint=not args.no_checkpoint,
            resume_from_checkpoint=not args.no_resume
        )

        try:
            stats = ingestor.ingest_data_type(config)
            duration = stats.end_time - stats.start_time if stats.start_time and stats.end_time else None
            print(f"\n🎉 {data_type.value.title()} ingestion completed!")
            print(f"   📊 Processed: {stats.total_processed}")
            print(f"   ✅ Inserted: {stats.total_inserted}")
            print(f"   ⏭️  Skipped: {stats.total_skipped}")
            print(f"   🕐 Duration: {duration}")

        except KeyboardInterrupt:
            print(f"\n⚠️  {data_type.value.title()} ingestion interrupted by user")
            break
        except Exception as e:
            print(f"\n❌ {data_type.value.title()} ingestion failed: {e}")


if __name__ == "__main__":
    main()
