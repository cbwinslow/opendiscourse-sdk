#!/usr/bin/env python3
"""
OpenStates Events Ingestion System
Comprehensive events data ingestion with participants and agenda
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
# EVENTS DATA MODELS
# ============================================================================

class EventParticipantModel(BaseModel):
    """Pydantic model for event participant data"""
    participant_id: str
    event_id: str
    person_id: Optional[str] = None
    organization_id: Optional[str] = None
    name: str
    role: Optional[str] = None
    note: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)


class EventAgendaItemModel(BaseModel):
    """Pydantic model for event agenda item data"""
    agenda_id: str
    event_id: str
    description: str
    order: int = 0
    notes: Optional[str] = None
    related_entities: List[Dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)


# ============================================================================
# EVENTS DATA VALIDATOR
# ============================================================================

class EventsDataValidator(OpenStatesDataValidator):
    """Extended data validator for events-specific data"""

    def validate_event_participant_data(self, participant_data: Dict[str, Any]) -> Optional[EventParticipantModel]:
        """Validate event participant data"""
        try:
            normalized_data = self._normalize_participant_fields(participant_data)
            participant = EventParticipantModel(**normalized_data)
            return participant
        except ValidationError as e:
            self.logger.warning(f"Event participant validation failed: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error validating event participant data: {e}")
            return None

    def validate_event_agenda_data(self, agenda_data: Dict[str, Any]) -> Optional[EventAgendaItemModel]:
        """Validate event agenda data"""
        try:
            normalized_data = self._normalize_agenda_fields(agenda_data)
            agenda = EventAgendaItemModel(**normalized_data)
            return agenda
        except ValidationError as e:
            self.logger.warning(f"Event agenda validation failed: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error validating event agenda data: {e}")
            return None

    def _normalize_participant_fields(self, participant_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize event participant data fields"""
        person = participant_data.get('person', {})
        organization = participant_data.get('organization', {})

        return {
            'participant_id': participant_data.get('id', f"{participant_data.get('event_id', '')}_{person.get('id', '')}_{organization.get('id', '')}"),
            'event_id': participant_data.get('event_id', ''),
            'person_id': person.get('id') if person else None,
            'organization_id': organization.get('id') if organization else None,
            'name': participant_data.get('name', person.get('name', organization.get('name', ''))),
            'role': participant_data.get('role', ''),
            'note': participant_data.get('note', '')
        }

    def _normalize_agenda_fields(self, agenda_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize event agenda data fields"""
        return {
            'agenda_id': agenda_data.get('id', f"{agenda_data.get('event_id', '')}_{agenda_data.get('order', 0)}"),
            'event_id': agenda_data.get('event_id', ''),
            'description': agenda_data.get('description', ''),
            'order': agenda_data.get('order', 0),
            'notes': agenda_data.get('notes', ''),
            'related_entities': agenda_data.get('related_entities', [])
        }


# ============================================================================
# EVENTS INGESTOR
# ============================================================================

class OpenStatesEventsIngestor:
    """Comprehensive events data ingestion with participants and agenda"""

    def __init__(self, db_conn, rate_manager: OpenStatesRateLimitManager,
                 pagination_manager: OpenStatesPaginationManager,
                 progress_monitor: OpenStatesProgressMonitor):
        self.db_conn = db_conn
        self.rate_manager = rate_manager
        self.pagination_manager = pagination_manager
        self.progress_monitor = progress_monitor
        self.validator = EventsDataValidator()
        self.logger = logging.getLogger(__name__)

        # API configuration
        self.api_key = get_optional_env_var('OPENSTATES_API_KEY')
        self.base_url = "https://v3.openstates.org"
        self.batch_size = 50
        self.max_retries = 3

    def ingest_events_with_details(self, jurisdiction: str = None) -> Dict[str, Any]:
        """Ingest events with full details and participants"""
        self.logger.info(f"Starting comprehensive events ingestion for jurisdiction: {jurisdiction}")

        results = {}

        # Phase 1: Basic events data
        try:
            basic_result = self.ingest_events(jurisdiction)
            results['basic_events'] = basic_result
            self.logger.info(f"✅ Basic events completed: {basic_result.get('records_processed', 0)} records")
        except Exception as e:
            self.logger.error(f"❌ Basic events failed: {e}")
            results['basic_events'] = {'error': str(e), 'success': False}

        # Phase 2: Event details enrichment
        if basic_result.get('records_processed', 0) > 0:
            try:
                details_result = self.ingest_event_details(jurisdiction)
                results['details_enrichment'] = details_result
                self.logger.info(f"✅ Event details completed: {details_result.get('records_processed', 0)} records")
            except Exception as e:
                self.logger.error(f"❌ Event details failed: {e}")
                results['details_enrichment'] = {'error': str(e), 'success': False}

        # Phase 3: Event participants
        try:
            participants_result = self.ingest_event_participants(jurisdiction)
            results['participants'] = participants_result
            self.logger.info(f"✅ Event participants completed: {participants_result.get('records_processed', 0)} records")
        except Exception as e:
            self.logger.error(f"❌ Event participants failed: {e}")
            results['participants'] = {'error': str(e), 'success': False}

        # Phase 4: Event agenda
        try:
            agenda_result = self.ingest_event_agenda(jurisdiction)
            results['agenda'] = agenda_result
            self.logger.info(f"✅ Event agenda completed: {agenda_result.get('records_processed', 0)} records")
        except Exception as e:
            self.logger.error(f"❌ Event agenda failed: {e}")
            results['agenda'] = {'error': str(e), 'success': False}

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

        self.logger.info(f"🎉 Comprehensive events ingestion completed: {total_processed} total records")
        return summary

    def ingest_events(self, jurisdiction: str = None) -> Dict[str, Any]:
        """Ingest basic events data with enhanced pagination and rate limiting"""
        self.logger.info(f"Ingesting basic events for jurisdiction: {jurisdiction}")

        total_processed = 0
        total_skipped = 0
        page = 1
        empty_page_count = 0

        while True:
            # Rate limiting
            self.rate_manager.wait_if_needed()

            # Fetch events
            events_data = self.fetch_events_batch(jurisdiction, page)
            events = events_data.get('results', [])

            if not events:
                empty_page_count += 1
                if not self.pagination_manager.should_continue_pagination(events_data, empty_page_count):
                    break
                continue

            self.logger.info(f"📦 Processing page {page} - {len(events)} events...")

            # Process events with validation
            new_events = []
            skipped_in_batch = 0

            for event_data in events:
                event_id = event_data.get('id')

                if not event_id:
                    skipped_in_batch += 1
                    continue

                # Validate with Pydantic
                validated_event = self.validator.validate_event_data(event_data)
                if not validated_event:
                    skipped_in_batch += 1
                    continue

                # Check if already processed (fingerprinting)
                if self.is_event_processed(event_id, event_data):
                    skipped_in_batch += 1
                    continue

                new_events.append(validated_event.dict())

            # Insert batch
            if new_events:
                inserted = self.insert_events_batch(new_events)
                total_processed += inserted
                self.logger.info(f"   ✅ Inserted {inserted} new events")
                self.rate_manager.handle_success()

            total_skipped += skipped_in_batch

            # Update progress
            category = jurisdiction or 'all'
            self.progress_monitor.update_progress('events', category, total_processed, total_processed + total_skipped)

            # Check pagination
            if not self.pagination_manager.should_continue_pagination(events_data, 0):
                break

            page += 1
            empty_page_count = 0

        self.logger.info(f"🎉 Events ingestion completed: {total_processed} processed, {total_skipped} skipped")

        return {
            'records_processed': total_processed,
            'records_skipped': total_skipped,
            'final_page': page
        }

    def fetch_events_batch(self, jurisdiction: str = None, page: int = 1) -> Dict[str, Any]:
        """Fetch a batch of events from OpenStates API"""
        url = f"{self.base_url}/events"
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

    def is_event_processed(self, event_id: str, event_data: Dict[str, Any]) -> bool:
        """Check if event was already processed using fingerprinting"""
        cursor = self.db_conn.cursor()

        try:
            # Create content hash for fingerprinting
            content_hash = hashlib.sha256(
                json.dumps(event_data, sort_keys=True).encode('utf-8')
            ).hexdigest()

            cursor.execute("""
                SELECT incremental.is_record_processed(
                    %s, %s, %s, %s::jsonb
                )
            """, ('openstates.org', 'events', event_id, json.dumps(event_data)))

            result = cursor.fetchone()
            return result[0] if result else False
        finally:
            cursor.close()

    def insert_events_batch(self, events: List[Dict[str, Any]]) -> int:
        """Insert a batch of events into the database"""
        if not events:
            return 0

        cursor = self.db_conn.cursor()

        try:
            query = """
                INSERT INTO openstates.events (
                    event_id, name, classification, description, jurisdiction,
                    start_date, end_date, status, location, created_at, updated_at
                ) VALUES %s
                ON CONFLICT (event_id) DO UPDATE SET
                    name = EXCLUDED.name,
                    classification = EXCLUDED.classification,
                    description = EXCLUDED.description,
                    jurisdiction = EXCLUDED.jurisdiction,
                    start_date = EXCLUDED.start_date,
                    end_date = EXCLUDED.end_date,
                    status = EXCLUDED.status,
                    location = EXCLUDED.location,
                    updated_at = EXCLUDED.updated_at
            """

            values = [
                (
                    e['event_id'], e['name'], e['classification'], e['description'],
                    Json(e['jurisdiction']), e['start_date'], e['end_date'],
                    e['status'], Json(e['location']), e['created_at'], e['updated_at']
                )
                for e in events
            ]

            execute_values(cursor, query, values)
            self.db_conn.commit()
            return len(events)

        except Exception as e:
            self.db_conn.rollback()
            self.logger.error(f"Error inserting events batch: {e}")
            raise
        finally:
            cursor.close()

    def ingest_event_details(self, jurisdiction: str = None) -> Dict[str, Any]:
        """Enrich events with detailed information"""
        self.logger.info(f"Ingesting event details for jurisdiction: {jurisdiction}")

        # Get all event IDs for the jurisdiction
        event_ids = self.get_event_ids(jurisdiction)

        if not event_ids:
            self.logger.info("No events found for details enrichment")
            return {'records_processed': 0, 'message': 'No events found'}

        total_processed = 0
        total_skipped = 0

        # Process events in batches
        for i in range(0, len(event_ids), self.batch_size):
            batch_ids = event_ids[i:i + self.batch_size]

            for event_id in batch_ids:
                # Rate limiting
                self.rate_manager.wait_if_needed()

                try:
                    # Fetch event details
                    event_details = self.fetch_event_details(event_id)

                    if event_details:
                        # Validate and insert
                        validated_event = self.validator.validate_event_data(event_details)
                        if validated_event:
                            self.insert_event_details(validated_event.dict())
                            total_processed += 1
                            self.rate_manager.handle_success()
                        else:
                            total_skipped += 1
                    else:
                        total_skipped += 1

                except Exception as e:
                    self.logger.error(f"Error processing event details for {event_id}: {e}")
                    total_skipped += 1

            # Update progress
            category = jurisdiction or 'all'
            self.progress_monitor.update_progress('event_details', category, total_processed, len(event_ids))

        self.logger.info(f"🎉 Event details completed: {total_processed} processed, {total_skipped} skipped")

        return {
            'records_processed': total_processed,
            'records_skipped': total_skipped
        }

    def fetch_event_details(self, event_id: str) -> Optional[Dict[str, Any]]:
        """Fetch detailed information for a specific event"""
        url = f"{self.base_url}/events/{event_id}"
        params = {'apikey': self.api_key}

        try:
            response = requests.get(url, params=params, timeout=30)

            if response.status_code == 429:
                self.rate_manager.handle_rate_limit_error()
                return None

            response.raise_for_status()
            return response.json()

        except Exception as e:
            self.logger.error(f"Error fetching event details for {event_id}: {e}")
            return None

    def insert_event_details(self, event_data: Dict[str, Any]):
        """Insert enriched event details"""
        cursor = self.db_conn.cursor()

        try:
            query = """
                UPDATE openstates.events SET
                    name = %s,
                    description = %s,
                    start_date = %s,
                    end_date = %s,
                    status = %s,
                    location = %s,
                    updated_at = %s
                WHERE event_id = %s
            """

            cursor.execute(query, (
                event_data.get('name'),
                event_data.get('description'),
                event_data.get('start_date'),
                event_data.get('end_date'),
                event_data.get('status'),
                Json(event_data.get('location', {})),
                datetime.now(),
                event_data['event_id']
            ))

            self.db_conn.commit()

        except Exception as e:
            self.db_conn.rollback()
            self.logger.error(f"Error inserting event details: {e}")
            raise
        finally:
            cursor.close()

    def ingest_event_participants(self, jurisdiction: str = None) -> Dict[str, Any]:
        """Ingest event participants"""
        self.logger.info(f"Ingesting event participants for jurisdiction: {jurisdiction}")

        # Get all event IDs
        event_ids = self.get_event_ids(jurisdiction)

        if not event_ids:
            self.logger.info("No events found for participants ingestion")
            return {'records_processed': 0, 'message': 'No events found'}

        total_processed = 0
        total_skipped = 0

        for event_id in event_ids:
            # Rate limiting
            self.rate_manager.wait_if_needed()

            try:
                # Fetch event participants
                participants_data = self.fetch_event_participants(event_id)

                if participants_data:
                    # Process participants
                    for participant_data in participants_data:
                        participant_data['event_id'] = event_id

                        # Validate
                        validated_participant = self.validator.validate_event_participant_data(participant_data)
                        if validated_participant:
                            self.insert_event_participant(validated_participant.dict())
                            total_processed += 1
                        else:
                            total_skipped += 1

                    self.rate_manager.handle_success()
                else:
                    total_skipped += 1

            except Exception as e:
                self.logger.error(f"Error processing participants for event {event_id}: {e}")
                total_skipped += 1

        self.logger.info(f"🎉 Event participants completed: {total_processed} processed, {total_skipped} skipped")

        return {
            'records_processed': total_processed,
            'records_skipped': total_skipped
        }

    def fetch_event_participants(self, event_id: str) -> Optional[List[Dict[str, Any]]]:
        """Fetch participants for a specific event"""
        url = f"{self.base_url}/events/{event_id}"
        params = {'apikey': self.api_key, 'include': 'participants'}

        try:
            response = requests.get(url, params=params, timeout=30)

            if response.status_code == 429:
                self.rate_manager.handle_rate_limit_error()
                return None

            response.raise_for_status()
            data = response.json()
            return data.get('participants', [])

        except Exception as e:
            self.logger.error(f"Error fetching event participants for {event_id}: {e}")
            return None

    def insert_event_participant(self, participant_data: Dict[str, Any]):
        """Insert event participant into database"""
        cursor = self.db_conn.cursor()

        try:
            query = """
                INSERT INTO openstates.event_participants (
                    participant_id, event_id, person_id, organization_id,
                    name, role, note, created_at
                ) VALUES %s
                ON CONFLICT (participant_id) DO UPDATE SET
                    person_id = EXCLUDED.person_id,
                    organization_id = EXCLUDED.organization_id,
                    name = EXCLUDED.name,
                    role = EXCLUDED.role,
                    note = EXCLUDED.note
            """

            values = [(
                participant_data['participant_id'], participant_data['event_id'],
                participant_data['person_id'], participant_data['organization_id'],
                participant_data['name'], participant_data['role'],
                participant_data['note'], participant_data['created_at']
            )]

            execute_values(cursor, query, values)
            self.db_conn.commit()

        except Exception as e:
            self.db_conn.rollback()
            self.logger.error(f"Error inserting event participant: {e}")
            raise
        finally:
            cursor.close()

    def ingest_event_agenda(self, jurisdiction: str = None) -> Dict[str, Any]:
        """Ingest event agenda"""
        self.logger.info(f"Ingesting event agenda for jurisdiction: {jurisdiction}")

        # Get all event IDs
        event_ids = self.get_event_ids(jurisdiction)

        if not event_ids:
            self.logger.info("No events found for agenda ingestion")
            return {'records_processed': 0, 'message': 'No events found'}

        total_processed = 0
        total_skipped = 0

        for event_id in event_ids:
            # Rate limiting
            self.rate_manager.wait_if_needed()

            try:
                # Fetch event agenda
                agenda_data = self.fetch_event_agenda(event_id)

                if agenda_data:
                    # Process agenda items
                    for agenda_item_data in agenda_data:
                        agenda_item_data['event_id'] = event_id

                        # Validate
                        validated_agenda = self.validator.validate_event_agenda_data(agenda_item_data)
                        if validated_agenda:
                            self.insert_event_agenda(validated_agenda.dict())
                            total_processed += 1
                        else:
                            total_skipped += 1

                    self.rate_manager.handle_success()
                else:
                    total_skipped += 1

            except Exception as e:
                self.logger.error(f"Error processing agenda for event {event_id}: {e}")
                total_skipped += 1

        self.logger.info(f"🎉 Event agenda completed: {total_processed} processed, {total_skipped} skipped")

        return {
            'records_processed': total_processed,
            'records_skipped': total_skipped
        }

    def fetch_event_agenda(self, event_id: str) -> Optional[List[Dict[str, Any]]]:
        """Fetch agenda for a specific event"""
        url = f"{self.base_url}/events/{event_id}"
        params = {'apikey': self.api_key, 'include': 'agenda'}

        try:
            response = requests.get(url, params=params, timeout=30)

            if response.status_code == 429:
                self.rate_manager.handle_rate_limit_error()
                return None

            response.raise_for_status()
            data = response.json()
            return data.get('agenda', [])

        except Exception as e:
            self.logger.error(f"Error fetching event agenda for {event_id}: {e}")
            return None

    def insert_event_agenda(self, agenda_data: Dict[str, Any]):
        """Insert event agenda item into database"""
        cursor = self.db_conn.cursor()

        try:
            query = """
                INSERT INTO openstates.event_agenda (
                    agenda_id, event_id, description, order, notes,
                    related_entities, created_at
                ) VALUES %s
                ON CONFLICT (agenda_id) DO UPDATE SET
                    description = EXCLUDED.description,
                    order = EXCLUDED.order,
                    notes = EXCLUDED.notes,
                    related_entities = EXCLUDED.related_entities
            """

            values = [(
                agenda_data['agenda_id'], agenda_data['event_id'],
                agenda_data['description'], agenda_data['order'],
                agenda_data['notes'], Json(agenda_data['related_entities']),
                agenda_data['created_at']
            )]

            execute_values(cursor, query, values)
            self.db_conn.commit()

        except Exception as e:
            self.db_conn.rollback()
            self.logger.error(f"Error inserting event agenda: {e}")
            raise
        finally:
            cursor.close()

    def get_event_ids(self, jurisdiction: str = None) -> List[str]:
        """Get all event IDs for the given jurisdiction"""
        cursor = self.db_conn.cursor()

        try:
            query = "SELECT event_id FROM openstates.events WHERE 1=1"
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
# MAIN EXECUTION FOR EVENTS
# ============================================================================

def main():
    """Main function for events ingestion"""
    print("🚀 OpenStates Events Ingestion System")
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

        # Initialize events ingestor
        events_ingestor = OpenStatesEventsIngestor(
            db_conn, rate_manager, pagination_manager, progress_monitor
        )

        # Example: Single jurisdiction events ingestion
        print("\n📍 Ingesting events for CA...")
        ca_result = events_ingestor.ingest_events_with_details('ca')
        print(f"✅ CA events completed: {ca_result['total_processed']} records")

        # Example: Multiple jurisdictions
        jurisdictions = ['tx', 'ny', 'fl']
        print(f"\n📍 Ingesting events for {len(jurisdictions)} jurisdictions...")

        total_processed = 0
        for jurisdiction in jurisdictions:
            result = events_ingestor.ingest_events_with_details(jurisdiction)
            total_processed += result['total_processed']
            print(f"✅ {jurisdiction} events completed: {result['total_processed']} records")

        print(f"\n🎉 All events ingestion completed: {total_processed} total records")

        # Display progress summary
        progress_summary = progress_monitor.get_summary()
        print(f"\n📊 Progress Summary:")
        print(f"   Total elapsed: {progress_summary.get('total_elapsed_seconds', 0):.1f}s")
        print(f"   Average rate: {progress_summary.get('average_rate', 0):.1f} records/s")

        db_conn.close()

    except Exception as e:
        print(f"❌ Fatal error: {e}")
        logging.error(f"Fatal error in events ingestion: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
