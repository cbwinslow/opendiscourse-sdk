#!/usr/bin/env python3
"""
Bulk Ingest Votes - Comprehensive Voting Data Ingestion
Raw API endpoint functions for bulk ingesting voting information

Usage:
    python bulk_ingest_votes.py congress 118 year 2020
    python bulk_ingest_votes.py openstates ca year 2023
    python bulk_ingest_votes.py govinfo BILLS year 2022
"""

import sys
import os
import json
import time
import requests
import psycopg2
import psycopg2.pool
from datetime import datetime
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add project root to path
sys.path.append('/home/cbwinslow/Videos/opendiscourse')

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

class VoteIngestionAPI:
    """Raw API endpoint functions for voting data ingestion"""

    def __init__(self):
        self.base_path = "/home/cbwinslow/Videos/opendiscourse"
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

    def _get_api_headers(self, source: str) -> Dict[str, str]:
        """Get API headers with authentication"""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "OpenDiscourse/VoteIngestion/1.0"
        }

        if source == "congress":
            headers["X-API-Key"] = os.getenv('CONGRESS_API_KEY')
        elif source == "openstates":
            headers["X-API-Key"] = os.getenv('OPENSTATES_API_KEY')
        elif source == "govinfo":
            headers["X-API-Key"] = os.getenv('GOVINFO_API_KEY')

        return headers

    def _make_api_request(self, url: str, params: Dict[str, Any], source: str) -> Optional[Dict[str, Any]]:
        """Make raw API request with retry logic"""
        max_retries = 3
        retry_delay = 2

        for attempt in range(max_retries):
            try:
                headers = self._get_api_headers(source)
                response = requests.get(url, params=params, headers=headers, timeout=30)

                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:  # Rate limited
                    retry_after = int(response.headers.get('Retry-After', 5))
                    print(f"🔄 Rate limited, retrying after {retry_after} seconds")
                    time.sleep(retry_after)
                else:
                    print(f"❌ API request failed: {response.status_code} - {response.text}")
                    return None

            except Exception as e:
                print(f"❌ API request error (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)

        return None

    def _save_to_database(self, table: str, data: List[Dict[str, Any]]) -> int:
        """Save voting data to database with transaction management"""
        if not self.db_pool:
            print("❌ Database pool not available")
            return 0

        try:
            conn = self.db_pool.getconn()
            cursor = conn.cursor()

            # Create table if not exists
            if table == "congress_votes":
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS congress_votes (
                        vote_id VARCHAR(100) PRIMARY KEY,
                        congress INT,
                        session INT,
                        bill_type VARCHAR(20),
                        bill_number VARCHAR(20),
                        vote_date TIMESTAMP,
                        vote_type VARCHAR(50),
                        result VARCHAR(50),
                        democratic_yes INT,
                        democratic_no INT,
                        democratic_present INT,
                        republican_yes INT,
                        republican_no INT,
                        republican_present INT,
                        independent_yes INT,
                        independent_no INT,
                        independent_present INT,
                        total_yes INT,
                        total_no INT,
                        total_present INT,
                        raw_data JSONB,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

            elif table == "openstates_votes":
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS openstates_votes (
                        vote_id VARCHAR(100) PRIMARY KEY,
                        jurisdiction VARCHAR(10),
                        session VARCHAR(20),
                        bill_id VARCHAR(100),
                        motion TEXT,
                        vote_date TIMESTAMP,
                        result VARCHAR(50),
                        yes_count INT,
                        no_count INT,
                        other_count INT,
                        raw_data JSONB,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

            elif table == "govinfo_votes":
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS govinfo_votes (
                        vote_id VARCHAR(100) PRIMARY KEY,
                        collection VARCHAR(50),
                        document_number VARCHAR(100),
                        vote_date TIMESTAMP,
                        vote_type VARCHAR(50),
                        result VARCHAR(50),
                        yea_count INT,
                        nay_count INT,
                        present_count INT,
                        not_voting_count INT,
                        raw_data JSONB,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

            # Insert data with conflict handling
            for record in data:
                if table == "congress_votes":
                    cursor.execute("""
                        INSERT INTO congress.votes (
                            congress_number, session_number, roll_call_number, question,
                            result, date, positions
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (congress_number, session_number, roll_call_number) DO NOTHING
                    """, (
                        record.get('congress'), record.get('session'), record.get('roll_call_number'),
                        record.get('question'), record.get('result'), record.get('date'),
                        json.dumps(record)
                    ))

                elif table == "openstates_votes":
                    cursor.execute("""
                        INSERT INTO openstates_votes (
                            vote_id, jurisdiction, session, bill_id, motion,
                            vote_date, result, yes_count, no_count, other_count, raw_data
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (vote_id) DO NOTHING
                    """, (
                        record.get('vote_id'), record.get('jurisdiction'), record.get('session'),
                        record.get('bill_id'), record.get('motion'),
                        record.get('vote_date'), record.get('result'),
                        record.get('yes_count'), record.get('no_count'),
                        record.get('other_count'), json.dumps(record)
                    ))

                elif table == "govinfo_votes":
                    cursor.execute("""
                        INSERT INTO govinfo_votes (
                            vote_id, collection, document_number, vote_date, vote_type,
                            result, yea_count, nay_count, present_count, not_voting_count, raw_data
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (vote_id) DO NOTHING
                    """, (
                        record.get('vote_id'), record.get('collection'), record.get('document_number'),
                        record.get('vote_date'), record.get('vote_type'), record.get('result'),
                        record.get('yea_count'), record.get('nay_count'),
                        record.get('present_count'), record.get('not_voting_count'),
                        json.dumps(record)
                    ))

            conn.commit()
            cursor.close()
            self.db_pool.putconn(conn)

            return len(data)

        except Exception as e:
            print(f"❌ Database save error: {e}")
            if conn:
                conn.rollback()
                self.db_pool.putconn(conn)
            return 0

    def ingest_congress_votes(self, congress: int, year: int, offset: int = 0, limit: int = 1000) -> int:
        """Bulk ingest Congress votes for specific congress and year"""
        print(f"📊 Ingesting Congress votes: Congress {congress}, Year {year}")

        base_url = "https://api.congress.gov/v3"
        endpoint = "/house-vote"  # Correct endpoint for House votes

        params = {
            "congress": congress,
            "limit": limit,
            "offset": offset,
            "year": year,
            "format": "json"
        }

        all_votes = []
        total_records = 0

        data = self._make_api_request(f"{base_url}{endpoint}", params, "congress")
        print(f"DEBUG: API response: {data}")  # Debug output
        if not data or 'houseRollCallVotes' not in data:
            print("No votes data found in response")
            return 0

        votes = data['houseRollCallVotes']
        print(f"DEBUG: Found {len(votes)} votes")  # Debug output
        if not votes:
            print("No votes found")
            return 0

        # Process votes
        for vote in votes:
            processed_vote = {
                'congress': congress,
                'session': vote.get('congress', congress),
                'roll_call_number': vote.get('rollCallNumber'),
                'question': vote.get('description') or vote.get('voteType'),
                'result': vote.get('result'),
                'date': vote.get('date')
            }
            all_votes.append(processed_vote)

        # Save batch to database
        if all_votes:
            saved = self._save_to_database("congress_votes", all_votes)
            total_records += saved
            print(f"📊 Saved {saved} Congress votes (Total: {total_records})")
            all_votes = []

        print(f"✅ Completed Congress votes ingestion: {total_records} records")
        return total_records

    def ingest_openstates_votes(self, jurisdiction: str, year: int, limit: int = 1000) -> int:
        """Bulk ingest OpenStates votes for specific jurisdiction and year"""
        print(f"📊 Ingesting OpenStates votes: {jurisdiction.upper()}, Year {year}")

        base_url = f"https://v3.openstates.org"
        endpoint = f"/votes"

        params = {
            "jurisdiction": jurisdiction,
            "year": year,
            "per_page": limit,
            "page": 1
        }

        all_votes = []
        total_records = 0

        while True:
            data = self._make_api_request(f"{base_url}{endpoint}", params, "openstates")
            if not data or 'results' not in data:
                break

            votes = data['results']
            if not votes:
                break

            # Process votes
            for vote in votes:
                processed_vote = {
                    'vote_id': vote.get('id'),
                    'jurisdiction': jurisdiction,
                    'session': vote.get('session'),
                    'bill_id': vote.get('bill_id'),
                    'motion': vote.get('motion'),
                    'vote_date': vote.get('date'),
                    'result': vote.get('result'),
                    'yes_count': vote.get('yes_count'),
                    'no_count': vote.get('no_count'),
                    'other_count': vote.get('other_count')
                }
                all_votes.append(processed_vote)

            # Save batch to database
            if all_votes:
                saved = self._save_to_database("openstates_votes", all_votes)
                total_records += saved
                print(f"📊 Saved {saved} OpenStates votes (Total: {total_records})")
                all_votes = []

            # Check for more data
            if len(votes) < limit or not data.get('next'):
                break

            params['page'] += 1

        print(f"✅ Completed OpenStates votes ingestion: {total_records} records")
        return total_records

    def ingest_govinfo_votes(self, collection: str, year: int, limit: int = 1000) -> int:
        """Bulk ingest GovInfo votes for specific collection and year"""
        print(f"📊 Ingesting GovInfo votes: {collection}, Year {year}")

        base_url = "https://api.govinfo.gov"
        endpoint = f"/collections/{collection}/votes"

        params = {
            "year": year,
            "pageSize": limit,
            "offset": 0
        }

        all_votes = []
        total_records = 0

        while True:
            data = self._make_api_request(f"{base_url}{endpoint}", params, "govinfo")
            if not data or 'votes' not in data:
                break

            votes = data['votes']
            if not votes:
                break

            # Process votes
            for vote in votes:
                processed_vote = {
                    'vote_id': vote.get('vote_id'),
                    'collection': collection,
                    'document_number': vote.get('document_number'),
                    'vote_date': vote.get('vote_date'),
                    'vote_type': vote.get('vote_type'),
                    'result': vote.get('result'),
                    'yea_count': vote.get('yea_count'),
                    'nay_count': vote.get('nay_count'),
                    'present_count': vote.get('present_count'),
                    'not_voting_count': vote.get('not_voting_count')
                }
                all_votes.append(processed_vote)

            # Save batch to database
            if all_votes:
                saved = self._save_to_database("govinfo_votes", all_votes)
                total_records += saved
                print(f"📊 Saved {saved} GovInfo votes (Total: {total_records})")
                all_votes = []

            # Check for more data
            if len(votes) < limit:
                break

            params['offset'] += limit

        print(f"✅ Completed GovInfo votes ingestion: {total_records} records")
        return total_records

    def bulk_ingest_all_votes(self, source: str, identifier: str, year: int) -> int:
        """Main bulk ingestion function"""
        print(f"🚀 Starting bulk vote ingestion: {source} {identifier} {year}")
        print("=" * 60)

        if source == "congress":
            return self.ingest_congress_votes(int(identifier), year)
        elif source == "openstates":
            return self.ingest_openstates_votes(identifier, year)
        elif source == "govinfo":
            return self.ingest_govinfo_votes(identifier, year)
        else:
            print(f"❌ Unknown source: {source}")
            return 0

def main():
    """Main entry point"""
    if len(sys.argv) != 4:
        print("Usage: python bulk_ingest_votes.py <source> <identifier> <year>")
        print("Examples:")
        print("  python bulk_ingest_votes.py congress 118 2020")
        print("  python bulk_ingest_votes.py openstates ca 2023")
        print("  python bulk_ingest_votes.py govinfo BILLS 2022")
        return

    source = sys.argv[1]
    identifier = sys.argv[2]
    year = int(sys.argv[3])

    try:
        ingestion = VoteIngestionAPI()
        total_records = ingestion.bulk_ingest_all_votes(source, identifier, year)

        print("\n" + "=" * 60)
        print(f"🎉 BULK VOTE INGESTION COMPLETE")
        print(f"✅ Source: {source} {identifier}")
        print(f"✅ Year: {year}")
        print(f"✅ Total Records Ingested: {total_records:,}")
        print("=" * 60)

    except KeyboardInterrupt:
        print("\n🛑 Vote ingestion cancelled by user")
    except Exception as e:
        print(f"\n❌ Vote ingestion failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
