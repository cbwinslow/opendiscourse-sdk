#!/usr/bin/env python3
"""
Congress.gov CLI Tool
Focused CLI for ingesting Congress members, bills, amendments, summaries, and text.
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

    def transform_bill_action(self, action_data: Dict, congress: int, bill_type: str, bill_number: int) -> tuple:
        """Transform bill action data"""
        return (
            congress,
            bill_type,
            bill_number,
            action_data.get('actionDate'),
            action_data.get('text', ''),
            action_data.get('type'),
            action_data.get('actionCode'),
            datetime.now()
        )

    def transform_bill_cosponsor(self, cosponsor_data: Dict, congress: int, bill_type: str, bill_number: int) -> tuple:
        """Transform bill cosponsor data"""
        return (
            congress,
            bill_type,
            bill_number,
            cosponsor_data.get('bioguideId'),
            cosponsor_data.get('sponsorshipDate'),
            cosponsor_data.get('isOriginalCosponsor'),
            datetime.now()
        )

    def transform_bill_subject(self, subject_data: Dict, congress: int, bill_type: str, bill_number: int) -> tuple:
        """Transform bill subject data"""
        # subject_data might be string or dict
        if isinstance(subject_data, dict):
            subject_name = subject_data.get('name', str(subject_data))
        else:
            subject_name = str(subject_data)

        return (
            congress,
            bill_type,
            bill_number,
            subject_name,
            datetime.now()
        )

    def transform_bill_title(self, title_data: Dict, congress: int, bill_type: str, bill_number: int) -> tuple:
        """Transform bill title data"""
        return (
            congress,
            bill_type,
            bill_number,
            title_data.get('title', ''),
            title_data.get('titleType'),
            title_data.get('titleTypeCode'),
            datetime.now()
        )

    def transform_related_bill(self, related_data: Dict, congress: int, bill_type: str, bill_number: int) -> tuple:
        """Transform related bill data"""
        rel_bill = related_data.get('relationshipDetails', [{}])[0] if related_data.get('relationshipDetails') else {}

        return (
            congress,
            bill_type,
            bill_number,
            related_data.get('congress'),
            related_data.get('type'),
            related_data.get('number'),
            rel_bill.get('type'),
            rel_bill.get('identifiedBy'),
            datetime.now()
        )

    def transform_committee_member(self, member_data: Dict, committee_id: str, congress: int, chamber_code: str) -> tuple:
        """Transform committee member data"""
        return (
            committee_id,
            member_data.get('bioguideId'),
            chamber_code,
            congress,
            member_data.get('rank', 0),
            member_data.get('title'),
            datetime.now()
        )

    def transform_amendment_action(self, action_data: Dict, congress: int, amendment_type: str, amendment_number: int) -> tuple:
        """Transform amendment action data"""
        return (
            congress,
            amendment_type,
            amendment_number,
            action_data.get('actionDate'),
            action_data.get('text', ''),
            action_data.get('type'),
            action_data.get('actionCode'),
            datetime.now()
        )

    def transform_amendment_sponsor(self, sponsor_data: Dict, congress: int, amendment_type: str, amendment_number: int) -> tuple:
        """Transform amendment sponsor data"""
        return (
            congress,
            amendment_type,
            amendment_number,
            sponsor_data.get('bioguideId'),
            sponsor_data.get('firstName'),
            sponsor_data.get('lastName'),
            sponsor_data.get('party'),
            sponsor_data.get('state'),
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

    def ingest_sessions(self):
        """Ingest congress sessions"""
        print("🚀 Starting Congress sessions ingestion")

        if not self.connect_db():
            return

        # Ensure table exists
        create_table_query = """
        CREATE TABLE IF NOT EXISTS congress.sessions (
            congress_number INTEGER,
            session_number INTEGER,
            type TEXT,
            start_date DATE,
            end_date DATE,
            created_at TIMESTAMP,
            updated_at TIMESTAMP,
            PRIMARY KEY (congress_number, session_number)
        );
        """
        if not self.dry_run:
            cursor = self.conn.cursor()
            cursor.execute(create_table_query)
            self.conn.commit()
            cursor.close()

        total_processed = 0
        offset = 0
        import re

        while True:
            params = {'limit': self.batch_size, 'offset': offset}
            data = self.get("/congress", params)

            if not data or not data.get('congresses'):
                break

            sessions = []
            for cong in data['congresses']:
                congress_num = cong.get('congress')
                if not congress_num:
                    # Try to extract from URL
                    url = cong.get('url', '')
                    match = re.search(r'/congress/(\d+)', url)
                    if match:
                        congress_num = int(match.group(1))
                    else:
                        continue

                if 'sessions' in cong:
                    for sess in cong['sessions']:
                        # Enrich session data with congress number
                        sess_data = sess.copy()
                        sess_data['congress'] = congress_num
                        sessions.append(self.transform_session(sess_data))

            if sessions:
                query = """
                INSERT INTO congress.sessions
                (congress_number, session_number, type, start_date, end_date, created_at)
                VALUES %s
                ON CONFLICT (congress_number, session_number) DO UPDATE SET
                    type = EXCLUDED.type,
                    start_date = EXCLUDED.start_date,
                    end_date = EXCLUDED.end_date,
                    updated_at = now()
                """

                if self.dry_run:
                    print(f"🔍 DRY RUN: Would insert {len(sessions)} sessions")
                    total_processed += len(sessions)
                else:
                    cursor = self.conn.cursor()
                    try:
                        from psycopg2.extras import execute_values
                        execute_values(cursor, query, sessions)
                        self.conn.commit()
                        total_processed += len(sessions)
                        print(f"✅ Processed {total_processed} sessions")
                    except Exception as e:
                        print(f"❌ Batch insert failed: {e}")
                        self.conn.rollback()
                        break
                    finally:
                        cursor.close()

            offset += self.batch_size
            time.sleep(0.1)

        self.close_db()
        print(f"🎉 Completed: {total_processed} Congress sessions")

    def ingest_chambers(self):
        """Ingest congress chambers"""
        print("🚀 Starting Congress chambers ingestion")

        if not self.connect_db():
            return

        # Ensure table exists
        create_table_query = """
        CREATE TABLE IF NOT EXISTS congress.chambers (
            chamber_code TEXT PRIMARY KEY,
            name TEXT,
            type TEXT,
            created_at TIMESTAMP,
            updated_at TIMESTAMP
        );
        """
        if not self.dry_run:
            cursor = self.conn.cursor()
            cursor.execute(create_table_query)
            self.conn.commit()
            cursor.close()

        # Hardcoded chambers since API endpoint /chamber doesn't exist
        chambers = [
            ('house', 'House of Representatives', 'house', datetime.now()),
            ('senate', 'Senate', 'senate', datetime.now()),
            ('joint', 'Joint Congress', 'joint', datetime.now())
        ]

        query = """
        INSERT INTO congress.chambers
        (chamber_code, name, type, created_at)
        VALUES %s
        ON CONFLICT (chamber_code) DO UPDATE SET
            name = EXCLUDED.name,
            type = EXCLUDED.type,
            updated_at = now()
        """

        if self.dry_run:
            print(f"🔍 DRY RUN: Would insert {len(chambers)} chambers")
        else:
            cursor = self.conn.cursor()
            try:
                from psycopg2.extras import execute_values
                execute_values(cursor, query, chambers)
                self.conn.commit()
                print(f"✅ Processed {len(chambers)} chambers")
            except Exception as e:
                print(f"❌ Batch insert failed: {e}")
                self.conn.rollback()
            finally:
                cursor.close()

        self.close_db()
        print(f"🎉 Completed: {len(chambers)} Congress chambers")

    def ingest_committees(self, congress: int):
        """Ingest congress committees"""
        print(f"🚀 Starting Congress {congress} committees ingestion")

        if not self.connect_db():
            return

        # Ensure table exists
        create_table_query = """
        CREATE TABLE IF NOT EXISTS congress.committees (
            committee_code TEXT,
            name TEXT,
            chamber TEXT,
            parent_committee_code TEXT,
            type TEXT,
            jurisdiction TEXT,
            created_at TIMESTAMP,
            updated_at TIMESTAMP,
            PRIMARY KEY (committee_code)
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
            params = {'limit': self.batch_size, 'offset': offset}
            # /committee/{congress} lists committees for that congress
            data = self.get(f"/committee/{congress}", params)

            if not data or not data.get('committees'):
                break

            committees = []
            for comm in data['committees']:
                committees.append(self.transform_congress_committee(comm))

            if committees:
                query = """
                INSERT INTO congress.committees
                (committee_code, name, chamber, parent_committee_code, type, jurisdiction, created_at)
                VALUES %s
                ON CONFLICT (committee_code) DO UPDATE SET
                    name = EXCLUDED.name,
                    chamber = EXCLUDED.chamber,
                    parent_committee_code = EXCLUDED.parent_committee_code,
                    type = EXCLUDED.type,
                    jurisdiction = EXCLUDED.jurisdiction,
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
                        print(f"✅ Processed {total_processed} committees")
                    except Exception as e:
                        print(f"❌ Batch insert failed: {e}")
                        self.conn.rollback()
                        break
                    finally:
                        cursor.close()

            offset += self.batch_size
            time.sleep(0.1)

        self.close_db()
        print(f"🎉 Completed: {total_processed} Congress committees")

    def ingest_votes(self, congress: int):
        """Ingest congress votes"""
        print(f"🚀 Starting Congress {congress} votes ingestion")

        if not self.connect_db():
            return

        # Ensure table exists
        create_table_query = """
        CREATE TABLE IF NOT EXISTS congress.votes (
            congress_number INTEGER,
            session_number INTEGER,
            roll_call_number INTEGER,
            question TEXT,
            result TEXT,
            date DATE,
            positions JSONB,
            created_at TIMESTAMP,
            updated_at TIMESTAMP,
            PRIMARY KEY (congress_number, session_number, roll_call_number)
        );
        """
        if not self.dry_run:
            cursor = self.conn.cursor()
            cursor.execute(create_table_query)
            self.conn.commit()
            cursor.close()

        total_processed = 0
        offset = 0

        # Only House votes are supported by the API currently via /house-vote
        # Senate votes endpoint /senate-vote does not exist yet.
        print("ℹ️ Note: Only House votes are currently supported by the Congress.gov API.")

        while True:
            params = {'congress': congress, 'limit': self.batch_size, 'offset': offset}
            data = self.get("/house-vote", params)

            if not data or not data.get('houseRollCallVotes'):
                break

            votes = []
            for vote in data['houseRollCallVotes']:
                # Filter by congress if API didn't filter correctly
                if vote.get('congress') != congress:
                    continue

                # Fetch details to get positions
                detail_url = vote.get('url')
                if not detail_url:
                    # Construct if missing: /house-vote/{congress}/{session}/{rollCall}
                    session = vote.get('sessionNumber')
                    roll_call = vote.get('rollCallNumber')
                    if session and roll_call:
                        detail_url = f"https://api.congress.gov/v3/house-vote/{congress}/{session}/{roll_call}"

                if detail_url:
                    # Remove base URL if present to use self.get properly or use full URL
                    # self.get appends base_url. detail_url is full URL.
                    # We can parse the path.
                    import urllib.parse
                    parsed = urllib.parse.urlparse(detail_url)
                    path = parsed.path.replace('/v3', '') # self.base_url includes /v3? No, base_url is .../v3
                    # self.base_url = "https://api.congress.gov/v3"
                    # So path should start with /house-vote...

                    detail_data = self.get(path)

                    # Detail response structure: {'houseVote': {...}} ?
                    # Let's assume standard wrapper.

                    if detail_data:
                        # The detail object might be wrapped in 'houseVote' or similar
                        # Based on list key 'houseRollCallVotes', detail might be 'houseRollCallVote' or 'houseVote'
                        # Let's check keys.
                        vote_detail = detail_data.get('houseVote', detail_data)
                        votes.append(self.transform_vote(vote_detail))

            if votes:
                query = """
                INSERT INTO congress.votes
                (congress_number, session_number, roll_call_number, question, result, date, positions, created_at)
                VALUES %s
                ON CONFLICT (congress_number, session_number, roll_call_number) DO UPDATE SET
                    question = EXCLUDED.question,
                    result = EXCLUDED.result,
                    date = EXCLUDED.date,
                    positions = EXCLUDED.positions,
                    updated_at = now()
                """

                if self.dry_run:
                    print(f"🔍 DRY RUN: Would insert {len(votes)} votes")
                    total_processed += len(votes)
                else:
                    cursor = self.conn.cursor()
                    try:
                        from psycopg2.extras import execute_values
                        execute_values(cursor, query, votes)
                        self.conn.commit()
                        total_processed += len(votes)
                        print(f"✅ Processed {len(votes)} votes")
                    except Exception as e:
                        print(f"❌ Batch insert failed: {e}")
                        self.conn.rollback()
                        # Don't break here, try next batch
                    finally:
                        cursor.close()

            offset += self.batch_size
            time.sleep(0.1)

        self.close_db()
        print(f"🎉 Completed: {total_processed} Congress votes")

    def ingest_bill_actions(self, congress: int):
        """Ingest bill actions for all bills in congress"""
        print(f"🚀 Starting bill actions for Congress {congress}")

        if not self.connect_db():
            return

        # Create table if not exists
        create_table_query = """
        CREATE TABLE IF NOT EXISTS congress.bill_actions (
            congress_number INTEGER,
            bill_type TEXT,
            bill_number INTEGER,
            action_date DATE,
            action_text TEXT,
            action_type TEXT,
            action_code TEXT,
            created_at TIMESTAMP,
            updated_at TIMESTAMP,
            PRIMARY KEY (congress_number, bill_type, bill_number, action_date, action_text)
        );
        """
        if not self.dry_run:
            cursor = self.conn.cursor()
            cursor.execute(create_table_query)
            self.conn.commit()
            cursor.close()

        # Get all bills for this congress
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT congress_number, bill_type, bill_number
            FROM congress.bills
            WHERE congress_number = %s
        """, (congress,))
        bills = cursor.fetchall()
        cursor.close()

        print(f"📋 Found {len(bills)} bills to process")

        total_processed = 0
        for bill_congress, bill_type, bill_number in bills:
            # Fetch actions for this bill
            endpoint = f"/bill/{bill_congress}/{bill_type.lower()}/{bill_number}/actions"
            data = self.get(endpoint)

            if not data or not data.get('actions'):
                continue

            actions = []
            for action in data['actions']:
                actions.append(self.transform_bill_action(
                    action, bill_congress, bill_type, bill_number
                ))

            if actions:
                query = """
                INSERT INTO congress.bill_actions
                (congress_number, bill_type, bill_number, action_date,
                 action_text, action_type, action_code, created_at)
                VALUES %s
                ON CONFLICT (congress_number, bill_type, bill_number, action_date, action_text)
                DO UPDATE SET
                    action_type = EXCLUDED.action_type,
                    action_code = EXCLUDED.action_code,
                    updated_at = now()
                """

                if self.dry_run:
                    print(f"🔍 DRY RUN: {bill_type}{bill_number} - {len(actions)} actions")
                    total_processed += len(actions)
                else:
                    cursor = self.conn.cursor()
                    try:
                        from psycopg2.extras import execute_values
                        execute_values(cursor, query, actions)
                        self.conn.commit()
                        total_processed += len(actions)
                        print(f"✅ {bill_type}{bill_number}: {len(actions)} actions")
                    except Exception as e:
                        print(f"❌ {bill_type}{bill_number}: {e}")
                        self.conn.rollback()
                    finally:
                        cursor.close()

            time.sleep(0.1)  # Rate limiting

        self.close_db()
        print(f"🎉 Completed: {total_processed} bill actions")

    def ingest_bill_cosponsors(self, congress: int):
        """Ingest bill cosponsors for all bills in congress"""
        print(f"🚀 Starting bill cosponsors for Congress {congress}")

        if not self.connect_db():
            return

        # Create table if not exists
        create_table_query = """
        CREATE TABLE IF NOT EXISTS congress.bill_cosponsors (
            congress_number INTEGER,
            bill_type TEXT,
            bill_number INTEGER,
            bioguide_id TEXT,
            sponsorship_date DATE,
            is_original_cosponsor BOOLEAN,
            created_at TIMESTAMP,
            updated_at TIMESTAMP,
            PRIMARY KEY (congress_number, bill_type, bill_number, bioguide_id)
        );
        """
        if not self.dry_run:
            cursor = self.conn.cursor()
            cursor.execute(create_table_query)
            self.conn.commit()
            cursor.close()

        # Get all bills
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT congress_number, bill_type, bill_number
            FROM congress.bills
            WHERE congress_number = %s
        """, (congress,))
        bills = cursor.fetchall()
        cursor.close()

        print(f"📋 Found {len(bills)} bills to process")

        total_processed = 0
        for bill_congress, bill_type, bill_number in bills:
            endpoint = f"/bill/{bill_congress}/{bill_type.lower()}/{bill_number}/cosponsors"
            data = self.get(endpoint)

            if not data or not data.get('cosponsors'):
                continue

            cosponsors = []
            for cosponsor in data['cosponsors']:
                cosponsors.append(self.transform_bill_cosponsor(
                    cosponsor, bill_congress, bill_type, bill_number
                ))

            if cosponsors:
                query = """
                INSERT INTO congress.bill_cosponsors
                (congress_number, bill_type, bill_number, bioguide_id,
                 sponsorship_date, is_original_cosponsor, created_at)
                VALUES %s
                ON CONFLICT (congress_number, bill_type, bill_number, bioguide_id)
                DO UPDATE SET
                    sponsorship_date = EXCLUDED.sponsorship_date,
                    is_original_cosponsor = EXCLUDED.is_original_cosponsor,
                    updated_at = now()
                """

                if self.dry_run:
                    print(f"🔍 DRY RUN: {bill_type}{bill_number} - {len(cosponsors)} cosponsors")
                    total_processed += len(cosponsors)
                else:
                    cursor = self.conn.cursor()
                    try:
                        from psycopg2.extras import execute_values
                        execute_values(cursor, query, cosponsors)
                        self.conn.commit()
                        total_processed += len(cosponsors)
                        print(f"✅ {bill_type}{bill_number}: {len(cosponsors)} cosponsors")
                    except Exception as e:
                        print(f"❌ {bill_type}{bill_number}: {e}")
                        self.conn.rollback()
                    finally:
                        cursor.close()

            time.sleep(0.1)

        self.close_db()
        print(f"🎉 Completed: {total_processed} bill cosponsors")

    def ingest_bill_subjects(self, congress: int):
        """Ingest bill subjects for all bills in congress"""
        print(f"🚀 Starting bill subjects for Congress {congress}")

        if not self.connect_db():
            return

        # Create table if not exists
        create_table_query = """
        CREATE TABLE IF NOT EXISTS congress.bill_subjects (
            congress_number INTEGER,
            bill_type TEXT,
            bill_number INTEGER,
            subject_name TEXT,
            created_at TIMESTAMP,
            updated_at TIMESTAMP,
            PRIMARY KEY (congress_number, bill_type, bill_number, subject_name)
        );
        """
        if not self.dry_run:
            cursor = self.conn.cursor()
            cursor.execute(create_table_query)
            self.conn.commit()
            cursor.close()

        # Get all bills
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT congress_number, bill_type, bill_number
            FROM congress.bills
            WHERE congress_number = %s
        """, (congress,))
        bills = cursor.fetchall()
        cursor.close()

        print(f"📋 Found {len(bills)} bills to process")

        total_processed = 0
        for bill_congress, bill_type, bill_number in bills:
            endpoint = f"/bill/{bill_congress}/{bill_type.lower()}/{bill_number}/subjects"
            data = self.get(endpoint)

            # Subjects might be in different formats
            subjects_list = data.get('subjects', {}).get('legislativeSubjects', []) if data else []

            if not subjects_list:
                continue

            subjects = []
            for subject in subjects_list:
                subjects.append(self.transform_bill_subject(
                    subject, bill_congress, bill_type, bill_number
                ))

            if subjects:
                query = """
                INSERT INTO congress.bill_subjects
                (congress_number, bill_type, bill_number, subject_name, created_at)
                VALUES %s
                ON CONFLICT (congress_number, bill_type, bill_number, subject_name)
                DO UPDATE SET
                    updated_at = now()
                """

                if self.dry_run:
                    print(f"🔍 DRY RUN: {bill_type}{bill_number} - {len(subjects)} subjects")
                    total_processed += len(subjects)
                else:
                    cursor = self.conn.cursor()
                    try:
                        from psycopg2.extras import execute_values
                        execute_values(cursor, query, subjects)
                        self.conn.commit()
                        total_processed += len(subjects)
                        print(f"✅ {bill_type}{bill_number}: {len(subjects)} subjects")
                    except Exception as e:
                        print(f"❌ {bill_type}{bill_number}: {e}")
                        self.conn.rollback()
                    finally:
                        cursor.close()

            time.sleep(0.1)

        self.close_db()
        print(f"🎉 Completed: {total_processed} bill subjects")

    def ingest_bill_titles(self, congress: int):
        """Ingest bill titles for all bills in congress"""
        print(f"🚀 Starting bill titles for Congress {congress}")

        if not self.connect_db():
            return

        # Create table if not exists
        create_table_query = """
        CREATE TABLE IF NOT EXISTS congress.bill_titles (
            congress_number INTEGER,
            bill_type TEXT,
            bill_number INTEGER,
            title TEXT,
            title_type TEXT,
            title_type_code TEXT,
            created_at TIMESTAMP,
            updated_at TIMESTAMP,
            PRIMARY KEY (congress_number, bill_type, bill_number, title)
        );
        """
        if not self.dry_run:
            cursor = self.conn.cursor()
            cursor.execute(create_table_query)
            self.conn.commit()
            cursor.close()

        # Get all bills
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT congress_number, bill_type, bill_number
            FROM congress.bills
            WHERE congress_number = %s
        """, (congress,))
        bills = cursor.fetchall()
        cursor.close()

        print(f"📋 Found {len(bills)} bills to process")

        total_processed = 0
        for bill_congress, bill_type, bill_number in bills:
            endpoint = f"/bill/{bill_congress}/{bill_type.lower()}/{bill_number}/titles"
            data = self.get(endpoint)

            if not data or not data.get('titles'):
                continue

            titles = []
            for title in data['titles']:
                titles.append(self.transform_bill_title(
                    title, bill_congress, bill_type, bill_number
                ))

            if titles:
                query = """
                INSERT INTO congress.bill_titles
                (congress_number, bill_type, bill_number, title,
                 title_type, title_type_code, created_at)
                VALUES %s
                ON CONFLICT (congress_number, bill_type, bill_number, title)
                DO UPDATE SET
                    title_type = EXCLUDED.title_type,
                    title_type_code = EXCLUDED.title_type_code,
                    updated_at = now()
                """

                if self.dry_run:
                    print(f"🔍 DRY RUN: {bill_type}{bill_number} - {len(titles)} titles")
                    total_processed += len(titles)
                else:
                    cursor = self.conn.cursor()
                    try:
                        from psycopg2.extras import execute_values
                        execute_values(cursor, query, titles)
                        self.conn.commit()
                        total_processed += len(titles)
                        print(f"✅ {bill_type}{bill_number}: {len(titles)} titles")
                    except Exception as e:
                        print(f"❌ {bill_type}{bill_number}: {e}")
                        self.conn.rollback()
                    finally:
                        cursor.close()

            time.sleep(0.1)

        self.close_db()
        print(f"🎉 Completed: {total_processed} bill titles")

    def ingest_related_bills(self, congress: int):
        """Ingest related bills for all bills in congress"""
        print(f"🚀 Starting related bills for Congress {congress}")

        if not self.connect_db():
            return

        # Create table if not exists
        create_table_query = """
        CREATE TABLE IF NOT EXISTS congress.related_bills (
            congress_number INTEGER,
            bill_type TEXT,
            bill_number INTEGER,
            related_congress INTEGER,
            related_bill_type TEXT,
            related_bill_number INTEGER,
            relationship_type TEXT,
            identified_by TEXT,
            created_at TIMESTAMP,
            updated_at TIMESTAMP,
            PRIMARY KEY (congress_number, bill_type, bill_number, related_congress, related_bill_type, related_bill_number)
        );
        """
        if not self.dry_run:
            cursor = self.conn.cursor()
            cursor.execute(create_table_query)
            self.conn.commit()
            cursor.close()

        # Get all bills
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT congress_number, bill_type, bill_number
            FROM congress.bills
            WHERE congress_number = %s
        """, (congress,))
        bills = cursor.fetchall()
        cursor.close()

        print(f"📋 Found {len(bills)} bills to process")

        total_processed = 0
        for bill_congress, bill_type, bill_number in bills:
            endpoint = f"/bill/{bill_congress}/{bill_type.lower()}/{bill_number}/relatedbills"
            data = self.get(endpoint)

            if not data or not data.get('relatedBills'):
                continue

            related = []
            for rel_bill in data['relatedBills']:
                related.append(self.transform_related_bill(
                    rel_bill, bill_congress, bill_type, bill_number
                ))

            if related:
                query = """
                INSERT INTO congress.related_bills
                (congress_number, bill_type, bill_number, related_congress,
                 related_bill_type, related_bill_number, relationship_type, identified_by, created_at)
                VALUES %s
                ON CONFLICT (congress_number, bill_type, bill_number, related_congress, related_bill_type, related_bill_number)
                DO UPDATE SET
                    relationship_type = EXCLUDED.relationship_type,
                    identified_by = EXCLUDED.identified_by,
                    updated_at = now()
                """

                if self.dry_run:
                    print(f"🔍 DRY RUN: {bill_type}{bill_number} - {len(related)} related bills")
                    total_processed += len(related)
                else:
                    cursor = self.conn.cursor()
                    try:
                        from psycopg2.extras import execute_values
                        execute_values(cursor, query, related)
                        self.conn.commit()
                        total_processed += len(related)
                        print(f"✅ {bill_type}{bill_number}: {len(related)} related bills")
                    except Exception as e:
                        print(f"❌ {bill_type}{bill_number}: {e}")
                        self.conn.rollback()
                    finally:
                        cursor.close()

            time.sleep(0.1)

        self.close_db()
        print(f"🎉 Completed: {total_processed} related bills")

    def ingest_committee_members(self, congress: int):
        """Ingest committee members for all committees"""
        print(f"🚀 Starting committee members ingestion for Congress {congress}")

        if not self.connect_db():
            return

        # Ensure table exists
        create_table_query = """
        CREATE TABLE IF NOT EXISTS congress.committee_members (
            congress_number INT,
            chamber VARCHAR(10),
            committee_code VARCHAR(10),
            bioguide_id VARCHAR(10),
            name TEXT,
            party VARCHAR(50),
            state VARCHAR(2),
            rank INT,
            created_at TIMESTAMP,
            updated_at TIMESTAMP,
            PRIMARY KEY (congress_number, chamber, committee_code, bioguide_id)
        );
        """
        if not self.dry_run:
            cursor = self.conn.cursor()
            cursor.execute(create_table_query)
            self.conn.commit()
            cursor.close()

        # Get all committees for this congress
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT committee_id, chamber_code
            FROM congress.committees
        """)
        committees = cursor.fetchall()
        cursor.close()

        print(f"📋 Found {len(committees)} committees to process")

        total_processed = 0
        for committee_id, chamber_code in committees:
            # Extract committee code from committee_id (format: hsag00 -> ag)
            # Committee IDs are like "hsag00" (house agriculture), "sshr00" (senate health)
            committee_code = committee_id[2:].rstrip('0')  # Remove prefix and trailing zeros

            # Fetch committee details including members
            endpoint = f"/committee/{congress}/{chamber_code.lower()}/{committee_code}"
            data = self.get(endpoint)

            if not data or not data.get('members'):
                continue

            members = []
            for member in data['members']:
                members.append(self.transform_committee_member(
                    member, committee_id, congress, chamber_code
                ))

            if members:
                query = """
                INSERT INTO congress.committee_members
                (committee_id, bioguide_id, chamber_code, congress_number,
                 rank_in_committee, title, created_at)
                VALUES %s
                ON CONFLICT (committee_member_id)
                DO UPDATE SET
                    bioguide_id = EXCLUDED.bioguide_id,
                    chamber_code = EXCLUDED.chamber_code,
                    congress_number = EXCLUDED.congress_number,
                    rank_in_committee = EXCLUDED.rank_in_committee,
                    title = EXCLUDED.title,
                    updated_at = now()
                """

                if self.dry_run:
                    print(f"🔍 Would insert {len(members)} members for {chamber_code}-{committee_code}")
                    total_processed += len(members)
                else:
                    cursor = self.conn.cursor()
                    try:
                        from psycopg2.extras import execute_values
                        execute_values(cursor, query, members)
                        self.conn.commit()
                        total_processed += len(members)
                        print(f"✅ {chamber}-{committee_code}: {len(members)} members")
                    except Exception as e:
                        print(f"❌ Failed {chamber}-{committee_code}: {e}")
                        self.conn.rollback()
                    finally:
                        cursor.close()

            time.sleep(0.1)  # Rate limiting

        self.close_db()
        print(f"🎉 Completed: {total_processed} committee members")

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
                ("congress.bill_text_versions", "Text Versions"),
                ("congress.sessions", "Sessions"),
                ("congress.chambers", "Chambers"),
                ("congress.committees", "Committees"),
                ("congress.votes", "Votes"),
                ("congress.bill_actions", "Bill Actions"),
                ("congress.bill_cosponsors", "Bill Cosponsors"),
                ("congress.bill_subjects", "Bill Subjects"),
                ("congress.bill_titles", "Bill Titles"),
                ("congress.related_bills", "Related Bills"),
                ("congress.committee_members", "Committee Members")
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

    # Ingest Sessions
    subparsers.add_parser('ingest-sessions', help='Ingest congress sessions')

    # Ingest Chambers
    subparsers.add_parser('ingest-chambers', help='Ingest congress chambers')

    # Ingest Committees
    comm_parser = subparsers.add_parser('ingest-committees', help='Ingest congress committees')
    comm_parser.add_argument('congress', type=int, help='Congress number')

    # Ingest Votes
    vote_parser = subparsers.add_parser('ingest-votes', help='Ingest congress votes')
    vote_parser.add_argument('congress', type=int, help='Congress number')

    # Ingest Bill Actions
    actions_parser = subparsers.add_parser('ingest-bill-actions', help='Ingest bill actions')
    actions_parser.add_argument('congress', type=int, help='Congress number')

    # Ingest Bill Cosponsors
    cosp_parser = subparsers.add_parser('ingest-bill-cosponsors', help='Ingest bill cosponsors')
    cosp_parser.add_argument('congress', type=int, help='Congress number')

    # Ingest Bill Subjects
    subj_parser = subparsers.add_parser('ingest-bill-subjects', help='Ingest bill subjects')
    subj_parser.add_argument('congress', type=int, help='Congress number')

    # Ingest Bill Titles
    titles_parser = subparsers.add_parser('ingest-bill-titles', help='Ingest bill titles')
    titles_parser.add_argument('congress', type=int, help='Congress number')

    # Ingest Related Bills
    related_parser = subparsers.add_parser('ingest-related-bills', help='Ingest related bills')
    related_parser.add_argument('congress', type=int, help='Congress number')

    # Ingest Committee Members
    comm_mem_parser = subparsers.add_parser('ingest-committee-members', help='Ingest committee members')
    comm_mem_parser.add_argument('congress', type=int, help='Congress number')

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
    elif args.command == 'ingest-sessions':
        cli.ingest_sessions()
    elif args.command == 'ingest-chambers':
        cli.ingest_chambers()
    elif args.command == 'ingest-committees':
        cli.ingest_committees(args.congress)
    elif args.command == 'ingest-votes':
        cli.ingest_votes(args.congress)
    elif args.command == 'ingest-bill-actions':
        cli.ingest_bill_actions(args.congress)
    elif args.command == 'ingest-bill-cosponsors':
        cli.ingest_bill_cosponsors(args.congress)
    elif args.command == 'ingest-bill-subjects':
        cli.ingest_bill_subjects(args.congress)
    elif args.command == 'ingest-bill-titles':
        cli.ingest_bill_titles(args.congress)
    elif args.command == 'ingest-related-bills':
        cli.ingest_related_bills(args.congress)
    elif args.command == 'ingest-committee-members':
        cli.ingest_committee_members(args.congress)
    elif args.command == 'status':
        cli.status()

if __name__ == "__main__":
    main()
