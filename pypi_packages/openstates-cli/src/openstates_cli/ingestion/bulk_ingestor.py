"""
Bulk data ingestion functions for OpenStates CLI with API endpoint mapping.
"""

import time
import json
import hashlib
from typing import Dict, Any, List, Optional, Callable, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging

from ..api.client import OpenStatesAPIClient, OpenStatesAPIBatchProcessor
from ..database.operations import DatabaseOperations
from ..utils.logger import get_logger
from ..utils.config import get_config


@dataclass
class OpenStatesEndpointMapping:
    """Mapping of OpenStates API endpoint to database table and processing function."""

    endpoint_path: str
    table_name: str
    data_type: str
    category: Optional[str] = None
    batch_size: int = 50
    rate_limit_delay: float = 0.15
    pagination_param: str = "page"
    max_retries: int = 3

    # Processing functions
    data_transformer: Optional[Callable[[List[Dict]], List[Dict]]] = None
    batch_processor: Optional[Callable[[List[Dict]], int]] = None
    progress_callback: Optional[Callable[[int, int], None]] = None


class OpenStatesRateLimitManager:
    """Rate limiting for OpenStates API with careful adherence to limits."""

    def __init__(self, base_delay: float = 0.15, max_delay: float = 5.0):
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.current_delay = base_delay
        self.last_request_time = None
        self.request_count = 0
        self.window_start = datetime.now()
        self.logger = get_logger(__name__)

    def wait_if_needed(self):
        """Wait if necessary to respect OpenStates rate limits (max 1000 requests/hour)."""
        now = datetime.now()

        # Reset window if more than 1 hour has passed
        if (now - self.window_start).total_seconds() > 3600:
            self.request_count = 0
            self.window_start = now

        # Check if we're approaching the limit
        if self.request_count >= 900:  # Safety margin
            remaining_time = 3600 - (now - self.window_start).total_seconds()
            if remaining_time > 0:
                self.logger.warning(f"Approaching hourly rate limit, waiting {remaining_time/60:.1f} minutes")
                time.sleep(remaining_time + 60)  # Extra safety margin
                self.request_count = 0
                self.window_start = datetime.now()

        # Base rate limiting (aim for ~1 request per 3.6 seconds to stay under limit)
        if self.last_request_time:
            elapsed = (now - self.last_request_time).total_seconds()
            if elapsed < self.current_delay:
                time.sleep(self.current_delay - elapsed)

        self.last_request_time = datetime.now()
        self.request_count += 1

    def handle_rate_limit_error(self):
        """Handle rate limit errors with exponential backoff."""
        self.current_delay = min(self.current_delay * 2, self.max_delay)
        self.logger.warning(f"Rate limit hit, increasing delay to {self.current_delay:.3f} seconds")
        time.sleep(self.current_delay)


class OpenStatesBulkIngestor:
    """Comprehensive bulk data ingestion for OpenStates API."""

    def __init__(self, config=None):
        """Initialize bulk ingestor with configuration."""
        self.config = config or get_config()
        self.api_client = OpenStatesAPIClient()
        self.db_ops = DatabaseOperations(self.config.database_url)
        self.rate_manager = OpenStatesRateLimitManager()
        self.logger = get_logger(__name__)

        # Track ingestion statistics
        self.ingestion_stats = {
            'total_records': 0,
            'processed_records': 0,
            'failed_records': 0,
            'start_time': datetime.now(),
            'endpoints_processed': []
        }

        # Setup endpoint mappings
        self._setup_endpoint_mappings()

    def _setup_endpoint_mappings(self):
        """Setup mappings between OpenStates API endpoints and database tables."""
        self.endpoint_mappings = {
            # People endpoints
            'people_search': OpenStatesEndpointMapping(
                endpoint_path="people",
                table_name="openstates.people",
                data_type="people",
                category="search",
                batch_size=50,
                rate_limit_delay=0.2,
                data_transformer=self._transform_people_data,
                batch_processor=self._process_people_batch
            ),

            'people_by_state': OpenStatesEndpointMapping(
                endpoint_path="people",
                table_name="openstates.people",
                data_type="people",
                category="{state}",
                batch_size=50,
                rate_limit_delay=0.2,
                data_transformer=self._transform_people_data,
                batch_processor=self._process_people_batch
            ),

            'person_details': OpenStatesEndpointMapping(
                endpoint_path="people/{person_id}",
                table_name="openstates.people",
                data_type="person_details",
                batch_size=1,
                rate_limit_delay=0.1,
                data_transformer=self._transform_person_details,
                batch_processor=self._process_people_batch
            ),

            # Bills endpoints
            'bills_search': OpenStatesEndpointMapping(
                endpoint_path="bills",
                table_name="openstates.bills",
                data_type="bills",
                category="search",
                batch_size=50,
                rate_limit_delay=0.2,
                data_transformer=self._transform_bills_data,
                batch_processor=self._process_bills_batch
            ),

            'bills_by_state': OpenStatesEndpointMapping(
                endpoint_path="bills",
                table_name="openstates.bills",
                data_type="bills",
                category="{state}",
                batch_size=50,
                rate_limit_delay=0.2,
                data_transformer=self._transform_bills_data,
                batch_processor=self._process_bills_batch
            ),

            'bill_details': OpenStatesEndpointMapping(
                endpoint_path="bills/{bill_id}",
                table_name="openstates.bills",
                data_type="bill_details",
                batch_size=1,
                rate_limit_delay=0.1,
                data_transformer=self._transform_bill_details,
                batch_processor=self._process_bills_batch
            ),

            'bills_by_person': OpenStatesEndpointMapping(
                endpoint_path="people/{person_id}/bills",
                table_name="openstates.bills",
                data_type="person_bills",
                category="{person_id}",
                batch_size=25,
                rate_limit_delay=0.15,
                data_transformer=self._transform_bills_data,
                batch_processor=self._process_bills_batch
            ),

            # Jurisdictions endpoints
            'jurisdictions': OpenStatesEndpointMapping(
                endpoint_path="jurisdictions",
                table_name="openstates.jurisdictions",
                data_type="jurisdictions",
                category="all",
                batch_size=100,
                rate_limit_delay=0.3,
                data_transformer=self._transform_jurisdictions_data,
                batch_processor=self._process_jurisdictions_batch
            ),

            'jurisdiction_details': OpenStatesEndpointMapping(
                endpoint_path="jurisdictions/{jurisdiction_id}",
                table_name="openstates.jurisdictions",
                data_type="jurisdiction_details",
                batch_size=1,
                rate_limit_delay=0.1,
                data_transformer=self._transform_jurisdiction_details,
                batch_processor=self._process_jurisdictions_batch
            ),

            # Committees endpoints
            'committees_by_state': OpenStatesEndpointMapping(
                endpoint_path="committees",
                table_name="openstates.committees",
                data_type="committees",
                category="{state}",
                batch_size=25,
                rate_limit_delay=0.2,
                data_transformer=self._transform_committees_data,
                batch_processor=self._process_committees_batch
            ),

            'committee_details': OpenStatesEndpointMapping(
                endpoint_path="committees/{committee_id}",
                table_name="openstates.committees",
                data_type="committee_details",
                batch_size=1,
                rate_limit_delay=0.1,
                data_transformer=self._transform_committee_details,
                batch_processor=self._process_committees_batch
            ),

            # Events endpoints
            'events_by_state': OpenStatesEndpointMapping(
                endpoint_path="events",
                table_name="openstates.events",
                data_type="events",
                category="{state}",
                batch_size=25,
                rate_limit_delay=0.2,
                data_transformer=self._transform_events_data,
                batch_processor=self._process_events_batch
            ),

            'event_details': OpenStatesEndpointMapping(
                endpoint_path="events/{event_id}",
                table_name="openstates.events",
                data_type="event_details",
                batch_size=1,
                rate_limit_delay=0.1,
                data_transformer=self._transform_event_details,
                batch_processor=self._process_events_batch
            )
        }

    def ingest_endpoint(self, endpoint_key: str, **path_params) -> Dict[str, Any]:
        """Ingest data from a specific OpenStates API endpoint."""
        if endpoint_key not in self.endpoint_mappings:
            raise ValueError(f"Unknown endpoint: {endpoint_key}")

        mapping = self.endpoint_mappings[endpoint_key]

        # Format endpoint path with parameters
        endpoint_path = mapping.endpoint_path
        for param, value in path_params.items():
            endpoint_path = endpoint_path.replace(f"{{{param}}}", str(value))

        # Get category with parameters
        category = mapping.category
        if category:
            for param, value in path_params.items():
                category = category.replace(f"{{{param}}}", str(value))

        self.logger.info(f"Starting OpenStates ingestion for endpoint: {endpoint_key}")

        # Get checkpoint for resuming
        checkpoint = self.db_ops.get_checkpoint('openstates.org', mapping.data_type, category)
        start_page = int(checkpoint.offset) if checkpoint and checkpoint else 1

        # Initialize statistics
        endpoint_stats = {
            'endpoint_key': endpoint_key,
            'endpoint_path': endpoint_path,
            'start_page': start_page,
            'total_processed': 0,
            'failed_batches': 0,
            'start_time': datetime.now()
        }

        try:
            # Perform bulk ingestion
            result = self._perform_bulk_ingestion(mapping, endpoint_path, path_params, start_page)

            endpoint_stats.update(result)
            endpoint_stats['end_time'] = datetime.now()
            endpoint_stats['duration'] = (endpoint_stats['end_time'] - endpoint_stats['start_time']).total_seconds()

            self.ingestion_stats['endpoints_processed'].append(endpoint_stats)

            self.logger.info(f"Completed OpenStates ingestion for {endpoint_key}: {result['total_processed']} records")
            return result

        except Exception as e:
            endpoint_stats['error'] = str(e)
            endpoint_stats['end_time'] = datetime.now()
            self.ingestion_stats['endpoints_processed'].append(endpoint_stats)

            self.logger.error(f"Failed OpenStates ingestion for {endpoint_key}: {e}")
            raise

    def _perform_bulk_ingestion(self, mapping: OpenStatesEndpointMapping, endpoint_path: str,
                              path_params: Dict[str, Any], start_page: int) -> Dict[str, Any]:
        """Perform bulk ingestion with pagination and rate limiting."""
        total_processed = 0
        failed_batches = 0
        current_page = start_page
        batch_count = 0

        # Setup rate limit for this endpoint
        self.rate_manager.current_delay = mapping.rate_limit_delay

        while True:
            batch_count += 1

            try:
                # Rate limiting
                self.rate_manager.wait_if_needed()

                # Fetch data with pagination
                self.logger.debug(f"Fetching OpenStates batch {batch_count} from {endpoint_path}, page {current_page}")

                # Build request parameters
                params = {
                    'page': current_page,
                    'per_page': mapping.batch_size
                }

                # Add path parameters to request
                if 'state' in path_params:
                    params['state'] = path_params['state']
                elif 'jurisdiction' in path_params:
                    params['jurisdiction'] = path_params['jurisdiction']

                # Make API request
                response = self.api_client._make_request(endpoint_path, params)

                if not response.get('results'):
                    self.logger.info(f"No more results at page {current_page}")
                    break

                # Get data from response
                batch_data = response['results']

                if not batch_data:
                    break

                # Apply data transformation if configured
                if mapping.data_transformer:
                    batch_data = mapping.data_transformer(batch_data, path_params)

                # Process batch
                if mapping.batch_processor:
                    processed_count = mapping.batch_processor(batch_data)
                else:
                    processed_count = self._default_batch_processor(batch_data, mapping.table_name)

                total_processed += processed_count

                # Update checkpoint
                next_page = current_page + 1
                self.db_ops.update_checkpoint(
                    'openstates.org', mapping.data_type,
                    mapping.category, str(next_page), total_processed
                )

                # Call progress callback if configured
                if mapping.progress_callback:
                    mapping.progress_callback(processed_count, total_processed)

                # Log progress
                if batch_count % 10 == 0:
                    self.logger.info(f"Processed {total_processed} records across {batch_count} batches")

                # Check if we're done
                pagination = response.get('pagination', {})
                if pagination.get('page') >= pagination.get('max_page', current_page):
                    break

                current_page = next_page

            except Exception as e:
                failed_batches += 1

                # Handle rate limit errors
                if "rate limit" in str(e).lower() or "429" in str(e):
                    self.rate_manager.handle_rate_limit_error()
                    continue

                # Handle other errors with retry logic
                if failed_batches < mapping.max_retries:
                    self.logger.warning(f"OpenStates batch {batch_count} failed, retrying ({failed_batches}/{mapping.max_retries}): {e}")
                    time.sleep(3 ** failed_batches)  # Exponential backoff
                    continue
                else:
                    self.logger.error(f"OpenStates batch {batch_count} failed after {mapping.max_retries} retries: {e}")
                    raise

        return {
            'total_processed': total_processed,
            'failed_batches': failed_batches,
            'batch_count': batch_count,
            'final_page': current_page
        }

    def _default_batch_processor(self, batch_data: List[Dict], table_name: str) -> int:
        """Default batch processor for inserting data."""
        try:
            # Generate fingerprints for deduplication
            for record in batch_data:
                record['fingerprint'] = self._generate_fingerprint(record)

            # Insert batch into database
            inserted_count = self.db_ops.insert_batch(table_name, batch_data)
            return inserted_count

        except Exception as e:
            self.logger.error(f"Default OpenStates batch processor failed: {e}")
            raise

    def _generate_fingerprint(self, record: Dict[str, Any]) -> str:
        """Generate SHA-256 fingerprint for record deduplication."""
        # Create a normalized string representation
        normalized = json.dumps(record, sort_keys=True, default=str)
        return hashlib.sha256(normalized.encode()).hexdigest()

    # Data transformation functions
    def _transform_people_data(self, people_data: List[Dict], path_params: Dict[str, Any]) -> List[Dict]:
        """Transform people API data to database format."""
        transformed = []

        for person in people_data:
            try:
                transformed_person = {
                    'person_id': person.get('id'),
                    'name': person.get('name', ''),
                    'first_name': self._extract_name_part(person.get('name', ''), 'first'),
                    'last_name': self._extract_name_part(person.get('name', ''), 'last'),
                    'party': person.get('party', ''),
                    'current_role': self._extract_current_role(person),
                    'jurisdiction': person.get('jurisdiction', {}),
                    'created_at': self._parse_datetime(person.get('created_at')),
                    'updated_at': self._parse_datetime(person.get('updated_at')),
                    'image_url': person.get('image', ''),
                    'gender': person.get('gender', ''),
                    'biography': person.get('biography', ''),
                    'links': person.get('links', []),
                    'sources': person.get('sources', []),
                    'extras': person.get('extras', {}),
                    'metadata': person
                }

                transformed.append(transformed_person)

            except Exception as e:
                self.logger.warning(f"Failed to transform OpenStates person data: {e}")
                continue

        return transformed

    def _transform_person_details(self, people_data: List[Dict], path_params: Dict[str, Any]) -> List[Dict]:
        """Transform detailed person API data."""
        return self._transform_people_data(people_data, path_params)

    def _transform_bills_data(self, bills_data: List[Dict], path_params: Dict[str, Any]) -> List[Dict]:
        """Transform bills API data to database format."""
        transformed = []

        for bill in bills_data:
            try:
                transformed_bill = {
                    'bill_id': bill.get('id'),
                    'identifier': bill.get('identifier', ''),
                    'title': bill.get('title', ''),
                    'classification': bill.get('classification', ''),
                    'subject': bill.get('subject', ''),
                    'abstract': bill.get('abstract', ''),
                    'jurisdiction': bill.get('jurisdiction', {}),
                    'legislative_session': bill.get('legislative_session', {}),
                    'sponsor': bill.get('sponsor', {}),
                    'from_organization': bill.get('from_organization', {}),
                    'created_at': self._parse_datetime(bill.get('created_at')),
                    'updated_at': self._parse_datetime(bill.get('updated_at')),
                    'actions': bill.get('actions', []),
                    'other_titles': bill.get('other_titles', []),
                    'documents': bill.get('documents', []),
                    'versions': bill.get('versions', []),
                    'sources': bill.get('sources', []),
                    'extras': bill.get('extras', {}),
                    'metadata': bill
                }

                transformed.append(transformed_bill)

            except Exception as e:
                self.logger.warning(f"Failed to transform OpenStates bill data: {e}")
                continue

        return transformed

    def _transform_bill_details(self, bills_data: List[Dict], path_params: Dict[str, Any]) -> List[Dict]:
        """Transform detailed bill API data."""
        return self._transform_bills_data(bills_data, path_params)

    def _transform_jurisdictions_data(self, jurisdictions_data: List[Dict], path_params: Dict[str, Any]) -> List[Dict]:
        """Transform jurisdictions API data to database format."""
        transformed = []

        for jurisdiction in jurisdictions_data:
            try:
                transformed_jurisdiction = {
                    'jurisdiction_id': jurisdiction.get('id'),
                    'name': jurisdiction.get('name', ''),
                    'classification': jurisdiction.get('classification', ''),
                    'url': jurisdiction.get('url', ''),
                    'feature_flags': jurisdiction.get('feature_flags', {}),
                    'divisions': jurisdiction.get('divisions', []),
                    'links': jurisdiction.get('links', []),
                    'created_at': self._parse_datetime(jurisdiction.get('created_at')),
                    'updated_at': self._parse_datetime(jurisdiction.get('updated_at')),
                    'extras': jurisdiction.get('extras', {}),
                    'metadata': jurisdiction
                }

                transformed.append(transformed_jurisdiction)

            except Exception as e:
                self.logger.warning(f"Failed to transform OpenStates jurisdiction data: {e}")
                continue

        return transformed

    def _transform_jurisdiction_details(self, jurisdictions_data: List[Dict], path_params: Dict[str, Any]) -> List[Dict]:
        """Transform detailed jurisdiction API data."""
        return self._transform_jurisdictions_data(jurisdictions_data, path_params)

    def _transform_committees_data(self, committees_data: List[Dict], path_params: Dict[str, Any]) -> List[Dict]:
        """Transform committees API data to database format."""
        transformed = []

        for committee in committees_data:
            try:
                transformed_committee = {
                    'committee_id': committee.get('id'),
                    'name': committee.get('name', ''),
                    'classification': committee.get('classification', ''),
                    'jurisdiction': committee.get('jurisdiction', {}),
                    'parent': committee.get('parent'),
                    'sources': committee.get('sources', []),
                    'members': committee.get('members', []),
                    'links': committee.get('links', []),
                    'created_at': self._parse_datetime(committee.get('created_at')),
                    'updated_at': self._parse_datetime(committee.get('updated_at')),
                    'extras': committee.get('extras', {}),
                    'metadata': committee
                }

                transformed.append(transformed_committee)

            except Exception as e:
                self.logger.warning(f"Failed to transform OpenStates committee data: {e}")
                continue

        return transformed

    def _transform_committee_details(self, committees_data: List[Dict], path_params: Dict[str, Any]) -> List[Dict]:
        """Transform detailed committee API data."""
        return self._transform_committees_data(committees_data, path_params)

    def _transform_events_data(self, events_data: List[Dict], path_params: Dict[str, Any]) -> List[Dict]:
        """Transform events API data to database format."""
        transformed = []

        for event in events_data:
            try:
                transformed_event = {
                    'event_id': event.get('id'),
                    'name': event.get('name', ''),
                    'classification': event.get('classification', ''),
                    'description': event.get('description', ''),
                    'jurisdiction': event.get('jurisdiction', {}),
                    'start_date': self._parse_datetime(event.get('start_date')),
                    'end_date': self._parse_datetime(event.get('end_date')),
                    'status': event.get('status', ''),
                    'location': event.get('location', {}),
                    'sources': event.get('sources', []),
                    'documents': event.get('documents', []),
                    'participants': event.get('participants', []),
                    'agenda': event.get('agenda', {}),
                    'links': event.get('links', []),
                    'created_at': self._parse_datetime(event.get('created_at')),
                    'updated_at': self._parse_datetime(event.get('updated_at')),
                    'extras': event.get('extras', {}),
                    'metadata': event
                }

                transformed.append(transformed_event)

            except Exception as e:
                self.logger.warning(f"Failed to transform OpenStates event data: {e}")
                continue

        return transformed

    def _transform_event_details(self, events_data: List[Dict], path_params: Dict[str, Any]) -> List[Dict]:
        """Transform detailed event API data."""
        return self._transform_events_data(events_data, path_params)

    # Batch processing functions
    def _process_people_batch(self, people_data: List[Dict]) -> int:
        """Process people batch."""
        try:
            return self.db_ops.insert_batch('openstates.people', people_data)
        except Exception as e:
            self.logger.error(f"OpenStates people batch processing failed: {e}")
            raise

    def _process_bills_batch(self, bills_data: List[Dict]) -> int:
        """Process bills batch."""
        try:
            return self.db_ops.insert_batch('openstates.bills', bills_data)
        except Exception as e:
            self.logger.error(f"OpenStates bills batch processing failed: {e}")
            raise

    def _process_jurisdictions_batch(self, jurisdictions_data: List[Dict]) -> int:
        """Process jurisdictions batch."""
        try:
            return self.db_ops.insert_batch('openstates.jurisdictions', jurisdictions_data)
        except Exception as e:
            self.logger.error(f"OpenStates jurisdictions batch processing failed: {e}")
            raise

    def _process_committees_batch(self, committees_data: List[Dict]) -> int:
        """Process committees batch."""
        try:
            return self.db_ops.insert_batch('openstates.committees', committees_data)
        except Exception as e:
            self.logger.error(f"OpenStates committees batch processing failed: {e}")
            raise

    def _process_events_batch(self, events_data: List[Dict]) -> int:
        """Process events batch."""
        try:
            return self.db_ops.insert_batch('openstates.events', events_data)
        except Exception as e:
            self.logger.error(f"OpenStates events batch processing failed: {e}")
            raise

    # Helper functions
    def _extract_name_part(self, full_name: str, part: str) -> str:
        """Extract first or last name from full name."""
        if not full_name:
            return ''

        parts = full_name.split()
        if part == 'first' and parts:
            return parts[0]
        elif part == 'last' and len(parts) > 1:
            return parts[-1]

        return full_name

    def _extract_current_role(self, person: Dict) -> Dict[str, Any]:
        """Extract current role from person data."""
        roles = person.get('roles', [])
        if roles:
            # Return the most recent role
            return roles[0]
        return {}

    def _parse_datetime(self, datetime_str: Optional[str]) -> Optional[str]:
        """Parse datetime string to ISO format."""
        if not datetime_str:
            return None

        try:
            return datetime.fromisoformat(datetime_str.replace('Z', '+00:00')).isoformat()
        except Exception:
            return datetime_str

    def ingest_all_states_data(self, states: List[str] = None) -> Dict[str, Any]:
        """Ingest all OpenStates data for specified states."""
        if not states:
            # Default to all 50 states
            states = [
                'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
                'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
                'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
                'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
                'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY'
            ]

        self.logger.info(f"Starting comprehensive OpenStates ingestion for {len(states)} states")

        results = {}

        # Define ingestion sequence per state
        ingestion_sequence = [
            ('people_by_state',),
            ('bills_by_state',),
            ('committees_by_state',),
            ('events_by_state',),
        ]

        for state in states:
            self.logger.info(f"Processing state: {state}")
            state_results = {}

            for endpoint_key_tuple in ingestion_sequence:
                endpoint_key = endpoint_key_tuple[0]

                try:
                    result = self.ingest_endpoint(endpoint_key, state=state)
                    state_results[endpoint_key] = result

                    # Pause between endpoints for the same state
                    time.sleep(3)

                except Exception as e:
                    self.logger.error(f"Failed to ingest OpenStates {endpoint_key} for {state}: {e}")
                    state_results[endpoint_key] = {'error': str(e)}

            results[state] = state_results

            # Longer pause between states
            time.sleep(5)

        # Generate summary
        total_processed = 0
        total_errors = 0

        for state_results in results.values():
            for endpoint_result in state_results.values():
                if 'total_processed' in endpoint_result:
                    total_processed += endpoint_result['total_processed']
                if 'failed_batches' in endpoint_result:
                    total_errors += endpoint_result['failed_batches']

        summary = {
            'states_processed': len(states),
            'total_processed': total_processed,
            'total_errors': total_errors,
            'state_results': results,
            'start_time': self.ingestion_stats['start_time'],
            'end_time': datetime.now(),
            'duration': (datetime.now() - self.ingestion_stats['start_time']).total_seconds()
        }

        self.logger.info(f"OpenStates ingestion completed: {total_processed} records, {total_errors} errors")
        return summary

    def get_ingestion_statistics(self) -> Dict[str, Any]:
        """Get comprehensive ingestion statistics."""
        end_time = datetime.now()
        duration = (end_time - self.ingestion_stats['start_time']).total_seconds()

        return {
            'total_records': self.ingestion_stats['total_records'],
            'processed_records': self.ingestion_stats['processed_records'],
            'failed_records': self.ingestion_stats['failed_records'],
            'success_rate': (self.ingestion_stats['processed_records'] / max(1, self.ingestion_stats['total_records'])) * 100,
            'start_time': self.ingestion_stats['start_time'],
            'end_time': end_time,
            'duration_seconds': duration,
            'records_per_second': self.ingestion_stats['processed_records'] / max(1, duration),
            'endpoints_processed': len(self.ingestion_stats['endpoints_processed']),
            'endpoint_details': self.ingestion_stats['endpoints_processed']
        }
