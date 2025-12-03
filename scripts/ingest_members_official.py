#!/usr/bin/env python3
"""
Congress Members Data Ingestion Script - Official API Structure
Ingests members data exactly as provided by Congress.gov API

Usage:
    python ingest_members_official.py [--congress-start 101] [--congress-end 118] [--batch-size 50]
"""

import os
import sys
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, date
from dataclasses import dataclass

import psycopg2
from psycopg2.extras import DictCursor, execute_values
import requests
from tenacity import retry, stop_after_attempt, wait_exponential

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class MemberIngestionConfig:
    """Configuration for members ingestion"""
    api_key: str
    db_host: str
    db_port: str
    db_name: str
    db_user: str
    db_password: str
    congress_start: int = 101
    congress_end: int = 118
    batch_size: int = 50
    request_delay: float = 0.5

class OfficialMembersIngestor:
    """Ingests Congress members data exactly as provided by the official API"""

    def __init__(self, config: MemberIngestionConfig):
        self.config = config
        self.db_conn = None
        self.session = requests.Session()
        self.session.headers.update({
            'X-API-Key': config.api_key,
            'Accept': 'application/json'
        })

        # API endpoints
        self.base_url = "https://api.congress.gov/v3"

        # Statistics
        self.stats = {
            'members_processed': 0,
            'terms_processed': 0,
            'errors': 0,
            'start_time': datetime.now()
        }

    def connect_database(self):
        """Connect to PostgreSQL database"""
        try:
            # Try Unix socket first for local connections
            if self.config.db_host == 'localhost':
                conn_params = {
                    'database': self.config.db_name,
                    'user': self.config.db_user
                }
            else:
                conn_params = {
                    'host': self.config.db_host,
                    'port': self.config.db_port,
                    'database': self.config.db_name,
                    'user': self.config.db_user
                }

            # Only add password if it's not empty
            if self.config.db_password:
                conn_params['password'] = self.config.db_password

            self.db_conn = psycopg2.connect(**conn_params)
            self.db_conn.autocommit = False
            logger.info("Connected to database successfully")
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def fetch_members_page(self, congress: int, offset: int = 0) -> Dict[str, Any]:
        """Fetch a page of members from Congress.gov API"""
        url = f"{self.base_url}/member/congress/{congress}"
        params = {
            'limit': self.config.batch_size,
            'offset': offset
        }

        response = self.session.get(url, params=params, timeout=30)
        response.raise_for_status()

        # Rate limiting
        import time
        time.sleep(self.config.request_delay)

        return response.json()

    def get_all_members_for_congress(self, congress: int) -> List[Dict[str, Any]]:
        """Get all members for a specific congress with pagination"""
        all_members = []
        offset = 0

        while True:
            try:
                logger.info(f"Fetching members for Congress {congress}, offset {offset}")
                data = self.fetch_members_page(congress, offset)

                members = data.get('members', [])
                if not members:
                    break

                all_members.extend(members)
                logger.info(f"Fetched {len(members)} members (total: {len(all_members)})")

                # Check if we have more pages
                pagination = data.get('pagination', {})
                next_url = pagination.get('next')
                if not next_url or offset >= pagination.get('count', 0):
                    break

                offset += len(members)

                # Safety check to prevent infinite loops
                if offset > 10000:  # Reasonable upper limit
                    logger.warning(f"Offset {offset} exceeds safety limit, stopping pagination")
                    break

            except Exception as e:
                logger.error(f"Error fetching members page: {e}")
                self.stats['errors'] += 1
                break

        return all_members

    def normalize_member_data(self, member_data: Dict[str, Any], congress: int) -> Dict[str, Any]:
        """Normalize member data to match official API structure exactly"""

        # Parse name field
        full_name = member_data.get('name', '')
        name_parts = full_name.split(', ')
        last_name = name_parts[0] if name_parts else ''
        first_name = name_parts[1] if len(name_parts) > 1 else ''

        # Handle first name with suffixes (e.g., "Eric A. \"Rick\"")
        if '"' in first_name:
            # Extract nickname from quotes
            nickname_start = first_name.find('"')
            nickname_end = first_name.find('"', nickname_start + 1)
            if nickname_start != -1 and nickname_end != -1:
                first_name = first_name[nickname_start + 1:nickname_end]

        return {
            'bioguide_id': member_data.get('bioguideId'),
            'first_name': first_name,
            'middle_name': None,
            'last_name': last_name,
            'suffix': None,
            'official_full_name': full_name,
            'birthday': None,
            'gender': None,
            'biography': '',  # Empty string for required field
            'birthplace': None,
            'death_date': None,
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }

    def normalize_term_data(self, member_data: Dict[str, Any], bioguide_id: str, congress: int) -> List[Dict[str, Any]]:
        """Normalize member terms data from API structure"""
        terms = []

        # State name to code mapping
        state_mapping = {
            'Alabama': 'AL', 'Alaska': 'AK', 'Arizona': 'AZ', 'Arkansas': 'AR',
            'California': 'CA', 'Colorado': 'CO', 'Connecticut': 'CT', 'Delaware': 'DE',
            'Florida': 'FL', 'Georgia': 'GA', 'Hawaii': 'HI', 'Idaho': 'ID',
            'Illinois': 'IL', 'Indiana': 'IN', 'Iowa': 'IA', 'Kansas': 'KS',
            'Kentucky': 'KY', 'Louisiana': 'LA', 'Maine': 'ME', 'Maryland': 'MD',
            'Massachusetts': 'MA', 'Michigan': 'MI', 'Minnesota': 'MN', 'Mississippi': 'MS',
            'Missouri': 'MO', 'Montana': 'MT', 'Nebraska': 'NE', 'Nevada': 'NV',
            'New Hampshire': 'NH', 'New Jersey': 'NJ', 'New Mexico': 'NM', 'New York': 'NY',
            'North Carolina': 'NC', 'North Dakota': 'ND', 'Ohio': 'OH', 'Oklahoma': 'OK',
            'Oregon': 'OR', 'Pennsylvania': 'PA', 'Rhode Island': 'RI', 'South Carolina': 'SC',
            'South Dakota': 'SD', 'Tennessee': 'TN', 'Texas': 'TX', 'Utah': 'UT',
            'Vermont': 'VT', 'Virginia': 'VA', 'Washington': 'WA', 'West Virginia': 'WV',
            'Wisconsin': 'WI', 'Wyoming': 'WY', 'American Samoa': 'AS', 'District of Columbia': 'DC',
            'Guam': 'GU', 'Northern Mariana Islands': 'MP', 'Puerto Rico': 'PR', 'Virgin Islands': 'VI'
        }

        # Party name to code mapping
        party_mapping = {
            'Democratic': 'D', 'Democrat': 'D', 'Democratic Party': 'D',
            'Republican': 'R', 'Republican Party': 'R',
            'Independent': 'I', 'Libertarian': 'L', 'Green': 'G'
        }

        # Handle the actual API structure: terms.item is an array
        terms_data = member_data.get('terms', {}).get('item', [])

        for item in terms_data:
            # Parse chamber
            chamber = item.get('chamber', '').lower()
            if 'house' in chamber:
                chamber_code = 'house'
            elif 'senate' in chamber:
                chamber_code = 'senate'
            else:
                chamber_code = chamber

            # Create start_date and end_date from years
            start_year = item.get('startYear')
            end_year = item.get('endYear')

            start_date = f"{start_year}-01-01" if start_year else None
            end_date = f"{end_year}-12-31" if end_year else None

            # Map state name to code
            state_name = member_data.get('state', '')
            state_code = state_mapping.get(state_name, None)

            # Map party name to code
            party_name = member_data.get('partyName', '')
            party_code = party_mapping.get(party_name, 'O')  # Default to 'Other'

            term_data = {
                'congress_number': congress,
                'chamber_code': chamber_code,
                'start_date': self.parse_date(start_date),
                'end_date': self.parse_date(end_date),
                'state_code': state_code,
                'district': str(member_data.get('district', '')) if member_data.get('district') else None,
                'party_code': party_code,
                'role_title': None,
                'leadership_role': None,
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }
            terms.append(term_data)

        return terms

    def parse_date(self, date_str: Optional[str]) -> Optional[date]:
        """Parse date string to date object"""
        if not date_str:
            return None

        try:
            # Handle YYYY-MM-DD format
            if '-' in date_str:
                return datetime.strptime(date_str[:10], '%Y-%m-%d').date()
            else:
                return datetime.strptime(date_str[:10], '%Y-%m-%d').date()
        except:
            logger.warning(f"Failed to parse date: {date_str}")
            return None

    def insert_members_batch(self, members: List[Dict[str, Any]], congress: int) -> int:
        """Insert a batch of members and their terms into the database"""
        if not members:
            return 0

        cursor = self.db_conn.cursor()

        try:
            # Insert members with UPSERT to handle duplicates across congresses
            member_query = """
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

            member_values = []
            all_terms = []

            for member in members:
                # Normalize member data
                normalized_member = self.normalize_member_data(member, congress)
                member_values.append((
                    normalized_member['bioguide_id'], normalized_member['first_name'],
                    normalized_member['middle_name'], normalized_member['last_name'],
                    normalized_member['suffix'], normalized_member['official_full_name'],
                    normalized_member['birthday'], normalized_member['gender'],
                    normalized_member['biography'], normalized_member['birthplace'],
                    normalized_member['death_date'], normalized_member['created_at'],
                    normalized_member['updated_at']
                ))

                # Normalize terms data
                terms = self.normalize_term_data(member, normalized_member['bioguide_id'], congress)
                for term in terms:
                    term['bioguide_id'] = normalized_member['bioguide_id']
                    all_terms.append(term)

            # Insert members
            execute_values(cursor, member_query, member_values)
            member_count = len(member_values)

            # Insert terms if any
            if all_terms:
                term_query = """
                    INSERT INTO congress.member_terms (
                        bioguide_id, congress_number, chamber_code, state_code,
                        district, party_code, start_date, end_date, role_title,
                        leadership_role, created_at, updated_at
                    ) VALUES %s
                """

                term_values = [
                    (
                        t['bioguide_id'], t['congress_number'], t['chamber_code'],
                        t['state_code'], t['district'], t['party_code'],
                        t['start_date'], t['end_date'], t['role_title'],
                        t['leadership_role'], t['created_at'], t['updated_at']
                    )
                    for t in all_terms
                ]

                execute_values(cursor, term_query, term_values)
                term_count = len(all_terms)
            else:
                term_count = 0

            self.db_conn.commit()
            logger.info(f"Inserted {member_count} members and {term_count} terms")

            self.stats['members_processed'] += member_count
            self.stats['terms_processed'] += term_count

            return member_count

        except Exception as e:
            self.db_conn.rollback()
            logger.error(f"Error inserting members batch: {e}")
            self.stats['errors'] += 1
            return 0
        finally:
            cursor.close()

    def ingest_all_congresses(self):
        """Ingest members data for all specified congresses"""
        logger.info(f"Starting ingestion for Congress {self.config.congress_start} to {self.config.congress_end}")

        for congress in range(self.config.congress_start, self.config.congress_end + 1):
            logger.info(f"\n{'='*60}")
            logger.info(f"Processing Congress {congress}")
            logger.info(f"{'='*60}")

            try:
                # Get all members for this congress
                members = self.get_all_members_for_congress(congress)

                if not members:
                    logger.warning(f"No members found for Congress {congress}")
                    continue

                # Insert in batches
                batch_size = 100
                for i in range(0, len(members), batch_size):
                    batch = members[i:i + batch_size]
                    inserted = self.insert_members_batch(batch, congress)

                    # Log progress
                    progress = (i + batch_size) / len(members) * 100
                    logger.info(f"Congress {congress} progress: {min(progress, 100):.1f}%")

                logger.info(f"Completed Congress {congress}")

            except Exception as e:
                logger.error(f"Error processing Congress {congress}: {e}")
                self.stats['errors'] += 1
                continue

        # Log final statistics
        self.log_final_statistics()

    def log_final_statistics(self):
        """Log final ingestion statistics"""
        end_time = datetime.now()
        duration = end_time - self.stats['start_time']

        logger.info(f"\n{'='*60}")
        logger.info("INGESTION COMPLETE")
        logger.info(f"{'='*60}")
        logger.info(f"Total Members Processed: {self.stats['members_processed']}")
        logger.info(f"Total Terms Processed: {self.stats['terms_processed']}")
        logger.info(f"Total Errors: {self.stats['errors']}")
        logger.info(f"Duration: {duration}")
        logger.info(f"Average Rate: {self.stats['members_processed']/duration.total_seconds():.2f} members/second")
        logger.info(f"{'='*60}")

    def close(self):
        """Clean up resources"""
        if self.db_conn:
            self.db_conn.close()
        if self.session:
            self.session.close()

def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(description="Ingest Congress members data - Official API Structure")
    parser.add_argument('--congress-start', type=int, default=101, help='Starting Congress number')
    parser.add_argument('--congress-end', type=int, default=118, help='Ending Congress number')
    parser.add_argument('--batch-size', type=int, default=50, help='API batch size')
    parser.add_argument('--dry-run', action='store_true', help='Run without inserting data')

    args = parser.parse_args()

    # Load configuration
    config = MemberIngestionConfig(
        api_key=os.getenv('CONGRESS_API_KEY'),
        db_host=os.getenv('DB_HOST', 'localhost'),
        db_port=os.getenv('DB_PORT', '5432'),
        db_name=os.getenv('DB_NAME', 'cbwinslow'),
        db_user=os.getenv('DB_USER', 'cbwinslow'),
        db_password=os.getenv('DB_PASSWORD', ''),
        congress_start=args.congress_start,
        congress_end=args.congress_end,
        batch_size=args.batch_size
    )

    # Validate configuration
    if not config.api_key:
        logger.error("CONGRESS_API_KEY not found in environment variables")
        sys.exit(1)

    if not config.db_password and config.db_user == 'cbwinslow':
        logger.info("Using cbwinslow user without password (local connection)")
    elif not config.db_password:
        logger.error("DB_PASSWORD not found in environment variables")
        sys.exit(1)

    # Create ingestor and run
    ingestor = OfficialMembersIngestor(config)

    try:
        if not args.dry_run:
            ingestor.connect_database()
            ingestor.ingest_all_congresses()
        else:
            logger.info("DRY RUN: Would ingest members data")
            logger.info(f"Congress range: {config.congress_start}-{config.congress_end}")
            logger.info(f"Batch size: {config.batch_size}")
    except KeyboardInterrupt:
        logger.info("Ingestion interrupted by user")
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        sys.exit(1)
    finally:
        ingestor.close()

if __name__ == "__main__":
    main()
