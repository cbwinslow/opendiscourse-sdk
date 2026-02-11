#!/usr/bin/env python3
"""
OpenStates CLI Tool
Focused CLI for ingesting OpenStates people, jurisdictions, bills, committees, and events.
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

import psycopg2
import requests

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

class OpenStatesCLI:
    def __init__(self, api_key: str, db_config: Dict, batch_size: int = 50, dry_run: bool = False):
        self.api_key = api_key
        self.db_config = db_config
        self.batch_size = batch_size
        self.dry_run = dry_run
        self.base_url = "https://v3.openstates.org"
        self.session = requests.Session()
        self.session.headers.update({'X-API-KEY': api_key})
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

    def transform_person(self, person_data: Dict) -> tuple:
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

    def transform_bill(self, bill_data: Dict) -> tuple:
        """Transform OpenStates bill data"""
        return (
            bill_data.get('id'),
            bill_data.get('identifier'),
            bill_data.get('title'),
            bill_data.get('classification', ['bill'])[0],
            bill_data.get('jurisdiction', {}).get('id'),
            bill_data.get('session'),
            json.dumps(bill_data.get('actions', [])),
            datetime.now()
        )

    def transform_committee(self, comm_data: Dict) -> tuple:
        """Transform OpenStates committee data"""
        return (
            comm_data.get('id'),
            comm_data.get('name'),
            comm_data.get('classification'),
            comm_data.get('jurisdiction', {}).get('id'),
            comm_data.get('parent_id'),
            json.dumps(comm_data.get('members', [])),
            datetime.now()
        )

    def transform_event(self, event_data: Dict) -> tuple:
        """Transform OpenStates event data"""
        return (
            event_data.get('id'),
            event_data.get('name'),
            event_data.get('description'),
            event_data.get('start_date'),
            event_data.get('end_date'),
            event_data.get('status'),
            event_data.get('jurisdiction', {}).get('id'),
            json.dumps(event_data.get('location', {})),
            datetime.now()
        )

    def transform_vote_event(self, vote_data: Dict) -> tuple:
        """Transform OpenStates vote event data"""
        return (
            vote_data.get('id'),
            vote_data.get('identifier'),
            vote_data.get('motion_text'),
            vote_data.get('result'),
            vote_data.get('start_date'),
            vote_data.get('bill_id'),
            vote_data.get('jurisdiction', {}).get('id'),
            json.dumps(vote_data.get('votes', [])),
            datetime.now()
        )

    def ingest_people(self, jurisdiction: str):
        """Ingest OpenStates people"""
        print(f"🚀 Starting OpenStates people ingestion for {jurisdiction}")

        if not self.connect_db():
            return

        total_processed = 0
        page = 1

        while True:
            params = {'jurisdiction': jurisdiction, 'page': page, 'per_page': self.batch_size}
            data = self.get("/people", params)

            if not data or not data.get('results'):
                break

            people = []
            for person in data['results']:
                transformed = self.transform_person(person)
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

                if self.dry_run:
                    print(f"🔍 DRY RUN: Would insert {len(people)} people")
                    total_processed += len(people)
                else:
                    cursor = self.conn.cursor()
                    try:
                        from psycopg2.extras import execute_values
                        execute_values(cursor, query, people)
                        self.conn.commit()
                        total_processed += len(people)
                        print(f"✅ Processed {total_processed} people (page {page})")
                    except Exception as e:
                        print(f"❌ Batch insert failed: {e}")
                        self.conn.rollback()
                        break
                    finally:
                        cursor.close()

            page += 1
            time.sleep(0.6)  # Rate limiting

        self.close_db()
        print(f"🎉 Completed: {total_processed} OpenStates people")

    def ingest_jurisdictions(self):
        """Ingest OpenStates jurisdictions"""
        print("🚀 Starting OpenStates jurisdictions ingestion")

        if not self.connect_db():
            return

        data = self.get("/jurisdictions")
        if not data or not data.get('results'):
            print("❌ No jurisdictions found")
            return

        jurisdictions = []
        for j in data['results']:
            jurisdictions.append((
                j.get('id'),
                j.get('name'),
                j.get('url'),
                j.get('classification'),
                j.get('division_id'),
                datetime.now()
            ))

        if jurisdictions:
            query = """
            INSERT INTO openstates.jurisdictions
            (id, name, url, classification, division_id, created_at)
            VALUES %s
            ON CONFLICT (id) DO UPDATE SET
                name = EXCLUDED.name,
                url = EXCLUDED.url,
                classification = EXCLUDED.classification,
                division_id = EXCLUDED.division_id,
                updated_at = now()
            """

            if self.dry_run:
                print(f"🔍 DRY RUN: Would insert {len(jurisdictions)} jurisdictions")
            else:
                cursor = self.conn.cursor()
                try:
                    from psycopg2.extras import execute_values
                    execute_values(cursor, query, jurisdictions)
                    self.conn.commit()
                    print(f"✅ Processed {len(jurisdictions)} jurisdictions")
                except Exception as e:
                    print(f"❌ Batch insert failed: {e}")
                    self.conn.rollback()
                finally:
                    cursor.close()

        self.close_db()

    def ingest_bills(self, jurisdiction: str):
        """Ingest OpenStates bills"""
        print(f"🚀 Starting OpenStates bills ingestion for {jurisdiction}")

        if not self.connect_db():
            return

        # Ensure table exists
        create_table_query = """
        CREATE TABLE IF NOT EXISTS openstates.bills (
            id TEXT PRIMARY KEY,
            identifier TEXT,
            title TEXT,
            classification TEXT,
            jurisdiction_id TEXT,
            session TEXT,
            actions JSONB,
            created_at TIMESTAMP,
            updated_at TIMESTAMP
        );
        """
        if not self.dry_run:
            cursor = self.conn.cursor()
            cursor.execute(create_table_query)
            self.conn.commit()
            cursor.close()

        total_processed = 0
        page = 1

        while True:
            params = {'jurisdiction': jurisdiction, 'page': page, 'per_page': self.batch_size}
            data = self.get("/bills", params)

            if not data or not data.get('results'):
                break

            bills = []
            for bill in data['results']:
                transformed = self.transform_bill(bill)
                if transformed[0]:
                    bills.append(transformed)

            if bills:
                query = """
                INSERT INTO openstates.bills
                (id, identifier, title, classification, jurisdiction_id, session, actions, created_at)
                VALUES %s
                ON CONFLICT (id) DO UPDATE SET
                    identifier = EXCLUDED.identifier,
                    title = EXCLUDED.title,
                    classification = EXCLUDED.classification,
                    jurisdiction_id = EXCLUDED.jurisdiction_id,
                    session = EXCLUDED.session,
                    actions = EXCLUDED.actions,
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
                        print(f"✅ Processed {total_processed} bills (page {page})")
                    except Exception as e:
                        print(f"❌ Batch insert failed: {e}")
                        self.conn.rollback()
                        break
                    finally:
                        cursor.close()

            page += 1
            time.sleep(0.6)

        self.close_db()
        print(f"🎉 Completed: {total_processed} OpenStates bills")

    def ingest_committees(self, jurisdiction: str):
        """Ingest OpenStates committees"""
        print(f"🚀 Starting OpenStates committees ingestion for {jurisdiction}")

        if not self.connect_db():
            return

        # Ensure table exists
        create_table_query = """
        CREATE TABLE IF NOT EXISTS openstates.committees (
            id TEXT PRIMARY KEY,
            name TEXT,
            classification TEXT,
            jurisdiction_id TEXT,
            parent_id TEXT,
            members JSONB,
            created_at TIMESTAMP,
            updated_at TIMESTAMP
        );
        """
        if not self.dry_run:
            cursor = self.conn.cursor()
            cursor.execute(create_table_query)
            self.conn.commit()
            cursor.close()

        total_processed = 0
        page = 1

        while True:
            params = {'jurisdiction': jurisdiction, 'page': page, 'per_page': self.batch_size}
            data = self.get("/committees", params)

            if not data or not data.get('results'):
                break

            committees = []
            for comm in data['results']:
                transformed = self.transform_committee(comm)
                if transformed[0]:
                    committees.append(transformed)

            if committees:
                query = """
                INSERT INTO openstates.committees
                (id, name, classification, jurisdiction_id, parent_id, members, created_at)
                VALUES %s
                ON CONFLICT (id) DO UPDATE SET
                    name = EXCLUDED.name,
                    classification = EXCLUDED.classification,
                    jurisdiction_id = EXCLUDED.jurisdiction_id,
                    parent_id = EXCLUDED.parent_id,
                    members = EXCLUDED.members,
                    updated_at = now()
                """

                if self.dry_run:
                    print(f"🔍 DRY RUN: Would insert {len(committees)} committees")
                    total_processed += len(committees)
                else:
                    cursor = self.conn.cursor()
                    try:
                        from psycopg2.extras import execute_values
                        execute_values(cursor, query, committees)
                        self.conn.commit()
                        total_processed += len(committees)
                        print(f"✅ Processed {total_processed} committees (page {page})")
                    except Exception as e:
                        print(f"❌ Batch insert failed: {e}")
                        self.conn.rollback()
                        break
                    finally:
                        cursor.close()

            page += 1
            time.sleep(0.6)

        self.close_db()
        print(f"🎉 Completed: {total_processed} OpenStates committees")

    def ingest_events(self, jurisdiction: str):
        """Ingest OpenStates events"""
        print(f"🚀 Starting OpenStates events ingestion for {jurisdiction}")

        if not self.connect_db():
            return

        # Ensure table exists
        create_table_query = """
        CREATE TABLE IF NOT EXISTS openstates.events (
            id TEXT PRIMARY KEY,
            name TEXT,
            description TEXT,
            start_date TIMESTAMP,
            end_date TIMESTAMP,
            status TEXT,
            jurisdiction_id TEXT,
            location JSONB,
            created_at TIMESTAMP,
            updated_at TIMESTAMP
        );
        """
        if not self.dry_run:
            cursor = self.conn.cursor()
            cursor.execute(create_table_query)
            self.conn.commit()
            cursor.close()

        total_processed = 0
        page = 1

        while True:
            params = {'jurisdiction': jurisdiction, 'page': page, 'per_page': self.batch_size}
            data = self.get("/events", params)

            if not data or not data.get('results'):
                break

            events = []
            for event in data['results']:
                transformed = self.transform_event(event)
                if transformed[0]:
                    events.append(transformed)

            if events:
                query = """
                INSERT INTO openstates.events
                (id, name, description, start_date, end_date, status, jurisdiction_id, location, created_at)
                VALUES %s
                ON CONFLICT (id) DO UPDATE SET
                    name = EXCLUDED.name,
                    description = EXCLUDED.description,
                    start_date = EXCLUDED.start_date,
                    end_date = EXCLUDED.end_date,
                    status = EXCLUDED.status,
                    jurisdiction_id = EXCLUDED.jurisdiction_id,
                    location = EXCLUDED.location,
                    updated_at = now()
                """

                if self.dry_run:
                    print(f"🔍 DRY RUN: Would insert {len(events)} events")
                    total_processed += len(events)
                else:
                    cursor = self.conn.cursor()
                    try:
                        from psycopg2.extras import execute_values
                        execute_values(cursor, query, events)
                        self.conn.commit()
                        total_processed += len(events)
                        print(f"✅ Processed {total_processed} events (page {page})")
                    except Exception as e:
                        print(f"❌ Batch insert failed: {e}")
                        self.conn.rollback()
                        break
                    finally:
                        cursor.close()

            page += 1
            time.sleep(0.6)

        self.close_db()
        print(f"🎉 Completed: {total_processed} OpenStates events")

    def ingest_vote_events(self, jurisdiction: str):
        """Ingest OpenStates vote events"""
        print(f"🚀 Starting OpenStates vote events ingestion for {jurisdiction}")

        if not self.connect_db():
            return

        # Ensure table exists
        create_table_query = """
        CREATE TABLE IF NOT EXISTS openstates.vote_events (
            id TEXT PRIMARY KEY,
            identifier TEXT,
            motion_text TEXT,
            result TEXT,
            start_date TIMESTAMP,
            bill_id TEXT,
            jurisdiction_id TEXT,
            votes JSONB,
            created_at TIMESTAMP,
            updated_at TIMESTAMP
        );
        """
        if not self.dry_run:
            cursor = self.conn.cursor()
            cursor.execute(create_table_query)
            self.conn.commit()
            cursor.close()

        total_processed = 0
        page = 1

        while True:
            params = {'jurisdiction': jurisdiction, 'page': page, 'per_page': self.batch_size}
            data = self.get("/votes", params)

            if not data or not data.get('results'):
                break

            vote_events = []
            for vote in data['results']:
                transformed = self.transform_vote_event(vote)
                if transformed[0]:
                    vote_events.append(transformed)

            if vote_events:
                query = """
                INSERT INTO openstates.vote_events
                (id, identifier, motion_text, result, start_date, bill_id, jurisdiction_id, votes, created_at)
                VALUES %s
                ON CONFLICT (id) DO UPDATE SET
                    identifier = EXCLUDED.identifier,
                    motion_text = EXCLUDED.motion_text,
                    result = EXCLUDED.result,
                    start_date = EXCLUDED.start_date,
                    bill_id = EXCLUDED.bill_id,
                    jurisdiction_id = EXCLUDED.jurisdiction_id,
                    votes = EXCLUDED.votes,
                    updated_at = now()
                """

                if self.dry_run:
                    print(f"🔍 DRY RUN: Would insert {len(vote_events)} vote events")
                    total_processed += len(vote_events)
                else:
                    cursor = self.conn.cursor()
                    try:
                        from psycopg2.extras import execute_values
                        execute_values(cursor, query, vote_events)
                        self.conn.commit()
                        total_processed += len(vote_events)
                        print(f"✅ Processed {total_processed} vote events (page {page})")
                    except Exception as e:
                        print(f"❌ Batch insert failed: {e}")
                        self.conn.rollback()
                        break
                    finally:
                        cursor.close()

            page += 1
            time.sleep(0.6)

        self.close_db()
        print(f"🎉 Completed: {total_processed} OpenStates vote events")

    def ingest_all_states(self):
        """Ingest data for all state jurisdictions"""
        print("🚀 Starting comprehensive OpenStates ingestion for ALL states")

        # First get all jurisdictions
        if not self.connect_db():
            return

        cursor = self.conn.cursor()
        try:
            cursor.execute("SELECT id, name FROM openstates.jurisdictions WHERE classification = 'state'")
            jurisdictions = cursor.fetchall()
        except Exception as e:
            print(f"❌ Failed to fetch jurisdictions: {e}")
            print("💡 Tip: Run 'ingest-jurisdictions' first")
            self.close_db()
            return
        finally:
            cursor.close()
            self.close_db()

        if not jurisdictions:
            print("❌ No jurisdictions found. Run 'ingest-jurisdictions' first.")
            return

        total_states = len(jurisdictions)
        print(f"📍 Found {total_states} states to process")

        for idx, (jid, name) in enumerate(jurisdictions, 1):
            print(f"\n{'='*60}")
            print(f"[{idx}/{total_states}] Processing: {name}")
            print(f"{'='*60}")

            # Extract state code from OCD-ID
            state_code = jid.split('state:')[-1].split('/')[0] if 'state:' in jid else jid

            try:
                # Run all ingestion functions for this state
                self.ingest_people(state_code)
                self.ingest_bills(state_code)
                self.ingest_committees(state_code)
                self.ingest_events(state_code)
                self.ingest_vote_events(state_code)
                self.ingest_organizations(state_code)
                self.ingest_sessions(state_code)
                # Skip documents by default as it's very slow (N+1)
                # self.ingest_documents(state_code)

                print(f"✅ Completed {name}")
            except Exception as e:
                print(f"❌ Error processing {name}: {e}")
                print("⏭️  Continuing to next state...")
                continue

        print(f"\n🎉 Completed ingestion for all {total_states} states")

    def status(self):
        """Show OpenStates data status"""
        if not self.connect_db():
            return

        cursor = self.conn.cursor()
        try:
            tables = [
                ("openstates.people", "People"),
                ("openstates.jurisdictions", "Jurisdictions"),
                ("openstates.bills", "Bills"),
                ("openstates.committees", "Committees"),
                ("openstates.events", "Events"),
                ("openstates.vote_events", "Vote Events")
            ]

            print("📊 OpenStates Data Status:")
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
    parser = argparse.ArgumentParser(description="OpenStates Ingestion CLI")
    parser.add_argument('--dry-run', action='store_true', help='Run without making changes')
    parser.add_argument('--batch-size', type=int, default=50, help='Batch size')

    subparsers = parser.add_subparsers(dest='command', required=True)

    # Ingest People
    people_parser = subparsers.add_parser('ingest-people', help='Ingest people')
    people_parser.add_argument('jurisdiction', help='Jurisdiction code (e.g., ca, tx)')

    # Ingest Jurisdictions
    subparsers.add_parser('ingest-jurisdictions', help='Ingest jurisdictions')

    # Ingest Bills
    bills_parser = subparsers.add_parser('ingest-bills', help='Ingest bills')
    bills_parser.add_argument('jurisdiction', help='Jurisdiction code (e.g., ca, tx)')

    # Ingest Committees
    comm_parser = subparsers.add_parser('ingest-committees', help='Ingest committees')
    comm_parser.add_argument('jurisdiction', help='Jurisdiction code (e.g., ca, tx)')

    # Ingest Events
    events_parser = subparsers.add_parser('ingest-events', help='Ingest events')
    events_parser.add_argument('jurisdiction', help='Jurisdiction code (e.g., ca, tx)')

    # Ingest Vote Events
    votes_parser = subparsers.add_parser('ingest-vote-events', help='Ingest vote events')
    votes_parser.add_argument('jurisdiction', help='Jurisdiction code (e.g., ca, tx)')

    # Ingest All States
    subparsers.add_parser('ingest-all-states', help='Ingest all state data (people, bills, committees, etc.)')

    # Status
    subparsers.add_parser('status', help='Show status')

    args = parser.parse_args()

    api_key = os.getenv('OPENSTATES_API_KEY')
    if not api_key:
        print("❌ OPENSTATES_API_KEY environment variable required")
        return

    db_config = {
        'database': 'opendiscourse',
        'user': 'cbwinslow',
        'host': '/var/run/postgresql'
    }

    cli = OpenStatesCLI(api_key, db_config, args.batch_size, args.dry_run)

    if args.command == 'ingest-people':
        cli.ingest_people(args.jurisdiction)
    elif args.command == 'ingest-jurisdictions':
        cli.ingest_jurisdictions()
    elif args.command == 'ingest-bills':
        cli.ingest_bills(args.jurisdiction)
    elif args.command == 'ingest-committees':
        cli.ingest_committees(args.jurisdiction)
    elif args.command == 'ingest-events':
        cli.ingest_events(args.jurisdiction)
    elif args.command == 'ingest-vote-events':
        cli.ingest_vote_events(args.jurisdiction)
    elif args.command == 'ingest-all-states':
        cli.ingest_all_states()
    elif args.command == 'status':
        cli.status()

if __name__ == "__main__":
    main()
