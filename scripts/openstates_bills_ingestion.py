#!/usr/bin/env python3
"""
OpenStates Bills Ingestion System
Comprehensive bills data ingestion with actions, votes, and relationships
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
# BILLS DATA MODELS
# ============================================================================

class BillActionModel(BaseModel):
    """Pydantic model for bill action data"""
    action_id: str
    bill_id: str
    description: str
    date: Optional[str] = None
    classification: Optional[str] = None
    organization: Optional[Dict[str, Any]] = None
    sources: List[Dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)


class BillVoteModel(BaseModel):
    """Pydantic model for bill vote data"""
    vote_id: str
    bill_id: str
    legislative_session: str
    motion_text: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    result: Optional[str] = None
    classification: Optional[str] = None
    organization: Optional[Dict[str, Any]] = None
    vote_counts: Optional[Dict[str, int]] = field(default_factory=dict)
    sources: List[Dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)


class BillSponsorshipModel(BaseModel):
    """Pydantic model for bill sponsorship data"""
    sponsorship_id: str
    bill_id: str
    person_id: Optional[str] = None
    organization_id: Optional[str] = None
    name: str
    role: Optional[str] = None
    classification: Optional[str] = None
    primary: bool = False
    created_at: datetime = field(default_factory=datetime.now)


# ============================================================================
# BILLS DATA VALIDATOR
# ============================================================================

class BillsDataValidator(OpenStatesDataValidator):
    """Extended data validator for bills-specific data"""

    def validate_bill_action_data(self, action_data: Dict[str, Any]) -> Optional[BillActionModel]:
        """Validate bill action data"""
        try:
            normalized_data = self._normalize_action_fields(action_data)
            action = BillActionModel(**normalized_data)
            return action
        except ValidationError as e:
            self.logger.warning(f"Bill action validation failed: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error validating bill action data: {e}")
            return None

    def validate_bill_vote_data(self, vote_data: Dict[str, Any]) -> Optional[BillVoteModel]:
        """Validate bill vote data"""
        try:
            normalized_data = self._normalize_vote_fields(vote_data)
            vote = BillVoteModel(**normalized_data)
            return vote
        except ValidationError as e:
            self.logger.warning(f"Bill vote validation failed: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error validating bill vote data: {e}")
            return None

    def validate_sponsorship_data(self, sponsorship_data: Dict[str, Any]) -> Optional[BillSponsorshipModel]:
        """Validate bill sponsorship data"""
        try:
            normalized_data = self._normalize_sponsorship_fields(sponsorship_data)
            sponsorship = BillSponsorshipModel(**normalized_data)
            return sponsorship
        except ValidationError as e:
            self.logger.warning(f"Sponsorship validation failed: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error validating sponsorship data: {e}")
            return None

    def _normalize_action_fields(self, action_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize bill action data fields"""
        return {
            'action_id': action_data.get('id', f"{action_data.get('bill_id', '')}_{action_data.get('date', '')}_{hash(action_data.get('description', ''))}"),
            'bill_id': action_data.get('bill_id', ''),
            'description': action_data.get('description', ''),
            'date': action_data.get('date'),
            'classification': action_data.get('classification', ''),
            'organization': action_data.get('organization', {}),
            'sources': action_data.get('sources', [])
        }

    def _normalize_vote_fields(self, vote_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize bill vote data fields"""
        return {
            'vote_id': vote_data.get('id', f"{vote_data.get('bill_id', '')}_{vote_data.get('start_date', '')}"),
            'bill_id': vote_data.get('bill_id', ''),
            'legislative_session': vote_data.get('legislative_session', ''),
            'motion_text': vote_data.get('motion_text', ''),
            'start_date': self._parse_datetime(vote_data.get('start_date')),
            'end_date': self._parse_datetime(vote_data.get('end_date')),
            'result': vote_data.get('result', ''),
            'classification': vote_data.get('classification', ''),
            'organization': vote_data.get('organization', {}),
            'vote_counts': vote_data.get('vote_counts', {}),
            'sources': vote_data.get('sources', [])
        }

    def _normalize_sponsorship_fields(self, sponsorship_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize sponsorship data fields"""
        person = sponsorship_data.get('person', {})
        organization = sponsorship_data.get('organization', {})

        return {
            'sponsorship_id': sponsorship_data.get('id', f"{sponsorship_data.get('bill_id', '')}_{person.get('id', '')}_{organization.get('id', '')}"),
            'bill_id': sponsorship_data.get('bill_id', ''),
            'person_id': person.get('id') if person else None,
            'organization_id': organization.get('id') if organization else None,
            'name': sponsorship_data.get('name', person.get('name', organization.get('name', ''))),
            'role': sponsorship_data.get('role', ''),
            'classification': sponsorship_data.get('classification', ''),
            'primary': sponsorship_data.get('primary', False)
        }


# ============================================================================
# BILLS INGESTOR
# ============================================================================

class OpenStatesBillsIngestor:
    """Comprehensive bills data ingestion with actions, votes, and relationships"""

    def __init__(self, db_conn, rate_manager: OpenStatesRateLimitManager,
                 pagination_manager: OpenStatesPaginationManager,
                 progress_monitor: OpenStatesProgressMonitor):
        self.db_conn = db_conn
        self.rate_manager = rate_manager
        self.pagination_manager = pagination_manager
        self.progress_monitor = progress_monitor
        self.validator = BillsDataValidator()
        self.logger = logging.getLogger(__name__)

        # API configuration
        self.api_key = get_optional_env_var('OPENSTATES_API_KEY')
        self.base_url = "https://v3.openstates.org"
        self.batch_size = 50
        self.max_retries = 3

    def ingest_bills_with_details(self, jurisdiction: str = None, session: str = None) -> Dict[str, Any]:
        """Ingest bills with full details and relationships"""
        self.logger.info(f"Starting comprehensive bills ingestion for jurisdiction: {jurisdiction}, session: {session}")

        results = {}

        # Phase 1: Basic bills data
        try:
            basic_result = self.ingest_bills(jurisdiction, session)
            results['basic_bills'] = basic_result
            self.logger.info(f"✅ Basic bills completed: {basic_result.get('records_processed', 0)} records")
        except Exception as e:
            self.logger.error(f"❌ Basic bills failed: {e}")
            results['basic_bills'] = {'error': str(e), 'success': False}

        # Phase 2: Bill details enrichment
        if basic_result.get('records_processed', 0) > 0:
            try:
                details_result = self.ingest_bill_details(jurisdiction, session)
                results['details_enrichment'] = details_result
                self.logger.info(f"✅ Bill details completed: {details_result.get('records_processed', 0)} records")
            except Exception as e:
                self.logger.error(f"❌ Bill details failed: {e}")
                results['details_enrichment'] = {'error': str(e), 'success': False}

        # Phase 3: Bill actions and votes
        try:
            actions_result = self.ingest_bill_actions(jurisdiction, session)
            results['actions_and_votes'] = actions_result
            self.logger.info(f"✅ Bill actions completed: {actions_result.get('records_processed', 0)} records")
        except Exception as e:
            self.logger.error(f"❌ Bill actions failed: {e}")
            results['actions_and_votes'] = {'error': str(e), 'success': False}

        # Phase 4: Bill sponsorships
        try:
            sponsorships_result = self.ingest_bill_sponsorships(jurisdiction, session)
            results['sponsorships'] = sponsorships_result
            self.logger.info(f"✅ Bill sponsorships completed: {sponsorships_result.get('records_processed', 0)} records")
        except Exception as e:
            self.logger.error(f"❌ Bill sponsorships failed: {e}")
            results['sponsorships'] = {'error': str(e), 'success': False}

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
            'session': session,
            'total_processed': total_processed,
            'phases_completed': success_count,
            'phases_total': len(results),
            'success_rate': (success_count / len(results)) * 100,
            'results': results
        }

        self.logger.info(f"🎉 Comprehensive bills ingestion completed: {total_processed} total records")
        return summary

    def ingest_bills(self, jurisdiction: str = None, session: str = None) -> Dict[str, Any]:
        """Ingest basic bills data with enhanced pagination and rate limiting"""
        self.logger.info(f"Ingesting basic bills for jurisdiction: {jurisdiction}, session: {session}")

        total_processed = 0
        total_skipped = 0
        page = 1
        empty_page_count = 0

        while True:
            # Rate limiting
            self.rate_manager.wait_if_needed()

            # Fetch bills
            bills_data = self.fetch_bills_batch(jurisdiction, session, page)
            bills = bills_data.get('results', [])

            if not bills:
                empty_page_count += 1
                if not self.pagination_manager.should_continue_pagination(bills_data, empty_page_count):
                    break
                continue

            self.logger.info(f"📦 Processing page {page} - {len(bills)} bills...")

            # Process bills with validation
            new_bills = []
            skipped_in_batch = 0

            for bill_data in bills:
                bill_id = bill_data.get('id')

                if not bill_id:
                    skipped_in_batch += 1
                    continue

                # Validate with Pydantic
                validated_bill = self.validator.validate_bill_data(bill_data)
                if not validated_bill:
                    skipped_in_batch += 1
                    continue

                # Check if already processed (fingerprinting)
                if self.is_bill_processed(bill_id, bill_data):
                    skipped_in_batch += 1
                    continue

                new_bills.append(validated_bill.dict())

            # Insert batch
            if new_bills:
                inserted = self.insert_bills_batch(new_bills)
                total_processed += inserted
                self.logger.info(f"   ✅ Inserted {inserted} new bills")
                self.rate_manager.handle_success()

            total_skipped += skipped_in_batch

            # Update progress
            category = f"{jurisdiction}_{session}" if jurisdiction and session else jurisdiction or 'all'
            self.progress_monitor.update_progress('bills', category, total_processed, total_processed + total_skipped)

            # Check pagination
            if not self.pagination_manager.should_continue_pagination(bills_data, 0):
                break

            page += 1
            empty_page_count = 0

        self.logger.info(f"🎉 Bills ingestion completed: {total_processed} processed, {total_skipped} skipped")

        return {
            'records_processed': total_processed,
            'records_skipped': total_skipped,
            'final_page': page
        }

    def fetch_bills_batch(self, jurisdiction: str = None, session: str = None, page: int = 1) -> Dict[str, Any]:
        """Fetch a batch of bills from OpenStates API"""
        url = f"{self.base_url}/bills"
        params = {
            'apikey': self.api_key,
            'per_page': min(self.batch_size, 50),
            'page': page
        }

        if jurisdiction:
            params['jurisdiction'] = jurisdiction

        if session:
            params['session'] = session

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

    def is_bill_processed(self, bill_id: str, bill_data: Dict[str, Any]) -> bool:
        """Check if bill was already processed using fingerprinting"""
        cursor = self.db_conn.cursor()

        try:
            # Create content hash for fingerprinting
            content_hash = hashlib.sha256(
                json.dumps(bill_data, sort_keys=True).encode('utf-8')
            ).hexdigest()

            cursor.execute("""
                SELECT incremental.is_record_processed(
                    %s, %s, %s, %s::jsonb
                )
            """, ('openstates.org', 'bills', bill_id, json.dumps(bill_data)))

            result = cursor.fetchone()
            return result[0] if result else False
        finally:
            cursor.close()

    def insert_bills_batch(self, bills: List[Dict[str, Any]]) -> int:
        """Insert a batch of bills into the database"""
        if not bills:
            return 0

        cursor = self.db_conn.cursor()

        try:
            query = """
                INSERT INTO openstates.bills (
                    bill_id, identifier, title, classification, subject, abstract,
                    jurisdiction, legislative_session, sponsor, from_organization,
                    created_at, updated_at
                ) VALUES %s
                ON CONFLICT (bill_id) DO UPDATE SET
                    identifier = EXCLUDED.identifier,
                    title = EXCLUDED.title,
                    classification = EXCLUDED.classification,
                    subject = EXCLUDED.subject,
                    abstract = EXCLUDED.abstract,
                    jurisdiction = EXCLUDED.jurisdiction,
                    legislative_session = EXCLUDED.legislative_session,
                    sponsor = EXCLUDED.sponsor,
                    from_organization = EXCLUDED.from_organization,
                    updated_at = EXCLUDED.updated_at
            """

            values = [
                (
                    b['bill_id'], b['identifier'], b['title'], b['classification'],
                    b['subject'], b['abstract'], Json(b['jurisdiction']),
                    Json(b['legislative_session']), Json(b['sponsor']),
                    Json(b['from_organization']), b['created_at'], b['updated_at']
                )
                for b in bills
            ]

            execute_values(cursor, query, values)
            self.db_conn.commit()
            return len(bills)

        except Exception as e:
            self.db_conn.rollback()
            self.logger.error(f"Error inserting bills batch: {e}")
            raise
        finally:
            cursor.close()

    def ingest_bill_details(self, jurisdiction: str = None, session: str = None) -> Dict[str, Any]:
        """Enrich bills with detailed information"""
        self.logger.info(f"Ingesting bill details for jurisdiction: {jurisdiction}, session: {session}")

        # Get all bill IDs for the jurisdiction/session
        bill_ids = self.get_bill_ids(jurisdiction, session)

        if not bill_ids:
            self.logger.info("No bills found for details enrichment")
            return {'records_processed': 0, 'message': 'No bills found'}

        total_processed = 0
        total_skipped = 0

        # Process bills in batches
        for i in range(0, len(bill_ids), self.batch_size):
            batch_ids = bill_ids[i:i + self.batch_size]

            for bill_id in batch_ids:
                # Rate limiting
                self.rate_manager.wait_if_needed()

                try:
                    # Fetch bill details
                    bill_details = self.fetch_bill_details(bill_id)

                    if bill_details:
                        # Validate and insert
                        validated_bill = self.validator.validate_bill_data(bill_details)
                        if validated_bill:
                            self.insert_bill_details(validated_bill.dict())
                            total_processed += 1
                            self.rate_manager.handle_success()
                        else:
                            total_skipped += 1
                    else:
                        total_skipped += 1

                except Exception as e:
                    self.logger.error(f"Error processing bill details for {bill_id}: {e}")
                    total_skipped += 1

            # Update progress
            category = f"{jurisdiction}_{session}" if jurisdiction and session else jurisdiction or 'all'
            self.progress_monitor.update_progress('bill_details', category, total_processed, len(bill_ids))

        self.logger.info(f"🎉 Bill details completed: {total_processed} processed, {total_skipped} skipped")

        return {
            'records_processed': total_processed,
            'records_skipped': total_skipped
        }

    def fetch_bill_details(self, bill_id: str) -> Optional[Dict[str, Any]]:
        """Fetch detailed information for a specific bill"""
        url = f"{self.base_url}/bills/{bill_id}"
        params = {'apikey': self.api_key}

        try:
            response = requests.get(url, params=params, timeout=30)

            if response.status_code == 429:
                self.rate_manager.handle_rate_limit_error()
                return None

            response.raise_for_status()
            return response.json()

        except Exception as e:
            self.logger.error(f"Error fetching bill details for {bill_id}: {e}")
            return None

    def insert_bill_details(self, bill_data: Dict[str, Any]):
        """Insert enriched bill details"""
        cursor = self.db_conn.cursor()

        try:
            query = """
                UPDATE openstates.bills SET
                    title = %s,
                    abstract = %s,
                    subject = %s,
                    updated_at = %s
                WHERE bill_id = %s
            """

            cursor.execute(query, (
                bill_data.get('title'),
                bill_data.get('abstract'),
                bill_data.get('subject'),
                datetime.now(),
                bill_data['bill_id']
            ))

            self.db_conn.commit()

        except Exception as e:
            self.db_conn.rollback()
            self.logger.error(f"Error inserting bill details: {e}")
            raise
        finally:
            cursor.close()

    def ingest_bill_actions(self, jurisdiction: str = None, session: str = None) -> Dict[str, Any]:
        """Ingest bill actions and votes"""
        self.logger.info(f"Ingesting bill actions for jurisdiction: {jurisdiction}, session: {session}")

        # Get all bill IDs
        bill_ids = self.get_bill_ids(jurisdiction, session)

        if not bill_ids:
            self.logger.info("No bills found for actions ingestion")
            return {'records_processed': 0, 'message': 'No bills found'}

        total_processed = 0
        total_skipped = 0

        for bill_id in bill_ids:
            # Rate limiting
            self.rate_manager.wait_if_needed()

            try:
                # Fetch bill actions
                actions_data = self.fetch_bill_actions(bill_id)

                if actions_data:
                    # Process actions
                    for action_data in actions_data:
                        action_data['bill_id'] = bill_id

                        # Validate
                        validated_action = self.validator.validate_bill_action_data(action_data)
                        if validated_action:
                            self.insert_bill_action(validated_action.dict())
                            total_processed += 1
                        else:
                            total_skipped += 1

                    self.rate_manager.handle_success()
                else:
                    total_skipped += 1

            except Exception as e:
                self.logger.error(f"Error processing actions for bill {bill_id}: {e}")
                total_skipped += 1

        self.logger.info(f"🎉 Bill actions completed: {total_processed} processed, {total_skipped} skipped")

        return {
            'records_processed': total_processed,
            'records_skipped': total_skipped
        }

    def fetch_bill_actions(self, bill_id: str) -> Optional[List[Dict[str, Any]]]:
        """Fetch actions for a specific bill"""
        url = f"{self.base_url}/bills/{bill_id}/actions"
        params = {'apikey': self.api_key}

        try:
            response = requests.get(url, params=params, timeout=30)

            if response.status_code == 429:
                self.rate_manager.handle_rate_limit_error()
                return None

            response.raise_for_status()
            data = response.json()
            return data.get('results', [])

        except Exception as e:
            self.logger.error(f"Error fetching bill actions for {bill_id}: {e}")
            return None

    def insert_bill_action(self, action_data: Dict[str, Any]):
        """Insert bill action into database"""
        cursor = self.db_conn.cursor()

        try:
            query = """
                INSERT INTO openstates.bill_actions (
                    action_id, bill_id, description, date, classification,
                    organization, sources, created_at
                ) VALUES %s
                ON CONFLICT (action_id) DO UPDATE SET
                    description = EXCLUDED.description,
                    date = EXCLUDED.date,
                    classification = EXCLUDED.classification,
                    organization = EXCLUDED.organization,
                    sources = EXCLUDED.sources
            """

            values = [(
                action_data['action_id'], action_data['bill_id'], action_data['description'],
                action_data['date'], action_data['classification'],
                Json(action_data['organization']), Json(action_data['sources']),
                action_data['created_at']
            )]

            execute_values(cursor, query, values)
            self.db_conn.commit()

        except Exception as e:
            self.db_conn.rollback()
            self.logger.error(f"Error inserting bill action: {e}")
            raise
        finally:
            cursor.close()

    def ingest_bill_sponsorships(self, jurisdiction: str = None, session: str = None) -> Dict[str, Any]:
        """Ingest bill sponsorships"""
        self.logger.info(f"Ingesting bill sponsorships for jurisdiction: {jurisdiction}, session: {session}")

        # Get all bill IDs
        bill_ids = self.get_bill_ids(jurisdiction, session)

        if not bill_ids:
            self.logger.info("No bills found for sponsorships ingestion")
            return {'records_processed': 0, 'message': 'No bills found'}

        total_processed = 0
        total_skipped = 0

        for bill_id in bill_ids:
            # Rate limiting
            self.rate_manager.wait_if_needed()

            try:
                # Fetch bill sponsorships
                sponsorships_data = self.fetch_bill_sponsorships(bill_id)

                if sponsorships_data:
                    # Process sponsorships
                    for sponsorship_data in sponsorships_data:
                        sponsorship_data['bill_id'] = bill_id

                        # Validate
                        validated_sponsorship = self.validator.validate_sponsorship_data(sponsorship_data)
                        if validated_sponsorship:
                            self.insert_bill_sponsorship(validated_sponsorship.dict())
                            total_processed += 1
                        else:
                            total_skipped += 1

                    self.rate_manager.handle_success()
                else:
                    total_skipped += 1

            except Exception as e:
                self.logger.error(f"Error processing sponsorships for bill {bill_id}: {e}")
                total_skipped += 1

        self.logger.info(f"🎉 Bill sponsorships completed: {total_processed} processed, {total_skipped} skipped")

        return {
            'records_processed': total_processed,
            'records_skipped': total_skipped
        }

    def fetch_bill_sponsorships(self, bill_id: str) -> Optional[List[Dict[str, Any]]]:
        """Fetch sponsorships for a specific bill"""
        url = f"{self.base_url}/bills/{bill_id}/sponsorships"
        params = {'apikey': self.api_key}

        try:
            response = requests.get(url, params=params, timeout=30)

            if response.status_code == 429:
                self.rate_manager.handle_rate_limit_error()
                return None

            response.raise_for_status()
            data = response.json()
            return data.get('results', [])

        except Exception as e:
            self.logger.error(f"Error fetching bill sponsorships for {bill_id}: {e}")
            return None

    def insert_bill_sponsorship(self, sponsorship_data: Dict[str, Any]):
        """Insert bill sponsorship into database"""
        cursor = self.db_conn.cursor()

        try:
            query = """
                INSERT INTO openstates.bill_sponsorships (
                    sponsorship_id, bill_id, person_id, organization_id,
                    name, role, classification, primary, created_at
                ) VALUES %s
                ON CONFLICT (sponsorship_id) DO UPDATE SET
                    person_id = EXCLUDED.person_id,
                    organization_id = EXCLUDED.organization_id,
                    name = EXCLUDED.name,
                    role = EXCLUDED.role,
                    classification = EXCLUDED.classification,
                    primary = EXCLUDED.primary
            """

            values = [(
                sponsorship_data['sponsorship_id'], sponsorship_data['bill_id'],
                sponsorship_data['person_id'], sponsorship_data['organization_id'],
                sponsorship_data['name'], sponsorship_data['role'],
                sponsorship_data['classification'], sponsorship_data['primary'],
                sponsorship_data['created_at']
            )]

            execute_values(cursor, query, values)
            self.db_conn.commit()

        except Exception as e:
            self.db_conn.rollback()
            self.logger.error(f"Error inserting bill sponsorship: {e}")
            raise
        finally:
            cursor.close()

    def get_bill_ids(self, jurisdiction: str = None, session: str = None) -> List[str]:
        """Get all bill IDs for the given jurisdiction and session"""
        cursor = self.db_conn.cursor()

        try:
            query = "SELECT bill_id FROM openstates.bills WHERE 1=1"
            params = []

            if jurisdiction:
                query += " AND jurisdiction->>'id' = %s"
                params.append(jurisdiction)

            if session:
                query += " AND legislative_session->>'id' = %s"
                params.append(session)

            cursor.execute(query, params)
            results = cursor.fetchall()
            return [row[0] for row in results]

        finally:
            cursor.close()


# ============================================================================
# MAIN EXECUTION FOR BILLS
# ============================================================================

def main():
    """Main function for bills ingestion"""
    print("🚀 OpenStates Bills Ingestion System")
    print("=" * 40)

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

        # Initialize bills ingestor
        bills_ingestor = OpenStatesBillsIngestor(
            db_conn, rate_manager, pagination_manager, progress_monitor
        )

        # Example: Single jurisdiction bills ingestion
        print("\n📍 Ingesting bills for CA (2023 session)...")
        ca_result = bills_ingestor.ingest_bills_with_details('ca', '2023')
        print(f"✅ CA bills completed: {ca_result['total_processed']} records")

        # Example: Multiple jurisdictions
        jurisdictions = ['tx', 'ny', 'fl']
        print(f"\n📍 Ingesting bills for {len(jurisdictions)} jurisdictions...")

        total_processed = 0
        for jurisdiction in jurisdictions:
            result = bills_ingestor.ingest_bills_with_details(jurisdiction, '2023')
            total_processed += result['total_processed']
            print(f"✅ {jurisdiction} bills completed: {result['total_processed']} records")

        print(f"\n🎉 All bills ingestion completed: {total_processed} total records")

        # Display progress summary
        progress_summary = progress_monitor.get_summary()
        print(f"\n📊 Progress Summary:")
        print(f"   Total elapsed: {progress_summary.get('total_elapsed_seconds', 0):.1f}s")
        print(f"   Average rate: {progress_summary.get('average_rate', 0):.1f} records/s")

        db_conn.close()

    except Exception as e:
        print(f"❌ Fatal error: {e}")
        logging.error(f"Fatal error in bills ingestion: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
