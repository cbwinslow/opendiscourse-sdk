#!/usr/bin/env python3
"""
Congress.gov CLI Tool
Focused CLI for ingesting Congress members, bills, amendments, summaries, and text.
"""

import argparse
import sys
import os
import time
import psycopg2
from datetime import datetime
from typing import Dict, List, Optional
import requests
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

class CongressCLI:
    def __init__(self, api_key: str, db_config: Dict, batch_size: int = 50, dry_run: bool = False):
        self.api_key = api_key
        self.db_config = db_config
        self.batch_size = batch_size
        self.dry_run = dry_run
        self.base_url = "https://api.congress.gov/v3"
        self.session = requests.Session()
        self.session.headers.update({
            'X-API-Key': api_key,
            'Accept': 'application/json'
        })
        self.conn = None

    def connect_db(self):
        """Establish database connection"""
        try:
            self.conn = psycopg2.connect(**self.db_config)
            return True
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return False

    def close_db(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()

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

    def transform_member(self, member_data: Dict, congress: int) -> tuple:
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

    def transform_bill(self, bill_data: Dict, congress: int) -> tuple:
        """Transform congress bill data"""
        bill = bill_data.get('bill', bill_data)

        # Map chamber codes
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

    def transform_amendment(self, amendment_data: Dict, congress: int) -> tuple:
        """Transform congress amendment data"""
        amdt = amendment_data
        return (
            congress,
            amdt.get('type', ''),
            int(amdt.get('number', 0)),
            amdt.get('description', ''),
            amdt.get('purpose', ''),
            amdt.get('latestAction', {}).get('actionDate'),
            amdt.get('latestAction', {}).get('text'),
            amdt.get('submittedDate'),
            datetime.now()
        )

    def transform_session(self, session_data: Dict) -> tuple:
        """Transform congress session data"""
        return (
            session_data.get('congress'),
            session_data.get('sessionNumber'),
            session_data.get('type'),
            session_data.get('startDate'),
            session_data.get('endDate'),
            datetime.now()
        )

    def transform_chamber(self, chamber_data: Dict) -> tuple:
        """Transform congress chamber data"""
        return (
            chamber_data.get('chamberCode'),
            chamber_data.get('name'),
            chamber_data.get('type'),
            datetime.now()
        )

    def transform_congress_committee(self, committee_data: Dict) -> tuple:
        """Transform congress committee data"""
        return (
            committee_data.get('committeeCode'),
            committee_data.get('name'),
            committee_data.get('chamber'),
            committee_data.get('parentCommitteeCode'),
            committee_data.get('type'),
            committee_data.get('jurisdiction'),
            datetime.now()
        )

    def transform_vote(self, vote_data: Dict) -> tuple:
        """Transform congress vote data"""
        return (
            vote_data.get('congress'),
            vote_data.get('session'),
            vote_data.get('rollCallNumber'),
            vote_data.get('question'),
            vote_data.get('result'),
            vote_data.get('date'),
            json.dumps(vote_data.get('positions', [])),
            datetime.now()
        )

    def transform_document_metadata(self, doc_data: Dict) -> tuple:
        """Transform document metadata for congress documents"""
        return (
            doc_data.get('documentHash'),
            doc_data.get('title'),
            doc_data.get('description'),
            doc_data.get('contentType'),
            doc_data.get('retrievedAt'),
            datetime.now()
        )

    def ingest_members(self, congress: int):
        """Ingest congress members"""
        print(f"🚀 Starting Congress {congress} members ingestion")

        if not self.connect_db():
            return

        total_processed = 0
        offset = 0

        while True:
            params = {'limit': self.batch_size, 'offset': offset}
            data = self.get(f"/member/congress/{congress}", params)

            if not data or not data.get('members'):
                break

            members = []
            for member in data['members']:
                transformed = self.transform_member(member, congress)
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

                if self.dry_run:
                    print(f"🔍 DRY RUN: Would insert {len(members)} members")
                    total_processed += len(members)
                else:
                    cursor = self.conn.cursor()
                    try:
                        from psycopg2.extras import execute_values
                        execute_values(cursor, query, members)
                        self.conn.commit()
                        total_processed += len(members)
                        print(f"✅ Processed {total_processed} members")
                    except Exception as e:
                        print(f"❌ Batch insert failed: {e}")
                        self.conn.rollback()
                        break
                    finally:
                        cursor.close()

            offset += self.batch_size
            time.sleep(0.1)  # Rate limiting

        self.close_db()
        print(f"🎉 Completed: {total_processed} Congress members")

    def ingest_bills(self, congress: int):
        """Ingest congress bills"""
        print(f"🚀 Starting Congress {congress} bills ingestion")

        if not self.connect_db():
            return

        total_processed = 0
        offset = 0

        while True:
            params = {'congress': congress, 'limit': self.batch_size, 'offset': offset}
            data = self.get("/bill", params)

            if not data or not data.get('bills'):
                break

            bills = []
            for bill in data['bills']:
                transformed = self.transform_bill(bill, congress)
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

                if self.dry_run:
                    print(f"🔍 DRY RUN: Would insert {len(bills)} bills")
                    total_processed += len(bills)
                else:
                    cursor = self.conn.cursor()
                    try:
                        from psycopg2.extras import execute_values
                        execute_values(cursor, query, bills)
                        self.conn.commit()
                        total_processed += len(bills)
                        print(f"✅ Processed {total_processed} bills")
                    except Exception as e:
                        print(f"❌ Batch insert failed: {e}")
                        self.conn.rollback()
                        break
                    finally:
                        cursor.close()

            offset += self.batch_size
            time.sleep(0.1)  # Rate limiting

        self.close_db()
        print(f"🎉 Completed: {total_processed} Congress bills")

    def ingest_amendments(self, congress: int):
        """Ingest congress amendments"""
        print(f"🚀 Starting Congress {congress} amendments ingestion")

        if not self.connect_db():
            return

        # Ensure table exists
        create_table_query = """
        CREATE TABLE IF NOT EXISTS congress.amendments (
            congress_number INTEGER,
            amendment_type TEXT,
            amendment_number INTEGER,
            description TEXT,
            purpose TEXT,
            latest_action_date DATE,
            latest_action_text TEXT,
            submitted_date DATE,
            created_at TIMESTAMP,
            updated_at TIMESTAMP,
            PRIMARY KEY (congress_number, amendment_type, amendment_number)
        );
        """
        if not self.dry_run:
            cursor = self.conn.cursor()
            cursor.execute(create_table_query)
            self.conn.commit()
            cursor.close()

        total_processed = 0
        offset = 0

        while True:
            params = {'congress': congress, 'limit': self.batch_size, 'offset': offset}
            data = self.get("/amendment", params)

            if not data or not data.get('amendments'):
                break

            amendments = []
            for amdt in data['amendments']:
                transformed = self.transform_amendment(amdt, congress)
                amendments.append(transformed)

            if amendments:
                query = """
                INSERT INTO congress.amendments
                (congress_number, amendment_type, amendment_number, description, purpose,
                 latest_action_date, latest_action_text, submitted_date, created_at)
                VALUES %s
                ON CONFLICT (congress_number, amendment_type, amendment_number) DO UPDATE SET
                    description = EXCLUDED.description,
                    purpose = EXCLUDED.purpose,
                    latest_action_date = EXCLUDED.latest_action_date,
                    latest_action_text = EXCLUDED.latest_action_text,
                    submitted_date = EXCLUDED.submitted_date,
                    updated_at = now()
                """

                if self.dry_run:
                    print(f"🔍 DRY RUN: Would insert {len(amendments)} amendments")
                    total_processed += len(amendments)
                else:
                    cursor = self.conn.cursor()
                    try:
                        from psycopg2.extras import execute_values
                        execute_values(cursor, query, amendments)
                        self.conn.commit()
                        total_processed += len(amendments)
                        print(f"✅ Processed {total_processed} amendments")
                    except Exception as e:
                        print(f"❌ Batch insert failed: {e}")
                        self.conn.rollback()
                        break
                    finally:
                        cursor.close()

            offset += self.batch_size
            time.sleep(0.1)

        self.close_db()
        print(f"🎉 Completed: {total_processed} Congress amendments")

    def ingest_summaries(self, congress: int):
        """Ingest bill summaries"""
        print(f"🚀 Starting Congress {congress} summaries ingestion")
        # Note: This iterates over bills to fetch summaries.

        if not self.connect_db():
            return

        # Ensure table exists
        create_table_query = """
        CREATE TABLE IF NOT EXISTS congress.bill_summaries (
            congress_number INTEGER,
            bill_type TEXT,
            bill_number INTEGER,
            action_date DATE,
            action_desc TEXT,
            text TEXT,
            created_at TIMESTAMP,
            updated_at TIMESTAMP,
            PRIMARY KEY (congress_number, bill_type, bill_number, action_date)
        );
        """
        if not self.dry_run:
            cursor = self.conn.cursor()
            cursor.execute(create_table_query)
            self.conn.commit()
            cursor.close()

        # Iterate bills
        offset = 0
        total_processed = 0

        while True:
            params = {'congress': congress, 'limit': self.batch_size, 'offset': offset}
            data = self.get("/bill", params)

            if not data or not data.get('bills'):
                break

            for bill in data['bills']:
                # Fetch summaries for each bill
                bill_type = bill.get('type')
                bill_number = bill.get('number')

                if not bill_type or not bill_number:
                    continue

                summaries_url = f"/bill/{congress}/{bill_type.lower()}/{bill_number}/summaries"
                summaries_data = self.get(summaries_url)

                if summaries_data and summaries_data.get('summaries'):
                    summaries = []
                    for summary in summaries_data['summaries']:
                        summaries.append((
                            congress,
                            bill_type,
                            bill_number,
                            summary.get('actionDate'),
                            summary.get('actionDesc'),
                            summary.get('text'),
                            datetime.now()
                        ))

                    if summaries:
                        query = """
                        INSERT INTO congress.bill_summaries
                        (congress_number, bill_type, bill_number, action_date, action_desc, text, created_at)
                        VALUES %s
                        ON CONFLICT (congress_number, bill_type, bill_number, action_date) DO UPDATE SET
                            action_desc = EXCLUDED.action_desc,
                            text = EXCLUDED.text,
                            updated_at = now()
                        """

                        if self.dry_run:
                            print(f"🔍 DRY RUN: Would insert {len(summaries)} summaries for {bill_type}{bill_number}")
                            total_processed += len(summaries)
                        else:
                            cursor = self.conn.cursor()
                            try:
                                from psycopg2.extras import execute_values
                                execute_values(cursor, query, summaries)
                                self.conn.commit()
                                total_processed += len(summaries)
                                print(f"✅ Processed {len(summaries)} summaries for {bill_type}{bill_number}")
                            except Exception as e:
                                print(f"❌ Insert failed: {e}")
                                self.conn.rollback()
                            finally:
                                cursor.close()

                time.sleep(0.1) # Rate limit per bill

            offset += self.batch_size

        self.close_db()
        print(f"🎉 Completed: {total_processed} Congress summaries")

    def ingest_text(self, congress: int):
        """Ingest bill text versions"""
        print(f"🚀 Starting Congress {congress} text versions ingestion")

        if not self.connect_db():
            return

        # Ensure table exists
        create_table_query = """
        CREATE TABLE IF NOT EXISTS congress.bill_text_versions (
            congress_number INTEGER,
            bill_type TEXT,
            bill_number INTEGER,
            version_code TEXT,
            date DATE,
            format TEXT,
            url TEXT,
            created_at TIMESTAMP,
            updated_at TIMESTAMP,
            PRIMARY KEY (congress_number, bill_type, bill_number, version_code, format)
        );
        """
        if not self.dry_run:
            cursor = self.conn.cursor()
            cursor.execute(create_table_query)
            self.conn.commit()
            cursor.close()

        offset = 0
        total_processed = 0

        while True:
            params = {'congress': congress, 'limit': self.batch_size, 'offset': offset}
            data = self.get("/bill", params)

            if not data or not data.get('bills'):
                break

            for bill in data['bills']:
                bill_type = bill.get('type')
                bill_number = bill.get('number')

                if not bill_type or not bill_number:
                    continue

                text_url = f"/bill/{congress}/{bill_type.lower()}/{bill_number}/text"
                text_data = self.get(text_url)

                if text_data and text_data.get('textVersions'):
                    versions = []
                    for version in text_data['textVersions']:
                        version_code = version.get('type')
                        date = version.get('date')

                        for fmt in version.get('formats', []):
                            versions.append((
                                congress,
                                bill_type,
                                bill_number,
                                version_code,
                                date,
                                fmt.get('type'),
                                fmt.get('url'),
                                datetime.now()
                            ))

                    if versions:
                        query = """
                        INSERT INTO congress.bill_text_versions
                        (congress_number, bill_type, bill_number, version_code, date, format, url, created_at)
                        VALUES %s
                        ON CONFLICT (congress_number, bill_type, bill_number, version_code, format) DO UPDATE SET
                            date = EXCLUDED.date,
                            url = EXCLUDED.url,
                            updated_at = now()
                        """

                        if self.dry_run:
                            print(f"🔍 DRY RUN: Would insert {len(versions)} text versions for {bill_type}{bill_number}")
                            total_processed += len(versions)
                        else:
                            cursor = self.conn.cursor()
                            try:
                                from psycopg2.extras import execute_values
                                execute_values(cursor, query, versions)
                                self.conn.commit()
                                total_processed += len(versions)
                                print(f"✅ Processed {len(versions)} text versions for {bill_type}{bill_number}")
                            except Exception as e:
                                print(f"❌ Insert failed: {e}")
                                self.conn.rollback()
                            finally:
                                cursor.close()

                time.sleep(0.1)

            offset += self.batch_size

        self.close_db()
        print(f"🎉 Completed: {total_processed} Congress text versions")

    def status(self):
        """Show Congress data status"""
        if not self.connect_db():
            return

        cursor = self.conn.cursor()
        try:
            tables = [
                ("congress.members", "Members"),
                ("congress.bills", "Bills"),
                ("congress.amendments", "Amendments"),
                ("congress.bill_summaries", "Summaries"),
                ("congress.bill_text_versions", "Text Versions")
            ]

            print("📊 Congress Data Status:")
            for table, label in tables:
                try:
                    cursor.execute(f"SELECT count(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    print(f"  {label:<15}: {count}")
                except psycopg2.errors.UndefinedTable:
                    print(f"  {label:<15}: Not initialized")
                    self.conn.rollback()

        except Exception as e:
            print(f"❌ Status check failed: {e}")
        finally:
            cursor.close()
            self.close_db()

def main():
    parser = argparse.ArgumentParser(description="Congress.gov Ingestion CLI")
    parser.add_argument('--dry-run', action='store_true', help='Run without making changes')
    parser.add_argument('--batch-size', type=int, default=50, help='Batch size')

    subparsers = parser.add_subparsers(dest='command', required=True)

    # Ingest Members
    members_parser = subparsers.add_parser('ingest-members', help='Ingest members')
    members_parser.add_argument('congress', type=int, help='Congress number')

    # Ingest Bills
    bills_parser = subparsers.add_parser('ingest-bills', help='Ingest bills')
    bills_parser.add_argument('congress', type=int, help='Congress number')

    # Ingest Amendments
    amdt_parser = subparsers.add_parser('ingest-amendments', help='Ingest amendments')
    amdt_parser.add_argument('congress', type=int, help='Congress number')

    # Ingest Summaries
    sum_parser = subparsers.add_parser('ingest-summaries', help='Ingest bill summaries')
    sum_parser.add_argument('congress', type=int, help='Congress number')

    # Ingest Text
    text_parser = subparsers.add_parser('ingest-text', help='Ingest bill text versions')
    text_parser.add_argument('congress', type=int, help='Congress number')

    # Status
    subparsers.add_parser('status', help='Show status')

    args = parser.parse_args()

    api_key = os.getenv('CONGRESS_API_KEY')
    if not api_key:
        print("❌ CONGRESS_API_KEY environment variable required")
        return

    db_config = {
        'database': 'opendiscourse',
        'user': 'cbwinslow',
        'host': '/var/run/postgresql'
    }

    cli = CongressCLI(api_key, db_config, args.batch_size, args.dry_run)

    if args.command == 'ingest-members':
        cli.ingest_members(args.congress)
    elif args.command == 'ingest-bills':
        cli.ingest_bills(args.congress)
    elif args.command == 'ingest-amendments':
        cli.ingest_amendments(args.congress)
    elif args.command == 'ingest-summaries':
        cli.ingest_summaries(args.congress)
    elif args.command == 'ingest-text':
        cli.ingest_text(args.congress)
    elif args.command == 'status':
        cli.status()

if __name__ == "__main__":
    main()
