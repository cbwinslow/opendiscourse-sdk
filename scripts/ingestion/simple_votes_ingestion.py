#!/usr/bin/env python3
"""
Simple Votes Ingestion Script
Focused on House Clerk XML data for roll call votes
"""

import os
import sys
import json
import time
import logging
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from pathlib import Path
import xml.etree.ElementTree as ET

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

import psycopg2
from psycopg2.extras import execute_values, DictCursor
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("votes_ingestion.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


@dataclass
class VotesIngestionConfig:
    """Configuration for votes ingestion"""

    database_url: str
    congress_api_key: str
    govinfo_api_key: str

    # Ingestion parameters
    batch_size: int = 100
    max_retries: int = 3
    retry_delay: float = 1.0
    request_timeout: int = 30

    # Source priorities
    sources: List[str] = None

    def __post_init__(self):
        if self.sources is None:
            self.sources = ["house-clerk"]


class SimpleVotesIngestor:
    """Simple votes ingestion system using House Clerk data"""

    def __init__(self, config: VotesIngestionConfig):
        self.config = config
        self.db_conn = None
        self.session = self._create_session()

        # Statistics
        self.stats = {
            "total_processed": 0,
            "successful": 0,
            "failed": 0,
            "duplicates": 0,
            "by_source": {source: 0 for source in config.sources},
            "start_time": None,
            "end_time": None,
        }

    def _create_session(self) -> requests.Session:
        """Create HTTP session with retry strategy"""
        session = requests.Session()

        retry_strategy = Retry(
            total=self.config.max_retries,
            backoff_factor=self.config.retry_delay,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"],
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    def connect_database(self):
        """Connect to PostgreSQL database"""
        try:
            self.db_conn = psycopg2.connect(
                host="/var/run/postgresql", user="cbwinslow", database="opendiscourse"
            )
            self.db_conn.autocommit = False
            logger.info("Database connection established")
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise

    def close_database(self):
        """Close database connection"""
        if self.db_conn:
            self.db_conn.close()
            logger.info("Database connection closed")

    def create_tables(self):
        """Create necessary tables if they don't exist"""
        with self.db_conn.cursor() as cursor:
            # Roll call votes table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS congress.roll_call_votes_bulk (
                    vote_id VARCHAR(50) PRIMARY KEY,
                    congress_number INTEGER,
                    session INTEGER,
                    chamber VARCHAR(20),
                    roll_call_number INTEGER,
                    vote_date DATE,
                    vote_time TIME,
                    vote_question TEXT,
                    vote_description TEXT,
                    vote_type VARCHAR(50),
                    vote_result VARCHAR(50),
                    yeas INTEGER,
                    nays INTEGER,
                    present INTEGER,
                    not_voting INTEGER,
                    democratic_position VARCHAR(20),
                    republican_position VARCHAR(20),
                    bill_id VARCHAR(50),
                    amendment_number VARCHAR(20),
                    nomination_number VARCHAR(20),
                    source VARCHAR(20),
                    raw_data JSONB,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                );
                
                CREATE INDEX IF NOT EXISTS idx_roll_call_votes_congress ON congress.roll_call_votes_bulk(congress_number);
                CREATE INDEX IF NOT EXISTS idx_roll_call_votes_date ON congress.roll_call_votes_bulk(vote_date);
                CREATE INDEX IF NOT EXISTS idx_roll_call_votes_chamber ON congress.roll_call_votes_bulk(chamber);
                CREATE INDEX IF NOT EXISTS idx_roll_call_votes_bill ON congress.roll_call_votes_bulk(bill_id);
                CREATE INDEX IF NOT EXISTS idx_roll_call_votes_source ON congress.roll_call_votes_bulk(source);
            """)

            # Vote positions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS congress.vote_positions_bulk (
                    id SERIAL PRIMARY KEY,
                    vote_id VARCHAR(50),
                    member_bioguide_id VARCHAR(20),
                    member_name VARCHAR(200),
                    member_party VARCHAR(20),
                    member_state VARCHAR(10),
                    vote_position VARCHAR(20),
                    vote_reason TEXT,
                    created_at TIMESTAMP DEFAULT NOW(),
                    FOREIGN KEY (vote_id) REFERENCES congress.roll_call_votes_bulk(vote_id)
                );
                
                CREATE INDEX IF NOT EXISTS idx_vote_positions_vote ON congress.vote_positions_bulk(vote_id);
                CREATE INDEX IF NOT EXISTS idx_vote_positions_member ON congress.vote_positions_bulk(member_bioguide_id);
                CREATE INDEX IF NOT EXISTS idx_vote_positions_position ON congress.vote_positions_bulk(vote_position);
            """)

            # Ingestion tracking
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS congress.votes_ingestion_tracking (
                    id SERIAL PRIMARY KEY,
                    source VARCHAR(50),
                    ingestion_type VARCHAR(50),
                    start_time TIMESTAMP,
                    end_time TIMESTAMP,
                    total_records INTEGER,
                    successful_records INTEGER,
                    failed_records INTEGER,
                    status VARCHAR(20),
                    error_details JSONB,
                    created_at TIMESTAMP DEFAULT NOW()
                );
            """)

            self.db_conn.commit()
            logger.info("Votes tables created/verified")

    def ingest_house_clerk_votes(
        self, congress: int = 118, limit: Optional[int] = None
    ) -> int:
        """Ingest House roll call votes from House Clerk XML data"""
        logger.info(f"Starting House Clerk votes ingestion for Congress {congress}")

        ingested_count = 0
        year = 2024  # Current session year

        # Get recent roll call votes from House Clerk
        base_url = "http://clerk.house.gov/cgi-bin/vote.asp"

        # Start from most recent and work backwards
        roll_number = 600  # Start with a high number and work down

        while ingested_count < (limit or 1000) and roll_number > 0:
            try:
                url = f"{base_url}?year={year}&rollnumber={roll_number}"

                response = self.session.get(url, timeout=self.config.request_timeout)
                response.raise_for_status()

                # Parse XML response
                root = ET.fromstring(response.text)

                # Extract vote metadata
                vote_metadata = root.find("vote-metadata")
                if vote_metadata is None:
                    roll_number -= 1
                    continue

                congress_num = int(vote_metadata.find("congress").text)
                if congress_num != congress:
                    roll_number -= 1
                    continue

                chamber = vote_metadata.find("chamber").text
                roll_call_num = int(vote_metadata.find("rollcall-num").text)
                vote_question = vote_metadata.find("vote-question").text
                vote_result = vote_metadata.find("vote-result").text
                action_date = self._parse_date(vote_metadata.find("action-date").text)
                action_time = self._parse_time(vote_metadata.find("action-time").text)
                vote_desc = vote_metadata.find("vote-desc").text

                # Extract vote totals
                vote_totals = vote_metadata.find("vote-totals")
                yeas = int(vote_totals.find("totals-by-vote/yea-total").text)
                nays = int(vote_totals.find("totals-by-vote/nay-total").text)
                present = int(vote_totals.find("totals-by-vote/present-total").text)
                not_voting = int(
                    vote_totals.find("totals-by-vote/not-voting-total").text
                )

                # Extract party positions
                democratic_position = None
                republican_position = None
                for party_total in vote_totals.findall("totals-by-party"):
                    party = party_total.find("party").text
                    if party == "Democratic":
                        democratic_position = (
                            party_total.find("yea-total").text
                            > party_total.find("nay-total").text
                        )
                    elif party == "Republican":
                        republican_position = (
                            party_total.find("yea-total").text
                            > party_total.find("nay-total").text
                        )

                # Extract bill info
                legis_num = vote_metadata.find("legis-num").text
                if legis_num:
                    # Parse bill number (e.g., "H R 10545" -> HR10545)
                    parts = legis_num.split()
                    if len(parts) >= 2:
                        bill_type = parts[0]
                        bill_number_str = parts[1]
                        try:
                            bill_number = int(bill_number_str)
                        except ValueError:
                            bill_number = None
                    else:
                        bill_type = None
                        bill_number = None
                else:
                    bill_type = None
                    bill_number = None

                # Create vote data
                vote_data = {
                    "vote_id": f"{congress}-house-{roll_call_num}",
                    "congress_number": congress,
                    "session": None,  # House Clerk doesn't provide session
                    "chamber": "House",
                    "roll_call_number": roll_call_num,
                    "vote_date": action_date,
                    "vote_time": action_time,
                    "vote_question": vote_question,
                    "vote_description": vote_desc,
                    "vote_type": "Roll Call Vote",
                    "vote_result": vote_result,
                    "yeas": yeas,
                    "nays": nays,
                    "present": present,
                    "not_voting": not_voting,
                    "democratic_position": "Yea" if democratic_position else "Nay",
                    "republican_position": "Yea" if republican_position else "Nay",
                    "bill_id": f"{bill_type}{bill_number}-{congress}"
                    if bill_type and bill_number
                    else None,
                    "amendment_number": None,
                    "nomination_number": None,
                    "source": "house-clerk",
                    "raw_data": response.text,
                }

                # Extract vote positions
                position_data = []
                vote_data_elem = root.find("vote-data")
                if vote_data_elem is not None:
                    for recorded_vote in vote_data_elem.findall("recorded-vote"):
                        legislator_elem = recorded_vote.find("legislator")
                        if legislator_elem is not None:
                            name_id = legislator_elem.get("name-id")
                            member_name = legislator_elem.get("unaccented-name")
                            party = legislator_elem.get("party")
                            state = legislator_elem.get("state")
                            vote_position = recorded_vote.find("vote").text

                            position_data.append(
                                {
                                    "vote_id": vote_data["vote_id"],
                                    "member_bioguide_id": name_id,
                                    "member_name": member_name,
                                    "member_party": party,
                                    "member_state": state,
                                    "vote_position": vote_position,
                                    "vote_reason": None,
                                }
                            )

                # Insert batch
                self._insert_votes_batch([vote_data], position_data, "house-clerk")
                ingested_count += 1

                logger.info(f"House Clerk: Processed roll call {roll_call_num}")

                # Rate limiting
                time.sleep(0.2)

                roll_number -= 1

            except Exception as e:
                logger.error(
                    f"Error processing House Clerk roll call {roll_number}: {e}"
                )
                roll_number -= 1
                continue

        self.stats["by_source"]["house-clerk"] = ingested_count
        logger.info(f"House Clerk votes ingestion completed: {ingested_count} votes")
        return ingested_count

    def _insert_votes_batch(
        self, votes: List[Dict], positions: List[Dict], source: str
    ):
        """Insert batch of votes and positions into database"""
        if not votes:
            return

        try:
            with self.db_conn.cursor() as cursor:
                # Insert votes
                vote_values = []
                for vote in votes:
                    vote_values.append(
                        (
                            vote.get("vote_id"),
                            vote.get("congress_number"),
                            vote.get("session"),
                            vote.get("chamber"),
                            vote.get("roll_call_number"),
                            vote.get("vote_date"),
                            vote.get("vote_time"),
                            vote.get("vote_question"),
                            vote.get("vote_description"),
                            vote.get("vote_type"),
                            vote.get("vote_result"),
                            vote.get("yeas"),
                            vote.get("nays"),
                            vote.get("present"),
                            vote.get("not_voting"),
                            vote.get("democratic_position"),
                            vote.get("republican_position"),
                            vote.get("bill_id"),
                            vote.get("amendment_number"),
                            vote.get("nomination_number"),
                            source,
                            json.dumps(vote.get("raw_data")),
                        )
                    )

                # Insert votes with ON CONFLICT handling
                vote_query = """
                    INSERT INTO congress.roll_call_votes_bulk (
                        vote_id, congress_number, session, chamber, roll_call_number,
                        vote_date, vote_time, vote_question, vote_description,
                        vote_type, vote_result, yeas, nays, present, not_voting,
                        democratic_position, republican_position, bill_id,
                        amendment_number, nomination_number, source, raw_data
                    ) VALUES %s
                    ON CONFLICT (vote_id) DO UPDATE SET
                        vote_description = EXCLUDED.vote_description,
                        vote_result = EXCLUDED.vote_result,
                        yeas = EXCLUDED.yeas,
                        nays = EXCLUDED.nays,
                        present = EXCLUDED.present,
                        not_voting = EXCLUDED.not_voting,
                        democratic_position = EXCLUDED.democratic_position,
                        republican_position = EXCLUDED.republican_position,
                        raw_data = EXCLUDED.raw_data,
                        updated_at = NOW()
                """

                execute_values(cursor, vote_query, vote_values)

                # Insert positions
                if positions:
                    position_values = []
                    for position in positions:
                        position_values.append(
                            (
                                position.get("vote_id"),
                                position.get("member_bioguide_id"),
                                position.get("member_name"),
                                position.get("member_party"),
                                position.get("member_state"),
                                position.get("vote_position"),
                                position.get("vote_reason"),
                            )
                        )

                    position_query = """
                        INSERT INTO congress.vote_positions_bulk (
                            vote_id, member_bioguide_id, member_name,
                            member_party, member_state, vote_position, vote_reason
                        ) VALUES %s
                        ON CONFLICT DO NOTHING
                    """

                    execute_values(cursor, position_query, position_values)

                self.db_conn.commit()

                self.stats["successful"] += len(votes)
                logger.info(
                    f"Inserted {len(votes)} votes and {len(positions)} positions from {source}"
                )

        except Exception as e:
            self.db_conn.rollback()
            self.stats["failed"] += len(votes)
            logger.error(f"Error inserting vote batch from {source}: {e}")
            raise

    def _parse_date(self, date_str):
        """Parse date string to datetime object"""
        if not date_str:
            return None

        try:
            # Try different date formats
            formats = [
                "%d-%b-%Y",  # e.g., "20-Dec-2024"
                "%Y-%m-%d",
                "%Y-%m-%dT%H:%M:%S%z",
                "%Y-%m-%dT%H:%M:%SZ",
                "%Y-%m-%dT%H:%M:%S",
                "%m/%d/%Y",
                "%Y-%m-%d %H:%M:%S",
            ]

            for fmt in formats:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue

            logger.warning(f"Could not parse date: {date_str}")
            return None

        except Exception as e:
            logger.error(f"Error parsing date {date_str}: {e}")
            return None

    def _parse_time(self, time_str):
        """Parse time string to time object"""
        if not time_str:
            return None

        try:
            formats = [
                "%I:%M %p",  # e.g., "5:59 PM"
                "%H:%M:%S",
                "%I:%M:%S %p",
            ]

            for fmt in formats:
                try:
                    return datetime.strptime(time_str, fmt).time()
                except ValueError:
                    continue

            logger.warning(f"Could not parse time: {time_str}")
            return None

        except Exception as e:
            logger.error(f"Error parsing time {time_str}: {e}")
            return None

    def run_ingestion(
        self, sources: Optional[List[str]] = None, **kwargs
    ) -> Dict[str, Any]:
        """Run complete votes ingestion process"""
        self.stats["start_time"] = datetime.now()

        try:
            self.connect_database()
            self.create_tables()

            sources_to_process = sources or self.config.sources

            for source in sources_to_process:
                logger.info(f"Starting votes ingestion from {source}")

                try:
                    if source == "house-clerk":
                        congress = kwargs.get("congress", 118)
                        limit = kwargs.get("limit")
                        self.ingest_house_clerk_votes(congress, limit)

                    else:
                        logger.warning(f"Unknown source: {source}")

                except Exception as e:
                    logger.error(f"Error in {source} votes ingestion: {e}")
                    continue

            self.stats["end_time"] = datetime.now()
            self.stats["total_processed"] = (
                self.stats["successful"] + self.stats["failed"]
            )

            # Record ingestion tracking
            self._record_ingestion_tracking()

            return self.stats

        finally:
            self.close_database()

    def _record_ingestion_tracking(self):
        """Record votes ingestion statistics"""
        try:
            with self.db_conn.cursor() as cursor:
                query = """
                    INSERT INTO congress.votes_ingestion_tracking (
                        source, ingestion_type, start_time, end_time,
                        total_records, successful_records, failed_records, status
                    ) VALUES (%s, %s, %s, %s, %s, %s)
                """

                cursor.execute(
                    query,
                    (
                        "bulk_votes",
                        "bulk_ingestion",
                        self.stats["start_time"],
                        self.stats["end_time"],
                        self.stats["total_processed"],
                        self.stats["successful"],
                        self.stats["failed"],
                        "completed"
                        if self.stats["failed"] == 0
                        else "completed_with_errors",
                    ),
                )

                self.db_conn.commit()

        except Exception as e:
            logger.error(f"Error recording votes ingestion tracking: {e}")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Simple Votes Ingestion")
    parser.add_argument("--congress", type=int, default=118, help="Congress number")
    parser.add_argument("--limit", type=int, help="Limit number of votes to ingest")
    parser.add_argument(
        "--sources", nargs="+", choices=["house-clerk"], help="Sources to ingest from"
    )
    parser.add_argument("--batch-size", type=int, default=10, help="Batch size")
    parser.add_argument(
        "--dry-run", action="store_true", help="Dry run (no database changes)"
    )

    args = parser.parse_args()

    # Load configuration
    config = VotesIngestionConfig(
        database_url=os.getenv(
            "DATABASE_URL", "postgresql://cbwinslow@/var/run/postgresql/opendiscourse"
        ),
        congress_api_key=os.getenv("CONGRESS_API_KEY", "dummy"),
        govinfo_api_key=os.getenv("GOVINFO_API_KEY", "dummy"),
        batch_size=args.batch_size,
    )

    # Run ingestion
    ingestor = SimpleVotesIngestor(config)

    try:
        stats = ingestor.run_ingestion(
            sources=args.sources, congress=args.congress, limit=args.limit
        )

        # Print summary
        print("\n" + "=" * 50)
        print("SIMPLE VOTES INGESTION SUMMARY")
        print("=" * 50)
        print(f"Start Time: {stats['start_time']}")
        print(f"End Time: {stats['end_time']}")
        print(f"Duration: {stats['end_time'] - stats['start_time']}")
        print(f"Total Processed: {stats['total_processed']}")
        print(f"Successful: {stats['successful']}")
        print(f"Failed: {stats['failed']}")
        print(f"Duplicates: {stats['duplicates']}")
        print("\nBy Source:")
        for source, count in stats["by_source"].items():
            print(f"  {source}: {count}")
        print("=" * 50)

    except Exception as e:
        logger.error(f"Votes ingestion failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
