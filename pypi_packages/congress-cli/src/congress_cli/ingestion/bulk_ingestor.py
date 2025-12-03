"""
Bulk data ingestion functions for Congress CLI with API endpoint mapping.
"""

import time
import json
import hashlib
from typing import Dict, Any, List, Optional, Callable, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging

from ..api.client import CongressAPIClient, CongressAPIBatchProcessor
from ..database.operations import DatabaseOperations
from ..models.api_models import CongressMember, CongressBill
from ..utils.logger import get_logger
from ..utils.config import get_config


@dataclass
class APIEndpointMapping:
    """Mapping of API endpoint to database table and processing function."""

    endpoint_path: str
    table_name: str
    data_type: str
    category: Optional[str] = None
    batch_size: int = 100
    rate_limit_delay: float = 0.1
    pagination_param: str = "offset"
    max_retries: int = 3

    # Processing functions
    data_transformer: Optional[Callable[[List[Dict]], List[Dict]]] = None
    batch_processor: Optional[Callable[[List[Dict]], int]] = None
    progress_callback: Optional[Callable[[int, int], None]] = None


class RateLimitManager:
    """Sophisticated rate limiting with adaptive timing."""

    def __init__(self, base_delay: float = 0.1, max_delay: float = 5.0):
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.current_delay = base_delay
        self.last_request_time = None
        self.request_times: List[datetime] = []
        self.logger = get_logger(__name__)

    def wait_if_needed(self):
        """Wait if necessary to respect rate limits."""
        now = datetime.now()

        # Clean old request times (last 10 seconds)
        cutoff = now - timedelta(seconds=10)
        self.request_times = [t for t in self.request_times if t > cutoff]

        # Calculate adaptive delay based on recent request frequency
        if len(self.request_times) > 0:
            avg_interval = (now - self.request_times[0]).total_seconds() / len(self.request_times)

            if avg_interval < self.base_delay:
                # Increase delay if we're requesting too frequently
                self.current_delay = min(self.current_delay * 1.5, self.max_delay)
            else:
                # Decrease delay if we have room
                self.current_delay = max(self.current_delay * 0.9, self.base_delay)

        # Wait if needed
        if self.last_request_time and (now - self.last_request_time).total_seconds() < self.current_delay:
            sleep_time = self.current_delay - (now - self.last_request_time).total_seconds()
            if sleep_time > 0:
                self.logger.debug(f"Rate limiting: sleeping {sleep_time:.3f} seconds")
                time.sleep(sleep_time)

        self.last_request_time = datetime.now()
        self.request_times.append(now)

    def handle_rate_limit_error(self):
        """Handle rate limit errors with exponential backoff."""
        self.current_delay = min(self.current_delay * 2, self.max_delay)
        self.logger.warning(f"Rate limit hit, increasing delay to {self.current_delay:.3f} seconds")
        time.sleep(self.current_delay)


class BulkDataIngestor:
    """Comprehensive bulk data ingestion with API endpoint mapping."""

    def __init__(self, config=None):
        """Initialize bulk ingestor with configuration."""
        self.config = config or get_config()
        self.api_client = CongressAPIClient()
        self.batch_processor = CongressAPIBatchProcessor(self.api_client)
        self.db_ops = DatabaseOperations(self.config.database_url)
        self.rate_manager = RateLimitManager()
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
        """Setup mappings between API endpoints and database tables."""
        self.endpoint_mappings = {
            # Members endpoints
            'members_current': APIEndpointMapping(
                endpoint_path="member/congress",
                table_name="congress.members",
                data_type="members",
                category="current",
                batch_size=250,
                rate_limit_delay=0.2,
                data_transformer=self._transform_members_data,
                batch_processor=self._process_members_batch
            ),

            'members_by_congress': APIEndpointMapping(
                endpoint_path="member/congress/{congress}",
                table_name="congress.members",
                data_type="members",
                category="{congress}",
                batch_size=250,
                rate_limit_delay=0.2,
                data_transformer=self._transform_members_data,
                batch_processor=self._process_members_batch
            ),

            'member_details': APIEndpointMapping(
                endpoint_path="member/{bioguide_id}",
                table_name="congress.members",
                data_type="member_details",
                batch_size=1,
                rate_limit_delay=0.1,
                data_transformer=self._transform_member_details,
                batch_processor=self._process_member_details_batch
            ),

            # Bills endpoints
            'bills_current': APIEndpointMapping(
                endpoint_path="bill/congress",
                table_name="congress.bills",
                data_type="bills",
                category="current",
                batch_size=250,
                rate_limit_delay=0.2,
                data_transformer=self._transform_bills_data,
                batch_processor=self._process_bills_batch
            ),

            'bills_by_congress': APIEndpointMapping(
                endpoint_path="bill/congress/{congress}",
                table_name="congress.bills",
                data_type="bills",
                category="{congress}",
                batch_size=250,
                rate_limit_delay=0.2,
                data_transformer=self._transform_bills_data,
                batch_processor=self._process_bills_batch
            ),

            'bill_details': APIEndpointMapping(
                endpoint_path="bill/{bill_id}",
                table_name="congress.bills",
                data_type="bill_details",
                batch_size=1,
                rate_limit_delay=0.1,
                data_transformer=self._transform_bill_details,
                batch_processor=self._process_bill_details_batch
            ),

            'bills_by_member': APIEndpointMapping(
                endpoint_path="member/{bioguide_id}/bills",
                table_name="congress.bills",
                data_type="member_bills",
                category="{bioguide_id}",
                batch_size=100,
                rate_limit_delay=0.15,
                data_transformer=self._transform_bills_data,
                batch_processor=self._process_bills_batch
            ),

            # Search endpoints
            'bill_search': APIEndpointMapping(
                endpoint_path="bill/search",
                table_name="congress.bills",
                data_type="search_results",
                batch_size=100,
                rate_limit_delay=0.3,
                data_transformer=self._transform_search_results,
                batch_processor=self._process_bills_batch
            )
        }

    def ingest_endpoint(self, endpoint_key: str, **path_params) -> Dict[str, Any]:
        """Ingest data from a specific API endpoint."""
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

        self.logger.info(f"Starting ingestion for endpoint: {endpoint_key}")

        # Get checkpoint for resuming
        checkpoint = self.db_ops.get_checkpoint('congress.gov', mapping.data_type, category)
        start_offset = int(checkpoint.offset) if checkpoint and checkpoint else 0

        # Initialize statistics
        endpoint_stats = {
            'endpoint_key': endpoint_key,
            'endpoint_path': endpoint_path,
            'start_offset': start_offset,
            'total_processed': 0,
            'failed_batches': 0,
            'start_time': datetime.now()
        }

        try:
            # Perform bulk ingestion
            result = self._perform_bulk_ingestion(mapping, endpoint_path, path_params, start_offset)

            endpoint_stats.update(result)
            endpoint_stats['end_time'] = datetime.now()
            endpoint_stats['duration'] = (endpoint_stats['end_time'] - endpoint_stats['start_time']).total_seconds()

            self.ingestion_stats['endpoints_processed'].append(endpoint_stats)

            self.logger.info(f"Completed ingestion for {endpoint_key}: {result['total_processed']} records")
            return result

        except Exception as e:
            endpoint_stats['error'] = str(e)
            endpoint_stats['end_time'] = datetime.now()
            self.ingestion_stats['endpoints_processed'].append(endpoint_stats)

            self.logger.error(f"Failed ingestion for {endpoint_key}: {e}")
            raise

    def _perform_bulk_ingestion(self, mapping: APIEndpointMapping, endpoint_path: str,
                              path_params: Dict[str, Any], start_offset: int) -> Dict[str, Any]:
        """Perform bulk ingestion with pagination and rate limiting."""
        total_processed = 0
        failed_batches = 0
        current_offset = start_offset
        batch_count = 0

        # Setup rate limit for this endpoint
        self.rate_manager.current_delay = mapping.rate_limit_delay

        while True:
            batch_count += 1

            try:
                # Rate limiting
                self.rate_manager.wait_if_needed()

                # Fetch data with pagination
                self.logger.debug(f"Fetching batch {batch_count} from {endpoint_path}, offset {current_offset}")

                # Build request parameters
                params = {
                    mapping.pagination_param: current_offset,
                    'limit': mapping.batch_size
                }

                # Add path parameters to request
                if path_params:
                    # For endpoints that need congress number in params
                    if 'congress' in endpoint_path and 'congress' in path_params:
                        params['congress'] = path_params['congress']

                # Make API request
                response = self.api_client._make_request(endpoint_path, params)

                if not response.get('results'):
                    self.logger.info(f"No more results at offset {current_offset}")
                    break

                # Process batch
                batch_data = response['results']

                # Apply data transformation if configured
                if mapping.data_transformer:
                    batch_data = mapping.data_transformer(batch_data)

                # Process batch
                if mapping.batch_processor:
                    processed_count = mapping.batch_processor(batch_data)
                else:
                    processed_count = self._default_batch_processor(batch_data, mapping.table_name)

                total_processed += processed_count

                # Update checkpoint
                next_offset = current_offset + len(batch_data)
                self.db_ops.update_checkpoint(
                    'congress.gov', mapping.data_type,
                    mapping.category, str(next_offset), total_processed
                )

                # Call progress callback if configured
                if mapping.progress_callback:
                    mapping.progress_callback(processed_count, total_processed)

                # Log progress
                if batch_count % 10 == 0:
                    self.logger.info(f"Processed {total_processed} records across {batch_count} batches")

                # Check if we're done
                if 'next_offset' not in response or not response['next_offset']:
                    break

                current_offset = int(response['next_offset'])

            except Exception as e:
                failed_batches += 1

                # Handle rate limit errors
                if "rate limit" in str(e).lower() or "429" in str(e):
                    self.rate_manager.handle_rate_limit_error()
                    continue

                # Handle other errors with retry logic
                if failed_batches < mapping.max_retries:
                    self.logger.warning(f"Batch {batch_count} failed, retrying ({failed_batches}/{mapping.max_retries}): {e}")
                    time.sleep(2 ** failed_batches)  # Exponential backoff
                    continue
                else:
                    self.logger.error(f"Batch {batch_count} failed after {mapping.max_retries} retries: {e}")
                    raise

        return {
            'total_processed': total_processed,
            'failed_batches': failed_batches,
            'batch_count': batch_count,
            'final_offset': current_offset
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
            self.logger.error(f"Default batch processor failed: {e}")
            raise

    def _generate_fingerprint(self, record: Dict[str, Any]) -> str:
        """Generate SHA-256 fingerprint for record deduplication."""
        # Create a normalized string representation
        normalized = json.dumps(record, sort_keys=True, default=str)
        return hashlib.sha256(normalized.encode()).hexdigest()

    # Data transformation functions
    def _transform_members_data(self, members_data: List[Dict]) -> List[Dict]:
        """Transform members API data to database format."""
        transformed = []

        for member in members_data:
            try:
                # Extract name components
                full_name = member.get('name', '')
                name_parts = full_name.split()

                transformed_member = {
                    'bioguide_id': member.get('bioguideId'),
                    'full_name': full_name,
                    'first_name': name_parts[0] if name_parts else '',
                    'last_name': name_parts[-1] if len(name_parts) > 1 else '',
                    'state': member.get('state', ''),
                    'district': member.get('district'),
                    'party': member.get('partyName'),
                    'chamber': 'House' if member.get('district') else 'Senate',
                    'term_start': self._parse_date(member.get('startDate')),
                    'term_end': self._parse_date(member.get('endDate')),
                    'url': member.get('url'),
                    'data': member
                }

                transformed.append(transformed_member)

            except Exception as e:
                self.logger.warning(f"Failed to transform member data: {e}")
                continue

        return transformed

    def _transform_member_details(self, members_data: List[Dict]) -> List[Dict]:
        """Transform detailed member API data."""
        return self._transform_members_data(members_data)

    def _transform_bills_data(self, bills_data: List[Dict]) -> List[Dict]:
        """Transform bills API data to database format."""
        transformed = []

        for bill in bills_data:
            try:
                # Parse bill ID
                bill_id = bill.get('bill', '')
                bill_type = bill.get('billType', '')
                bill_number = bill.get('billNumber', '')
                congress = bill.get('congress', 118)

                transformed_bill = {
                    'bill_id': f"{bill_type}{congress}-{bill_number}",
                    'title': bill.get('title', ''),
                    'congress': congress,
                    'bill_type': bill_type,
                    'chamber': 'House' if bill_type in ['hr', 'hres', 'hjres', 'hconres'] else 'Senate',
                    'introduced_date': self._parse_date(bill.get('introducedDate')),
                    'sponsor_bioguide_id': bill.get('sponsor', {}).get('bioguideId') if bill.get('sponsor') else None,
                    'cosponsors': bill.get('cosponsors', []),
                    'committees': bill.get('committees', []),
                    'actions': bill.get('actions', []),
                    'text_versions': bill.get('textVersions', []),
                    'latest_action': bill.get('latestAction'),
                    'status': bill.get('status'),
                    'url': bill.get('url'),
                    'data': bill
                }

                transformed.append(transformed_bill)

            except Exception as e:
                self.logger.warning(f"Failed to transform bill data: {e}")
                continue

        return transformed

    def _transform_bill_details(self, bills_data: List[Dict]) -> List[Dict]:
        """Transform detailed bill API data."""
        return self._transform_bills_data(bills_data)

    def _transform_search_results(self, search_data: List[Dict]) -> List[Dict]:
        """Transform search results to bill format."""
        # Search results are in the same format as bills
        return self._transform_bills_data(search_data)

    # Batch processing functions
    def _process_members_batch(self, members_data: List[Dict]) -> int:
        """Process members batch with validation."""
        try:
            # Validate with Pydantic models
            validated_members = []
            for member_data in members_data:
                try:
                    member = CongressMember(**member_data)
                    validated_members.append(member.dict())
                except Exception as e:
                    self.logger.warning(f"Member validation failed: {e}")
                    continue

            # Insert validated members
            if validated_members:
                return self.db_ops.insert_batch('congress.members', validated_members)

            return 0

        except Exception as e:
            self.logger.error(f"Members batch processing failed: {e}")
            raise

    def _process_member_details_batch(self, members_data: List[Dict]) -> int:
        """Process member details batch."""
        return self._process_members_batch(members_data)

    def _process_bills_batch(self, bills_data: List[Dict]) -> int:
        """Process bills batch with validation."""
        try:
            # Validate with Pydantic models
            validated_bills = []
            for bill_data in bills_data:
                try:
                    bill = CongressBill(**bill_data)
                    validated_bills.append(bill.dict())
                except Exception as e:
                    self.logger.warning(f"Bill validation failed: {e}")
                    continue

            # Insert validated bills
            if validated_bills:
                return self.db_ops.insert_batch('congress.bills', validated_bills)

            return 0

        except Exception as e:
            self.logger.error(f"Bills batch processing failed: {e}")
            raise

    def _process_bill_details_batch(self, bills_data: List[Dict]) -> int:
        """Process bill details batch."""
        return self._process_bills_batch(bills_data)

    def _parse_date(self, date_str: Optional[str]) -> Optional[str]:
        """Parse date string to ISO format."""
        if not date_str:
            return None

        try:
            # Handle various date formats
            if 'T' in date_str:
                # ISO format with time
                return datetime.fromisoformat(date_str.replace('Z', '+00:00')).date().isoformat()
            else:
                # Date only format
                return datetime.strptime(date_str, '%Y-%m-%d').date().isoformat()
        except Exception:
            return date_str  # Return original if parsing fails

    def ingest_all_congress_data(self, congress: int = 118) -> Dict[str, Any]:
        """Ingest all data for a specific congress."""
        self.logger.info(f"Starting comprehensive ingestion for Congress {congress}")

        results = {}

        # Define ingestion sequence
        ingestion_sequence = [
            ('members_by_congress', {'congress': congress}),
            ('bills_by_congress', {'congress': congress}),
        ]

        for endpoint_key, params in ingestion_sequence:
            try:
                result = self.ingest_endpoint(endpoint_key, **params)
                results[endpoint_key] = result

                # Brief pause between endpoints
                time.sleep(1)

            except Exception as e:
                self.logger.error(f"Failed to ingest {endpoint_key}: {e}")
                results[endpoint_key] = {'error': str(e)}

        # Generate summary
        total_processed = sum(r.get('total_processed', 0) for r in results.values() if 'total_processed' in r)
        total_errors = sum(r.get('failed_batches', 0) for r in results.values() if 'failed_batches' in r)

        summary = {
            'congress': congress,
            'total_processed': total_processed,
            'total_errors': total_errors,
            'endpoints': results,
            'start_time': self.ingestion_stats['start_time'],
            'end_time': datetime.now(),
            'duration': (datetime.now() - self.ingestion_stats['start_time']).total_seconds()
        }

        self.logger.info(f"Congress {congress} ingestion completed: {total_processed} records, {total_errors} errors")
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
