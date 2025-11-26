#!/usr/bin/env python3
"""
Enhanced OpenStates Data Ingestion System
Comprehensive bulk ingestion with rate limiting, pagination, parallel processing, and orchestration
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


# ============================================================================
# DATA MODELS (Pydantic Validation)
# ============================================================================

class PersonModel(BaseModel):
    """Pydantic model for OpenStates person data validation"""
    person_id: str
    name: str
    family_name: Optional[str] = None
    given_name: Optional[str] = None
    image: Optional[str] = None
    gender: Optional[str] = None
    biography: Optional[str] = None
    birth_date: Optional[str] = None
    death_date: Optional[str] = None
    primary_party: Optional[str] = None
    jurisdiction_id: str
    current_role_data: Optional[Dict[str, Any]] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


class BillModel(BaseModel):
    """Pydantic model for OpenStates bill data validation"""
    bill_id: str
    identifier: str
    title: str
    classification: Optional[str] = None
    subject: Optional[str] = None
    abstract: Optional[str] = None
    jurisdiction: Dict[str, Any]
    legislative_session: Dict[str, Any]
    sponsor: Optional[Dict[str, Any]] = None
    from_organization: Optional[Dict[str, Any]] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


class CommitteeModel(BaseModel):
    """Pydantic model for OpenStates committee data validation"""
    committee_id: str
    name: str
    classification: Optional[str] = None
    jurisdiction: Dict[str, Any]
    parent: Optional[str] = None
    sources: List[Dict[str, Any]] = field(default_factory=list)
    members: List[Dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


class EventModel(BaseModel):
    """Pydantic model for OpenStates event data validation"""
    event_id: str
    name: str
    classification: Optional[str] = None
    description: Optional[str] = None
    jurisdiction: Dict[str, Any]
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: Optional[str] = None
    location: Optional[Dict[str, Any]] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


class JurisdictionModel(BaseModel):
    """Pydantic model for OpenStates jurisdiction data validation"""
    jurisdiction_id: str
    name: str
    classification: Optional[str] = None
    url: Optional[str] = None
    feature_flags: Dict[str, Any] = field(default_factory=dict)
    divisions: List[Dict[str, Any]] = field(default_factory=list)
    links: List[Dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


# ============================================================================
# RATE LIMITING SYSTEM
# ============================================================================

class OpenStatesRateLimitManager:
    """Sophisticated rate limiting for 1000 requests/hour limit"""

    def __init__(self, base_delay: float = 0.15, max_delay: float = 5.0):
        self.base_delay = base_delay  # ~1 request per 3.6 seconds
        self.max_delay = max_delay
        self.hourly_limit = 1000
        self.request_times: List[datetime] = []
        self.adaptive_factor = 1.0
        self.last_request_time: Optional[datetime] = None
        self.logger = logging.getLogger(__name__)

    def wait_if_needed(self):
        """Intelligent rate limiting with hourly tracking"""
        now = datetime.now()

        # Clean old requests (older than 1 hour)
        cutoff = now - timedelta(hours=1)
        self.request_times = [t for t in self.request_times if t > cutoff]

        # Check if approaching limit
        if len(self.request_times) >= 950:  # Safety margin
            oldest_request = self.request_times[0] if self.request_times else now
            sleep_time = 3600 - (now - oldest_request).total_seconds()
            if sleep_time > 0:
                self.logger.warning(f"Approaching hourly limit, waiting {sleep_time/60:.1f} minutes")
                time.sleep(sleep_time + 60)  # Extra safety margin
                self.request_times = []

        # Base rate limiting
        if self.last_request_time:
            elapsed = (now - self.last_request_time).total_seconds()
            required_delay = self.base_delay * self.adaptive_factor

            if elapsed < required_delay:
                time.sleep(required_delay - elapsed)

        # Adaptive timing based on recent success rate
        if self.adaptive_factor > 1.0:
            time.sleep(self.base_delay * self.adaptive_factor)
        else:
            time.sleep(self.base_delay)

        self.last_request_time = datetime.now()
        self.request_times.append(self.last_request_time)

    def handle_rate_limit_error(self):
        """Handle rate limit errors with exponential backoff"""
        self.adaptive_factor = min(self.adaptive_factor * 2.0, 10.0)
        self.logger.warning(f"Rate limit hit, increasing adaptive factor to {self.adaptive_factor}")
        time.sleep(self.base_delay * self.adaptive_factor)

    def handle_success(self):
        """Gradually reduce adaptive factor on success"""
        if self.adaptive_factor > 1.0:
            self.adaptive_factor = max(1.0, self.adaptive_factor * 0.9)


# ============================================================================
# PAGINATION MANAGEMENT
# ============================================================================

class OpenStatesPaginationManager:
    """Advanced pagination with offset tracking and resume capability"""

    def __init__(self, page_size: int = 200):
        self.page_size = page_size  # Increased to 200 for efficiency
        self.max_consecutive_empty_pages = 3
        self.offset_cache: Dict[str, int] = {}
        self.logger = logging.getLogger(__name__)

    def get_next_page_params(self, data_type: str, category: str) -> Dict[str, Any]:
        """Get next pagination parameters from checkpoint"""
        # This would integrate with the checkpoint system
        return {
            'page': 1,
            'per_page': self.page_size,
            'resume': False,
            'total_processed': 0
        }

    def should_continue_pagination(self, response_data: Dict, empty_page_count: int) -> bool:
        """Determine if pagination should continue"""
        results = response_data.get('results', [])
        pagination = response_data.get('pagination', {})

        # Stop if no results and we've had multiple empty pages
        if not results and empty_page_count >= self.max_consecutive_empty_pages:
            return False

        # Stop if pagination indicates end
        current_page = pagination.get('page', 1)
        max_page = pagination.get('max_page', 1)

        return current_page < max_page and len(results) > 0


# ============================================================================
# DATA VALIDATION
# ============================================================================

class OpenStatesDataValidator:
    """Advanced data validation with Pydantic models"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def validate_person_data(self, person_data: Dict[str, Any]) -> Optional[PersonModel]:
        """Validate person data with comprehensive checks"""
        try:
            # Extract and normalize fields
            normalized_data = self._normalize_person_fields(person_data)

            # Validate with Pydantic
            person = PersonModel(**normalized_data)
            return person
        except ValidationError as e:
            self.logger.warning(f"Person validation failed: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error validating person data: {e}")
            return None

    def validate_bill_data(self, bill_data: Dict[str, Any]) -> Optional[BillModel]:
        """Validate bill data with comprehensive checks"""
        try:
            normalized_data = self._normalize_bill_fields(bill_data)
            bill = BillModel(**normalized_data)
            return bill
        except ValidationError as e:
            self.logger.warning(f"Bill validation failed: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error validating bill data: {e}")
            return None

    def validate_committee_data(self, committee_data: Dict[str, Any]) -> Optional[CommitteeModel]:
        """Validate committee data with comprehensive checks"""
        try:
            normalized_data = self._normalize_committee_fields(committee_data)
            committee = CommitteeModel(**normalized_data)
            return committee
        except ValidationError as e:
            self.logger.warning(f"Committee validation failed: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error validating committee data: {e}")
            return None

    def validate_event_data(self, event_data: Dict[str, Any]) -> Optional[EventModel]:
        """Validate event data with comprehensive checks"""
        try:
            normalized_data = self._normalize_event_fields(event_data)
            event = EventModel(**normalized_data)
            return event
        except ValidationError as e:
            self.logger.warning(f"Event validation failed: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error validating event data: {e}")
            return None

    def validate_jurisdiction_data(self, jurisdiction_data: Dict[str, Any]) -> Optional[JurisdictionModel]:
        """Validate jurisdiction data with comprehensive checks"""
        try:
            normalized_data = self._normalize_jurisdiction_fields(jurisdiction_data)
            jurisdiction = JurisdictionModel(**normalized_data)
            return jurisdiction
        except ValidationError as e:
            self.logger.warning(f"Jurisdiction validation failed: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error validating jurisdiction data: {e}")
            return None

    def _normalize_person_fields(self, person_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize person data fields"""
        # Handle jurisdiction - can be dict or string
        jurisdiction = person_data.get('jurisdiction', {})
        if isinstance(jurisdiction, str):
            jurisdiction_id = jurisdiction
        elif isinstance(jurisdiction, dict):
            jurisdiction_id = jurisdiction.get('id', '')
        else:
            jurisdiction_id = ''

        return {
            'person_id': person_data.get('id', ''),
            'name': person_data.get('name', ''),
            'family_name': person_data.get('familyName'),
            'given_name': person_data.get('givenName'),
            'image': person_data.get('image'),
            'gender': person_data.get('gender'),
            'biography': person_data.get('biography'),
            'birth_date': self._parse_date(person_data.get('birthDate')),
            'death_date': self._parse_date(person_data.get('deathDate')),
            'primary_party': person_data.get('primaryParty', ''),
            'jurisdiction_id': jurisdiction_id,
            'current_role_data': person_data.get('currentRole', {})
        }

    def _normalize_bill_fields(self, bill_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize bill data fields"""
        return {
            'bill_id': bill_data.get('id', ''),
            'identifier': bill_data.get('identifier', ''),
            'title': bill_data.get('title', ''),
            'classification': bill_data.get('classification', ''),
            'subject': bill_data.get('subject', ''),
            'abstract': bill_data.get('abstract', ''),
            'jurisdiction': bill_data.get('jurisdiction', {}),
            'legislative_session': bill_data.get('legislativeSession', {}),
            'sponsor': bill_data.get('sponsor', {}),
            'from_organization': bill_data.get('fromOrganization', {})
        }

    def _normalize_committee_fields(self, committee_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize committee data fields"""
        return {
            'committee_id': committee_data.get('id', ''),
            'name': committee_data.get('name', ''),
            'classification': committee_data.get('classification', ''),
            'jurisdiction': committee_data.get('jurisdiction', {}),
            'parent': committee_data.get('parent'),
            'sources': committee_data.get('sources', []),
            'members': committee_data.get('members', [])
        }

    def _normalize_event_fields(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize event data fields"""
        return {
            'event_id': event_data.get('id', ''),
            'name': event_data.get('name', ''),
            'classification': event_data.get('classification', ''),
            'description': event_data.get('description', ''),
            'jurisdiction': event_data.get('jurisdiction', {}),
            'start_date': self._parse_datetime(event_data.get('start_date')),
            'end_date': self._parse_datetime(event_data.get('end_date')),
            'status': event_data.get('status', ''),
            'location': event_data.get('location', {})
        }

    def _normalize_jurisdiction_fields(self, jurisdiction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize jurisdiction data fields"""
        return {
            'jurisdiction_id': jurisdiction_data.get('id', ''),
            'name': jurisdiction_data.get('name', ''),
            'classification': jurisdiction_data.get('classification', ''),
            'url': jurisdiction_data.get('url', ''),
            'feature_flags': jurisdiction_data.get('featureFlags', {}),
            'divisions': jurisdiction_data.get('divisions', []),
            'links': jurisdiction_data.get('links', [])
        }

    def _parse_date(self, date_str: Optional[str]) -> Optional[str]:
        """Parse date string to ISO format"""
        if not date_str:
            return None

        try:
            # Try common date formats
            for fmt in ['%Y-%m-%d', '%Y/%m/%d', '%m/%d/%Y', '%Y-%m-%dT%H:%M:%S']:
                try:
                    parsed_date = datetime.strptime(date_str, fmt)
                    return parsed_date.strftime('%Y-%m-%d')
                except ValueError:
                    continue
            return None
        except Exception:
            return None

    def _parse_datetime(self, datetime_str: Optional[str]) -> Optional[datetime]:
        """Parse datetime string to datetime object"""
        if not datetime_str:
            return None

        try:
            return datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
        except Exception:
            return None


# ============================================================================
# PARALLEL PROCESSING
# ============================================================================

class OpenStatesParallelProcessor:
    """Sophisticated parallel processing with rate limit awareness"""

    def __init__(self, max_workers: int = 2):  # Limited due to rate limits
        self.max_workers = max_workers
        self.semaphore = threading.Semaphore(max_workers)
        self.active_requests = 0
        self.request_lock = threading.Lock()
        self.logger = logging.getLogger(__name__)

    def process_jurisdictions_parallel(self, ingestor, jurisdictions: List[str]) -> Dict[str, Any]:
        """Process multiple jurisdictions in parallel with rate limit coordination"""

        results = {}

        def process_jurisdiction_thread(jurisdiction: str) -> Dict[str, Any]:
            """Process single jurisdiction in thread"""
            with self.semaphore:
                with self.request_lock:
                    self.active_requests += 1

                try:
                    result = ingestor.ingest_jurisdiction_complete(jurisdiction)
                    return {'jurisdiction': jurisdiction, 'result': result, 'success': True}
                except Exception as e:
                    self.logger.error(f"Jurisdiction {jurisdiction} failed: {e}")
                    return {'jurisdiction': jurisdiction, 'error': str(e), 'success': False}
                finally:
                    with self.request_lock:
                        self.active_requests -= 1

        # Process in parallel with rate limit coordination
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_jurisdiction = {
                executor.submit(process_jurisdiction_thread, jur): jur
                for jur in jurisdictions
            }

            for future in concurrent.futures.as_completed(future_to_jurisdiction):
                jurisdiction = future_to_jurisdiction[future]
                result = future.result()
                results[jurisdiction] = result

        return results


# ============================================================================
# PROGRESS MONITORING
# ============================================================================

class OpenStatesProgressMonitor:
    """Advanced progress monitoring with real-time ETA"""

    def __init__(self):
        self.start_time = datetime.now()
        self.progress_history: List[Dict[str, Any]] = []
        self.logger = logging.getLogger(__name__)

    def update_progress(self, data_type: str, category: str, processed: int, total: int):
        """Update progress with ETA calculation"""
        now = datetime.now()
        elapsed = (now - self.start_time).total_seconds()

        if processed > 0 and total > 0:
            rate = processed / elapsed
            eta_seconds = (total - processed) / rate if rate > 0 else 0
            eta = now + timedelta(seconds=eta_seconds)

            progress_data = {
                'timestamp': now,
                'data_type': data_type,
                'category': category,
                'processed': processed,
                'total': total,
                'percentage': (processed / total * 100),
                'rate': rate,
                'eta': eta
            }

            self.progress_history.append(progress_data)

            # Log progress
            self.logger.info(
                f"{data_type}/{category}: {processed:,}/{total:,} "
                f"({progress_data['percentage']:.1f}%) "
                f"Rate: {rate:.1f}/s ETA: {eta.strftime('%H:%M:%S')}"
            )

    def get_summary(self) -> Dict[str, Any]:
        """Get progress summary"""
        if not self.progress_history:
            return {'status': 'No progress recorded'}

        latest = self.progress_history[-1]
        total_time = (datetime.now() - self.start_time).total_seconds()

        return {
            'total_elapsed_seconds': total_time,
            'latest_progress': latest,
            'total_data_types': len(set(p['data_type'] for p in self.progress_history)),
            'average_rate': sum(p['rate'] for p in self.progress_history) / len(self.progress_history)
        }


# ============================================================================
# MAIN ENHANCED INGESTOR
# ============================================================================

class EnhancedOpenStatesIngestor:
    """Enhanced OpenStates ingestion with comprehensive functionality"""

    def __init__(self):
        # Validate API key
        api_keys = validate_api_keys()
        if not api_keys['openstates.org']:
            raise ValueError("OPENSTATES_API_KEY not found in environment variables")

        self.api_key = get_optional_env_var('OPENSTATES_API_KEY')
        self.base_url = "https://v3.openstates.org"
        self.batch_size = 50
        self.max_retries = 3

        # Initialize components
        self.rate_manager = OpenStatesRateLimitManager()
        self.pagination_manager = OpenStatesPaginationManager()
        self.validator = OpenStatesDataValidator()
        self.progress_monitor = OpenStatesProgressMonitor()
        self.parallel_processor = OpenStatesParallelProcessor()

        # Database connection
        self.db_conn = psycopg2.connect(
            database='cbwinslow',
            user='cbwinslow'
        )
        self.db_conn.autocommit = False

        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def ingest_jurisdiction_complete(self, jurisdiction: str) -> Dict[str, Any]:
        """Ingest complete data for a jurisdiction"""
        self.logger.info(f"Starting complete ingestion for jurisdiction: {jurisdiction}")

        results = {}

        # Phase 1: People
        try:
            people_result = self.ingest_people_with_details(jurisdiction)
            results['people'] = people_result
            self.logger.info(f"✅ People ingestion completed: {people_result.get('total_processed', 0)} records")
        except Exception as e:
            self.logger.error(f"❌ People ingestion failed: {e}")
            results['people'] = {'error': str(e), 'success': False}

        # Phase 2: Bills
        try:
            bills_result = self.ingest_bills_with_details(jurisdiction)
            results['bills'] = bills_result
            self.logger.info(f"✅ Bills ingestion completed: {bills_result.get('total_processed', 0)} records")
        except Exception as e:
            self.logger.error(f"❌ Bills ingestion failed: {e}")
            results['bills'] = {'error': str(e), 'success': False}

        # Phase 3: Committees
        try:
            committees_result = self.ingest_committees_with_details(jurisdiction)
            results['committees'] = committees_result
            self.logger.info(f"✅ Committees ingestion completed: {committees_result.get('total_processed', 0)} records")
        except Exception as e:
            self.logger.error(f"❌ Committees ingestion failed: {e}")
            results['committees'] = {'error': str(e), 'success': False}

        # Phase 4: Events
        try:
            events_result = self.ingest_events_with_details(jurisdiction)
            results['events'] = events_result
            self.logger.info(f"✅ Events ingestion completed: {events_result.get('total_processed', 0)} records")
        except Exception as e:
            self.logger.error(f"❌ Events ingestion failed: {e}")
            results['events'] = {'error': str(e), 'success': False}

        # Generate summary
        total_processed = sum(
            result.get('total_processed', 0)
            for result in results.values()
            if isinstance(result, dict) and 'total_processed' in result
        )

        success_count = sum(
            1 for result in results.values()
            if isinstance(result, dict) and result.get('success', True)
        )

        summary = {
            'jurisdiction': jurisdiction,
            'total_processed': total_processed,
            'data_types_processed': success_count,
            'data_types_total': len(results),
            'success_rate': (success_count / len(results)) * 100,
            'results': results
        }

        self.logger.info(f"🎉 Complete ingestion for {jurisdiction}: {total_processed} total records")
        return summary

    def ingest_people_with_details(self, jurisdiction: str = None) -> Dict[str, Any]:
        """Ingest people with full details and relationships"""
        self.logger.info(f"Starting people ingestion for jurisdiction: {jurisdiction}")

        # Phase 1: Basic people data
        basic_result = self.ingest_people(jurisdiction)

        # Phase 2: Person details enrichment
        details_result = self.ingest_person_details(jurisdiction)

        # Phase 3: Person-bill relationships
        relationships_result = self.ingest_person_bill_relationships(jurisdiction)

        total_processed = sum([
            basic_result.get('records_processed', 0),
            details_result.get('records_processed', 0),
            relationships_result.get('records_processed', 0)
        ])

        return {
            'basic_people': basic_result,
            'details_enrichment': details_result,
            'relationships': relationships_result,
            'total_processed': total_processed
        }

    def ingest_people(self, jurisdiction: str = None) -> Dict[str, Any]:
        """Ingest basic people data with enhanced pagination and rate limiting"""
        self.logger.info(f"Ingesting people for jurisdiction: {jurisdiction}")

        total_processed = 0
        total_skipped = 0
        page = 1
        empty_page_count = 0

        while True:
            # Rate limiting
            self.rate_manager.wait_if_needed()

            # Fetch people
            people_data = self.fetch_people_batch(jurisdiction, page)
            people = people_data.get('results', [])

            if not people:
                empty_page_count += 1
                if not self.pagination_manager.should_continue_pagination(people_data, empty_page_count):
                    break
                continue

            self.logger.info(f"📦 Processing page {page} - {len(people)} people...")

            # Process people with validation
            new_people = []
            skipped_in_batch = 0

            for person_data in people:
                person_id = person_data.get('id')

                if not person_id:
                    skipped_in_batch += 1
                    continue

                # Validate with Pydantic
                validated_person = self.validator.validate_person_data(person_data)
                if not validated_person:
                    skipped_in_batch += 1
                    continue

                # Check if already processed (fingerprinting)
                if self.is_record_processed(person_id, person_data):
                    skipped_in_batch += 1
                    continue

                new_people.append(validated_person.dict())

            # Insert batch
            if new_people:
                inserted = self.insert_people_batch(new_people)
                total_processed += inserted
                self.logger.info(f"   ✅ Inserted {inserted} new people")
                self.rate_manager.handle_success()

            total_skipped += skipped_in_batch

            # Update progress
            self.progress_monitor.update_progress('people', jurisdiction or 'all', total_processed, total_processed + total_skipped)

            # Check pagination
            if not self.pagination_manager.should_continue_pagination(people_data, 0):
                break

            page += 1
            empty_page_count = 0

        self.logger.info(f"🎉 People ingestion completed: {total_processed} processed, {total_skipped} skipped")

        return {
            'records_processed': total_processed,
            'records_skipped': total_skipped,
            'final_page': page
        }

    def fetch_people_batch(self, jurisdiction: str = None, page: int = 1) -> Dict[str, Any]:
        """Fetch a batch of people from OpenStates API with enhanced error handling"""
        url = f"{self.base_url}/people"
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

    def is_record_processed(self, person_id: str, person_data: Dict[str, Any]) -> bool:
        """Check if record was already processed using fingerprinting"""
        cursor = self.db_conn.cursor()

        try:
            # Create content hash for fingerprinting
            content_hash = hashlib.sha256(
                json.dumps(person_data, sort_keys=True).encode('utf-8')
            ).hexdigest()

            cursor.execute("""
                SELECT incremental.is_record_processed(
                    %s, %s, %s, %s::jsonb
                )
            """, ('openstates.org', 'people', person_id, json.dumps(person_data)))

            result = cursor.fetchone()
            return result[0] if result else False
        finally:
            cursor.close()

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
                    p['person_id'], p['name'], p['family_name'], p['given_name'],
                    p['image'], p['gender'], p['biography'], p['birth_date'],
                    p['death_date'], p['primary_party'], p['jurisdiction_id'],
                    Json(p['current_role_data']), p['created_at'], p['updated_at']
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
        finally:
            cursor.close()

    # Placeholder methods for other data types (to be implemented)
    def ingest_person_details(self, jurisdiction: str = None) -> Dict[str, Any]:
        """Ingest person details enrichment"""
        # TODO: Implement person details ingestion
        return {'records_processed': 0, 'message': 'Person details not yet implemented'}

    def ingest_person_bill_relationships(self, jurisdiction: str = None) -> Dict[str, Any]:
        """Ingest person-bill relationships"""
        # TODO: Implement person-bill relationships
        return {'records_processed': 0, 'message': 'Person-bill relationships not yet implemented'}

    def ingest_bills_with_details(self, jurisdiction: str = None) -> Dict[str, Any]:
        """Ingest bills with full details and relationships"""
        # TODO: Implement bills ingestion
        return {'records_processed': 0, 'message': 'Bills ingestion not yet implemented'}

    def ingest_committees_with_details(self, jurisdiction: str = None) -> Dict[str, Any]:
        """Ingest committees with full details and memberships"""
        # TODO: Implement committees ingestion
        return {'records_processed': 0, 'message': 'Committees ingestion not yet implemented'}

    def ingest_events_with_details(self, jurisdiction: str = None) -> Dict[str, Any]:
        """Ingest events with full details and participants"""
        # TODO: Implement events ingestion
        return {'records_processed': 0, 'message': 'Events ingestion not yet implemented'}

    def ingest_all_jurisdictions_parallel(self, jurisdictions: List[str] = None) -> Dict[str, Any]:
        """Ingest multiple jurisdictions in parallel"""
        if not jurisdictions:
            jurisdictions = ['ca', 'tx', 'ny', 'fl', 'pa', 'il', 'oh', 'ga', 'nc', 'mi']

        self.logger.info(f"Starting parallel ingestion for {len(jurisdictions)} jurisdictions")

        results = self.parallel_processor.process_jurisdictions_parallel(self, jurisdictions)

        # Generate summary
        completed = sum(1 for r in results.values() if r.get('success', False))
        total_processed = sum(
            r.get('result', {}).get('total_processed', 0)
            for r in results.values()
            if r.get('success', False)
        )

        summary = {
            'jurisdictions_processed': completed,
            'jurisdictions_total': len(jurisdictions),
            'total_records_processed': total_processed,
            'success_rate': (completed / len(jurisdictions)) * 100,
            'results': results
        }

        self.logger.info(f"🎉 Parallel ingestion completed: {completed}/{len(jurisdictions)} jurisdictions, {total_processed} total records")
        return summary


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main function for enhanced OpenStates ingestion"""
    print("🚀 Enhanced OpenStates Data Ingestion System")
    print("=" * 50)

    try:
        # Initialize enhanced ingestor
        ingestor = EnhancedOpenStatesIngestor()

        # Example: Single jurisdiction ingestion
        print("\n📍 Ingesting single jurisdiction (CA)...")
        ca_result = ingestor.ingest_jurisdiction_complete('ca')
        print(f"✅ CA completed: {ca_result['total_processed']} records")

        # Example: Parallel jurisdiction ingestion
        print("\n📍 Ingesting multiple jurisdictions in parallel...")
        jurisdictions = ['tx', 'ny', 'fl']
        parallel_result = ingestor.ingest_all_jurisdictions_parallel(jurisdictions)
        print(f"✅ Parallel completed: {parallel_result['total_records_processed']} records")

        # Display progress summary
        progress_summary = ingestor.progress_monitor.get_summary()
        print(f"\n📊 Progress Summary:")
        print(f"   Total elapsed: {progress_summary.get('total_elapsed_seconds', 0):.1f}s")
        print(f"   Data types: {progress_summary.get('total_data_types', 0)}")
        print(f"   Average rate: {progress_summary.get('average_rate', 0):.1f} records/s")

        print("\n🎉 Enhanced OpenStates ingestion completed successfully!")

    except Exception as e:
        print(f"❌ Fatal error: {e}")
        logging.error(f"Fatal error in enhanced ingestion: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
