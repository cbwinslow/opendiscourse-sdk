#!/usr/bin/env python3
"""
OpenDiscourse CLI Tool
Simplified data ingestion with complete abstraction
"""

import argparse
import json
import os
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import psycopg2
import requests

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

@dataclass
class IngestionConfig:
    """Configuration for ingestion operations"""
    db_name: str = "opendiscourse"
    db_user: str = "cbwinslow"
    db_host: str = "/var/run/postgresql"
    batch_size: int = 50
    dry_run: bool = False

class DatabaseLayer:
    """Abstract database operations"""

    def __init__(self, config: IngestionConfig):
        self.config = config
        self.conn = None

    def connect(self):
        """Establish database connection"""
        try:
            self.conn = psycopg2.connect(
                database=self.config.db_name,
                user=self.config.db_user,
                host=self.config.db_host
            )
            return True
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return False

    def execute_query(self, query: str, params: tuple = None) -> bool:
        """Execute a single query"""
        if not self.conn:
            return False

        cursor = self.conn.cursor()
        try:
            cursor.execute(query, params)
            self.conn.commit()
            return True
        except Exception as e:
            print(f"❌ Query failed: {e}")
            self.conn.rollback()
            return False
        finally:
            cursor.close()

    def execute_batch(self, query: str, data: List[tuple]) -> bool:
        """Execute batch insert"""
        if not self.conn or self.config.dry_run:
            print(f"🔍 DRY RUN: Would insert {len(data)} records")
            return True

        cursor = self.conn.cursor()
        try:
            from psycopg2.extras import execute_values
            execute_values(cursor, query, data)
            self.conn.commit()
            return True
        except Exception as e:
            print(f"❌ Batch insert failed: {e}")
            self.conn.rollback()
            return False
        finally:
            cursor.close()

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()

class APILayer:
    """Abstract API operations"""

    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'X-API-Key': api_key,
            'Accept': 'application/json'
        })

    def get(self, endpoint: str, params: dict = None) -> Optional[Dict]:
        """Make GET request with error handling"""
        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ API request failed: {e}")
            return None

class CongressAPI(APILayer):
    """Congress.gov API wrapper"""

    def __init__(self, api_key: str):
        super().__init__(api_key, "https://api.congress.gov/v3")

    def get_members(self, congress: int, offset: int = 0) -> Optional[Dict]:
        """Get members for a congress"""
        return self.get(f"/member/congress/{congress}", {'limit': self.config.batch_size, 'offset': offset})

    def get_bills(self, congress: int, offset: int = 0) -> Optional[Dict]:
        """Get bills for a congress"""
        return self.get("/bill", {'congress': congress, 'limit': self.config.batch_size, 'offset': offset})

class OpenStatesAPI(APILayer):
    """OpenStates API wrapper"""

    def __init__(self, api_key: str):
        super().__init__(api_key, "https://v3.openstates.org")
        self.session.headers.update({'X-API-KEY': api_key})

    def get_people(self, jurisdiction: str, page: int = 1) -> Optional[Dict]:
        """Get people for a jurisdiction"""
        return self.get("/people", {'jurisdiction': jurisdiction, 'page': page})

    def get_jurisdictions(self) -> Optional[Dict]:
        """Get all jurisdictions"""
        return self.get("/jurisdictions")

class DataTransformer:
    """Transform API data to database format"""

    @staticmethod
    def transform_congress_member(member_data: Dict, congress: int) -> tuple:
        """Transform congress member data"""
        member = member_data.get('member', member_data)
        return (
            member.get('bioguideId'),
            member.get('fullName'),
            member.get('firstName'),
            member.get('lastName'),
            member.get('party'),
            member.get('state'),
            member.get('district'),
            congress,
            member.get('active'),
            datetime.now()
        )

    @staticmethod
    def transform_congress_bill(bill_data: Dict, congress: int) -> tuple:
        """Transform congress bill data"""
        bill = bill_data.get('bill', bill_data)

        # Map chamber codes to match database
        chamber_mapping = {
            'House': 'house',
            'Senate': 'senate',
            'Joint': 'joint'
        }
        origin_chamber = chamber_mapping.get(bill.get('originChamber', ''), bill.get('originChamber', '').lower())

        return (
            congress,
            bill.get('type', ''),
            int(bill.get('number', 0)),
            origin_chamber,
            bill.get('introducedDate'),
            bill.get('latestAction', {}).get('actionDate'),
            bill.get('latestAction', {}).get('text'),
            bill.get('policyArea', {}).get('name') if bill.get('policyArea') else '',
            bill.get('title', ''),
            bill.get('sponsor', {}).get('bioguideId'),
            datetime.now()
        )

    @staticmethod
    def transform_openstates_person(person_data: Dict) -> tuple:
        """Transform OpenStates person data"""
        return (
            person_data.get('id'),
            person_data.get('name'),
            person_data.get('givenName'),
            person_data.get('familyName'),
            person_data.get('party'),
            person_data.get('current_role', {}).get('jurisdiction_id'),
            json.dumps(person_data.get('sources', [])),
            datetime.now()
        )

class IngestionEngine:
    """Main ingestion orchestrator"""

    def __init__(self, config: IngestionConfig):
        self.config = config
        self.db = DatabaseLayer(config)
        self.transformer = DataTransformer()

    def ingest_congress_members(self, congress: int, api_key: str) -> bool:
        """Ingest congress members"""
        print(f"🚀 Starting Congress {congress} members ingestion")

        if not self.db.connect():
            return False

        api = CongressAPI(api_key)
        api.config = self.config

        total_processed = 0
        offset = 0

        while True:
            data = api.get_members(congress, offset)
            if not data or not data.get('members'):
                break

            # Transform and batch insert
            members = []
            for member in data['members']:
                transformed = self.transformer.transform_congress_member(member, congress)
                if transformed[0]:  # Has bioguideId
                    members.append(transformed)

            if members:
                query = """
                INSERT INTO congress.members
                (bioguide_id, full_name, first_name, last_name, party, state, district,
                 congress_number, active, created_at)
                VALUES %s
                ON CONFLICT (bioguide_id) DO UPDATE SET
                    full_name = EXCLUDED.full_name,
                    party = EXCLUDED.party,
                    state = EXCLUDED.state,
                    district = EXCLUDED.district,
                    active = EXCLUDED.active,
                    updated_at = now()
                """

                if self.db.execute_batch(query, members):
                    total_processed += len(members)
                    print(f"✅ Processed {total_processed} members")
                else:
                    break

            offset += self.config.batch_size
            time.sleep(0.1)  # Rate limiting

        self.db.close()
        print(f"🎉 Completed: {total_processed} Congress members")
        return True

    def ingest_congress_bills(self, congress: int, api_key: str) -> bool:
        """Ingest congress bills"""
        print(f"🚀 Starting Congress {congress} bills ingestion")

        if not self.db.connect():
            return False

        api = CongressAPI(api_key)
        api.config = self.config

        total_processed = 0
        offset = 0

        while True:
            data = api.get_bills(congress, offset)
            if not data or not data.get('bills'):
                break

            # Transform and batch insert
            bills = []
            for bill in data['bills']:
                transformed = self.transformer.transform_congress_bill(bill, congress)
                if transformed[2] > 0:  # Has valid bill number
                    bills.append(transformed)

            if bills:
                query = """
                INSERT INTO congress.bills
                (congress_number, bill_type, bill_number, origin_chamber, introduced_date,
                 latest_action_date, latest_action_text, policy_area, official_title,
                 sponsor_bioguide_id, created_at)
                VALUES %s
                ON CONFLICT (congress_number, bill_type, bill_number) DO UPDATE SET
                    origin_chamber = EXCLUDED.origin_chamber,
                    introduced_date = EXCLUDED.introduced_date,
                    latest_action_date = EXCLUDED.latest_action_date,
                    latest_action_text = EXCLUDED.latest_action_text,
                    policy_area = EXCLUDED.policy_area,
                    official_title = EXCLUDED.official_title,
                    sponsor_bioguide_id = EXCLUDED.sponsor_bioguide_id,
                    updated_at = now()
                """

                if self.db.execute_batch(query, bills):
                    total_processed += len(bills)
                    print(f"✅ Processed {total_processed} bills")
                else:
                    break

            offset += self.config.batch_size
            time.sleep(0.1)  # Rate limiting

        self.db.close()
        print(f"🎉 Completed: {total_processed} Congress bills")
        return True

    def ingest_openstates_people(self, jurisdiction: str, api_key: str) -> bool:
        """Ingest OpenStates people"""
        print(f"🚀 Starting OpenStates people ingestion for {jurisdiction}")

        if not self.db.connect():
            return False

        api = OpenStatesAPI(api_key)
        api.config = self.config

        total_processed = 0
        page = 1

        while True:
            data = api.get_people(jurisdiction, page)
            if not data or not data.get('results'):
                break

            # Transform and batch insert
            people = []
            for person in data['results']:
                transformed = self.transformer.transform_openstates_person(person)
                if transformed[0]:  # Has ID
                    people.append(transformed)

            if people:
                query = """
                INSERT INTO openstates.people
                (id, name, given_name, family_name, party, jurisdiction_id, sources, created_at)
                VALUES %s
                ON CONFLICT (id) DO UPDATE SET
                    name = EXCLUDED.name,
                    given_name = EXCLUDED.given_name,
                    family_name = EXCLUDED.family_name,
                    party = EXCLUDED.party,
                    jurisdiction_id = EXCLUDED.jurisdiction_id,
                    sources = EXCLUDED.sources,
                    updated_at = now()
                """

                if self.db.execute_batch(query, people):
                    total_processed += len(people)
                    print(f"✅ Processed {total_processed} people (page {page})")
                else:
                    break

            page += 1
            time.sleep(0.6)  # Rate limiting for OpenStates

        self.db.close()
        print(f"🎉 Completed: {total_processed} OpenStates people")
        return True

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description="OpenDiscourse CLI Tool")
    parser.add_argument('--dry-run', action='store_true', help='Run without making changes')
    parser.add_argument('--batch-size', type=int, default=50, help='Batch size for processing')

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Congress commands
    congress_parser = subparsers.add_parser('congress', help='Congress data operations')
    congress_subparsers = congress_parser.add_subparsers(dest='congress_command')

    members_parser = congress_subparsers.add_parser('members', help='Ingest Congress members')
    members_parser.add_argument('congress', type=int, help='Congress number (116, 117, 118)')

    bills_parser = congress_subparsers.add_parser('bills', help='Ingest Congress bills')
    bills_parser.add_argument('congress', type=int, help='Congress number (116, 117, 118)')

    # OpenStates commands
    openstates_parser = subparsers.add_parser('openstates', help='OpenStates data operations')
    openstates_subparsers = openstates_parser.add_subparsers(dest='openstates_command')

    people_parser = openstates_subparsers.add_parser('people', help='Ingest OpenStates people')
    people_parser.add_argument('jurisdiction', help='Jurisdiction code (ca, tx, ny, etc.)')

    # Status command
    status_parser = subparsers.add_parser('status', help='Show database status')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Load configuration
    config = IngestionConfig(
        dry_run=args.dry_run,
        batch_size=args.batch_size
    )

    # Load API keys
    api_keys = {
        'congress': os.getenv('CONGRESS_API_KEY'),
        'openstates': os.getenv('OPENSTATES_API_KEY'),
        'govinfo': os.getenv('GOVINFO_API_KEY')
    }

    # Initialize engine
    engine = IngestionEngine(config)

    # Execute commands
    if args.command == 'congress':
        if args.congress_command == 'members':
            if not api_keys['congress']:
                print("❌ CONGRESS_API_KEY required")
                return
            engine.ingest_congress_members(args.congress, api_keys['congress'])

        elif args.congress_command == 'bills':
            if not api_keys['congress']:
                print("❌ CONGRESS_API_KEY required")
                return
            engine.ingest_congress_bills(args.congress, api_keys['congress'])

    elif args.command == 'openstates':
        if args.openstates_command == 'people':
            if not api_keys['openstates']:
                print("❌ OPENSTATES_API_KEY required")
                return
            engine.ingest_openstates_people(args.jurisdiction, api_keys['openstates'])

    elif args.command == 'status':
        print("📊 Database Status:")
        db = DatabaseLayer(config)
        if db.connect():
            cursor = db.conn.cursor()

            # Get counts
            queries = [
                ("Congress Members", "SELECT count(*) FROM congress.members"),
                ("Congress Bills", "SELECT count(*) FROM congress.bills"),
                ("OpenStates People", "SELECT count(*) FROM openstates.people"),
                ("OpenStates Jurisdictions", "SELECT count(*) FROM openstates.jurisdictions")
            ]

            for name, query in queries:
                cursor.execute(query)
                count = cursor.fetchone()[0]
                print(f"  {name}: {count}")

            cursor.close()
            db.close()

if __name__ == "__main__":
    main()
