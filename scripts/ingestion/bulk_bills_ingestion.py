#!/usr/bin/env python3
"""
Bulk Bills Ingestion Script
Comprehensive ingestion of congressional bills from multiple sources
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
    handlers=[logging.FileHandler("bills_ingestion.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


@dataclass
class IngestionConfig:
    """Configuration for bills ingestion"""

    database_url: str
    congress_api_key: str
    govinfo_api_key: str
    openstates_api_key: str

    # Ingestion parameters
    batch_size: int = 100
    max_retries: int = 3
    retry_delay: float = 1.0
    request_timeout: int = 30

    # Source priorities
    sources: List[str] = None

    def __post_init__(self):
        if self.sources is None:
            self.sources = ["congress", "govinfo", "openstates"]


class BulkBillsIngestor:
    """Comprehensive bills ingestion system"""

    def __init__(self, config: IngestionConfig):
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
            # Bills table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS congress.bills_bulk (
                    bill_id VARCHAR(50) PRIMARY KEY,
                    congress_number INTEGER,
                    bill_type VARCHAR(10),
                    bill_number INTEGER,
                    official_title TEXT,
                    short_title TEXT,
                    introduced_date DATE,
                    updated_date TIMESTAMP,
                    sponsor_bioguide_id VARCHAR(20),
                    sponsor_party VARCHAR(20),
                    sponsor_state VARCHAR(10),
                    committee_code VARCHAR(20),
                    policy_area VARCHAR(100),
                    subjects TEXT[],
                    summary TEXT,
                    latest_action TEXT,
                    latest_action_date DATE,
                    status VARCHAR(50),
                    source VARCHAR(20),
                    raw_data JSONB,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                );
                
                CREATE INDEX IF NOT EXISTS idx_bills_bulk_congress ON congress.bills_bulk(congress_number);
                CREATE INDEX IF NOT EXISTS idx_bills_bulk_type ON congress.bills_bulk(bill_type);
                CREATE INDEX IF NOT EXISTS idx_bills_bulk_date ON congress.bills_bulk(introduced_date);
                CREATE INDEX IF NOT EXISTS idx_bills_bulk_sponsor ON congress.bills_bulk(sponsor_bioguide_id);
                CREATE INDEX IF NOT EXISTS idx_bills_bulk_source ON congress.bills_bulk(source);
                CREATE INDEX IF NOT EXISTS idx_bills_bulk_status ON congress.bills_bulk(status);
            """)

            # Ingestion tracking
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS congress.ingestion_tracking (
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
            logger.info("Tables created/verified")

    def ingest_congress_bills(
        self, congress: int = 118, limit: Optional[int] = None
    ) -> int:
        """Ingest bills from Congress.gov API"""
        logger.info(f"Starting Congress.gov bills ingestion for Congress {congress}")

        base_url = "https://api.congress.gov/v3"
        headers = {
            "X-API-Key": self.config.congress_api_key,
            "Accept": "application/json",
        }

        ingested_count = 0
        offset = 0

        while True:
            try:
                # Get bills list
                url = f"{base_url}/bill/{congress}"
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
                bills = data.get("bills", [])

                if not bills:
                    break

                # Process bills in batch
                batch_data = []
                for bill in bills:
                    bill_data = self._process_congress_bill(bill, congress)
                    if bill_data:
                        batch_data.append(bill_data)

                # Insert batch
                if batch_data:
                    self._insert_bills_batch(batch_data, "congress")
                    ingested_count += len(batch_data)
                    logger.info(f"Congress.gov: Processed {ingested_count} bills")

                # Check limits
                if limit and ingested_count >= limit:
                    break

                # Check pagination
                pagination = data.get("pagination", {})
                if offset >= pagination.get("count", 0):
                    break

                offset += len(bills)

                # Rate limiting
                time.sleep(0.1)

            except Exception as e:
                logger.error(f"Error in Congress.gov ingestion: {e}")
                break

        self.stats["by_source"]["congress"] = ingested_count
        logger.info(f"Congress.gov ingestion completed: {ingested_count} bills")
        return ingested_count

    def ingest_govinfo_bills(
        self, collection: str = "BILLS", limit: Optional[int] = None
    ) -> int:
        """Ingest bills from GovInfo API"""
        logger.info(f"Starting GovInfo bills ingestion for collection {collection}")

        base_url = "https://api.govinfo.gov"
        headers = {
            "X-Api-Key": self.config.govinfo_api_key,
            "Accept": "application/json",
        }

        ingested_count = 0

        try:
            # Get collection items
            url = f"{base_url}/collections/{collection}/2023/2024"
            params = {
                "pageSize": min(self.config.batch_size, 100),
                "offset": ingested_count,
            }

            response = self.session.get(
                url, headers=headers, params=params, timeout=self.config.request_timeout
            )
            response.raise_for_status()

            data = response.json()
            packages = data.get("packages", [])

            for package in packages[:limit] if limit else packages:
                try:
                    bill_data = self._process_govinfo_package(package)
                    if bill_data:
                        self._insert_bills_batch([bill_data], "govinfo")
                        ingested_count += 1

                        if ingested_count % 10 == 0:
                            logger.info(f"GovInfo: Processed {ingested_count} bills")

                except Exception as e:
                    logger.error(
                        f"Error processing GovInfo package {package.get('packageId')}: {e}"
                    )
                    continue

                # Rate limiting
                time.sleep(0.2)

        except Exception as e:
            logger.error(f"Error in GovInfo ingestion: {e}")

        self.stats["by_source"]["govinfo"] = ingested_count
        logger.info(f"GovInfo ingestion completed: {ingested_count} bills")
        return ingested_count

    def ingest_openstates_bills(
        self, state: str = "ca", limit: Optional[int] = None
    ) -> int:
        """Ingest bills from OpenStates API"""
        logger.info(f"Starting OpenStates bills ingestion for state {state}")

        base_url = "https://v3.openstates.org"
        headers = {
            "X-API-Key": self.config.openstates_api_key,
            "Accept": "application/json",
        }

        ingested_count = 0
        page = 1

        while True:
            try:
                # Get bills list
                url = f"{base_url}/bills"
                params = {
                    "jurisdiction": f"ocd-jurisdiction/country:us/state:{state}/government",
                    "page": page,
                    "per_page": min(self.config.batch_size, 50),
                    "sort": "updated_desc",
                    "include": "sponsorships,actions,documents",
                }

                response = self.session.get(
                    url,
                    headers=headers,
                    params=params,
                    timeout=self.config.request_timeout,
                )
                response.raise_for_status()

                data = response.json()
                bills = data.get("results", [])

                if not bills:
                    break

                # Process bills
                batch_data = []
                for bill in bills:
                    bill_data = self._process_openstates_bill(bill, state)
                    if bill_data:
                        batch_data.append(bill_data)

                # Insert batch
                if batch_data:
                    self._insert_bills_batch(batch_data, "openstates")
                    ingested_count += len(batch_data)
                    logger.info(f"OpenStates {state}: Processed {ingested_count} bills")

                # Check limits
                if limit and ingested_count >= limit:
                    break

                # Check pagination
                pagination = data.get("pagination", {})
                if not pagination.get("next"):
                    break

                page += 1

                # Rate limiting
                time.sleep(0.1)

            except Exception as e:
                logger.error(f"Error in OpenStates ingestion: {e}")
                break

        self.stats["by_source"]["openstates"] = ingested_count
        logger.info(f"OpenStates ingestion completed: {ingested_count} bills")
        return ingested_count

    def _process_congress_bill(self, bill: Dict, congress: int) -> Optional[Dict]:
        """Process bill from Congress.gov API"""
        try:
            bill_id = bill.get("bill", "").replace(".", "")
            if not bill_id:
                return None

            # Extract bill components
            parts = bill_id.split("-")
            if len(parts) < 2:
                return None

            bill_type = parts[0]
            bill_number = int(parts[1]) if parts[1].isdigit() else None

            # Get detailed bill information
            detail_url = (
                f"https://api.congress.gov/v3/bill/{congress}/{bill_type}/{bill_number}"
            )
            headers = {
                "X-API-Key": self.config.congress_api_key,
                "Accept": "application/json",
            }

            detail_response = self.session.get(detail_url, headers=headers, timeout=10)
            if detail_response.status_code != 200:
                logger.warning(
                    f"Failed to get details for {bill_id}: {detail_response.status_code}"
                )
                return None

            detail_data = detail_response.json().get("bill", {})

            # Extract sponsor information
            sponsor_info = (
                detail_data.get("sponsors", [{}])[0]
                if detail_data.get("sponsors")
                else {}
            )
            sponsor_bioguide_id = sponsor_info.get("bioguideId")

            # Get sponsor party and state from members table
            sponsor_party = None
            sponsor_state = None
            if sponsor_bioguide_id:
                sponsor_party, sponsor_state = self._get_member_info(
                    sponsor_bioguide_id
                )

            # Extract policy area and subjects
            policy_area = detail_data.get("policyArea", {}).get("name")
            subjects = [subj.get("name") for subj in detail_data.get("subjects", [])]

            # Extract latest action
            latest_action = detail_data.get("latestAction", {})
            latest_action_text = latest_action.get("text")
            latest_action_date = self._parse_date(latest_action.get("actionDate"))

            return {
                "bill_id": bill_id,
                "congress_number": congress,
                "bill_type": bill_type,
                "bill_number": bill_number,
                "official_title": detail_data.get("title"),
                "short_title": detail_data.get("shortTitle"),
                "introduced_date": self._parse_date(detail_data.get("introducedDate")),
                "updated_date": datetime.now(),
                "sponsor_bioguide_id": sponsor_bioguide_id,
                "sponsor_party": sponsor_party,
                "sponsor_state": sponsor_state,
                "committee_code": detail_data.get("committees", [{}])[0].get("code")
                if detail_data.get("committees")
                else None,
                "policy_area": policy_area,
                "subjects": subjects,
                "summary": detail_data.get("summary", {}).get("text"),
                "latest_action": latest_action_text,
                "latest_action_date": latest_action_date,
                "status": detail_data.get("status"),
                "source": "congress",
                "raw_data": detail_data,
            }

        except Exception as e:
            logger.error(
                f"Error processing Congress bill {bill.get('bill', 'unknown')}: {e}"
            )
            return None

    def _process_govinfo_package(self, package: Dict) -> Optional[Dict]:
        """Process bill package from GovInfo API"""
        try:
            package_id = package.get("packageId")
            if not package_id:
                return None

            # Parse package ID to extract bill info
            # Example: BILLS-118hr1234-ih
            parts = package_id.split("-")
            if len(parts) < 3:
                return None

            congress_part = parts[1]
            bill_part = parts[2]

            # Extract congress number
            congress = int(congress_part[:3]) if congress_part[:3].isdigit() else None

            # Extract bill type and number
            bill_type = None
            bill_number = None

            for bill_type_code in [
                "hr",
                "s",
                "hres",
                "sres",
                "hjres",
                "sjres",
                "hconres",
                "sconres",
            ]:
                if bill_part.startswith(bill_type_code):
                    bill_type = bill_type_code.upper()
                    number_part = bill_part[len(bill_type_code) :]
                    bill_number = (
                        int("".join(filter(str.isdigit, number_part)))
                        if number_part
                        else None
                    )
                    break

            if not all([congress, bill_type, bill_number]):
                return None

            # Get detailed package information
            detail_url = f"https://api.govinfo.gov/packages/{package_id}"
            headers = {
                "X-Api-Key": self.config.govinfo_api_key,
                "Accept": "application/json",
            }

            detail_response = self.session.get(detail_url, headers=headers, timeout=10)
            if detail_response.status_code != 200:
                return None

            detail_data = detail_response.json()

            # Extract title and other information
            title = detail_data.get("title", "")
            summary = detail_data.get("summary", "")

            return {
                "bill_id": f"{bill_type}{bill_number}-{congress}",
                "congress_number": congress,
                "bill_type": bill_type,
                "bill_number": bill_number,
                "official_title": title,
                "short_title": None,
                "introduced_date": self._parse_date(detail_data.get("dateIssued")),
                "updated_date": datetime.now(),
                "sponsor_bioguide_id": None,
                "sponsor_party": None,
                "sponsor_state": None,
                "committee_code": None,
                "policy_area": None,
                "subjects": [],
                "summary": summary,
                "latest_action": None,
                "latest_action_date": None,
                "status": detail_data.get("status"),
                "source": "govinfo",
                "raw_data": detail_data,
            }

        except Exception as e:
            logger.error(
                f"Error processing GovInfo package {package.get('packageId', 'unknown')}: {e}"
            )
            return None

    def _process_openstates_bill(self, bill: Dict, state: str) -> Optional[Dict]:
        """Process bill from OpenStates API"""
        try:
            identifier = bill.get("identifier", "")
            if not identifier:
                return None

            # Extract bill type and number from identifier
            # Example: 2023-2024/CA/SB/1234
            parts = identifier.split("/")
            if len(parts) < 4:
                return None

            session = parts[0]
            bill_type = parts[2].upper()
            bill_number = parts[3]

            # Extract session year for congress number
            year = int(session.split("-")[0]) if "-" in session else int(session)
            congress = self._year_to_congress(year)

            # Extract sponsor information
            sponsorships = bill.get("sponsorships", [])
            primary_sponsor = None
            for sponsorship in sponsorships:
                if sponsorship.get("primary"):
                    primary_sponsor = sponsorship
                    break

            sponsor_bioguide_id = None
            sponsor_party = None
            sponsor_state = state.upper()

            if primary_sponsor:
                person = primary_sponsor.get("person", {})
                sponsor_name = person.get("name")
                # OpenStates doesn't provide bioguide ID directly
                # Would need additional mapping

            # Extract actions
            actions = bill.get("actions", [])
            latest_action = actions[0] if actions else None
            latest_action_text = (
                latest_action.get("description") if latest_action else None
            )
            latest_action_date = (
                self._parse_date(latest_action.get("date")) if latest_action else None
            )

            # Extract subjects
            subjects = [subj.get("name") for subj in bill.get("subject", [])]

            return {
                "bill_id": f"{bill_type}{bill_number}-{congress}",
                "congress_number": congress,
                "bill_type": bill_type,
                "bill_number": int(bill_number) if bill_number.isdigit() else None,
                "official_title": bill.get("title"),
                "short_title": bill.get("shortTitle"),
                "introduced_date": self._parse_date(bill.get("createdAt")),
                "updated_date": datetime.now(),
                "sponsor_bioguide_id": sponsor_bioguide_id,
                "sponsor_party": sponsor_party,
                "sponsor_state": sponsor_state,
                "committee_code": None,
                "policy_area": None,
                "subjects": subjects,
                "summary": bill.get("abstract"),
                "latest_action": latest_action_text,
                "latest_action_date": latest_action_date,
                "status": bill.get("status"),
                "source": "openstates",
                "raw_data": bill,
            }

        except Exception as e:
            logger.error(
                f"Error processing OpenStates bill {bill.get('identifier', 'unknown')}: {e}"
            )
            return None

    def _insert_bills_batch(self, bills: List[Dict], source: str):
        """Insert batch of bills into database"""
        if not bills:
            return

        try:
            with self.db_conn.cursor() as cursor:
                # Prepare data for insertion
                values = []
                for bill in bills:
                    values.append(
                        (
                            bill.get("bill_id"),
                            bill.get("congress_number"),
                            bill.get("bill_type"),
                            bill.get("bill_number"),
                            bill.get("official_title"),
                            bill.get("short_title"),
                            bill.get("introduced_date"),
                            bill.get("updated_date"),
                            bill.get("sponsor_bioguide_id"),
                            bill.get("sponsor_party"),
                            bill.get("sponsor_state"),
                            bill.get("committee_code"),
                            bill.get("policy_area"),
                            bill.get("subjects"),
                            bill.get("summary"),
                            bill.get("latest_action"),
                            bill.get("latest_action_date"),
                            bill.get("status"),
                            source,
                            json.dumps(bill.get("raw_data")),
                        )
                    )

                # Insert with ON CONFLICT handling
                query = """
                    INSERT INTO congress.bills_bulk (
                        bill_id, congress_number, bill_type, bill_number,
                        official_title, short_title, introduced_date, updated_date,
                        sponsor_bioguide_id, sponsor_party, sponsor_state,
                        committee_code, policy_area, subjects, summary,
                        latest_action, latest_action_date, status, source, raw_data
                    ) VALUES %s
                    ON CONFLICT (bill_id) DO UPDATE SET
                        official_title = EXCLUDED.official_title,
                        short_title = EXCLUDED.short_title,
                        updated_date = EXCLUDED.updated_date,
                        latest_action = EXCLUDED.latest_action,
                        latest_action_date = EXCLUDED.latest_action_date,
                        status = EXCLUDED.status,
                        raw_data = EXCLUDED.raw_data,
                        updated_at = NOW()
                """

                execute_values(cursor, query, values)
                self.db_conn.commit()

                self.stats["successful"] += len(bills)
                logger.info(f"Inserted {len(bills)} bills from {source}")

        except Exception as e:
            self.db_conn.rollback()
            self.stats["failed"] += len(bills)
            logger.error(f"Error inserting batch from {source}: {e}")
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

    def _year_to_congress(self, year: int) -> int:
        """Convert year to Congress number"""
        # Congress starts on odd years
        # Formula: congress = ((year - 1789) // 2) + 1
        return ((year - 1789) // 2) + 1

    def run_ingestion(
        self, sources: Optional[List[str]] = None, **kwargs
    ) -> Dict[str, Any]:
        """Run complete ingestion process"""
        self.stats["start_time"] = datetime.now()

        try:
            self.connect_database()
            self.create_tables()

            sources_to_process = sources or self.config.sources

            for source in sources_to_process:
                logger.info(f"Starting ingestion from {source}")

                try:
                    if source == "congress":
                        congress = kwargs.get("congress", 118)
                        limit = kwargs.get("congress_limit")
                        self.ingest_congress_bills(congress, limit)

                    elif source == "govinfo":
                        collection = kwargs.get("govinfo_collection", "BILLS")
                        limit = kwargs.get("govinfo_limit")
                        self.ingest_govinfo_bills(collection, limit)

                    elif source == "openstates":
                        state = kwargs.get("openstates_state", "ca")
                        limit = kwargs.get("openstates_limit")
                        self.ingest_openstates_bills(state, limit)

                    else:
                        logger.warning(f"Unknown source: {source}")

                except Exception as e:
                    logger.error(f"Error in {source} ingestion: {e}")
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
        """Record ingestion statistics"""
        try:
            with self.db_conn.cursor() as cursor:
                query = """
                    INSERT INTO congress.ingestion_tracking (
                        source, ingestion_type, start_time, end_time,
                        total_records, successful_records, failed_records, status
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """

                cursor.execute(
                    query,
                    (
                        "bulk_bills",
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
            logger.error(f"Error recording ingestion tracking: {e}")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Bulk Bills Ingestion")
    parser.add_argument("--congress", type=int, default=118, help="Congress number")
    parser.add_argument("--congress-limit", type=int, help="Limit Congress.gov bills")
    parser.add_argument(
        "--govinfo-collection", default="BILLS", help="GovInfo collection"
    )
    parser.add_argument("--govinfo-limit", type=int, help="Limit GovInfo bills")
    parser.add_argument(
        "--openstates-state", default="ca", help="OpenStates state code"
    )
    parser.add_argument("--openstates-limit", type=int, help="Limit OpenStates bills")
    parser.add_argument(
        "--sources",
        nargs="+",
        choices=["congress", "govinfo", "openstates"],
        help="Sources to ingest from",
    )
    parser.add_argument("--batch-size", type=int, default=100, help="Batch size")
    parser.add_argument(
        "--dry-run", action="store_true", help="Dry run (no database changes)"
    )

    args = parser.parse_args()

    # Load configuration
    config = IngestionConfig(
        database_url=os.getenv("DATABASE_URL"),
        congress_api_key=os.getenv("CONGRESS_API_KEY"),
        govinfo_api_key=os.getenv("GOVINFO_API_KEY"),
        openstates_api_key=os.getenv("OPENSTATES_API_KEY"),
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

    if not config.openstates_api_key and "openstates" in (
        args.sources or config.sources
    ):
        logger.error(
            "OPENSTATES_API_KEY environment variable is required for OpenStates ingestion"
        )
        sys.exit(1)

    # Run ingestion
    ingestor = BulkBillsIngestor(config)

    try:
        stats = ingestor.run_ingestion(
            sources=args.sources,
            congress=args.congress,
            congress_limit=args.congress_limit,
            govinfo_collection=args.govinfo_collection,
            govinfo_limit=args.govinfo_limit,
            openstates_state=args.openstates_state,
            openstates_limit=args.openstates_limit,
        )

        # Print summary
        print("\n" + "=" * 50)
        print("BULK BILLS INGESTION SUMMARY")
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
        logger.error(f"Ingestion failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
