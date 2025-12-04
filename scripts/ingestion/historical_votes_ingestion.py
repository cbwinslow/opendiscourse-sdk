#!/usr/bin/env python3
"""
Historical Congress Votes Ingestion Script
Ingests votes from multiple congresses (113th-118th) for 10 years of data
"""

import argparse
import logging
import os
import sys
import time
from datetime import datetime
from typing import Dict, List, Optional

import psycopg2
import requests
import xml.etree.ElementTree as ET
from psycopg2.extras import execute_values
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class IngestionConfig:
    """Configuration for votes ingestion"""

    def __init__(self):
        self.db_host = os.getenv("DB_HOST", "/var/run/postgresql")
        self.db_port = int(os.getenv("DB_PORT", "5432"))
        self.db_name = os.getenv("DB_NAME", "opendiscourse")
        self.db_user = os.getenv("DB_USER", "postgres")
        self.db_password = os.getenv("DB_PASSWORD", "")
        self.request_timeout = int(os.getenv("REQUEST_TIMEOUT", "30"))
        self.rate_limit_delay = float(os.getenv("RATE_LIMIT_DELAY", "1.0"))
        self.batch_size = int(os.getenv("BATCH_SIZE", "100"))
        self.max_retries = int(os.getenv("MAX_RETRIES", "3"))


class VotesIngestor:
    """Handles ingestion of congressional roll call votes"""

    def __init__(self, config: IngestionConfig):
        self.config = config
        self.session = self._create_session()
        self.conn = None

    def _create_session(self) -> requests.Session:
        """Create HTTP session with retry strategy"""
        session = requests.Session()
        retry_strategy = Retry(
            total=self.config.max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    def connect_db(self):
        """Establish database connection"""
        try:
            self.conn = psycopg2.connect(
                host=self.config.db_host,
                port=self.config.db_port,
                database=self.config.db_name,
                user=self.config.db_user,
                password=self.config.db_password,
            )
            logger.info("Database connection established")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise

    def close_db(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")

    def create_tables(self):
        """Verify votes tables exist"""
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM congress.roll_call_votes_bulk LIMIT 1")
                cursor.execute("SELECT COUNT(*) FROM congress.vote_positions_bulk LIMIT 1")
                self.conn.commit()
            logger.info("Votes tables verified")
        except Exception as e:
            logger.error(f"Failed to verify tables: {e}")
            raise

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string"""
        if not date_str:
            return None
        try:
            return datetime.strptime(date_str, "%m/%d/%Y").date()
        except ValueError:
            return None

    def _parse_time(self, time_str: str) -> Optional[datetime.time]:
        """Parse time string"""
        if not time_str:
            return None
        try:
            return datetime.strptime(time_str, "%H:%M:%S").time()
        except ValueError:
            return None

    def ingest_house_clerk_votes(self, congress: int, limit: Optional[int] = None):
        """Ingest votes from House Clerk for a specific Congress"""
        logger.info(f"Starting House Clerk votes ingestion for Congress {congress}")

        ingested_count = 0

        # Get recent roll call votes from House Clerk
        base_url = "http://clerk.house.gov/cgi-bin/vote.asp"

        # Calculate year range for the Congress
        congress_years = {
            113: (2013, 2014),
            114: (2015, 2016),
            115: (2017, 2018),
            116: (2019, 2020),
            117: (2021, 2022),
            118: (2023, 2024),
        }

        years = congress_years.get(congress, (2024, 2024))

        # Process each year in the Congress
        for year in years:
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
                    not_voting = int(vote_totals.find("totals-by-vote/not-voting-total").text)

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

                    # Create vote data matching existing table structure
                    vote_data = {
                        "vote_id": f"{congress}-house-{roll_call_num}",
                        "congress_number": congress,
                        "session": 1,  # Default session
                        "chamber": chamber,
                        "roll_call_number": roll_call_num,
                        "vote_date": action_date,
                        "vote_time": action_time,
                        "vote_question": vote_question,
                        "vote_description": vote_desc,
                        "vote_type": vote_question,
                        "vote_result": vote_result,
                        "yeas": yeas,
                        "nays": nays,
                        "present": present,
                        "not_voting": not_voting,
                        "democratic_position": "support"
                        if democratic_position
                        else "oppose"
                        if democratic_position is False
                        else None,
                        "republican_position": "support"
                        if republican_position
                        else "oppose"
                        if republican_position is False
                        else None,
                        "bill_id": f"{bill_type}{bill_number}"
                        if bill_type and bill_number
                        else None,
                        "source": "house-clerk",
                    }

                    # Extract member positions
                    positions = []
                    for member in root.findall("voted-member"):
                        bioguide_id = member.find("legislator").attrib.get("name-id")
                        name = member.find("legislator").attrib.get("unaccented-name")
                        party = member.find("legislator").attrib.get("party")
                        state = member.find("legislator").attrib.get("state")
                        district_str = member.find("legislator").attrib.get("district")
                        district = int(district_str) if district_str else None
                        vote_cast = member.find("vote").text

                        positions.append(
                            {
                                "vote_id": vote_data["vote_id"],
                                "bioguide_id": bioguide_id,
                                "name": name,
                                "party": party,
                                "state": state,
                                "district": district,
                                "vote_cast": vote_cast,
                            }
                        )

                    # Insert vote and positions
                    self._insert_vote(vote_data, positions)

                    ingested_count += 1
                    logger.info(
                        f"House Clerk: Processed roll call {roll_call_num} (Congress {congress}, Year {year})"
                    )

                    # Rate limiting
                    time.sleep(self.config.rate_limit_delay)

                except Exception as e:
                    logger.error(f"Error processing House Clerk roll call {roll_number}: {e}")
                    roll_number -= 1
                    continue

                roll_number -= 1

        logger.info(f"House Clerk votes ingestion completed: {ingested_count} votes")
        return ingested_count

    def _insert_vote(self, vote_data: Dict, positions: List[Dict]):
        """Insert vote and positions into database"""
        try:
            with self.conn.cursor() as cursor:
                # Insert vote
                vote_columns = vote_data.keys()
                vote_values = list(vote_data.values())
                vote_placeholders = ", ".join(["%s"] * len(vote_columns))

                vote_query = f"""
                INSERT INTO congress.roll_call_votes_bulk ({", ".join(vote_columns)})
                VALUES ({vote_placeholders})
                ON CONFLICT (vote_id) DO UPDATE SET
                    vote_result = EXCLUDED.vote_result,
                    yeas = EXCLUDED.yeas,
                    nays = EXCLUDED.nays,
                    present = EXCLUDED.present,
                    not_voting = EXCLUDED.not_voting,
                    democratic_position = EXCLUDED.democratic_position,
                    republican_position = EXCLUDED.republican_position,
                    updated_at = CURRENT_TIMESTAMP
                """

                cursor.execute(vote_query, vote_values)

                # Insert positions
                if positions:
                    position_columns = positions[0].keys()
                    position_values = [
                        tuple(pos[col] for col in position_columns) for pos in positions
                    ]
                    position_placeholders = ", ".join(["%s"] * len(position_columns))

                    position_query = f"""
                    INSERT INTO congress.vote_positions_bulk ({", ".join(position_columns)})
                    VALUES %s
                    ON CONFLICT (id) DO UPDATE SET
                        vote_cast = EXCLUDED.vote_cast,
                        updated_at = CURRENT_TIMESTAMP
                    """

                    execute_values(cursor, position_query, position_values)

                self.conn.commit()
                logger.info(f"Inserted 1 votes and {len(positions)} positions from house-clerk")

        except Exception as e:
            if self.conn:
                self.conn.rollback()
            logger.error(f"Failed to insert vote: {e}")
            raise

    def ingest_votes(self, congress: Optional[int] = None, limit: Optional[int] = None):
        """Main ingestion method"""
        if not self.conn:
            self.connect_db()

        self.create_tables()

        total_ingested = 0
        sources = ["house-clerk"]

        for source in sources:
            logger.info(f"Starting votes ingestion from {source}")

            if congress:
                # Ingest specific congress
                if source == "house-clerk":
                    ingested = self.ingest_house_clerk_votes(congress, limit)
                    total_ingested += ingested
            else:
                # Ingest all congresses (113th-118th)
                for c in range(113, 119):
                    if source == "house-clerk":
                        ingested = self.ingest_house_clerk_votes(c, limit)
                        total_ingested += ingested

        return total_ingested


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Ingest congressional roll call votes")
    parser.add_argument("--congress", type=int, help="Congress number (e.g., 118)")
    parser.add_argument("--limit", type=int, help="Maximum number of votes to ingest")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    config = IngestionConfig()
    ingestor = VotesIngestor(config)

    try:
        start_time = datetime.now()
        total_processed = ingestor.ingest_votes(args.congress, args.limit)
        end_time = datetime.now()

        duration = end_time - start_time
        logger.info(f"Ingestion completed in {duration}")
        logger.info(f"Total votes processed: {total_processed}")

        print("\n" + "=" * 50)
        print("HISTORICAL VOTES INGESTION SUMMARY")
        print("=" * 50)
        print(f"Start Time: {start_time}")
        print(f"End Time: {end_time}")
        print(f"Duration: {duration}")
        print(f"Total Processed: {total_processed}")
        print("=" * 50)

    except KeyboardInterrupt:
        logger.info("Ingestion interrupted by user")
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        sys.exit(1)
    finally:
        ingestor.close_db()


if __name__ == "__main__":
    main()
