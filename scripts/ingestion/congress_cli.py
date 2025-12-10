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
import json
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
        # Map chamber codes
        chamber_mapping = {
            'House': 'house',
            'Senate': 'senate',
            'Joint': 'joint'
        }
        chamber_raw = committee_data.get('chamber', '')
        chamber_code = chamber_mapping.get(chamber_raw, chamber_raw.lower())

        # Use systemCode as ID, or url, or code
        committee_id = committee_data.get('systemCode') or committee_data.get('code')

        parent_id = None
        if committee_data.get('parentCommittee'):
            parent_id = committee_data['parentCommittee'].get('systemCode')

        return (
            committee_id,
            committee_data.get('name'),
            chamber_code,
            parent_id,
            committee_data.get('type'),
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

        # Static list of chambers
        chambers = [
            ('house', 'House of Representatives', 'lower'),
            ('senate', 'Senate', 'upper'),
            ('joint', 'Joint Session', 'joint')
        ]

        query = """
        INSERT INTO congress.chambers (chamber_code, name, type)
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

    def ingest_committees(self, congress: int):
        """Ingest congress committees"""
        print(f"🚀 Starting Congress {congress} committees ingestion")

        if not self.connect_db():
            return

        # Ensure table exists
        create_table_query = """
        CREATE TABLE IF NOT EXISTS congress.committees (
            committee_id TEXT PRIMARY KEY,
            chamber_code TEXT,
            name TEXT,
            type TEXT,
            url TEXT,
            established_at DATE,
            terminated_at DATE,
            parent_committee_id TEXT,
            jurisdiction TEXT,
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
        offset = 0

        while True:
            params = {'congress': congress, 'limit': self.batch_size, 'offset': offset}
            data = self.get("/committee", params)

            if not data or not data.get('committees'):
                break

            committees = []
            for comm in data['committees']:
                transformed = self.transform_congress_committee(comm)
                if transformed[0]: # Has committeeCode
                    committees.append(transformed)

            if committees:
                query = """
                INSERT INTO congress.committees
                (committee_id, name, chamber_code, parent_committee_id, type, created_at)
                VALUES %s
                ON CONFLICT (committee_id) DO UPDATE SET
                    name = EXCLUDED.name,
                    chamber_code = EXCLUDED.chamber_code,
                    parent_committee_id = EXCLUDED.parent_committee_id,
                    type = EXCLUDED.type,
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
        """Ingest congress votes (roll call votes)"""
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

        # Only House votes are supported by the API currently via /house-vote
        print("ℹ️ Note: Only House votes are currently supported by the Congress.gov API.")

        offset = 0
        while True:
            # List votes for a session
            # Endpoint: /house-vote
            url = "/house-vote"
            params = {'congress': congress, 'limit': self.batch_size, 'offset': offset}
            data = self.get(url, params)

            if not data or not data.get('houseRollCallVotes'):
                break

            votes = []
            for vote in data['houseRollCallVotes']:
                # Enrich with session info if needed
                # vote object has 'congress', 'sessionNumber', 'rollCallNumber', 'date', 'question', 'result', 'url'

                # Fetch detail for positions
                detail_url = vote.get('url')
                # detail_url is full URL. We need to fetch it.
                # self.get handles full URL if we pass it?
                # self.get prepends base_url if not starting with http.
                # If it starts with http, requests.get is called?
                # Let's check self.get implementation.
                # Assuming self.get handles it or we need to strip base.

                # If detail_url is "https://api.congress.gov/v3/house-vote/..."
                # We can strip base.
                if detail_url and detail_url.startswith(self.base_url):
                    detail_path = detail_url[len(self.base_url):]
                elif detail_url:
                    # Just try passing it? Or parse.
                    import urllib.parse
                    parsed = urllib.parse.urlparse(detail_url)
                    detail_path = parsed.path.replace('/v3', '') # Assuming /v3 is in base path
                else:
                    detail_path = None

                if detail_path:
                    detail_data = self.get(detail_path)
                    if detail_data and detail_data.get('houseVote'):
                         votes.append(self.transform_vote(detail_data['houseVote']))

                time.sleep(0.1) # Rate limit for detail fetch

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
                else:
                    cursor = self.conn.cursor()
                    try:
                        from psycopg2.extras import execute_values
                        execute_values(cursor, query, votes)
                        self.conn.commit()
                        print(f"✅ Processed {len(votes)} votes")
                    except Exception as e:
                        print(f"❌ Batch insert failed: {e}")
                        self.conn.rollback()
                    finally:
                        cursor.close()

            if not data.get('pagination', {}).get('next'):
                 break
            offset += self.batch_size
            time.sleep(0.1)

        self.close_db()
        print(f"🎉 Completed Congress votes")

    def ingest_bill_details(self, congress: int, detail_type: str):
        """
        Generic ingestor for bill details (actions, cosponsors, subjects, titles, related bills).
        detail_type options: 'actions', 'cosponsors', 'subjects', 'titles', 'related'
        """
        print(f"🚀 Starting Congress {congress} bill {detail_type} ingestion")

        if not self.connect_db():
            return

        # Map detail type to table and transform function
        config = {
            'actions': {
                'table': 'congress.bill_actions',
                'transform': self.transform_bill_action,
                'endpoint_suffix': 'actions',
                'data_key': 'actions',
                'columns': '(bill_id, action_date, action_text, type, action_code, created_at)', # Simplified, needs mapping to schema
                # The schema uses bill_id (UUID). We have congress/type/number.
                # We need to lookup UUID or use natural keys if schema allows.
                # The migration 001_congress_schema.sql uses UUIDs for bills.
                # But we are ingesting from API which gives us natural keys.
                # We either need to query for UUIDs or insert using natural keys if we modify schema/query.
                # For this CLI, let's assume we can look up UUIDs or we need to adapt.
                # Wait, the previous ingest_bills inserts into congress.bills with natural keys?
                # Let's check ingest_bills.
                # ingest_bills inserts: (congress_number, bill_type, bill_number, ...)
                # It does NOT insert UUID. The UUID is generated by DEFAULT gen_random_uuid().
                # So we can't easily insert into child tables using UUID unless we lookup.
                # OR we can use a subquery in INSERT: (SELECT bill_id FROM congress.bills WHERE ...)

                # Let's use the subquery approach for the UUID.
                'insert_query': """
                INSERT INTO congress.bill_actions
                (bill_id, action_date, action_text, action_code, created_at)
                SELECT b.bill_id, v.action_date, v.action_text, v.action_code, v.created_at
                FROM (VALUES %s) AS v(congress, type, number, action_date, action_text, action_type, action_code, created_at)
                JOIN congress.bills b ON b.congress_number = CAST(v.congress AS INTEGER) AND b.bill_type = v.type AND b.bill_number = CAST(v.number AS INTEGER)
                ON CONFLICT DO NOTHING
                """
            },
            'cosponsors': {
                'table': 'congress.bill_cosponsors',
                'transform': self.transform_bill_cosponsor,
                'endpoint_suffix': 'cosponsors',
                'data_key': 'cosponsors',
                'insert_query': """
                INSERT INTO congress.bill_cosponsors
                (bill_id, bioguide_id, cosponsored_date, is_original_cosponsor, created_at)
                SELECT b.bill_id, v.bioguide_id, v.sponsorship_date, v.is_original, v.created_at
                FROM (VALUES %s) AS v(congress, type, number, bioguide_id, sponsorship_date, is_original, created_at)
                JOIN congress.bills b ON b.congress_number = CAST(v.congress AS INTEGER) AND b.bill_type = v.type AND b.bill_number = CAST(v.number AS INTEGER)
                ON CONFLICT (bill_id, bioguide_id) DO UPDATE SET
                    cosponsored_date = EXCLUDED.cosponsored_date,
                    is_original_cosponsor = EXCLUDED.is_original_cosponsor,
                    updated_at = now()
                """
            },
            'subjects': {
                'table': 'congress.bill_subjects',
                'transform': self.transform_bill_subject,
                'endpoint_suffix': 'subjects',
                'data_key': 'subjects',
                'insert_query': """
                INSERT INTO congress.bill_subjects
                (bill_id, subject_term, created_at)
                SELECT b.bill_id, v.subject_name, v.created_at
                FROM (VALUES %s) AS v(congress, type, number, subject_name, created_at)
                JOIN congress.bills b ON b.congress_number = CAST(v.congress AS INTEGER) AND b.bill_type = v.type AND b.bill_number = CAST(v.number AS INTEGER)
                ON CONFLICT (bill_id, subject_term) DO NOTHING
                """
            },
            'titles': {
                'table': 'congress.bill_titles',
                'transform': self.transform_bill_title,
                'endpoint_suffix': 'titles',
                'data_key': 'titles',
                'insert_query': """
                INSERT INTO congress.bill_titles
                (bill_id, title, title_type, created_at)
                SELECT b.bill_id, v.title, v.title_type, v.created_at
                FROM (VALUES %s) AS v(congress, type, number, title, title_type, title_type_code, created_at)
                JOIN congress.bills b ON b.congress_number = CAST(v.congress AS INTEGER) AND b.bill_type = v.type AND b.bill_number = CAST(v.number AS INTEGER)
                ON CONFLICT DO NOTHING
                """
            },
            'related': {
                'table': 'congress.related_bills',
                'transform': self.transform_related_bill,
                'endpoint_suffix': 'relatedbills',
                'data_key': 'relatedBills',
                'insert_query': """
                INSERT INTO congress.related_bills
                (bill_id, related_bill_type, related_bill_number, related_congress, relationship_type, created_at)
                SELECT b.bill_id, v.rel_type, CAST(v.rel_number AS INTEGER), CAST(v.rel_congress AS INTEGER), v.relationship, v.created_at
                FROM (VALUES %s) AS v(congress, type, number, rel_congress, rel_type, rel_number, relationship, identified_by, created_at)
                JOIN congress.bills b ON b.congress_number = CAST(v.congress AS INTEGER) AND b.bill_type = v.type AND b.bill_number = CAST(v.number AS INTEGER)
                ON CONFLICT (bill_id, related_bill_type, related_bill_number, related_congress) DO NOTHING
                """
            }
        }

        cfg = config.get(detail_type)
        if not cfg:
            print(f"❌ Unknown detail type: {detail_type}")
            return

        offset = 0
        total_processed = 0

        # Iterate over bills to fetch details
        # This is inefficient but necessary if no bulk endpoint exists.
        # We can optimize by fetching bills from DB first to get the list.

        # Fetch bills from DB to iterate
        cursor = self.conn.cursor()
        cursor.execute("SELECT bill_type, bill_number FROM congress.bills WHERE congress_number = %s", (congress,))
        bills_to_process = cursor.fetchall()
        cursor.close()

        print(f"  Found {len(bills_to_process)} bills to process for {detail_type}")

        for bill_type, bill_number in bills_to_process:
            url = f"/bill/{congress}/{bill_type.lower()}/{bill_number}/{cfg['endpoint_suffix']}"
            data = self.get(url)

            if data and data.get(cfg['data_key']):
                items = []
                for item in data[cfg['data_key']]:
                    # Pass extra args if needed by transform
                    if detail_type == 'actions':
                        items.append(cfg['transform'](item, congress, bill_type, bill_number))
                    elif detail_type == 'cosponsors':
                        items.append(cfg['transform'](item, congress, bill_type, bill_number))
                    elif detail_type == 'subjects':
                         # API returns 'subjects': {'legislativeSubjects': [...], 'policyArea': ...}
                         # or just list? Check API.
                         # Assuming list for now based on transform.
                         # If nested, we need to adjust.
                         # transform_bill_subject expects item.
                         if 'legislativeSubjects' in item: # Handle nested structure if present
                             for sub in item['legislativeSubjects']:
                                 items.append(cfg['transform'](sub, congress, bill_type, bill_number))
                         else:
                             items.append(cfg['transform'](item, congress, bill_type, bill_number))
                    elif detail_type == 'titles':
                        items.append(cfg['transform'](item, congress, bill_type, bill_number))
                    elif detail_type == 'related':
                        items.append(cfg['transform'](item, congress, bill_type, bill_number))

                if items:
                    if self.dry_run:
                        print(f"🔍 DRY RUN: Would insert {len(items)} {detail_type} for {bill_type}{bill_number}")
                        total_processed += len(items)
                    else:
                        cursor = self.conn.cursor()
                        try:
                            from psycopg2.extras import execute_values
                            execute_values(cursor, cfg['insert_query'], items)
                            self.conn.commit()
                            total_processed += len(items)
                            # print(f"✅ Processed {len(items)} {detail_type} for {bill_type}{bill_number}")
                        except Exception as e:
                            print(f"❌ Batch insert failed for {bill_type}{bill_number}: {e}")
                            self.conn.rollback()
                        finally:
                            cursor.close()

            time.sleep(0.1) # Rate limit

        self.close_db()
        print(f"🎉 Completed: {total_processed} Congress {detail_type}")


    def ingest_committee_members(self, congress: int):
        """Ingest committee members for all committees"""
        print(f"🚀 Starting committee members ingestion for Congress {congress}")

        if not self.connect_db():
            return

        # Ensure table exists and has unique constraint for upsert
        create_table_query = """
        CREATE TABLE IF NOT EXISTS congress.committee_members (
            committee_member_id  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            committee_id         text NOT NULL,
            bioguide_id          text,
            chamber_code         text,
            congress_number      integer,
            rank_in_committee    integer,
            title                text,
            created_at           timestamptz NOT NULL DEFAULT now(),
            updated_at           timestamptz NOT NULL DEFAULT now()
        );
        CREATE UNIQUE INDEX IF NOT EXISTS idx_committee_members_unique
        ON congress.committee_members (committee_id, bioguide_id) WHERE bioguide_id IS NOT NULL;
        """

        if not self.dry_run:
            cursor = self.conn.cursor()
            cursor.execute(create_table_query)
            self.conn.commit()
            cursor.close()

        # Get all committees for this congress
        cursor = self.conn.cursor()
        cursor.execute("SELECT committee_id, chamber_code FROM congress.committees")
        committees = cursor.fetchall()
        cursor.close()

        print(f"📋 Found {len(committees)} committees to process")

        total_processed = 0
        for committee_id, chamber_code in committees:
            # Extract committee code from committee_id (format: hsag00 -> ag)
            code = committee_id
            if code.startswith('hs') or code.startswith('ss') or code.startswith('js'):
                code = code[2:]
            if code.endswith('00'):
                code = code[:-2]

            endpoint = f"/committee/{congress}/{chamber_code.lower()}/{code}"
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
                (committee_id, bioguide_id, chamber_code, congress_number, rank_in_committee, title, created_at)
                VALUES %s
                ON CONFLICT (committee_id, bioguide_id) WHERE bioguide_id IS NOT NULL
                DO UPDATE SET
                    chamber_code = EXCLUDED.chamber_code,
                    congress_number = EXCLUDED.congress_number,
                    rank_in_committee = EXCLUDED.rank_in_committee,
                    title = EXCLUDED.title,
                    updated_at = now()
                """

                if self.dry_run:
                    print(f"🔍 DRY RUN: {committee_id} - {len(members)} members")
                    total_processed += len(members)
                else:
                    cursor = self.conn.cursor()
                    try:
                        from psycopg2.extras import execute_values
                        execute_values(cursor, query, members)
                        self.conn.commit()
                        total_processed += len(members)
                    except Exception as e:
                        print(f"❌ {committee_id}: {e}")
                        self.conn.rollback()
                    finally:
                        cursor.close()

            time.sleep(0.1)

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

    # Ingest Bill Details
    details_parser = subparsers.add_parser('ingest-bill-details', help='Ingest bill details (actions, cosponsors, etc)')
    details_parser.add_argument('congress', type=int, help='Congress number')
    details_parser.add_argument('type', choices=['actions', 'cosponsors', 'subjects', 'titles', 'related'], help='Type of detail to ingest')

    args = parser.parse_args()

    api_key = os.getenv('CONGRESS_GOV_API_KEY') or os.getenv('CONGRESS_API_KEY')
    if not api_key:
        print("❌ CONGRESS_GOV_API_KEY or CONGRESS_API_KEY environment variable required")
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
        cli.ingest_bill_details(args.congress, 'actions')
    elif args.command == 'ingest-bill-cosponsors':
        cli.ingest_bill_details(args.congress, 'cosponsors')
    elif args.command == 'ingest-bill-subjects':
        cli.ingest_bill_details(args.congress, 'subjects')
    elif args.command == 'ingest-bill-titles':
        cli.ingest_bill_details(args.congress, 'titles')
    elif args.command == 'ingest-related-bills':
        cli.ingest_bill_details(args.congress, 'related')
    elif args.command == 'ingest-committee-members':
        cli.ingest_committee_members(args.congress)
    elif args.command == 'ingest-bill-details':
        cli.ingest_bill_details(args.congress, args.type)
    elif args.command == 'status':
        cli.status()

if __name__ == "__main__":
    main()
