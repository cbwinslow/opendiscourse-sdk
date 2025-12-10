#!/usr/bin/env python3
"""
Multi-Threaded Bulk Data Ingestion System
A robust, scalable system for ingesting large volumes of government data
with advanced error handling, parallel processing, and monitoring.
"""

import os
import sys
import json
import time
import logging
import argparse
import requests
import psycopg2
import threading
import queue
import traceback
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import wraps
from collections import defaultdict
import warnings
from pathlib import Path

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

# Configure comprehensive logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/multi_threaded_ingestion.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class IngestionTask:
    """Represents a single ingestion task"""
    task_id: str
    source: str
    params: Dict[str, Any]
    priority: int = 1
    retry_count: int = 0
    max_retries: int = 3
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

@dataclass
class TaskResult:
    """Result of a single ingestion task"""
    task_id: str
    source: str
    success: bool
    records_processed: int = 0
    records_successful: int = 0
    records_failed: int = 0
    start_time: float = 0.0
    end_time: float = 0.0
    error_message: str = None
    data: List[Dict[str, Any]] = None

    def __post_init__(self):
        if self.data is None:
            self.data = []

    @property
    def duration(self) -> float:
        return self.end_time - self.start_time

    @property
    def success_rate(self) -> float:
        if self.records_processed == 0:
            return 0.0
        return (self.records_successful / self.records_processed) * 100

class RateLimiter:
    """Thread-safe rate limiter for API calls"""

    def __init__(self, max_calls: int, time_window: int = 60):
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = []
        self.lock = threading.Lock()

    def wait(self):
        """Wait if necessary to stay within rate limits"""
        with self.lock:
            now = time.time()
            # Remove calls outside the time window
            self.calls = [call_time for call_time in self.calls if now - call_time < self.time_window]

            # If we've reached the limit, wait
            if len(self.calls) >= self.max_calls:
                sleep_time = self.time_window - (now - self.calls[0])
                if sleep_time > 0:
                    logger.debug(f"Rate limit reached, sleeping for {sleep_time:.2f} seconds")
                    time.sleep(sleep_time)
                    # Clean up old calls after sleeping
                    now = time.time()
                    self.calls = [call_time for call_time in self.calls if now - call_time < self.time_window]

            # Record this call
            self.calls.append(now)

class DatabaseManager:
    """Manages database operations with connection pooling"""

    def __init__(self, db_config: Dict[str, Any]):
        self.db_config = db_config
        self.pool = None
        self._setup_pool()

    def _setup_pool(self):
        """Setup database connection pool"""
        try:
            from psycopg2 import pool
            self.pool = pool.ThreadedConnectionPool(
                minconn=5,
                maxconn=20,
                **self.db_config
            )
            logger.info("✅ Database connection pool established")
        except Exception as e:
            logger.error(f"❌ Failed to setup database pool: {e}")
            self.pool = None

    def get_connection(self):
        """Get connection from pool"""
        if self.pool:
            return self.pool.getconn()
        return None

    def return_connection(self, conn):
        """Return connection to pool"""
        if self.pool and conn:
            self.pool.putconn(conn)

    def execute_batch_insert(self, table_name: str, data: List[Dict[str, Any]],
                           conflict_columns: List[str] = None) -> Tuple[int, int]:
        """Execute batch insert with conflict handling"""
        conn = self.get_connection()
        if not conn:
            return 0, len(data)

        try:
            successful = 0
            failed = 0

            with conn.cursor() as cursor:
                for item in data:
                    try:
                        columns = list(item.keys())
                        values = list(item.values())

                        # Build INSERT query
                        if conflict_columns:
                            # Use ON CONFLICT for PostgreSQL
                            conflict_clause = f"ON CONFLICT ({', '.join(conflict_columns)}) DO UPDATE SET "
                            update_columns = [col for col in columns if col not in conflict_columns]
                            if update_columns:
                                set_clause = ', '.join([f"{col} = EXCLUDED.{col}" for col in update_columns])
                                conflict_clause += set_clause
                            else:
                                conflict_clause = "ON CONFLICT DO NOTHING"

                            query = f"""
                            INSERT INTO {table_name} ({', '.join(columns)})
                            VALUES ({', '.join(['%s'] * len(values))})
                            {conflict_clause}
                            """
                        else:
                            query = f"""
                            INSERT INTO {table_name} ({', '.join(columns)})
                            VALUES ({', '.join(['%s'] * len(values))})
                            ON CONFLICT DO NOTHING
                            """

                        cursor.execute(query, values)
                        if cursor.rowcount > 0:
                            successful += 1
                        conn.commit()

                    except Exception as e:
                        failed += 1
                        conn.rollback()
                        logger.debug(f"Failed to insert record: {e}")

            return successful, failed

        except Exception as e:
            logger.error(f"Batch insert failed: {e}")
            return 0, len(data)
        finally:
            self.return_connection(conn)

class APIRateLimitedClient:
    """HTTP client with rate limiting and retry logic"""

    def __init__(self, rate_limiter: RateLimiter, max_retries: int = 3, timeout: int = 30):
        self.rate_limiter = rate_limiter
        self.max_retries = max_retries
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'OpenDiscourse-MultiThread/2.0',
            'Accept': 'application/json'
        })

    def get(self, url: str, params: Dict[str, Any] = None, headers: Dict[str, Any] = None) -> Optional[Dict]:
        """Make GET request with rate limiting and retry logic"""
        last_exception = None

        for attempt in range(self.max_retries):
            try:
                # Apply rate limiting
                self.rate_limiter.wait()

                # Prepare request
                request_params = params.copy() if params else {}
                request_headers = {'Accept': 'application/json'}
                if headers:
                    request_headers.update(headers)

                # Make request
                response = self.session.get(
                    url,
                    params=request_params,
                    headers=request_headers,
                    timeout=self.timeout
                )

                # Check for rate limiting
                if response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', 60))
                    logger.warning(f"Rate limited, waiting {retry_after} seconds")
                    time.sleep(retry_after)
                    continue

                # Check for other errors
                response.raise_for_status()

                return response.json()

            except requests.exceptions.RequestException as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    delay = (2 ** attempt)  # Exponential backoff
                    logger.warning(f"Request failed (attempt {attempt + 1}), retrying in {delay}s: {e}")
                    time.sleep(delay)
                continue

        logger.error(f"All {self.max_retries} attempts failed")
        if last_exception:
            logger.error(f"Final error: {last_exception}")
        return None

class CongressDataFetcher:
    """Fetches data from Congress.gov API"""

    def __init__(self, api_client: APIRateLimitedClient, api_key: str):
        self.api_client = api_client
        self.api_key = api_key
        self.base_url = "https://api.congress.gov/v3"

    def fetch_bills(self, congress: int, bill_type: str = None, limit: int = 250,
                   offset: int = 0) -> List[Dict[str, Any]]:
        """Fetch bills from Congress.gov"""
        params = {
            'congress': congress,
            'limit': min(limit, 250),  # API max is 250
            'offset': offset,
            'api_key': self.api_key
        }

        if bill_type:
            params['type'] = bill_type.upper()

        url = f"{self.base_url}/bill"
        logger.debug(f"Fetching Congress bills: {params}")

        data = self.api_client.get(url, params)
        if data and 'bills' in data:
            return data['bills']

        return []

    def fetch_members(self, congress: int, limit: int = 250, offset: int = 0) -> List[Dict[str, Any]]:
        """Fetch members from Congress.gov"""
        params = {
            'congress': congress,
            'limit': min(limit, 250),
            'offset': offset,
            'api_key': self.api_key
        }

        url = f"{self.base_url}/member/congress/{congress}"
        logger.debug(f"Fetching Congress members: {params}")

        data = self.api_client.get(url, params)
        if data and 'members' in data:
            return data['members']

        return []

class OpenStatesDataFetcher:
    """Fetches data from OpenStates API"""

    def __init__(self, api_client: APIRateLimitedClient, api_key: str):
        self.api_client = api_client
        self.api_key = api_key
        self.base_url = "https://v3.openstates.org"

    def fetch_bills(self, jurisdiction: str, limit: int = 100, page: int = 1) -> List[Dict[str, Any]]:
        """Fetch bills from OpenStates"""
        params = {
            'jurisdiction': jurisdiction,
            'page': page,
            'per_page': min(limit, 100),
            'apikey': self.api_key
        }

        url = f"{self.base_url}/bills"
        logger.debug(f"Fetching OpenStates bills: {params}")

        data = self.api_client.get(url, params)
        if data and 'results' in data:
            return data['results']

        return []

class GovInfoDataFetcher:
    """Fetches data from GovInfo API"""

    def __init__(self, api_client: APIRateLimitedClient, api_key: str):
        self.api_client = api_client
        self.api_key = api_key
        self.base_url = "https://www.govinfo.gov/bulkdata"

    def fetch_collection(self, collection: str, year: int = None, limit: int = 100,
                        page: int = 1) -> List[Dict[str, Any]]:
        """Fetch documents from GovInfo"""
        params = {
            'pageSize': min(limit, 100),
            'page': page,
            'api_key': self.api_key
        }

        if year:
            url = f"{self.base_url}/{collection}/{year}"
        else:
            url = f"{self.base_url}/{collection}"

        logger.debug(f"Fetching GovInfo {collection}: {params}")

        data = self.api_client.get(url, params)
        if data and 'packages' in data:
            return data['packages']

        return []

class MultiThreadedBulkIngestion:
    """Main class for multi-threaded bulk data ingestion"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

        # Initialize components
        self.rate_limiter = RateLimiter(
            max_calls=config.get('max_requests_per_minute', 100),
            time_window=60
        )

        self.api_client = APIRateLimitedClient(
            rate_limiter=self.rate_limiter,
            max_retries=config.get('max_retries', 3),
            timeout=config.get('timeout', 30)
        )

        self.db_manager = DatabaseManager(config.get('database', {}))

        # Initialize data fetchers
        self.congress_fetcher = CongressDataFetcher(
            self.api_client,
            config.get('congress_api_key', '')
        )
        self.openstates_fetcher = OpenStatesDataFetcher(
            self.api_client,
            config.get('openstates_api_key', '')
        )
        self.govinfo_fetcher = GovInfoDataFetcher(
            self.api_client,
            config.get('govinfo_api_key', '')
        )

        # Thread pool
        self.max_workers = config.get('max_workers', 10)
        self.thread_pool = ThreadPoolExecutor(max_workers=self.max_workers)

        # Task tracking
        self.pending_tasks = queue.PriorityQueue()
        self.completed_tasks = []
        self.failed_tasks = []
        self.task_results = {}

        # Statistics
        self.stats = {
            'total_tasks': 0,
            'completed_tasks': 0,
            'failed_tasks': 0,
            'total_records': 0,
            'successful_records': 0,
            'failed_records': 0,
            'start_time': time.time()
        }

        logger.info(f"🚀 Multi-threaded ingestion initialized with {self.max_workers} workers")

    def create_congress_tasks(self, congresses: List[int], bill_types: List[str] = None) -> List[IngestionTask]:
        """Create Congress ingestion tasks"""
        tasks = []

        if bill_types is None:
            bill_types = ['hr', 's', 'hjres', 'sjres', 'hconres', 'sconres', 'hres', 'sres']

        for congress in congresses:
            # Members task (high priority)
            tasks.append(IngestionTask(
                task_id=f"congress_members_{congress}",
                source="congress",
                params={
                    'action': 'fetch_members',
                    'congress': congress,
                    'table': 'congress.members'
                },
                priority=1
            ))

            # Bills tasks (medium priority)
            for bill_type in bill_types:
                tasks.append(IngestionTask(
                    task_id=f"congress_bills_{congress}_{bill_type}",
                    source="congress",
                    params={
                        'action': 'fetch_bills',
                        'congress': congress,
                        'bill_type': bill_type,
                        'table': 'congress.bills'
                    },
                    priority=2
                ))

        return tasks

    def create_openstates_tasks(self, jurisdictions: List[str]) -> List[IngestionTask]:
        """Create OpenStates ingestion tasks"""
        tasks = []

        for jurisdiction in jurisdictions:
            # Bills task
            tasks.append(IngestionTask(
                task_id=f"openstates_bills_{jurisdiction}",
                source="openstates",
                params={
                    'action': 'fetch_bills',
                    'jurisdiction': jurisdiction,
                    'table': 'openstates.bills'
                },
                priority=3
            ))

        return tasks

    def create_govinfo_tasks(self, collections: List[str], years: List[int] = None) -> List[IngestionTask]:
        """Create GovInfo ingestion tasks"""
        tasks = []

        if years is None:
            years = list(range(2020, 2025))  # Last 5 years

        for collection in collections:
            for year in years:
                tasks.append(IngestionTask(
                    task_id=f"govinfo_{collection}_{year}",
                    source="govinfo",
                    params={
                        'action': 'fetch_collection',
                        'collection': collection,
                        'year': year,
                        'table': f'govinfo.{collection.lower()}'
                    },
                    priority=4
                ))

        return tasks

    def process_task(self, task: IngestionTask) -> TaskResult:
        """Process a single ingestion task"""
        result = TaskResult(
            task_id=task.task_id,
            source=task.source,
            start_time=time.time()
        )

        try:
            logger.info(f"🔄 Processing task: {task.task_id}")

            # Fetch data based on source and action
            data = []
            if task.source == 'congress':
                data = self._fetch_congress_data(task.params)
            elif task.source == 'openstates':
                data = self._fetch_openstates_data(task.params)
            elif task.source == 'govinfo':
                data = self._fetch_govinfo_data(task.params)

            result.records_processed = len(data)

            if data:
                # Insert into database
                successful, failed = self.db_manager.execute_batch_insert(
                    task.params['table'],
                    data,
                    conflict_columns=['id']  # Adjust based on table schema
                )

                result.records_successful = successful
                result.records_failed = failed
                result.data = data
                result.success = True

                logger.info(f"✅ Task completed: {task.task_id} - {len(data)} records")
            else:
                result.success = True  # No data is not necessarily a failure
                logger.info(f"ℹ️  Task completed: {task.task_id} - No data found")

        except Exception as e:
            result.success = False
            result.error_message = str(e)
            result.records_failed = 1
            logger.error(f"❌ Task failed: {task.task_id} - {e}")
            logger.debug(traceback.format_exc())

        finally:
            result.end_time = time.time()

        return result

    def _fetch_congress_data(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fetch data from Congress.gov"""
        if params['action'] == 'fetch_members':
            return self._fetch_congress_members(params['congress'])
        elif params['action'] == 'fetch_bills':
            return self._fetch_congress_bills(params['congress'], params.get('bill_type'))
        return []

    def _fetch_openstates_data(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fetch data from OpenStates"""
        if params['action'] == 'fetch_bills':
            return self._fetch_openstates_bills(params['jurisdiction'])
        return []

    def _fetch_govinfo_data(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fetch data from GovInfo"""
        if params['action'] == 'fetch_collection':
            return self._fetch_govinfo_collection(params['collection'], params.get('year'))
        return []

    def _fetch_congress_members(self, congress: int) -> List[Dict[str, Any]]:
        """Fetch Congress members with pagination"""
        all_members = []
        offset = 0
        limit = 250

        while True:
            members = self.congress_fetcher.fetch_members(congress, limit, offset)
            if not members:
                break

            # Transform data
            for member in members:
                if isinstance(member, dict) and 'member' in member:
                    member_data = member['member']
                else:
                    member_data = member

                transformed = {
                    'id': member_data.get('bioguideId'),
                    'full_name': member_data.get('fullName'),
                    'first_name': member_data.get('firstName'),
                    'last_name': member_data.get('lastName'),
                    'party': member_data.get('party'),
                    'state': member_data.get('state'),
                    'district': member_data.get('district'),
                    'congress_number': congress,
                    'active': member_data.get('active', True),
                    'created_at': datetime.now().isoformat()
                }
                all_members.append(transformed)

            if len(members) < limit:
                break

            offset += limit

        return all_members

    def _fetch_congress_bills(self, congress: int, bill_type: str = None) -> List[Dict[str, Any]]:
        """Fetch Congress bills with pagination"""
        all_bills = []
        offset = 0
        limit = 250

        while True:
            bills = self.congress_fetcher.fetch_bills(congress, bill_type, limit, offset)
            if not bills:
                break

            # Transform data
            for bill in bills:
                if isinstance(bill, dict) and 'bill' in bill:
                    bill_data = bill['bill']
                else:
                    bill_data = bill

                # Handle chamber mapping
                origin_chamber = bill_data.get('originChamber', '').lower()
                if origin_chamber in ['house', 'senate', 'joint']:
                    chamber_code = origin_chamber
                else:
                    chamber_code = 'house'  # Default

                transformed = {
                    'id': f"{congress}-{bill_data.get('type', '')}-{bill_data.get('number', '')}",
                    'congress_number': congress,
                    'bill_type': bill_data.get('type', ''),
                    'bill_number': bill_data.get('number', ''),
                    'origin_chamber': chamber_code,
                    'title': bill_data.get('title', ''),
                    'introduced_date': bill_data.get('introducedDate'),
                    'latest_action_date': bill_data.get('latestAction', {}).get('actionDate'),
                    'latest_action_text': bill_data.get('latestAction', {}).get('text'),
                    'policy_area': bill_data.get('policyArea', {}).get('name') if bill_data.get('policyArea') else '',
                    'sponsor_bioguide_id': bill_data.get('sponsor', {}).get('bioguideId'),
                    'created_at': datetime.now().isoformat()
                }
                all_bills.append(transformed)

            if len(bills) < limit:
                break

            offset += limit

        return all_bills

    def _fetch_openstates_bills(self, jurisdiction: str) -> List[Dict[str, Any]]:
        """Fetch OpenStates bills with pagination"""
        all_bills = []
        page = 1
        limit = 100

        while True:
            bills = self.openstates_fetcher.fetch_bills(jurisdiction, limit, page)
            if not bills:
                break

            # Transform data
            for bill in bills:
                transformed = {
                    'id': bill.get('id'),
                    'jurisdiction': bill.get('jurisdiction', {}).get('id'),
                    'session': bill.get('session'),
                    'identifier': bill.get('identifier'),
                    'title': bill.get('title'),
                    'classification': bill.get('classification', ['bill'])[0] if bill.get('classification') else 'bill',
                    'subjects': json.dumps(bill.get('subject', [])),
                    'actions': json.dumps(bill.get('actions', [])),
                    'created_at': datetime.now().isoformat()
                }
                all_bills.append(transformed)

            page += 1

        return all_bills

    def _fetch_govinfo_collection(self, collection: str, year: int = None) -> List[Dict[str, Any]]:
        """Fetch GovInfo collection data"""
        packages = self.govinfo_fetcher.fetch_collection(collection, year)

        # Transform data
        documents = []
        for package in packages:
            transformed = {
                'id': package.get('packageId'),
                'collection_code': package.get('collectionCode'),
                'title': package.get('title'),
                'congress_number': package.get('congressNumber'),
                'chamber_code': package.get('chamberCode', '').lower(),
                'bill_type': package.get('billType'),
                'bill_number': package.get('billNumber'),
                'doc_class': package.get('docClass'),
                'granule_count': package.get('granuleCount', 0),
                'date_issued': package.get('dateIssued'),
                'last_modified': package.get('lastModified'),
                'created_at': datetime.now().isoformat()
            }
            documents.append(transformed)

        return documents

    def add_tasks(self, tasks: List[IngestionTask]):
        """Add tasks to the queue"""
        for task in tasks:
            self.pending_tasks.put((task.priority, task.task_id, task))
            self.stats['total_tasks'] += 1

        logger.info(f"📋 Added {len(tasks)} tasks to queue")

    def run_ingestion(self) -> Dict[str, Any]:
        """Run the multi-threaded ingestion process"""
        logger.info("🚀 Starting multi-threaded bulk ingestion")

        try:
            # Process tasks
            while not self.pending_tasks.empty():
                try:
                    _, _, task = self.pending_tasks.get_nowait()

                    # Submit task to thread pool
                    future = self.thread_pool.submit(self.process_task, task)

                    # Process result
                    result = future.result()

                    if result.success:
                        self.completed_tasks.append(task)
                        self.stats['completed_tasks'] += 1
                        self.stats['successful_records'] += result.records_successful
                    else:
                        self.failed_tasks.append(task)
                        self.stats['failed_tasks'] += 1

                        # Retry if possible
                        if task.retry_count < task.max_retries:
                            task.retry_count += 1
                            task.priority += 1  # Lower priority for retries
                            self.pending_tasks.put((task.priority, task.task_id, task))
                            logger.info(f"🔄 Retrying task: {task.task_id} (attempt {task.retry_count})")

                    self.stats['total_records'] += result.records_processed
                    self.stats['failed_records'] += result.records_failed

                    # Log progress
                    progress = (self.stats['completed_tasks'] + self.stats['failed_tasks']) / self.stats['total_tasks'] * 100
                    logger.info(f"📊 Progress: {progress:.1f}% ({self.stats['completed_tasks']}/{self.stats['total_tasks']} completed)")

                except queue.Empty:
                    break
                except Exception as e:
                    logger.error(f"Error processing task: {e}")
                    self.stats['failed_tasks'] += 1

        except KeyboardInterrupt:
            logger.info("🛑 Ingestion interrupted by user")

        finally:
            self.thread_pool.shutdown(wait=True)

        return self._generate_report()

    def _generate_report(self) -> Dict[str, Any]:
        """Generate final ingestion report"""
        end_time = time.time()
        total_duration = end_time - self.stats['start_time']

        report = {
            'timestamp': datetime.now().isoformat(),
            'duration': total_duration,
            'statistics': self.stats.copy(),
            'task_breakdown': {
                'congress': {'completed': 0, 'failed': 0},
                'openstates': {'completed': 0, 'failed': 0},
                'govinfo': {'completed': 0, 'failed': 0}
            },
            'top_sources': []
        }

        # Count tasks by source
        for task in self.completed_tasks:
            report['task_breakdown'][task.source]['completed'] += 1

        for task in self.failed_tasks:
            report['task_breakdown'][task.source]['failed'] += 1

        # Calculate success rates
        for source in report['task_breakdown']:
            stats = report['task_breakdown'][source]
            total = stats['completed'] + stats['failed']
            if total > 0:
                stats['success_rate'] = stats['completed'] / total * 100
            else:
                stats['success_rate'] = 0.0

        logger.info("📊 Multi-threaded ingestion completed")
        logger.info(f"  Total tasks: {self.stats['total_tasks']}")
        logger.info(f"  Completed: {self.stats['completed_tasks']}")
        logger.info(f"  Failed: {self.stats['failed_tasks']}")
        logger.info(f"  Records: {self.stats['total_records']}")
        logger.info(f"  Duration: {total_duration:.2f}s")

        return report

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Multi-Threaded Bulk Data Ingestion')
    parser.add_argument('--congresses', nargs='+', type=int, default=[118],
                       help='Congress numbers to process')
    parser.add_argument('--jurisdictions', nargs='+', default=['ca', 'tx', 'ny'],
                       help='OpenStates jurisdictions to process')
    parser.add_argument('--collections', nargs='+', default=['BILLS', 'CRPT'],
                       help='GovInfo collections to process')
    parser.add_argument('--workers', type=int, default=10, help='Number of worker threads')
    parser.add_argument('--rate-limit', type=int, default=100, help='Requests per minute')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')

    args = parser.parse_args()

    if args.debug:
        logger.setLevel(logging.DEBUG)

    # Load configuration
    config = {
        'max_workers': args.workers,
        'max_requests_per_minute': args.rate_limit,
        'congress_api_key': os.getenv('CONGRESS_API_KEY', ''),
        'openstates_api_key': os.getenv('OPENSTATES_API_KEY', ''),
        'govinfo_api_key': os.getenv('GOVINFO_API_KEY', ''),
        'database': {
            'database': 'opendiscourse',
            'user': 'cbwinslow',
            'host': '/var/run/postgresql'
        }
    }

    # Validate required API keys
    required_keys = {
        'CONGRESS_API_KEY': config['congress_api_key'],
        'OPENSTATES_API_KEY': config['openstates_api_key'],
        'GOVINFO_API_KEY': config['govinfo_api_key']
    }

    missing_keys = [key for key, value in required_keys.items() if not value]
    if missing_keys:
        logger.error(f"❌ Missing API keys: {missing_keys}")
        sys.exit(1)

    logger.info("✅ All API keys validated")

    # Initialize ingestion system
    ingestion = MultiThreadedBulkIngestion(config)

    # Create tasks
    tasks = []

    # Congress tasks
    congress_tasks = ingestion.create_congress_tasks(args.congresses)
    tasks.extend(congress_tasks)

    # OpenStates tasks
    openstates_tasks = ingestion.create_openstates_tasks(args.jurisdictions)
    tasks.extend(openstates_tasks)

    # GovInfo tasks
    govinfo_tasks = ingestion.create_govinfo_tasks(args.collections)
    tasks.extend(govinfo_tasks)

    # Add all tasks
    ingestion.add_tasks(tasks)

    # Run ingestion
    report = ingestion.run_ingestion()

    # Print summary
    stats = report['statistics']
    print("\n" + "="*80)
    print("🎉 MULTI-THREADED BULK INGESTION COMPLETED")
    print("="*80)
    print(f"📊 Total Tasks: {stats['total_tasks']}")
    print(f"✅ Completed: {stats['completed_tasks']}")
    print(f"❌ Failed: {stats['failed_tasks']}")
    print(f"📈 Success Rate: {(stats['completed_tasks'] / stats['total_tasks'] * 100):.1f}%")
    print(f"📄 Records Processed: {stats['total_records']:,}")
    print(f"⏱️ Duration: {report['duration']:.2f} seconds")

    print("\n📋 By Source:")
    for source, stats in report['task_breakdown'].items():
        print(f"  {source.capitalize()}: {stats['completed']} completed, {stats['failed']} failed ({stats['success_rate']:.1f}% success)")

    # Save report
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = f"multi_threaded_ingestion_report_{timestamp}.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2, default=str)

    print(f"\n📄 Report saved to: {report_file}")
    print("="*80)

if __name__ == "__main__":
    main()
