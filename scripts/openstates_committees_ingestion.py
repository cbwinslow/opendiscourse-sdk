#!/usr/bin/env python3
"""
OpenStates Committees Ingestion System
Comprehensive committees data ingestion with memberships and details
"""

import os
import sys
import requests
import hashlib
import json
import time
import logging
import psycopg2
import threading
import concurrent.futures
from psycopg2.extras import execute_values, Json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from pydantic import BaseModel, ValidationError
from enum import Enum

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rate_limiter import adaptive_limiters
from env_config import get_optional_env_var, validate_api_keys
from enhanced_openstates_ingestion import (
    OpenStatesRateLimitManager, OpenStatesPaginationManager,
    OpenStatesDataValidator, OpenStatesProgressMonitor
)


# ============================================================================
# COMMITTEES DATA MODELS
# ============================================================================

class CommitteeMemberModel(BaseModel):
    """Pydantic model for committee member data"""
    membership_id: str
    committee_id: str
    person_id: Optional[str] = None
    name: str
    role: Optional[str] = None
    person_name: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)


class CommitteeMeetingModel(BaseModel):
    """Pydantic model for committee meeting data"""
    meeting_id: str
    committee_id: str
    name: str
    description: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: Optional[str] = None
    location: Optional[Dict[str, Any]] = None
    created_at: datetime = field(default_factory=datetime.now)


# ============================================================================
# COMMITTEES DATA VALIDATOR
# ============================================================================

class CommitteesDataValidator(OpenStatesDataValidator):
    """Extended data validator for committees-specific data"""

    def validate_committee_member_data(self, member_data: Dict[str, Any]) -> Optional[CommitteeMemberModel]:
        """Validate committee member data"""
        try:
            normalized_data = self._normalize_member_fields(member_data)
            member = CommitteeMemberModel(**normalized_data)
            return member
        except ValidationError as e:
            self.logger.warning(f"Committee member validation failed: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error validating committee member data: {e}")
            return None

    def validate_committee_meeting_data(self, meeting_data: Dict[str, Any]) -> Optional[CommitteeMeetingModel]:
        """Validate committee meeting data"""
        try:
            normalized_data = self._normalize_meeting_fields(meeting_data)
            meeting = CommitteeMeetingModel(**normalized_data)
            return meeting
        except ValidationError as e:
            self.logger.warning(f"Committee meeting validation failed: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error validating committee meeting data: {e}")
            return None

    def _normalize_member_fields(self, member_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize committee member data fields"""
        person = member_data.get('person', {})

        return {
            'membership_id': member_data.get('id', f"{member_data.get('committee_id', '')}_{person.get('id', '')}_{member_data.get('role', '')}"),
            'committee_id': member_data.get('committee_id', ''),
            'person_id': person.get('id') if person else None,
            'name': member_data.get('name', person.get('name', '')),
            'role': member_data.get('role', ''),
            'person_name': person.get('name') if person else None,
            'start_date': member_data.get('start_date'),
            'end_date': member_data.get('end_date')
        }

    def _normalize_meeting_fields(self, meeting_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize committee meeting data fields"""
        return {
            'meeting_id': meeting_data.get('id', f"{meeting_data.get('committee_id', '')}_{meeting_data.get('start_date', '')}"),
            'committee_id': meeting_data.get('committee_id', ''),
            'name': meeting_data.get('name', ''),
            'description': meeting_data.get('description', ''),
            'start_date': self._parse_datetime(meeting_data.get('start_date')),
            'end_date': self._parse_datetime(meeting_data.get('end_date')),
            'status': meeting_data.get('status', ''),
            'location': meeting_data.get('location', {})
        }


# ============================================================================
# COMMITTEES INGESTOR
# ============================================================================

class OpenStatesCommitteesIngestor:
    """Comprehensive committees data ingestion with memberships and details"""

    def __init__(self, db_conn, rate_manager: OpenStatesRateLimitManager,
                 pagination_manager: OpenStatesPaginationManager,
                 progress_monitor: OpenStatesProgressMonitor):
        self.db_conn = db_conn
        self.rate_manager = rate_manager
        self.pagination_manager = pagination_manager
        self.progress_monitor = progress_monitor
        self.validator = CommitteesDataValidator()
        self.logger = logging.getLogger(__name__)

        # API configuration
        self.api_key = get_optional_env_var('OPENSTATES_API_KEY')
        self.base_url = "https://v3.openstates.org"
        self.batch_size = 50
        self.max_retries = 3

    def ingest_committees_with_details(self, jurisdiction: str = None) -> Dict[str, Any]:
        """Ingest committees with full details and memberships"""
        self.logger.info(f"Starting comprehensive committees ingestion for jurisdiction: {jurisdiction}")

        results = {}

        # Phase 1: Basic committees data
        try:
            basic_result = self.ingest_committees(jurisdiction)
            results['basic_committees'] = basic_result
            self.logger.info(f"✅ Basic committees completed: {basic_result.get('records_processed', 0)} records")
        except Exception as e:
            self.logger.error(f"❌ Basic committees failed: {e}")
            results['basic_committees'] = {'error': str(e), 'success': False}

        # Phase 2: Committee details enrichment
        if basic_result.get('records_processed', 0) > 0:
            try:
                details_result = self.ingest_committee_details(jurisdiction)
                results['details_enrichment'] = details_result
                self.logger.info(f"✅ Committee details completed: {details_result.get('records_processed', 0)} records")
            except Exception as e:
                self.logger.error(f"❌ Committee details failed: {e}")
                results['details_enrichment'] = {'error': str(e), 'success': False}

        # Phase 3: Committee memberships
        try:
            memberships_result = self.ingest_committee_memberships(jurisdiction)
            results['memberships'] = memberships_result
            self.logger.info(f"✅ Committee memberships completed: {memberships_result.get('records_processed', 0)} records")
        except Exception as e:
            self.logger.error(f"❌ Committee memberships failed: {e}")
            results['memberships'] = {'error': str(e), 'success': False}

        # Phase 4: Committee meetings
        try:
            meetings_result = self.ingest_committee_meetings(jurisdiction)
            results['meetings'] = meetings_result
            self.logger.info(f"✅ Committee meetings completed: {meetings_result.get('records_processed', 0)} records")
        except Exception as e:
            self.logger.error(f"❌ Committee meetings failed: {e}")
            results['meetings'] = {'error': str(e), 'success': False}

        # Generate summary
        total_processed = sum(
            result.get('records_processed', 0)
            for result in results.values()
            if isinstance(result, dict) and 'records_processed' in result
        )

        success_count = sum(
            1 for result in results.values()
            if isinstance(result, dict) and result.get('success', True)
        )

        summary = {
            'jurisdiction': jurisdiction,
            'total_processed': total_processed,
            'phases_completed': success_count,
            'phases_total': len(results),
            'success_rate': (success_count / len(results)) * 100,
            'results': results
        }

        self.logger.info(f"🎉 Comprehensive committees ingestion completed: {total_processed} total records")
        return summary

    def ingest_committees(self, jurisdiction: str = None) -> Dict[str, Any]:
        """Ingest basic committees data with enhanced pagination and rate limiting"""
        self.logger.info(f"Ingesting basic committees for jurisdiction: {jurisdiction}")

        total_processed = 0
        total_skipped = 0
        page = 1
        empty_page_count = 0

        while True:
            # Rate limiting
            self.rate_manager.wait_if_needed()

            # Fetch committees
            committees_data = self.fetch_committees_batch(jurisdiction, page)
            committees = committees_data.get('results', [])

            if not committees:
                empty_page_count += 1
                if not self.pagination_manager.should_continue_pagination(committees_data, empty_page_count):
                    break
                continue

            self.logger.info(f"📦 Processing page {page} - {len(committees)} committees...")

            # Process committees with validation
            new_committees = []
            skipped_in_batch = 0

            for committee_data in committees:
                committee_id = committee_data.get('id')

                if not committee_id:
                    skipped_in_batch += 1
                    continue

                # Validate with Pydantic
                validated_committee = self.validator.validate_committee_data(committee_data)
                if not validated_committee:
                    skipped_in_batch += 1
                    continue

                # Check if already processed (fingerprinting)
                if self.is_committee_processed(committee_id, committee_data):
                    skipped_in_batch += 1
                    continue

                new_committees.append(validated_committee.dict())

            # Insert batch
            if new_committees:
                inserted = self.insert_committees_batch(new_committees)
                total_processed += inserted
                self.logger.info(f"   ✅ Inserted {inserted} new committees")
                self.rate_manager.handle_success()

            total_skipped += skipped_in_batch

            # Update progress
            category = jurisdiction or 'all'
            self.progress_monitor.update_progress('committees', category, total_processed, total_processed + total_skipped)

            # Check pagination
            if not self.pagination_manager.should_continue_pagination(committees_data, 0):
                break

            page += 1
            empty_page_count = 0

        self.logger.info(f"🎉 Committees ingestion completed: {total_processed} processed, {total_skipped} skipped")

        return {
            'records_processed': total_processed,
            'records_skipped': total_skipped,
            'final_page': page
        }

    def fetch_committees_batch(self, jurisdiction: str = None, page: int = 1) -> Dict[str, Any]:
        """Fetch a batch of committees from OpenStates API"""
        url = f"{self.base_url}/committees"
        params = {
            'apikey': self.api_key,
            'per_page': min(self.batch_size, 50),
            'page': page
        }

        if jurisdiction:
            params['jurisdiction'] = jurisdiction

        for attempt in range(self.max_retries):
            try:
                response = requests.get(url, params=params, timeout=30)

                # Handle rate limiting
                if response.status_code == 429:
                    self.rate_manager.handle_rate_limit_error()
                    continue

                response.raise_for_status()

                data = response.json()

                if 'results' not in data:
                    self.logger.warning("No 'results' key in API response")
                    return {'results': [], 'pagination': {}}

                return data

            except requests.exceptions.RequestException as e:
                self.logger.error(f"API request failed on attempt {attempt + 1}: {e}")
                if attempt == self.max_retries - 1:
                    raise
                time.sleep(2 ** attempt)  # Exponential backoff

        return {'results': [], 'pagination': {}}

    def is_committee_processed(self, committee_id: str, committee_data: Dict[str, Any]) -> bool:
        """Check if committee was already processed using fingerprinting"""
        cursor = self.db_conn.cursor()

        try:
            # Create content hash for fingerprinting
            content_hash = hashlib.sha256(
                json.dumps(committee_data, sort_keys=True).encode('utf-8')
            ).hexdigest()

            cursor.execute("""
                SELECT incremental.is_record_processed(
                    %s, %s, %s, %s::jsonb
                )
            """, ('openstates.org', 'committees', committee_id, json.dumps(committee_data)))

            result = cursor.fetchone()
            return result[0] if result else False
        finally:
            cursor.close()

    def insert_committees_batch(self, committees: List[Dict[str, Any]]) -> int:
        """Insert a batch of committees into the database"""
        if not committees:
            return 0

        cursor = self.db_conn.cursor()

        try:
            query = """
                INSERT INTO openstates.committees (
                    committee_id, name, classification, jurisdiction, parent,
                    sources, members, created_at, updated_at
                ) VALUES %s
                ON CONFLICT (committee_id) DO UPDATE SET
                    name = EXCLUDED.name,
                    classification = EXCLUDED.classification,
                    jurisdiction = EXCLUDED.jurisdiction,
                    parent = EXCLUDED.parent,
                    sources = EXCLUDED.sources,
                    members = EXCLUDED.members,
                    updated_at = EXCLUDED.updated_at
            """

            values = [
                (
                    c['committee_id'], c['name'], c['classification'],
                    Json(c['jurisdiction']), c['parent'],
                    Json(c['sources']), Json(c['members']),
                    c['created_at'], c['updated_at']
                )
                for c in committees
            ]

            execute_values(cursor, query, values)
            self.db_conn.commit()
            return len(committees)

        except Exception as e:
            self.db_conn.rollback()
            self.logger.error(f"Error inserting committees batch: {e}")
            raise
        finally:
            cursor.close()

    def ingest_committee_details(self, jurisdiction: str = None) -> Dict[str, Any]:
        """Enrich committees with detailed information"""
        self.logger.info(f"Ingesting committee details for jurisdiction: {jurisdiction}")

        # Get all committee IDs for the jurisdiction
        committee_ids = self.get_committee_ids(jurisdiction)

        if not committee_ids:
            self.logger.info("No committees found for details enrichment")
            return {'records_processed': 0, 'message': 'No committees found'}

        total_processed = 0
        total_skipped = 0

        # Process committees in batches
        for i in range(0, len(committee_ids), self.batch_size):
            batch_ids = committee_ids[i:i + self.batch_size]

            for committee_id in batch_ids:
                # Rate limiting
                self.rate_manager.wait_if_needed()

                try:
                    # Fetch committee details
                    committee_details = self.fetch_committee_details(committee_id)

                    if committee_details:
                        # Validate and insert
                        validated_committee = self.validator.validate_committee_data(committee_details)
                        if validated_committee:
                            self.insert_committee_details(validated_committee.dict())
                            total_processed += 1
                            self.rate_manager.handle_success()
                        else:
                            total_skipped += 1
                    else:
                        total_skipped += 1

                except Exception as e:
                    self.logger.error(f"Error processing committee details for {committee_id}: {e}")
                    total_skipped += 1

            # Update progress
            category = jurisdiction or 'all'
            self.progress_monitor.update_progress('committee_details', category, total_processed, len(committee_ids))

        self.logger.info(f"🎉 Committee details completed: {total_processed} processed, {total_skipped} skipped")

        return {
            'records_processed': total_processed,
            'records_skipped': total_skipped
        }

    def fetch_committee_details(self, committee_id: str) -> Optional[Dict[str, Any]]:
        """Fetch detailed information for a specific committee"""
        url = f"{self.base_url}/committees/{committee_id}"
        params = {'apikey': self.api_key}

        try:
            response = requests.get(url, params=params, timeout=30)

            if response.status_code == 429:
                self.rate_manager.handle_rate_limit_error()
                return None

            response.raise_for_status()
            return response.json()

        except Exception as e:
            self.logger.error(f"Error fetching committee details for {committee_id}: {e}")
            return None

    def insert_committee_details(self, committee_data: Dict[str, Any]):
        """Insert enriched committee details"""
        cursor = self.db_conn.cursor()

        try:
            query = """
                UPDATE openstates.committees SET
                    name = %s,
                    classification = %s,
                    parent = %s,
                    sources = %s,
                    members = %s,
                    updated_at = %s
                WHERE committee_id = %s
            """

            cursor.execute(query, (
                committee_data.get('name'),
                committee_data.get('classification'),
                committee_data.get('parent'),
                Json(committee_data.get('sources', [])),
                Json(committee_data.get('members', [])),
                datetime.now(),
                committee_data['committee_id']
            ))

            self.db_conn.commit()

        except Exception as e:
            self.db_conn.rollback()
            self.logger.error(f"Error inserting committee details: {e}")
            raise
        finally:
            cursor.close()

    def ingest_committee_memberships(self, jurisdiction: str = None) -> Dict[str, Any]:
        """Ingest committee memberships"""
        self.logger.info(f"Ingesting committee memberships for jurisdiction: {jurisdiction}")

        # Get all committee IDs
        committee_ids = self.get_committee_ids(jurisdiction)

        if not committee_ids:
            self.logger.info("No committees found for memberships ingestion")
            return {'records_processed': 0, 'message': 'No committees found'}

        total_processed = 0
        total_skipped = 0

        for committee_id in committee_ids:
            # Rate limiting
            self.rate_manager.wait_if_needed()

            try:
                # Fetch committee memberships
                memberships_data = self.fetch_committee_memberships(committee_id)

                if memberships_data:
                    # Process memberships
                    for membership_data in memberships_data:
                        membership_data['committee_id'] = committee_id

                        # Validate
                        validated_membership = self.validator.validate_committee_member_data(membership_data)
                        if validated_membership:
                            self.insert_committee_membership(validated_membership.dict())
                            total_processed += 1
                        else:
                            total_skipped += 1

                    self.rate_manager.handle_success()
                else:
                    total_skipped += 1

            except Exception as e:
                self.logger.error(f"Error processing memberships for committee {committee_id}: {e}")
                total_skipped += 1

        self.logger.info(f"🎉 Committee memberships completed: {total_processed} processed, {total_skipped} skipped")

        return {
            'records_processed': total_processed,
            'records_skipped': total_skipped
        }

    def fetch_committee_memberships(self, committee_id: str) -> Optional[List[Dict[str, Any]]]:
        """Fetch memberships for a specific committee"""
        url = f"{self.base_url}/committees/{committee_id}"
        params = {'apikey': self.api_key, 'include': 'members'}

        try:
            response = requests.get(url, params=params, timeout=30)

            if response.status_code == 429:
                self.rate_manager.handle_rate_limit_error()
                return None

            response.raise_for_status()
            data = response.json()
            return data.get('members', [])

        except Exception as e:
            self.logger.error(f"Error fetching committee memberships for {committee_id}: {e}")
            return None

    def insert_committee_membership(self, membership_data: Dict[str, Any]):
        """Insert committee membership into database"""
        cursor = self.db_conn.cursor()

        try:
            query = """
                INSERT INTO openstates.committee_memberships (
                    membership_id, committee_id, person_id, name, role,
                    person_name, start_date, end_date, created_at
                ) VALUES %s
                ON CONFLICT (membership_id) DO UPDATE SET
                    person_id = EXCLUDED.person_id,
                    name = EXCLUDED.name,
                    role = EXCLUDED.role,
                    person_name = EXCLUDED.person_name,
                    start_date = EXCLUDED.start_date,
                    end_date = EXCLUDED.end_date
            """

            values = [(
                membership_data['membership_id'], membership_data['committee_id'],
                membership_data['person_id'], membership_data['name'],
                membership_data['role'], membership_data['person_name'],
                membership_data['start_date'], membership_data['end_date'],
                membership_data['created_at']
            )]

            execute_values(cursor, query, values)
            self.db_conn.commit()

        except Exception as e:
            self.db_conn.rollback()
            self.logger.error(f"Error inserting committee membership: {e}")
            raise
        finally:
            cursor.close()

    def ingest_committee_meetings(self, jurisdiction: str = None) -> Dict[str, Any]:
        """Ingest committee meetings"""
        self.logger.info(f"Ingesting committee meetings for jurisdiction: {jurisdiction}")

        # Get all committee IDs
        committee_ids = self.get_committee_ids(jurisdiction)

        if not committee_ids:
            self.logger.info("No committees found for meetings ingestion")
            return {'records_processed': 0, 'message': 'No committees found'}

        total_processed = 0
        total_skipped = 0

        for committee_id in committee_ids:
            # Rate limiting
            self.rate_manager.wait_if_needed()

            try:
                # Fetch committee meetings
                meetings_data = self.fetch_committee_meetings(committee_id)

                if meetings_data:
                    # Process meetings
                    for meeting_data in meetings_data:
                        meeting_data['committee_id'] = committee_id

                        # Validate
                        validated_meeting = self.validator.validate_committee_meeting_data(meeting_data)
                        if validated_meeting:
                            self.insert_committee_meeting(validated_meeting.dict())
                            total_processed += 1
                        else:
                            total_skipped += 1

                    self.rate_manager.handle_success()
                else:
                    total_skipped += 1

            except Exception as e:
                self.logger.error(f"Error processing meetings for committee {committee_id}: {e}")
                total_skipped += 1

        self.logger.info(f"🎉 Committee meetings completed: {total_processed} processed, {total_skipped} skipped")

        return {
            'records_processed': total_processed,
            'records_skipped': total_skipped
        }

    def fetch_committee_meetings(self, committee_id: str) -> Optional[List[Dict[str, Any]]]:
        """Fetch meetings for a specific committee"""
        # Note: OpenStates API may not have a dedicated meetings endpoint
        # This would need to be implemented based on actual API capabilities
        # For now, return empty list as placeholder
        return []

    def insert_committee_meeting(self, meeting_data: Dict[str, Any]):
        """Insert committee meeting into database"""
        cursor = self.db_conn.cursor()

        try:
            query = """
                INSERT INTO openstates.committee_meetings (
                    meeting_id, committee_id, name, description,
                    start_date, end_date, status, location, created_at
                ) VALUES %s
                ON CONFLICT (meeting_id) DO UPDATE SET
                    name = EXCLUDED.name,
                    description = EXCLUDED.description,
                    start_date = EXCLUDED.start_date,
                    end_date = EXCLUDED.end_date,
                    status = EXCLUDED.status,
                    location = EXCLUDED.location
            """

            values = [(
                meeting_data['meeting_id'], meeting_data['committee_id'],
                meeting_data['name'], meeting_data['description'],
                meeting_data['start_date'], meeting_data['end_date'],
                meeting_data['status'], Json(meeting_data['location']),
                meeting_data['created_at']
            )]

            execute_values(cursor, query, values)
            self.db_conn.commit()

        except Exception as e:
            self.db_conn.rollback()
            self.logger.error(f"Error inserting committee meeting: {e}")
            raise
        finally:
            cursor.close()

    def get_committee_ids(self, jurisdiction: str = None) -> List[str]:
        """Get all committee IDs for the given jurisdiction"""
        cursor = self.db_conn.cursor()

        try:
            query = "SELECT committee_id FROM openstates.committees WHERE 1=1"
            params = []

            if jurisdiction:
                query += " AND jurisdiction->>'id' = %s"
                params.append(jurisdiction)

            cursor.execute(query, params)
            results = cursor.fetchall()
            return [row[0] for row in results]

        finally:
            cursor.close()


# ============================================================================
# MAIN EXECUTION FOR COMMITTEES
# ============================================================================

def main():
    """Main function for committees ingestion"""
    print("🚀 OpenStates Committees Ingestion System")
    print("=" * 45)

    try:
        # Initialize components
        rate_manager = OpenStatesRateLimitManager()
        pagination_manager = OpenStatesPaginationManager()
        progress_monitor = OpenStatesProgressMonitor()

        # Database connection
        db_conn = psycopg2.connect(
            database='cbwinslow',
            user='cbwinslow'
        )

        # Initialize committees ingestor
        committees_ingestor = OpenStatesCommitteesIngestor(
            db_conn, rate_manager, pagination_manager, progress_monitor
        )

        # Example: Single jurisdiction committees ingestion
        print("\n📍 Ingesting committees for CA...")
        ca_result = committees_ingestor.ingest_committees_with_details('ca')
        print(f"✅ CA committees completed: {ca_result['total_processed']} records")

        # Example: Multiple jurisdictions
        jurisdictions = ['tx', 'ny', 'fl']
        print(f"\n📍 Ingesting committees for {len(jurisdictions)} jurisdictions...")

        total_processed = 0
        for jurisdiction in jurisdictions:
            result = committees_ingestor.ingest_committees_with_details(jurisdiction)
            total_processed += result['total_processed']
            print(f"✅ {jurisdiction} committees completed: {result['total_processed']} records")

        print(f"\n🎉 All committees ingestion completed: {total_processed} total records")

        # Display progress summary
        progress_summary = progress_monitor.get_summary()
        print(f"\n📊 Progress Summary:")
        print(f"   Total elapsed: {progress_summary.get('total_elapsed_seconds', 0):.1f}s")
        print(f"   Average rate: {progress_summary.get('average_rate', 0):.1f} records/s")

        db_conn.close()

    except Exception as e:
        print(f"❌ Fatal error: {e}")
        logging.error(f"Fatal error in committees ingestion: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
