#!/usr/bin/env python3
"""
Bulk Votes Ingestion Script
Comprehensive ingestion of congressional roll call votes from multiple sources
"""

import os
import sys
import json
import time
import logging
import asyncio
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

import psycopg2
from psycopg2.extras import execute_values, DictCursor
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import pandas as pd
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
            self.sources = ["congress", "govinfo"]


class BulkVotesIngestor:
    """Comprehensive votes ingestion system"""

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
            self.db_conn = psycopg2.connect(self.config.database_url)
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

    def ingest_congress_votes(
        self, congress: int = 118, chamber: str = "both", limit: Optional[int] = None
    ) -> int:
        """Ingest roll call votes from Congress.gov API"""
        logger.info(
            f"Starting Congress.gov votes ingestion for Congress {congress}, chamber: {chamber}"
        )

        base_url = "https://api.congress.gov/v3"
        headers = {
            "X-API-Key": self.config.congress_api_key,
            "Accept": "application/json",
        }

        ingested_count = 0

        chambers = ["house", "senate"] if chamber == "both" else [chamber]

        for ch in chambers:
            offset = 0

            while True:
                try:
                    # Get votes list
                    url = f"{base_url}/roll-call-votes/{congress}/{ch}"
                    params = {
                        "limit": min(self.config.batch_size, 250),  # API limit
                        "offset": offset,
                    }

                    response = self.session.get(
                        url,
                        headers=headers,
                        params=params,
                        timeout=self.config.request_timeout,
                    )
                    response.raise_for_status()

                    data = response.json()
                    votes = data.get("rollCallVotes", [])

                    if not votes:
                        break

                    # Process votes in batch
                    batch_data = []
                    position_data = []

                    for vote in votes:
                        vote_data, positions = self._process_congress_vote(
                            vote, congress, ch
                        )
                        if vote_data:
                            batch_data.append(vote_data)
                            position_data.extend(positions)

                    # Insert batch
                    if batch_data:
                        self._insert_votes_batch(batch_data, position_data, "congress")
                        ingested_count += len(batch_data)
                        logger.info(
                            f"Congress.gov {ch}: Processed {ingested_count} votes"
                        )

                    # Check limits
                    if limit and ingested_count >= limit:
                        break

                    # Check pagination
                    pagination = data.get("pagination", {})
                    if offset >= pagination.get("count", 0):
                        break

                    offset += len(votes)

                    # Rate limiting
                    time.sleep(0.1)

                except Exception as e:
                    logger.error(f"Error in Congress.gov {ch} votes ingestion: {e}")
                    break

        self.stats["by_source"]["congress"] = ingested_count
        logger.info(f"Congress.gov votes ingestion completed: {ingested_count} votes")
        return ingested_count

    def ingest_govinfo_votes(
        self, collection: str = "CRPT", limit: Optional[int] = None
    ) -> int:
        """Ingest votes from GovInfo API (Congressional Record)"""
        logger.info(f"Starting GovInfo votes ingestion for collection {collection}")

        base_url = "https://api.govinfo.gov"
        headers = {
            "X-Api-Key": self.config.govinfo_api_key,
            "Accept": "application/json",
        }

        ingested_count = 0

        try:
            # Get collection items for recent Congressional Record
            current_year = datetime.now().year
            url = f"{base_url}/collections/{collection}/{current_year}"

            params = {"pageSize": min(self.config.batch_size, 100), "offset": 0}

            response = self.session.get(
                url, headers=headers, params=params, timeout=self.config.request_timeout
            )
            response.raise_for_status()

            data = response.json()
            packages = data.get("packages", [])

            for package in packages[:limit] if limit else packages:
                try:
                    # Check if this package contains roll call votes
                    package_id = package.get("packageId")
                    if not "crpt" in package_id.lower():
                        continue

                    vote_data, position_data = self._process_govinfo_package(package)
                    if vote_data:
                        self._insert_votes_batch([vote_data], position_data, "govinfo")
                        ingested_count += 1

                        if ingested_count % 10 == 0:
                            logger.info(f"GovInfo: Processed {ingested_count} votes")

                except Exception as e:
                    logger.error(
                        f"Error processing GovInfo package {package.get('packageId')}: {e}"
                    )
                    continue

                # Rate limiting
                time.sleep(0.2)

        except Exception as e:
            logger.error(f"Error in GovInfo votes ingestion: {e}")

        self.stats["by_source"]["govinfo"] = ingested_count
        logger.info(f"GovInfo votes ingestion completed: {ingested_count} votes")
        return ingested_count

    def _process_congress_vote(
        self, vote: Dict, congress: int, chamber: str
    ) -> Tuple[Optional[Dict], List[Dict]]:
        """Process vote from Congress.gov API"""
        try:
            vote_id = vote.get("rollCallNumber")
            if not vote_id:
                return None, []

            # Get detailed vote information
            detail_url = f"https://api.congress.gov/v3/roll-call-votes/{congress}/{chamber}/{vote_id}"
            headers = {
                "X-API-Key": self.config.congress_api_key,
                "Accept": "application/json",
            }

            detail_response = self.session.get(detail_url, headers=headers, timeout=10)
            if detail_response.status_code != 200:
                logger.warning(
                    f"Failed to get vote details for {vote_id}: {detail_response.status_code}"
                )
                return None, []

            detail_data = detail_response.json().get("vote", {})

            # Extract vote information
            vote_date = self._parse_date(detail_data.get("date"))
            vote_time = self._parse_time(detail_data.get("time"))

            # Extract vote counts
            vote_totals = detail_data.get("totals", {})
            yeas = vote_totals.get("yea", {}).get("count", 0)
            nays = vote_totals.get("nay", {}).get("count", 0)
            present = vote_totals.get("present", {}).get("count", 0)
            not_voting = vote_totals.get("not_voting", {}).get("count", 0)

            # Extract bill information
            bill = detail_data.get("bill", {})
            bill_id = None
            if bill:
                bill_type = bill.get("type")
                bill_number = bill.get("number")
                if bill_type and bill_number:
                    bill_id = f"{bill_type}{bill_number}-{congress}"

            # Extract vote positions
            positions = []
            vote_positions = detail_data.get("votePositions", [])

            for position in vote_positions:
                member = position.get("member", {})
                member_bioguide_id = member.get("bioguideId")
                member_name = member.get("fullName")

                # Get member party and state from database
                member_party = None
                member_state = None
                if member_bioguide_id:
                    member_party, member_state = self._get_member_info(
                        member_bioguide_id
                    )

                vote_position = position.get("votePosition")
                vote_reason = position.get("voteExplanation")

                positions.append(
                    {
                        "vote_id": f"{congress}-{chamber}-{vote_id}",
                        "member_bioguide_id": member_bioguide_id,
                        "member_name": member_name,
                        "member_party": member_party,
                        "member_state": member_state,
                        "vote_position": vote_position,
                        "vote_reason": vote_reason,
                    }
                )

            return {
                "vote_id": f"{congress}-{chamber}-{vote_id}",
                "congress_number": congress,
                "session": detail_data.get("congress", congress),
                "chamber": chamber.capitalize(),
                "roll_call_number": vote_id,
                "vote_date": vote_date,
                "vote_time": vote_time,
                "vote_question": detail_data.get("question"),
                "vote_description": detail_data.get("description"),
                "vote_type": detail_data.get("voteType"),
                "vote_result": detail_data.get("result"),
                "yeas": yeas,
                "nays": nays,
                "present": present,
                "not_voting": not_voting,
                "democratic_position": detail_data.get("democraticPosition"),
                "republican_position": detail_data.get("republicanPosition"),
                "bill_id": bill_id,
                "amendment_number": detail_data.get("amendment", {}).get("number"),
                "nomination_number": detail_data.get("nomination", {}).get("number"),
                "source": "congress",
                "raw_data": detail_data,
            }, positions

        except Exception as e:
            logger.error(
                f"Error processing Congress vote {vote.get('rollCallNumber', 'unknown')}: {e}"
            )
            return None, []

    def _process_govinfo_package(
        self, package: Dict
    ) -> Tuple[Optional[Dict], List[Dict]]:
        """Process vote package from GovInfo API"""
        try:
            package_id = package.get("packageId")
            if not package_id:
                return None, []

            # Get detailed package information
            detail_url = f"https://api.govinfo.gov/packages/{package_id}"
            headers = {
                "X-Api-Key": self.config.govinfo_api_key,
                "Accept": "application/json",
            }

            detail_response = self.session.get(detail_url, headers=headers, timeout=10)
            if detail_response.status_code != 200:
                return None, []

            detail_data = detail_response.json()

            # Extract basic information
            title = detail_data.get("title", "")
            date_issued = self._parse_date(detail_data.get("dateIssued"))

            # GovInfo Congressional Record doesn't provide structured vote data
            # This would require parsing the full text content
            # For now, create a basic record

            vote_id = f"govinfo-{package_id}"

            return {
                "vote_id": vote_id,
                "congress_number": None,  # Would need to parse from title
                "session": None,
                "chamber": None,  # Would need to parse from title
                "roll_call_number": None,
                "vote_date": date_issued,
                "vote_time": None,
                "vote_question": title,
                "vote_description": detail_data.get("summary", ""),
                "vote_type": "congressional_record",
                "vote_result": None,
                "yeas": None,
                "nays": None,
                "present": None,
                "not_voting": None,
                "democratic_position": None,
                "republican_position": None,
                "bill_id": None,
                "amendment_number": None,
                "nomination_number": None,
                "source": "govinfo",
                "raw_data": detail_data,
            }, []

        except Exception as e:
            logger.error(
                f"Error processing GovInfo vote package {package.get('packageId', 'unknown')}: {e}"
            )
            return None, []

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

    def _get_member_info(self, bioguide_id: str) -> Tuple[Optional[str], Optional[str]]:
        """Get member party and state from database"""
        try:
            with self.db_conn.cursor(cursor_factory=DictCursor) as cursor:
                query = """
                    SELECT mt.party_code, mt.state
                    FROM congress.member_terms mt
                    WHERE mt.bioguide_id = %s
                    ORDER BY mt.start_date DESC
                    LIMIT 1
                """
                cursor.execute(query, (bioguide_id,))
                result = cursor.fetchone()

                if result:
                    return result["party_code"], result["state"]
                return None, None

        except Exception as e:
            logger.error(f"Error getting member info for {bioguide_id}: {e}")
            return None, None

    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse date string to datetime object"""
        if not date_str:
            return None

        try:
            # Try different date formats
            formats = [
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

    def _parse_time(self, time_str: Optional[str]) -> Optional[datetime.time]:
        """Parse time string to time object"""
        if not time_str:
            return None

        try:
            formats = ["%H:%M:%S", "%I:%M %p", "%H:%M"]

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
                    if source == "congress":
                        congress = kwargs.get("congress", 118)
                        chamber = kwargs.get("chamber", "both")
                        limit = kwargs.get("congress_limit")
                        self.ingest_congress_votes(congress, chamber, limit)

                    elif source == "govinfo":
                        collection = kwargs.get("govinfo_collection", "CRPT")
                        limit = kwargs.get("govinfo_limit")
                        self.ingest_govinfo_votes(collection, limit)

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
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
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
    parser = argparse.ArgumentParser(description="Bulk Votes Ingestion")
    parser.add_argument("--congress", type=int, default=118, help="Congress number")
    parser.add_argument(
        "--chamber", choices=["house", "senate", "both"], default="both", help="Chamber"
    )
    parser.add_argument("--congress-limit", type=int, help="Limit Congress.gov votes")
    parser.add_argument(
        "--govinfo-collection", default="CRPT", help="GovInfo collection"
    )
    parser.add_argument("--govinfo-limit", type=int, help="Limit GovInfo votes")
    parser.add_argument(
        "--sources",
        nargs="+",
        choices=["congress", "govinfo"],
        help="Sources to ingest from",
    )
    parser.add_argument("--batch-size", type=int, default=100, help="Batch size")
    parser.add_argument(
        "--dry-run", action="store_true", help="Dry run (no database changes)"
    )

    args = parser.parse_args()

    # Load configuration
    config = VotesIngestionConfig(
        database_url=os.getenv("DATABASE_URL"),
        congress_api_key=os.getenv("CONGRESS_API_KEY"),
        govinfo_api_key=os.getenv("GOVINFO_API_KEY"),
        batch_size=args.batch_size,
    )

    # Validate configuration
    if not config.database_url:
        logger.error("DATABASE_URL environment variable is required")
        sys.exit(1)

    if not config.congress_api_key and "congress" in (args.sources or config.sources):
        logger.error(
            "CONGRESS_API_KEY environment variable is required for Congress.gov ingestion"
        )
        sys.exit(1)

    if not config.govinfo_api_key and "govinfo" in (args.sources or config.sources):
        logger.error(
            "GOVINFO_API_KEY environment variable is required for GovInfo ingestion"
        )
        sys.exit(1)

    # Run ingestion
    ingestor = BulkVotesIngestor(config)

    try:
        stats = ingestor.run_ingestion(
            sources=args.sources,
            congress=args.congress,
            chamber=args.chamber,
            congress_limit=args.congress_limit,
            govinfo_collection=args.govinfo_collection,
            govinfo_limit=args.govinfo_limit,
        )

        # Print summary
        print("\n" + "=" * 50)
        print("BULK VOTES INGESTION SUMMARY")
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
