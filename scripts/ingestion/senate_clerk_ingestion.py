#!/usr/bin/env python3
"""
Senate Clerk Voting Data Ingestion
Integrates Senate roll call votes into our parallel ingestion system
"""

import logging
import re
import time
from typing import Dict, List, Optional, Tuple
from datetime import datetime

import requests
import xml.etree.ElementTree as ET
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class SenateClerkIngestor:
    """Handles Senate Clerk voting data ingestion"""

    def __init__(self, config):
        self.config = config
        self.session = self._create_session()

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

    def get_senate_roll_calls(self, congress: int, year: int) -> List[Tuple[int, str]]:
        """Get list of Senate roll call votes for a congress and year"""
        # Senate Clerk provides roll call lists by Congress and year
        base_url = "https://www.senate.gov"

        # Try different Senate Clerk URL patterns
        urls = [
            f"{base_url}/legislative/votes_roll_call_votes_{congress}.htm",
            f"{base_url}/legislative/votes_{congress}th_congress.htm",
            f"{base_url}/legislative/votes_{congress}th_congress_{year}.htm",
        ]

        for url in urls:
            try:
                logger.info(f"Fetching Senate roll call list from: {url}")
                response = self.session.get(url, timeout=self.config.request_timeout)
                response.raise_for_status()

                # Parse HTML to find roll call links
                roll_calls = self._parse_senate_roll_call_page(response.text)
                if roll_calls:
                    logger.info(
                        f"Found {len(roll_calls)} Senate roll calls for {congress}th Congress, {year}"
                    )
                    return roll_calls

            except Exception as e:
                logger.warning(f"Failed to fetch from {url}: {e}")
                continue

        logger.warning(f"No Senate roll calls found for {congress}th Congress, {year}")
        return []

    def _parse_senate_roll_call_page(self, html_content: str) -> List[Tuple[int, str]]:
        """Parse Senate roll call page HTML to extract vote information"""
        roll_calls = []

        # Look for roll call vote links in the HTML
        # Pattern: votes_roll_call_vote000001.htm
        pattern = r"votes_roll_call_vote(\d+)\.htm"
        matches = re.findall(pattern, html_content)

        for match in matches:
            roll_number = int(match)
            roll_calls.append((roll_number, f"votes_roll_call_vote{match}.htm"))

        return sorted(roll_calls, reverse=True)  # Most recent first

    def ingest_senate_roll_call(
        self, congress: int, year: int, roll_number: int, vote_file: str
    ) -> Optional[Dict]:
        """Ingest a single Senate roll call vote"""
        try:
            base_url = "https://www.senate.gov"
            url = f"{base_url}/legislative/votes_roll_call_votes_{congress}/{vote_file}"

            logger.debug(f"Fetching Senate roll call {roll_number} from: {url}")
            response = self.session.get(url, timeout=self.config.request_timeout)
            response.raise_for_status()

            # Parse XML response (Senate Clerk provides XML)
            root = ET.fromstring(response.text)

            # Extract vote metadata
            vote_data = self._extract_senate_vote_data(root, congress, roll_number, year)
            if vote_data:
                logger.info(
                    f"Processed Senate roll call {roll_number}: {vote_data.get('vote_question', 'Unknown')}"
                )
                return vote_data

        except Exception as e:
            logger.error(f"Failed to ingest Senate roll call {roll_number}: {e}")
            return None

    def _extract_senate_vote_data(
        self, root, congress: int, roll_number: int, year: int
    ) -> Optional[Dict]:
        """Extract vote data from Senate XML"""
        try:
            # Senate XML structure may differ from House
            vote_metadata = root.find(".//vote")
            if vote_metadata is None:
                return None

            # Extract basic vote information
            vote_question = self._safe_get_text(vote_metadata, "question")
            vote_result = self._safe_get_text(vote_metadata, "result")
            vote_date = self._safe_get_text(vote_metadata, "date")

            # Extract vote totals
            yeas = 0
            nays = 0
            present = 0
            not_voting = 0

            vote_totals = vote_metadata.find(".//totals")
            if vote_totals is not None:
                yeas = int(self._safe_get_text(vote_totals, "yeas") or "0")
                nays = int(self._safe_get_text(vote_totals, "nays") or "0")
                present = int(self._safe_get_text(vote_totals, "present") or "0")
                not_voting = int(self._safe_get_text(vote_totals, "not_voting") or "0")

            # Extract bill information
            bill_number = None
            bill_type = None
            bill_elem = vote_metadata.find(".//bill")
            if bill_elem is not None:
                bill_number = self._safe_get_text(bill_elem, "number")
                bill_type = self._safe_get_text(bill_elem, "type")

            # Create vote data matching our table structure
            vote_data = {
                "vote_id": f"{congress}-senate-{roll_number}",
                "congress_number": congress,
                "chamber": "Senate",
                "roll_call_number": roll_number,
                "vote_question": vote_question,
                "vote_result": vote_result,
                "vote_date": self._parse_date(vote_date),
                "vote_time": None,  # Senate may not provide time
                "vote_description": vote_question,
                "vote_type": "roll_call",
                "yeas": yeas,
                "nays": nays,
                "present": present,
                "not_voting": not_voting,
                "democratic_position": None,  # Would need party analysis
                "republican_position": None,  # Would need party analysis
                "bill_id": f"{bill_type}{bill_number}" if bill_type and bill_number else None,
                "amendment_number": None,
                "nomination_number": None,
                "source": "senate-clerk",
            }

            return vote_data

        except Exception as e:
            logger.error(f"Error extracting Senate vote data: {e}")
            return None

    def _safe_get_text(self, element, tag: str) -> Optional[str]:
        """Safely get text from XML element"""
        if element is None:
            return None
        child = element.find(tag)
        return child.text if child is not None else None

    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime.date]:
        """Parse Senate date string"""
        if not date_str:
            return None
        try:
            # Senate dates might be in different formats
            for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%Y%m%d"]:
                try:
                    return datetime.strptime(date_str, fmt).date()
                except ValueError:
                    continue
            return None
        except Exception:
            return None

    def ingest_senate_congress(self, congress: int, year: int) -> Dict:
        """Ingest all Senate votes for a specific congress and year"""
        results = {"processed": 0, "successful": 0, "failed": 0, "duplicates": 0}

        logger.info(f"Starting Senate ingestion for {congress}th Congress, {year}")

        # Get list of roll calls
        roll_calls = self.get_senate_roll_calls(congress, year)

        if not roll_calls:
            logger.warning(f"No Senate roll calls found for {congress}th Congress, {year}")
            return results

        for roll_number, vote_file in roll_calls:
            try:
                vote_data = self.ingest_senate_roll_call(congress, year, roll_number, vote_file)
                if vote_data:
                    success = self._insert_vote_data(vote_data)
                    if success:
                        results["successful"] += 1
                    else:
                        results["duplicates"] += 1
                else:
                    results["failed"] += 1

                results["processed"] += 1

                # Rate limiting
                time.sleep(self.config.rate_limit_delay)

            except Exception as e:
                results["failed"] += 1
                logger.error(f"Error processing Senate roll call {roll_number}: {e}")

        logger.info(f"Senate ingestion completed for {congress}th Congress, {year}: {results}")
        return results

    def _insert_vote_data(self, vote_data: Dict) -> bool:
        """Insert vote data into database (using existing parallel system)"""
        try:
            import psycopg2

            conn = psycopg2.connect(
                host=self.config.db_host,
                port=self.config.db_port,
                database=self.config.db_name,
                user=self.config.db_user,
                password=self.config.db_password,
            )

            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO congress.roll_call_votes_bulk 
                    (vote_id, congress_number, chamber, roll_call_number, vote_question, 
                     vote_result, vote_date, vote_description, vote_type, yeas, nays, 
                     present, not_voting, bill_id, source)
                    VALUES (%(vote_id)s, %(congress_number)s, %(chamber)s, %(roll_call_number)s,
                            %(vote_question)s, %(vote_result)s, %(vote_date)s, %(vote_description)s,
                            %(vote_type)s, %(yeas)s, %(nays)s, %(present)s, %(not_voting)s,
                            %(bill_id)s, %(source)s)
                    ON CONFLICT (vote_id) DO NOTHING
                """,
                    vote_data,
                )

                success = cursor.rowcount > 0
                conn.commit()
                return success

        except Exception as e:
            logger.error(f"Failed to insert Senate vote data: {e}")
            return False
        finally:
            if "conn" in locals():
                conn.close()
