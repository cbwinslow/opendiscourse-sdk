#!/usr/bin/env python3
"""
Senate Clerk Data Ingestion Module

This module provides functionality for ingesting Senate voting data
from the Senate Clerk's official data sources, complementing the
House data from Congress.gov API.
"""

import logging
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, TypedDict
import xml.etree.ElementTree as ET
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import psycopg2
from psycopg2 import pool, sql
import json

# Add project root to path
sys.path.append("/home/cbwinslow/Videos/opendiscourse")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("/home/cbwinslow/Videos/opendiscourse/logs/senate_clerk_ingestion.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)

# Constants
SENATE_CLERK_BASE_URL = (
    "https://www.senate.gov/legislative/Public_Disclosure/Legislative_Records/Votes.xml"
)
DEFAULT_TIMEOUT = 30
RATE_LIMIT_DELAY = 1.0  # seconds between requests


class SenateVoteData(TypedDict):
    """Structure for Senate vote data"""

    congress: int
    session: int
    vote_number: int
    vote_date: str
    vote_question: str
    vote_result: str
    vote_title: str
    yeas: int
    nays: int
    present: int
    absent: int
    vote_type: str
    vote_position: str
    member_id: str
    member_name: str
    member_state: str
    member_party: str


class SenateClerkIngester:
    """Handles Senate voting data ingestion from Senate Clerk"""

    def __init__(self, db_pool=None, timeout: int = DEFAULT_TIMEOUT):
        """Initialize the Senate Clerk ingester

        Args:
            db_pool: PostgreSQL connection pool
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        self.db_pool = db_pool
        self.session = self._create_session()
        self.base_url = SENATE_CLERK_BASE_URL

        # Statistics
        self.stats = {
            "total_votes": 0,
            "successful_votes": 0,
            "failed_votes": 0,
            "total_positions": 0,
            "successful_positions": 0,
            "failed_positions": 0,
            "start_time": datetime.now(),
            "errors": [],
        }

    def _create_session(self) -> requests.Session:
        """Create a requests session with retry logic"""
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    def fetch_senate_votes_xml(
        self, congress: Optional[int] = None, session: Optional[int] = None
    ) -> Optional[str]:
        """Fetch the Senate votes XML data

        Args:
            congress: Congress number (e.g., 118)
            session: Session number (e.g., 1, 2)

        Returns:
            XML content as string or None if failed
        """
        try:
            # Construct URL for specific congress and session
            if congress and session:
                url = f"https://www.senate.gov/legislative/LIS/roll_call_lists/vote_menu_{congress}_{session}.xml"
            else:
                # Get the most recent congress/session
                url = "https://www.senate.gov/legislative/LIS/roll_call_lists/vote_menu_118_2.xml"

            logger.info("Fetching Senate votes XML from %s", url)

            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()

            return response.text

        except requests.exceptions.RequestException as e:
            error_msg = f"Failed to fetch Senate votes XML: {e}"
            logger.error(error_msg)
            self.stats["errors"].append(error_msg)
            return None

    def parse_senate_votes_xml(self, xml_content: str) -> List[Dict]:
        """Parse Senate votes XML content

        Args:
            xml_content: XML content string

        Returns:
            List of vote dictionaries
        """
        try:
            logger.info("Parsing Senate votes XML content")

            root = ET.fromstring(xml_content)
            votes = []

            # Senate XML structure may vary - this is a general approach
            for vote_elem in root.findall(".//vote"):
                try:
                    vote_data = {
                        "congress": int(vote_elem.get("congress", 0)),
                        "session": int(vote_elem.get("session", 0)),
                        "vote_number": int(vote_elem.get("vote_number", 0)),
                        "vote_date": vote_elem.get("date", ""),
                        "vote_question": vote_elem.get("question", ""),
                        "vote_result": vote_elem.get("result", ""),
                        "vote_title": vote_elem.get("title", ""),
                        "yeas": int(vote_elem.get("yeas", 0)),
                        "nays": int(vote_elem.get("nays", 0)),
                        "present": int(vote_elem.get("present", 0)),
                        "absent": int(vote_elem.get("absent", 0)),
                        "vote_type": vote_elem.get("type", ""),
                        "members": [],
                    }

                    # Parse member positions
                    for member_elem in vote_elem.findall(".//member"):
                        member_data = {
                            "member_id": member_elem.get("id", ""),
                            "member_name": member_elem.get("name", ""),
                            "member_state": member_elem.get("state", ""),
                            "member_party": member_elem.get("party", ""),
                            "vote_position": member_elem.get("vote", ""),
                        }
                        vote_data["members"].append(member_data)

                    votes.append(vote_data)

                except (ValueError, AttributeError) as e:
                    logger.warning("Error parsing vote element: %s", e)
                    continue

            logger.info("Parsed %d Senate votes from XML", len(votes))
            return votes

        except ET.ParseError as e:
            error_msg = f"Failed to parse Senate votes XML: {e}"
            logger.error(error_msg)
            self.stats["errors"].append(error_msg)
            return []

    def save_senate_vote_to_db(self, vote_data: Dict) -> Optional[int]:
        """Save a Senate vote to the database
        
        Args:
            vote_data: Vote data dictionary
            
        Returns:
            Vote ID if successful, None otherwise
        """
        if not self.db_pool:
            logger.warning("No database connection available")
            return None
            
        try:
            conn = self.db_pool.getconn()
            try:
                cursor = conn.cursor()

                # Insert into congress.votes table
                insert_query = sql.SQL("""
                    INSERT INTO congress.votes (
                        congress_number, session_number, roll_call_number, 
                        vote_date, vote_question, vote_result, vote_title,
                        yeas, nays, present, absent, vote_type, chamber,
                        created_at, updated_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    ) ON CONFLICT (congress_number, session_number, roll_call_number, chamber) 
                    DO UPDATE SET
                        vote_question = EXCLUDED.vote_question,
                        vote_result = EXCLUDED.vote_result,
                        vote_title = EXCLUDED.vote_title,
                        yeas = EXCLUDED.yeas,
                        nays = EXCLUDED.nays,
                        present = EXCLUDED.present,
                        absent = EXCLUDED.absent,
                        vote_type = EXCLUDED.vote_type,
                        updated_at = %s
                    WHERE congress.votes.congress_number = EXCLUDED.congress_number 
                      AND congress.votes.session_number = EXCLUDED.session_number 
                      AND congress.votes.roll_call_number = EXCLUDED.roll_call_number 
                      AND congress.votes.chamber = EXCLUDED.chamber
                """)

                cursor.execute(insert_query, (
                    vote_data['congress'],
                    vote_data['session'],
                    vote_data['vote_number'],
                    vote_data['vote_date'],
                    vote_data['vote_question'],
                    vote_data['vote_result'],
                    vote_data['vote_title'],
                    vote_data['yeas'],
                    vote_data['nays'],
                    vote_data['present'],
                    vote_data['absent'],
                    vote_data['vote_type'],
                    'Senate',
                    datetime.now(),
                    datetime.now()
                ))

                vote_id = cursor.fetchone()[0]
                
                # Save member positions
                for member in vote_data.get('members', []):
                    member_insert_query = sql.SQL("""
                        INSERT INTO congress.vote_positions (
                            vote_id, member_id, member_name, member_state, 
                            member_party, vote_position, created_at
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s
                        ) ON CONFLICT (vote_id, member_id) 
                        DO UPDATE SET
                            vote_position = EXCLUDED.vote_position,
                            updated_at = %s
                        WHERE congress.vote_positions.vote_id = EXCLUDED.vote_id 
                          AND congress.vote_positions.member_id = EXCLUDED.member_id
                    """)

                    cursor.execute(member_insert_query, (
                        vote_id,
                        member.get('member_id', ''),
                        member.get('member_name', ''),
                        member.get('member_state', ''),
                        member.get('member_party', ''),
                        member.get('vote_position', ''),
                        datetime.now()
                    ))

                conn.commit()
                cursor.close()
                
                logger.info(f"Successfully saved Senate vote {vote_data.get('vote_number', 'N/A')} to database (ID: {vote_id})")
                return vote_id
                
            except Exception as e:
                logger.error(f"Failed to save Senate vote to database: {e}")
                return None
            finally:
                if self.db_pool:
                    self.db_pool.putconn(conn)

        except Exception as e:
            error_msg = f"Failed to save Senate vote to database: {e}"
            logger.error(error_msg)
            self.stats["errors"].append(error_msg)
            return None

    def _save_vote_position(self, cursor, vote_id: int, member_data: Dict, vote_data: Dict):
        """Save a member's vote position

        Args:
            cursor: Database cursor
            vote_id: Vote ID
            member_data: Member vote position data
            vote_data: Vote data for context
        """
        try:
            insert_query = sql.SQL("""
                INSERT INTO congress.vote_positions (
                    vote_id, member_id, member_name, member_state, 
                    member_party, vote_position, created_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s
                ) ON CONFLICT (vote_id, member_id)
                DO UPDATE SET
                    vote_position = EXCLUDED.vote_position,
                    updated_at = EXCLUDED.updated_at
            """)

            cursor.execute(
                insert_query,
                (
                    vote_id,
                    member_data["member_id"],
                    member_data["member_name"],
                    member_data["member_state"],
                    member_data["member_party"],
                    member_data["vote_position"],
                    datetime.now(),
                ),
            )

        except Exception as e:
            logger.warning(
                "Failed to save vote position for %s: %s",
                member_data.get("member_name", "Unknown"),
                e,
            )

    def ingest_senate_votes(self, limit: Optional[int] = None) -> Dict[str, int]:
        """Main method to ingest Senate votes

        Args:
            limit: Maximum number of votes to process (None for all)

        Returns:
            Dictionary with ingestion statistics
        """
        logger.info("Starting Senate votes ingestion")

        # Fetch XML data
        xml_content = self.fetch_senate_votes_xml()
        if not xml_content:
            logger.error("Failed to fetch Senate votes XML")
            return self.stats

        # Parse XML
        votes = self.parse_senate_votes_xml(xml_content)
        if not votes:
            logger.error("No votes found in XML content")
            return self.stats

        # Apply limit if specified
        if limit:
            votes = votes[:limit]

        logger.info("Processing %d Senate votes", len(votes))

        # Process each vote
        for idx, vote_data in enumerate(votes, 1):
            self.stats["total_votes"] += 1

            logger.info(
                "Processing vote %d/%d: Congress %s, Session %s, Vote %s",
                idx,
                len(votes),
                vote_data.get("congress", "Unknown"),
                vote_data.get("session", "Unknown"),
                vote_data.get("vote_number", "Unknown"),
            )

            # Save vote to database
            vote_id = self.save_senate_vote_to_db(vote_data)

            if vote_id:
                self.stats["successful_votes"] += 1
                self.stats["total_positions"] += len(vote_data.get("members", []))
                self.stats["successful_positions"] += len(vote_data.get("members", []))
            else:
                self.stats["failed_votes"] += 1

            # Rate limiting
            time.sleep(RATE_LIMIT_DELAY)

        # Calculate duration
        end_time = datetime.now()
        duration = end_time - self.stats["start_time"]
        self.stats["duration_seconds"] = duration.total_seconds()

        logger.info("Senate votes ingestion completed in %.2f seconds", duration.total_seconds())
        return self.stats

    def print_statistics(self):
        """Print ingestion statistics"""
        duration = datetime.now() - self.stats["start_time"]

        print("\n" + "=" * 60)
        print("Senate Clerk Ingestion Statistics")
        print("=" * 60)
        print(f"Total votes processed:     {self.stats['total_votes']}")
        print(f"Successful votes:          {self.stats['successful_votes']}")
        print(f"Failed votes:              {self.stats['failed_votes']}")
        print(f"Total positions:          {self.stats['total_positions']}")
        print(f"Successful positions:      {self.stats['successful_positions']}")
        print(f"Duration:                  {duration}")

        if self.stats["total_votes"] > 0:
            vote_success_rate = (self.stats["successful_votes"] / self.stats["total_votes"]) * 100
            print(f"Vote success rate:         {vote_success_rate:.1f}%")

        if self.stats["errors"]:
            print(f"\nErrors encountered:")
            for error in self.stats["errors"][:5]:  # Show first 5 errors
                print(f"  - {error}")
            if len(self.stats["errors"]) > 5:
                print(f"  ... and {len(self.stats['errors']) - 5} more errors")

        print("=" * 60 + "\n")


def main():
    """Main function for Senate Clerk ingestion"""
    import argparse

    parser = argparse.ArgumentParser(description="Senate Clerk data ingestion")
    parser.add_argument("--limit", type=int, help="Maximum number of votes to process")
    parser.add_argument(
        "--dry-run", action="store_true", help="Parse XML but don't save to database"
    )

    args = parser.parse_args()
    
    # Setup database connection pool
    db_pool = None
    if not args.dry_run:
        try:
            from psycopg2 import pool
            db_pool = pool.ThreadedConnectionPool(
                minconn=5,
                maxconn=20,
                database="opendiscourse",
                user="cbwinslow",
                host="/var/run/postgresql"
            )
            logger.info("✅ Database connection pool established")
        except Exception as e:
            logger.error(f"❌ Failed to setup database pool: {e}")
            db_pool = None
    
    # Create ingester
    ingester = SenateClerkIngester(db_pool=db_pool)
    
    try:
        # Run ingestion
        if args.dry_run:
            result = ingester.ingest_senate_votes(
                congress=args.congress,
                session=args.session,
                limit=args.limit
            )
        else:
            result = ingester.ingest_senate_votes(
                congress=args.congress,
                session=args.session,
                limit=args.limit
            )
        
        # Print results
        if "error" in result:
            print(f"❌ Error: {result['error']}")
        else:
            print("✅ Senate Clerk Ingestion Results:")
            print(f"  Congress: {result['congress']}")
            print(f"  Session: {result['session']}")
            print(f"  Total Votes: {result['total_votes']}")
            print(f"  Successful: {result['successful_votes']}")
            print(f"  Failed: {result['failed_votes']}")
            print(f"  Total Positions: {result['total_positions']}")
            if args.limit:
                print(f"  Limit Applied: {result['limit_applied']}")
    
    except KeyboardInterrupt:
        print("\n🛑 Senate Clerk ingestion interrupted by user")
    except Exception as e:
        print(f"\n❌ Fatal error during Senate Clerk ingestion: {e}")
        sys.exit(1)

    # Setup database connection pool
    db_pool = None
    if not args.dry_run:
        try:
            db_pool = psycopg2.pool.ThreadedConnectionPool(
                minconn=5,
                maxconn=20,
                database="opendiscourse",
                user="cbwinslow",
                host="/var/run/postgresql",
            )
            logger.info("Database connection pool established")
        except Exception as e:
            logger.error(f"Failed to setup database pool: {e}")
            return

    try:
        # Create ingester
        ingester = SenateClerkIngester(db_pool=db_pool)

        if args.dry_run:
            logger.info("DRY RUN MODE: Will parse XML but not save to database")
            # Just fetch and parse, don't save
            xml_content = ingester.fetch_senate_votes_xml()
            if xml_content:
                votes = ingester.parse_senate_votes_xml(xml_content)
                logger.info("DRY RUN: Parsed %d votes (not saved to database)", len(votes))
            else:
                logger.error("DRY RUN: Failed to fetch XML content")
        else:
            # Full ingestion
            stats = ingester.ingest_senate_votes(limit=args.limit)
            ingester.print_statistics()

    except KeyboardInterrupt:
        logger.info("Senate ingestion interrupted by user")
    except Exception as e:
        logger.error("Fatal error during Senate ingestion: %s", e, exc_info=True)
    finally:
        if db_pool:
            db_pool.closeall()
            logger.info("Database connections closed")


if __name__ == "__main__":
    main()
