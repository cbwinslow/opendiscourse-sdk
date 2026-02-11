"""
Bulk data ingestion functions for GovInfo CLI with API endpoint mapping.
"""

import hashlib
import json
import re
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from ..api.client import GovInfoAPIClient
from ..database.operations import DatabaseOperations
from ..utils.config import get_config
from ..utils.logger import get_logger


@dataclass
class GovInfoEndpointMapping:
    """Mapping of GovInfo API endpoint to database table and processing function."""

    endpoint_path: str
    table_name: str
    data_type: str
    category: Optional[str] = None
    batch_size: int = 100
    rate_limit_delay: float = 0.2
    pagination_param: str = "offset"
    max_retries: int = 3

    # Processing functions
    data_transformer: Optional[Callable[[List[Dict]], List[Dict]]] = None
    batch_processor: Optional[Callable[[List[Dict]], int]] = None
    progress_callback: Optional[Callable[[int, int], None]] = None


class GovInfoRateLimitManager:
    """Rate limiting for GovInfo API with strict adherence to limits."""

    def __init__(self, base_delay: float = 0.2, max_delay: float = 10.0):
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.current_delay = base_delay
        self.last_request_time = None
        self.request_count = 0
        self.window_start = datetime.now()
        self.logger = get_logger(__name__)

    def wait_if_needed(self):
        """Wait if necessary to respect GovInfo rate limits (max 40 requests/minute)."""
        now = datetime.now()

        # Reset window if more than 1 minute has passed
        if (now - self.window_start).total_seconds() > 60:
            self.request_count = 0
            self.window_start = now

        # Check if we're approaching the limit
        if self.request_count >= 35:  # Safety margin
            remaining_time = 60 - (now - self.window_start).total_seconds()
            if remaining_time > 0:
                self.logger.info(f"Approaching rate limit, waiting {remaining_time:.1f} seconds")
                time.sleep(remaining_time + 1)  # Extra safety margin
                self.request_count = 0
                self.window_start = datetime.now()

        # Base rate limiting
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


class GovInfoBulkIngestor:
    """Comprehensive bulk data ingestion for GovInfo API."""

    def __init__(self, config=None):
        """Initialize bulk ingestor with configuration."""
        self.config = config or get_config()
        self.api_client = GovInfoAPIClient()
        self.db_ops = DatabaseOperations(self.config.database_url)
        self.rate_manager = GovInfoRateLimitManager()
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
        """Setup mappings between GovInfo API endpoints and database tables."""
        self.endpoint_mappings = {
            # Collections endpoints
            'collections_bills': GovInfoEndpointMapping(
                endpoint_path="collections/BILLS/{date}",
                table_name="govinfo.packages",
                data_type="collections",
                category="bills",
                batch_size=100,
                rate_limit_delay=0.3,
                data_transformer=self._transform_collection_data,
                batch_processor=self._process_packages_batch
            ),

            'collections_crec': GovInfoEndpointMapping(
                endpoint_path="collections/CREC/{date}",
                table_name="govinfo.packages",
                data_type="collections",
                category="congressional_record",
                batch_size=100,
                rate_limit_delay=0.3,
                data_transformer=self._transform_collection_data,
                batch_processor=self._process_packages_batch
            ),

            'collections_chrg': GovInfoEndpointMapping(
                endpoint_path="collections/CHRG/{date}",
                table_name="govinfo.packages",
                data_type="collections",
                category="committee_hearings",
                batch_size=100,
                rate_limit_delay=0.3,
                data_transformer=self._transform_collection_data,
                batch_processor=self._process_packages_batch
            ),

            # Package content endpoints
            'package_content': GovInfoEndpointMapping(
                endpoint_path="packages/{package_id}",
                table_name="govinfo.granules",
                data_type="package_content",
                category="{package_id}",
                batch_size=1,
                rate_limit_delay=0.5,
                data_transformer=self._transform_package_content,
                batch_processor=self._process_granules_batch
            ),

            # Committee endpoints
            'committees_house': GovInfoEndpointMapping(
                endpoint_path="committee/house",
                table_name="govinfo.committees",
                data_type="committees",
                category="house",
                batch_size=50,
                rate_limit_delay=0.4,
                data_transformer=self._transform_committee_data,
                batch_processor=self._process_committees_batch
            ),

            'committees_senate': GovInfoEndpointMapping(
                endpoint_path="committee/senate",
                table_name="govinfo.committees",
                data_type="committees",
                category="senate",
                batch_size=50,
                rate_limit_delay=0.4,
                data_transformer=self._transform_committee_data,
                batch_processor=self._process_committees_batch
            ),

            # Member endpoints (from Congressional Directory)
            'congressional_directory': GovInfoEndpointMapping(
                endpoint_path="collections/CDIR/{date}",
                table_name="govinfo.members",
                data_type="members",
                category="directory",
                batch_size=50,
                rate_limit_delay=0.5,
                data_transformer=self._transform_directory_members,
                batch_processor=self._process_members_batch
            )
        }

    def ingest_endpoint(self, endpoint_key: str, **path_params) -> Dict[str, Any]:
        """Ingest data from a specific GovInfo API endpoint."""
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

        self.logger.info(f"Starting GovInfo ingestion for endpoint: {endpoint_key}")

        # Get checkpoint for resuming
        checkpoint = self.db_ops.get_checkpoint('govinfo.gov', mapping.data_type, category)
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

            self.logger.info(f"Completed GovInfo ingestion for {endpoint_key}: {result['total_processed']} records")
            return result

        except Exception as e:
            endpoint_stats['error'] = str(e)
            endpoint_stats['end_time'] = datetime.now()
            self.ingestion_stats['endpoints_processed'].append(endpoint_stats)

            self.logger.error(f"Failed GovInfo ingestion for {endpoint_key}: {e}")
            raise

    def _perform_bulk_ingestion(self, mapping: GovInfoEndpointMapping, endpoint_path: str,
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
                self.logger.debug(f"Fetching GovInfo batch {batch_count} from {endpoint_path}, offset {current_offset}")

                # Build request parameters
                params = {
                    'offset': current_offset,
                    'pageSize': mapping.batch_size
                }

                # Make API request
                response = self.api_client._make_request(endpoint_path, params)

                if not response.get('packages') and not response.get('granules'):
                    self.logger.info(f"No more results at offset {current_offset}")
                    break

                # Get data from response (packages or granules)
                batch_data = response.get('packages', response.get('granules', []))

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
                next_offset = current_offset + len(batch_data)
                self.db_ops.update_checkpoint(
                    'govinfo.gov', mapping.data_type,
                    mapping.category, str(next_offset), total_processed
                )

                # Call progress callback if configured
                if mapping.progress_callback:
                    mapping.progress_callback(processed_count, total_processed)

                # Log progress
                if batch_count % 5 == 0:  # Less frequent due to rate limits
                    self.logger.info(f"Processed {total_processed} records across {batch_count} batches")

                # Check if we're done
                if len(batch_data) < mapping.batch_size:
                    break

                current_offset = next_offset

            except Exception as e:
                failed_batches += 1

                # Handle rate limit errors
                if "rate limit" in str(e).lower() or "429" in str(e):
                    self.rate_manager.handle_rate_limit_error()
                    continue

                # Handle other errors with retry logic
                if failed_batches < mapping.max_retries:
                    self.logger.warning(f"GovInfo batch {batch_count} failed, retrying ({failed_batches}/{mapping.max_retries}): {e}")
                    time.sleep(5 ** failed_batches)  # Longer backoff for GovInfo
                    continue
                else:
                    self.logger.error(f"GovInfo batch {batch_count} failed after {mapping.max_retries} retries: {e}")
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
            self.logger.error(f"Default GovInfo batch processor failed: {e}")
            raise

    def _generate_fingerprint(self, record: Dict[str, Any]) -> str:
        """Generate SHA-256 fingerprint for record deduplication."""
        # Create a normalized string representation
        normalized = json.dumps(record, sort_keys=True, default=str)
        return hashlib.sha256(normalized.encode()).hexdigest()

    # Data transformation functions
    def _transform_collection_data(self, packages_data: List[Dict], path_params: Dict[str, Any]) -> List[Dict]:
        """Transform collection packages data to database format."""
        transformed = []

        for package in packages_data:
            try:
                transformed_package = {
                    'package_id': package.get('packageId'),
                    'collection_code': path_params.get('collection_code', 'BILLS'),
                    'title': package.get('title', ''),
                    'congress_number': self._extract_congress_from_package(package),
                    'chamber_code': self._extract_chamber_from_package(package),
                    'bill_type': self._extract_bill_type_from_package(package),
                    'bill_number': self._extract_bill_number_from_package(package),
                    'document_class': package.get('docClass', ''),
                    'doc_number': package.get('docNumber', ''),
                    'granule_count': package.get('granuleCount', 0),
                    'date_issued': self._parse_date(package.get('dateIssued')),
                    'last_modified': self._parse_datetime(package.get('lastModified')),
                    'summary': package.get('summary', ''),
                    'origin': package.get('origin', ''),
                    'urls': package.get('download', {}),
                    'metadata': package,
                    'retrieved_at': datetime.now().isoformat()
                }

                transformed.append(transformed_package)

            except Exception as e:
                self.logger.warning(f"Failed to transform GovInfo package data: {e}")
                continue

        return transformed

    def _transform_package_content(self, content_data: List[Dict], path_params: Dict[str, Any]) -> List[Dict]:
        """Transform package content/granules data to database format."""
        transformed = []

        for granule in content_data:
            try:
                transformed_granule = {
                    'granule_id': granule.get('granuleId'),
                    'package_id': path_params.get('package_id'),
                    'granule_class': granule.get('granuleClass', ''),
                    'title': granule.get('title', ''),
                    'sequence_number': granule.get('sequence', 0),
                    'granule_date': self._parse_date(granule.get('granuleDate')),
                    'last_modified': self._parse_datetime(granule.get('lastModified')),
                    'metadata': granule,
                    'text_url': granule.get('txtUrl'),
                    'pdf_url': granule.get('pdfUrl'),
                    'xml_url': granule.get('xmlUrl'),
                    'zip_url': granule.get('zipUrl')
                }

                transformed.append(transformed_granule)

            except Exception as e:
                self.logger.warning(f"Failed to transform GovInfo granule data: {e}")
                continue

        return transformed

    def _transform_committee_data(self, committees_data: List[Dict], path_params: Dict[str, Any]) -> List[Dict]:
        """Transform committee data to database format."""
        transformed = []

        for committee in committees_data:
            try:
                transformed_committee = {
                    'committee_code': committee.get('code', ''),
                    'committee_name': committee.get('name', ''),
                    'chamber_code': path_params.get('chamber', 'HOUSE'),
                    'parent_committee_code': committee.get('parentCode'),
                    'type': committee.get('type', ''),
                    'established_date': self._parse_date(committee.get('established')),
                    'terminated_date': self._parse_date(committee.get('terminated')),
                    'url': committee.get('url', ''),
                    'jurisdiction': committee.get('jurisdiction', ''),
                    'metadata': committee
                }

                transformed.append(transformed_committee)

            except Exception as e:
                self.logger.warning(f"Failed to transform GovInfo committee data: {e}")
                continue

        return transformed

    def _transform_directory_members(self, directory_data: List[Dict], path_params: Dict[str, Any]) -> List[Dict]:
        """Transform Congressional Directory member data to database format."""
        transformed = []

        for package in directory_data:
            try:
                # Get package content to extract member data
                package_id = package.get('packageId')
                content = self.api_client.get_package_content(package_id)

                # Parse members from directory content
                members = self._parse_members_from_directory(content)

                for member in members:
                    transformed_member = {
                        'member_id': member.get('bioguide_id', f"dir_{package_id}_{member.get('name', '').replace(' ', '_')}"),
                        'bioguide_id': member.get('bioguide_id'),
                        'first_name': member.get('first_name', ''),
                        'middle_name': member.get('middle_name', ''),
                        'last_name': member.get('last_name', ''),
                        'suffix': member.get('suffix', ''),
                        'full_name': member.get('full_name', member.get('name', '')),
                        'preferred_name': member.get('preferred_name', ''),
                        'birthday': self._parse_date(member.get('birthday')),
                        'gender': member.get('gender', ''),
                        'party_code': member.get('party', ''),
                        'state': member.get('state', ''),
                        'district': member.get('district', ''),
                        'url': member.get('url', ''),
                        'twitter_handle': member.get('twitter', ''),
                        'youtube_handle': member.get('youtube', ''),
                        'facebook_handle': member.get('facebook', ''),
                        'biography_text': member.get('biography', ''),
                        'photo_url': member.get('photo_url', ''),
                        'metadata': member
                    }

                    transformed.append(transformed_member)

            except Exception as e:
                self.logger.warning(f"Failed to transform GovInfo directory data: {e}")
                continue

        return transformed

    # Batch processing functions
    def _process_packages_batch(self, packages_data: List[Dict]) -> int:
        """Process packages batch."""
        try:
            return self.db_ops.insert_batch('govinfo.packages', packages_data)
        except Exception as e:
            self.logger.error(f"GovInfo packages batch processing failed: {e}")
            raise

    def _process_granules_batch(self, granules_data: List[Dict]) -> int:
        """Process granules batch."""
        try:
            return self.db_ops.insert_batch('govinfo.granules', granules_data)
        except Exception as e:
            self.logger.error(f"GovInfo granules batch processing failed: {e}")
            raise

    def _process_committees_batch(self, committees_data: List[Dict]) -> int:
        """Process committees batch."""
        try:
            return self.db_ops.insert_batch('govinfo.committees', committees_data)
        except Exception as e:
            self.logger.error(f"GovInfo committees batch processing failed: {e}")
            raise

    def _process_members_batch(self, members_data: List[Dict]) -> int:
        """Process members batch."""
        try:
            return self.db_ops.insert_batch('govinfo.members', members_data)
        except Exception as e:
            self.logger.error(f"GovInfo members batch processing failed: {e}")
            raise

    # Helper functions
    def _extract_congress_from_package(self, package: Dict) -> Optional[int]:
        """Extract congress number from package data."""
        title = package.get('title', '')
        # Look for patterns like "118th Congress" or "Congress 118"
        match = re.search(r'(\d+)(?:st|nd|rd|th)?\s+congress', title, re.IGNORECASE)
        if match:
            return int(match.group(1))
        return None

    def _extract_chamber_from_package(self, package: Dict) -> Optional[str]:
        """Extract chamber from package data."""
        title = package.get('title', '').lower()
        if 'house' in title:
            return 'HOUSE'
        elif 'senate' in title:
            return 'SENATE'
        return None

    def _extract_bill_type_from_package(self, package: Dict) -> Optional[str]:
        """Extract bill type from package data."""
        title = package.get('title', '').lower()
        if 'h.r.' in title or 'hr' in title:
            return 'hr'
        elif 's.' in title:
            return 's'
        elif 'h.res.' in title or 'hres' in title:
            return 'hres'
        elif 's.res.' in title or 'sres' in title:
            return 'sres'
        return None

    def _extract_bill_number_from_package(self, package: Dict) -> Optional[str]:
        """Extract bill number from package data."""
        title = package.get('title', '')
        # Look for patterns like "H.R.1234" or "S.567"
        match = re.search(r'[HHS]\.?[RrEeSsLlJj]?\s*(\d+)', title)
        if match:
            return match.group(1)
        return None

    def _parse_members_from_directory(self, content: str) -> List[Dict]:
        """Parse member information from Congressional Directory text content."""
        members = []

        # Basic pattern matching for member information
        # This is a simplified parser - real implementation would be more sophisticated
        lines = content.split('\n')
        current_member = {}

        for line in lines:
            line = line.strip()

            # Look for member name patterns
            if re.match(r'^[A-Z][a-z]+ [A-Z][a-z]+', line):
                if current_member:
                    members.append(current_member)
                current_member = {'name': line}

            # Look for state information
            elif re.match(r'^[A-Z]{2}$', line):
                current_member['state'] = line

            # Look for party information
            elif line in ['Democrat', 'Republican', 'Independent']:
                current_member['party'] = line[0]  # D, R, I

        # Add last member
        if current_member:
            members.append(current_member)

        return members

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

    def _parse_datetime(self, datetime_str: Optional[str]) -> Optional[str]:
        """Parse datetime string to ISO format."""
        if not datetime_str:
            return None

        try:
            return datetime.fromisoformat(datetime_str.replace('Z', '+00:00')).isoformat()
        except Exception:
            return datetime_str

    def ingest_all_govinfo_data(self, congress: int = 118, start_date: str = None) -> Dict[str, Any]:
        """Ingest all GovInfo data for a specific time period."""
        if not start_date:
            # Default to start of the congress
            start_date = f"{congress-1}-01-03"  # Approximate start date

        self.logger.info(f"Starting comprehensive GovInfo ingestion for Congress {congress} from {start_date}")

        results = {}

        # Define ingestion sequence
        ingestion_sequence = [
            ('collections_bills', {'date': start_date, 'collection_code': 'BILLS'}),
            ('collections_crec', {'date': start_date, 'collection_code': 'CREC'}),
            ('collections_chrg', {'date': start_date, 'collection_code': 'CHRG'}),
            ('congressional_directory', {'date': start_date}),
            ('committees_house', {'chamber': 'HOUSE'}),
            ('committees_senate', {'chamber': 'SENATE'}),
        ]

        for endpoint_key, params in ingestion_sequence:
            try:
                result = self.ingest_endpoint(endpoint_key, **params)
                results[endpoint_key] = result

                # Longer pause between GovInfo endpoints due to strict rate limits
                time.sleep(2)

            except Exception as e:
                self.logger.error(f"Failed to ingest GovInfo {endpoint_key}: {e}")
                results[endpoint_key] = {'error': str(e)}

        # Generate summary
        total_processed = sum(r.get('total_processed', 0) for r in results.values() if 'total_processed' in r)
        total_errors = sum(r.get('failed_batches', 0) for r in results.values() if 'failed_batches' in r)

        summary = {
            'congress': congress,
            'start_date': start_date,
            'total_processed': total_processed,
            'total_errors': total_errors,
            'endpoints': results,
            'start_time': self.ingestion_stats['start_time'],
            'end_time': datetime.now(),
            'duration': (datetime.now() - self.ingestion_stats['start_time']).total_seconds()
        }

        self.logger.info(f"GovInfo ingestion completed: {total_processed} records, {total_errors} errors")
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
