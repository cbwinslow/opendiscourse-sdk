#!/usr/bin/env python3
"""
Incremental OpenStates People Ingestion Script
"""

import hashlib
import json
import logging
import os
import sys
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import psycopg2
import requests
from env_config import get_optional_env_var, validate_api_keys
from psycopg2.extras import Json, execute_values
from rate_limiter import adaptive_limiters

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class IncrementalOpenStatesIngestor:
    """Incremental OpenStates people ingestion with checkpoint tracking"""

    def __init__(self):
        # Validate API key
        api_keys = validate_api_keys()
        if not api_keys["openstates.org"]:
            raise ValueError("OPENSTATES_API_KEY not found in environment variables")

        self.api_key = get_optional_env_var("OPENSTATES_API_KEY")
        self.base_url = "https://v3.openstates.org"
        self.batch_size = 50
        self.max_retries = 3

        # Database connection (env-driven with sensible defaults)
        db_host = os.getenv("DB_HOST", "localhost")
        db_port = os.getenv("DB_PORT", "5432")
        db_name = os.getenv("DB_NAME", "cbwinslow")
        db_user = os.getenv("DB_USER", "cbwinslow")
        db_password = os.getenv("DB_PASSWORD", None)
        self.db_conn = psycopg2.connect(
            dbname=db_name,
            user=db_user,
            password=db_password,
            host=db_host,
            port=db_port,
        )
        self.db_conn.autocommit = False

        # Setup logging
        self.logger = logging.getLogger(__name__)

        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def get_next_ingestion_params(self, jurisdiction: str = None) -> Dict[str, Any]:
        """Get next ingestion parameters from checkpoint"""
        cursor = self.db_conn.cursor()

        try:
            category = jurisdiction if jurisdiction else "all"

            cursor.execute(
                """
                SELECT * FROM incremental.get_next_ingestion_params(
                    %s, %s, %s
                )
            """,
                ("openstates.org", "people", category),
            )

            result = cursor.fetchone()
            if result:
                return {
                    "next_offset": result[0],
                    "next_page": result[1],
                    "start_from_id": result[2],
                    "start_from_timestamp": result[3],
                    "is_completed": result[4],
                }
            else:
                return {
                    "next_offset": 0,
                    "next_page": 1,
                    "start_from_id": None,
                    "start_from_timestamp": None,
                    "is_completed": False,
                }
        finally:
            cursor.close()

    def create_checkpoint(
        self, jurisdiction: str = None, total_estimated: int = None
    ) -> None:
        """Create or get checkpoint for this jurisdiction"""
        cursor = self.db_conn.cursor()

        try:
            category = jurisdiction if jurisdiction else "all"

            cursor.execute(
                """
                SELECT incremental.get_or_create_checkpoint(
                    %s, %s, %s, %s
                )
            """,
                ("openstates.org", "people", category, total_estimated),
            )

            self.db_conn.commit()
        finally:
            cursor.close()

    def update_checkpoint(
        self,
        jurisdiction: str = None,
        last_page: int = None,
        records_processed: int = 0,
        is_completed: bool = False,
    ) -> None:
        """Update checkpoint progress"""
        cursor = self.db_conn.cursor()

        try:
            category = jurisdiction if jurisdiction else "all"

            cursor.execute(
                """
                CALL incremental.update_checkpoint_progress(
                    %s, %s, %s,
                    NULL, %s, NULL, NULL,
                    %s, %s
                )
            """,
                (
                    "openstates.org",
                    "people",
                    category,
                    last_page,
                    records_processed,
                    is_completed,
                ),
            )

            self.db_conn.commit()
        except Exception as e:
            self.db_conn.rollback()
            self.logger.error(f"Failed to update checkpoint: {e}")
            raise
        finally:
            cursor.close()

    def is_record_processed(self, person_id: str, person_data: Dict[str, Any]) -> bool:
        """Check if record was already processed using fingerprinting"""
        cursor = self.db_conn.cursor()

        try:
            # Create content hash for fingerprinting
            content_hash = hashlib.sha256(
                json.dumps(person_data, sort_keys=True).encode("utf-8")
            ).hexdigest()

            cursor.execute(
                """
                SELECT incremental.is_record_processed(
                    %s, %s, %s, %s::jsonb
                )
            """,
                ("openstates.org", "people", person_id, json.dumps(person_data)),
            )

            result = cursor.fetchone()
            return result[0] if result else False
        finally:
            cursor.close()

    def fetch_people_batch(
        self, jurisdiction: str = None, page: int = 1
    ) -> Dict[str, Any]:
        """Fetch a batch of people from OpenStates API"""
        # Use adaptive rate limiting
        adaptive_limiters["openstates.org"].wait_for_token()

        url = f"{self.base_url}/people"
        params = {
            "apikey": self.api_key,
            "per_page": min(self.batch_size, 50),  # OpenStates max is 50
            "page": page,
        }

        if jurisdiction:
            params["jurisdiction"] = jurisdiction

        for attempt in range(self.max_retries):
            try:
                response = requests.get(url, params=params, timeout=30)

                # Update rate limiter based on response
                adaptive_limiters["openstates.org"].update_from_response(
                    response.headers
                )
                adaptive_limiters["openstates.org"].handle_error(response.status_code)

                response.raise_for_status()

                data = response.json()

                if "results" not in data:
                    self.logger.warning("No 'results' key in API response")
                    return {"results": [], "pagination": {}}

                return data

            except requests.exceptions.RequestException as e:
                # Handle rate limit errors
                if hasattr(e, "response") and e.response.status_code == 429:
                    adaptive_limiters["openstates.org"].handle_error(429)
                    self.logger.warning(
                        f"Rate limit hit on attempt {attempt + 1}, waiting..."
                    )
                    time.sleep(5 * (attempt + 1))  # Exponential backoff
                    continue

                self.logger.error(f"API request failed on attempt {attempt + 1}: {e}")
                if attempt == self.max_retries - 1:
                    raise
                time.sleep(2**attempt)  # Exponential backoff

            except requests.exceptions.RequestException as e:
                if attempt == self.max_retries - 1:
                    raise
                self.logger.warning(f"Attempt {attempt + 1} failed: {e}")
                time.sleep(2**attempt)

        return {"results": [], "pagination": {}}

    def normalize_person_data(self, person_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize person data for database insertion"""
        # Handle jurisdiction - can be dict or string
        jurisdiction = person_data.get("jurisdiction", {})
        if isinstance(jurisdiction, str):
            jurisdiction_id = jurisdiction
        elif isinstance(jurisdiction, dict):
            jurisdiction_id = jurisdiction.get("id", "")
        else:
            jurisdiction_id = ""

        current_role = person_data.get("currentRole", {})

        return {
            "person_id": person_data.get("id"),
            "name": person_data.get("name"),
            "family_name": person_data.get("familyName"),
            "given_name": person_data.get("givenName"),
            "image": person_data.get("image"),
            "gender": person_data.get("gender"),
            "biography": person_data.get("biography"),
            "birth_date": self.parse_date(person_data.get("birthDate")),
            "death_date": self.parse_date(person_data.get("deathDate")),
            "primary_party": person_data.get("primaryParty", ""),
            "jurisdiction_id": jurisdiction_id,
            "current_role_data": Json(current_role) if current_role else None,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }

    def parse_date(self, date_str: Optional[str]) -> Optional[str]:
        """Parse date string in various formats"""
        if not date_str:
            return None

        try:
            # Try common date formats
            for fmt in ["%Y-%m-%d", "%Y/%m/%d", "%m/%d/%Y", "%Y-%m-%dT%H:%M:%S"]:
                try:
                    parsed_date = datetime.strptime(date_str, fmt)
                    return parsed_date.strftime("%Y-%m-%d")
                except ValueError:
                    continue

            # If no format matches, return None
            self.logger.warning(f"Could not parse date: {date_str}")
            return None

        except Exception as e:
            self.logger.warning(f"Error parsing date '{date_str}': {e}")
            return None

    def insert_people_batch(self, people: List[Dict[str, Any]]) -> int:
        """Insert a batch of people into the database"""
        if not people:
            return 0

        cursor = self.db_conn.cursor()

        try:
            query = """
                INSERT INTO openstates.people (
                    person_id, name, family_name, given_name, image, gender, biography,
                    birth_date, death_date, primary_party, jurisdiction_id,
                    current_role_data, created_at, updated_at
                ) VALUES %s
                ON CONFLICT (person_id) DO UPDATE SET
                    name = EXCLUDED.name,
                    family_name = EXCLUDED.family_name,
                    given_name = EXCLUDED.given_name,
                    image = EXCLUDED.image,
                    gender = EXCLUDED.gender,
                    biography = EXCLUDED.biography,
                    birth_date = EXCLUDED.birth_date,
                    death_date = EXCLUDED.death_date,
                    primary_party = EXCLUDED.primary_party,
                    jurisdiction_id = EXCLUDED.jurisdiction_id,
                    current_role_data = EXCLUDED.current_role_data,
                    updated_at = EXCLUDED.updated_at
            """

            values = [
                (
                    p["person_id"],
                    p["name"],
                    p["family_name"],
                    p["given_name"],
                    p["image"],
                    p["gender"],
                    p["biography"],
                    p["birth_date"],
                    p["death_date"],
                    p["primary_party"],
                    p["jurisdiction_id"],
                    p["current_role_data"],
                    p["created_at"],
                    p["updated_at"],
                )
                for p in people
            ]

            execute_values(cursor, query, values)
            self.db_conn.commit()
            return len(people)

        except Exception as e:
            self.db_conn.rollback()
            self.logger.error(f"Error inserting people batch: {e}")
            raise

    def start_ingestion_session(self, jurisdiction: str = None) -> str:
        """Start ingestion session tracking"""
        category = jurisdiction if jurisdiction else "all"
        session_id = (
            f"openstates_people_{category}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )

        cursor = self.db_conn.cursor()
        try:
            cursor.execute(
                """
                CALL incremental.start_ingestion_session(
                    %s, %s, %s, %s::jsonb
                )
            """,
                (
                    session_id,
                    "openstates.org",
                    "people",
                    json.dumps(
                        {"jurisdiction": jurisdiction, "batch_size": self.batch_size}
                    ),
                ),
            )
            self.db_conn.commit()
        finally:
            cursor.close()

        return session_id

    def complete_ingestion_session(
        self, session_id: str, status: str = "completed", error_summary: str = None
    ):
        """Complete ingestion session"""
        cursor = self.db_conn.cursor()
        try:
            cursor.execute(
                """
                CALL incremental.complete_ingestion_session(%s, %s, %s)
            """,
                (session_id, status, error_summary),
            )
            self.db_conn.commit()
        finally:
            cursor.close()

    def ingest_people(self, jurisdiction: str = None) -> Dict[str, Any]:
        """Ingest people data incrementally"""

        # Get checkpoint info
        params = self.get_next_ingestion_params(jurisdiction)

        if params["is_completed"]:
            jurisdiction_str = f" for {jurisdiction}" if jurisdiction else ""
            print(f"✅ OpenStates people{jurisdiction_str} already completed")
            return {
                "jurisdiction": jurisdiction,
                "status": "already_completed",
                "records_processed": 0,
                "records_skipped": 0,
            }

        # Create checkpoint if needed
        self.create_checkpoint(jurisdiction)

        # Start session
        session_id = self.start_ingestion_session(jurisdiction)

        jurisdiction_str = f" for {jurisdiction}" if jurisdiction else ""
        print(f"🚀 Starting incremental OpenStates people ingestion{jurisdiction_str}")
        print(f"📍 Starting from page: {params['next_page']}")

        try:
            page = params["next_page"]
            total_processed = 0
            total_skipped = 0

            while True:
                # Fetch batch
                batch_data = self.fetch_people_batch(jurisdiction, page)
                people = batch_data.get("results", [])

                if not people:
                    print("✅ No more people found")
                    break

                print(f"📦 Processing page {page} - {len(people)} people...")

                # Process each person
                new_people = []
                skipped_in_batch = 0

                for person_data in people:
                    person_id = person_data.get("id")

                    if not person_id:
                        skipped_in_batch += 1
                        continue

                    # Check if already processed
                    if self.is_record_processed(person_id, person_data):
                        skipped_in_batch += 1
                        continue

                    # Normalize and add to batch
                    try:
                        normalized = self.normalize_person_data(person_data)
                        if normalized["person_id"]:
                            new_people.append(normalized)
                    except Exception as e:
                        self.logger.error(f"Error normalizing person {person_id}: {e}")
                        skipped_in_batch += 1
                        continue

                # Insert new people
                if new_people:
                    inserted = self.insert_people_batch(new_people)
                    total_processed += inserted
                    print(f"   ✅ Inserted {inserted} new people")

                total_skipped += skipped_in_batch

                # Update checkpoint
                self.update_checkpoint(jurisdiction, page, len(new_people))

                # Check if we're done
                pagination = batch_data.get("pagination", {})
                max_page = pagination.get("max_page", 0)
                current_page = pagination.get("page", 0)

                print(f"   📄 Page {current_page} of {max_page}")

                if current_page >= max_page or len(people) < self.batch_size:
                    print("✅ Reached end of pagination")
                    break

                page += 1
                time.sleep(1)  # Rate limiting

            # Mark checkpoint as completed
            self.update_checkpoint(jurisdiction, page, 0, True)

            # Complete session
            self.complete_ingestion_session(session_id, "completed")

            print(f"🎉 OpenStates people ingestion{jurisdiction_str} completed!")
            print(f"📊 Processed: {total_processed}, Skipped: {total_skipped}")

            return {
                "jurisdiction": jurisdiction,
                "status": "completed",
                "records_processed": total_processed,
                "records_skipped": total_skipped,
                "final_page": page,
            }

        except Exception as e:
            self.complete_ingestion_session(session_id, "failed", str(e))
            raise

    def ingest_all_jurisdictions(self, jurisdictions: List[str] = None):
        """Ingest all jurisdictions or specific list"""
        if not jurisdictions:
            # Get all jurisdictions from API or use common ones
            jurisdictions = ["ca", "tx", "ny", "fl", "pa", "il", "oh", "ga", "nc", "mi"]

        print(
            f"🚀 Starting incremental ingestion for {len(jurisdictions)} jurisdictions"
        )

        results = []

        for jurisdiction in jurisdictions:
            try:
                result = self.ingest_people(jurisdiction)
                results.append(result)
                print(f"✅ Jurisdiction {jurisdiction} completed")
            except Exception as e:
                print(f"❌ Jurisdiction {jurisdiction} failed: {e}")
                results.append(
                    {"jurisdiction": jurisdiction, "status": "failed", "error": str(e)}
                )

        # Summary
        completed = sum(1 for r in results if r.get("status") == "completed")
        total_processed = sum(r.get("records_processed", 0) for r in results)
        total_skipped = sum(r.get("records_skipped", 0) for r in results)

        print("\n🎉 All jurisdictions ingestion completed!")
        print("📊 Summary:")
        print(f"   Jurisdictions completed: {completed}/{len(results)}")
        print(f"   Total records processed: {total_processed}")
        print(f"   Total records skipped: {total_skipped}")

        return results

    def get_checkpoint_status(self):
        """Get status of all checkpoints"""
        cursor = self.db_conn.cursor()

        try:
            cursor.execute(
                "SELECT * FROM incremental.checkpoint_status WHERE data_source = 'openstates.org'"
            )
            checkpoints = cursor.fetchall()

            print("\n📋 OpenStates.org Checkpoint Status:")
            print("-" * 80)
            for cp in checkpoints:
                completion_pct = cp[8] if cp[8] is not None else 0.0
                last_run = cp[9] if cp[9] is not None else "Never"
                print(
                    f"{cp[0]} | {cp[1]} | {cp[2]} | {cp[11]} | {completion_pct:.1f}% | {last_run}"
                )

            return checkpoints
        finally:
            cursor.close()


def main():
    """Main function"""
    ingestor = IncrementalOpenStatesIngestor()

    # Show current checkpoint status
    ingestor.get_checkpoint_status()

    # Ingest all people (or specific jurisdictions)
    results = ingestor.ingest_all_jurisdictions(["ca", "tx", "ny"])

    # Show final status
    ingestor.get_checkpoint_status()


if __name__ == "__main__":
    main()
