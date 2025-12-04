#!/usr/bin/env python3
"""
Comprehensive Data Ingestion Script for OpenDiscourse
Handles Congress.gov, GovInfo, and OpenStates data ingestion
with robust error handling, logging, and database integration
"""

import os
import sys
import json
import time
import logging
import argparse
import requests
import psycopg2
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import wraps
import traceback
import yaml
import re
import hashlib
import socket
import ssl
from urllib.parse import urlparse, urljoin
from collections import defaultdict
import warnings

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ingestion.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Constants
CONGRESS_API_BASE = "https://api.congress.gov/v3"
GOVINFO_API_BASE = "https://www.govinfo.gov/bulkdata"
OPENSTATES_API_BASE = "https://v3.openstates.org"
DEFAULT_TIMEOUT = 30
MAX_RETRIES = 3
RETRY_DELAY = 5
BATCH_SIZE = 50
MAX_WORKERS = 10

@dataclass
class IngestionConfig:
    """Configuration for data ingestion"""
    congress_api_key: str = ""
    govinfo_api_key: str = ""
    openstates_api_key: str = ""
    database_url: str = ""
    data_directory: str = "data"
    log_level: str = "INFO"
    max_workers: int = MAX_WORKERS
    batch_size: int = BATCH_SIZE
    timeout: int = DEFAULT_TIMEOUT
    max_retries: int = MAX_RETRIES

@dataclass
class IngestionResult:
    """Result of ingestion operation"""
    source: str
    records_processed: int = 0
    records_successful: int = 0
    records_failed: int = 0
    start_time: float = 0.0
    end_time: float = 0.0
    errors: List[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []

    def duration(self) -> float:
        """Calculate duration of ingestion"""
        return self.end_time - self.start_time

    def success_rate(self) -> float:
        """Calculate success rate"""
        if self.records_processed == 0:
            return 0.0
        return (self.records_successful / self.records_processed) * 100

class DataIngestionManager:
    """Comprehensive data ingestion manager"""

    def __init__(self, config: IngestionConfig = None):
        self.config = config or self._load_default_config()
        self._setup_logging()
        self._validate_config()
        self.session = self._create_session()
        self.database_connection = None
        self.ingestion_results = []

    def _load_default_config(self) -> IngestionConfig:
        """Load default configuration"""
        try:
            # Try to load from environment variables first
            config = IngestionConfig(
                congress_api_key=os.getenv('CONGRESS_API_KEY', ''),
                govinfo_api_key=os.getenv('GOVINFO_API_KEY', ''),
                openstates_api_key=os.getenv('OPENSTATES_API_KEY', ''),
                database_url=os.getenv('DATABASE_URL', ''),
                data_directory=os.getenv('DATA_DIRECTORY', 'data'),
                log_level=os.getenv('LOG_LEVEL', 'INFO'),
                max_workers=int(os.getenv('MAX_WORKERS', MAX_WORKERS)),
                batch_size=int(os.getenv('BATCH_SIZE', BATCH_SIZE)),
                timeout=int(os.getenv('TIMEOUT', DEFAULT_TIMEOUT)),
                max_retries=int(os.getenv('MAX_RETRIES', MAX_RETRIES))
            )

            # Try to load from config file
            config_file = 'ingestion_config.yaml'
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    file_config = yaml.safe_load(f)
                    for field, value in file_config.items():
                        if hasattr(config, field):
                            setattr(config, field, value)

            return config
        except Exception as e:
            logger.warning(f"Failed to load configuration: {str(e)}")
            return IngestionConfig()

    def _setup_logging(self):
        """Setup logging based on configuration"""
        try:
            log_level = getattr(logging, self.config.log_level.upper(), logging.INFO)
            logger.setLevel(log_level)
            for handler in logger.handlers:
                handler.setLevel(log_level)
        except Exception as e:
            logger.error(f"Failed to setup logging: {str(e)}")

    def _validate_config(self):
        """Validate configuration"""
        try:
            # Create data directory if it doesn't exist
            os.makedirs(self.config.data_directory, exist_ok=True)

            # Validate database URL if provided
            if self.config.database_url:
                try:
                    result = urlparse(self.config.database_url)
                    if not all([result.scheme, result.netloc]):
                        raise ValueError("Invalid database URL format")
                except Exception as e:
                    logger.warning(f"Database URL validation failed: {str(e)}")

            logger.info("Configuration validated successfully")
        except Exception as e:
            logger.error(f"Configuration validation failed: {str(e)}")
            raise

    def _create_session(self) -> requests.Session:
        """Create HTTP session with retry logic"""
        session = requests.Session()

        # Set default headers
        session.headers.update({
            'User-Agent': 'OpenDiscourse-Ingestion/2.0',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })

        # Configure timeouts
        session.timeout = self.config.timeout

        return session

    @staticmethod
    def _retry_on_failure(func):
        """Retry decorator for API calls"""
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(self.config.max_retries):
                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    last_exception = e
                    logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")
                    if attempt < self.config.max_retries - 1:
                        time.sleep(self.config.timeout * (attempt + 1))
                    continue

            logger.error(f"All {self.config.max_retries} attempts failed")
            raise last_exception

        return wrapper

    def _connect_to_database(self):
        """Establish database connection"""
        if not self.config.database_url:
            logger.warning("No database URL configured, skipping database connection")
            return None

        try:
            if self.database_connection and not self.database_connection.closed:
                return self.database_connection

            logger.info(f"Connecting to database: {self.config.database_url}")
            self.database_connection = psycopg2.connect(self.config.database_url)
            logger.info("Database connection established successfully")
            return self.database_connection
        except Exception as e:
            logger.error(f"Database connection failed: {str(e)}")
            self.database_connection = None
            return None

    def _execute_query(self, query: str, params: tuple = None, fetch: bool = False):
        """Execute SQL query"""
        conn = self._connect_to_database()
        if not conn:
            return None

        try:
            with conn.cursor() as cursor:
                cursor.execute(query, params or ())
                if fetch:
                    return cursor.fetchall()
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Query execution failed: {str(e)}")
            conn.rollback()
            return None

    def _setup_database_schema(self):
        """Setup database schema if needed"""
        try:
            # Check if tables exist, create if not
            tables_to_create = [
                """
                CREATE TABLE IF NOT EXISTS congress_bills (
                    bill_id VARCHAR(50) PRIMARY KEY,
                    congress INT NOT NULL,
                    bill_type VARCHAR(10) NOT NULL,
                    bill_number VARCHAR(10) NOT NULL,
                    title TEXT,
                    sponsor_bioguide_id VARCHAR(50),
                    introduced_date TIMESTAMP,
                    policy_area VARCHAR(100),
                    subjects TEXT[],
                    url TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS govinfo_documents (
                    document_id VARCHAR(100) PRIMARY KEY,
                    document_type VARCHAR(50) NOT NULL,
                    publication_date TIMESTAMP,
                    title TEXT,
                    download_url TEXT,
                    file_size INT,
                    pages INT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS openstates_bills (
                    bill_id VARCHAR(100) PRIMARY KEY,
                    state VARCHAR(50) NOT NULL,
                    session VARCHAR(50) NOT NULL,
                    bill_type VARCHAR(20) NOT NULL,
                    bill_number VARCHAR(20) NOT NULL,
                    title TEXT,
                    sponsor_name TEXT,
                    introduced_date TIMESTAMP,
                    updated_date TIMESTAMP,
                    url TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            ]

            for table_sql in tables_to_create:
                self._execute_query(table_sql)

            logger.info("Database schema setup completed")
            return True
        except Exception as e:
            logger.error(f"Database schema setup failed: {str(e)}")
            return False

    def _normalize_bill_data(self, bill_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize Congress bill data"""
        try:
            bill = bill_data.get('bill', {})

            # Extract basic information
            bill_id = bill.get('billId', '')
            bill_type = bill.get('type', '').lower()
            bill_number = bill.get('number', '')

            # Parse bill_id to get components
            if '-' in bill_id:
                parts = bill_id.split('-')
                if len(parts) >= 2:
                    bill_type = parts[0].lower()
                    bill_number = parts[1]

            # Extract title
            titles = bill.get('titles', [])
            primary_title = titles[0].get('title', '') if titles else ''

            # Get sponsor
            sponsor = bill.get('sponsor', {})
            sponsor_bioguide = sponsor.get('bioguideId', '')

            # Get introduction date
            introduced_date = bill.get('introducedDate', '')
            if introduced_date:
                introduced_date = datetime.fromisoformat(
                    introduced_date.replace('Z', '+00:00')
                )

            # Get policy areas
            policy_areas = bill.get('policyArea', {})
            policy_area_name = policy_areas.get('name', '')

            # Get subjects
            subjects = bill.get('subjects', [])
            subject_names = [s.get('name', '') for s in subjects if s.get('name')]

            return {
                'bill_id': bill_id,
                'congress': 118,  # Default to current congress
                'bill_type': bill_type,
                'bill_number': bill_number,
                'title': primary_title,
                'sponsor_bioguide_id': sponsor_bioguide,
                'introduced_date': introduced_date,
                'policy_area': policy_area_name,
                'subjects': subject_names,
                'url': bill.get('url', '')
            }
        except Exception as e:
            logger.error(f"Bill data normalization failed: {str(e)}")
            return None

    def _normalize_govinfo_data(self, document_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize GovInfo document data"""
        try:
            return {
                'document_id': document_data.get('documentId', ''),
                'document_type': document_data.get('documentType', ''),
                'publication_date': document_data.get('publicationDate', ''),
                'title': document_data.get('title', ''),
                'download_url': document_data.get('downloadUrl', ''),
                'file_size': document_data.get('fileSize', 0),
                'pages': document_data.get('pages', 0)
            }
        except Exception as e:
            logger.error(f"GovInfo data normalization failed: {str(e)}")
            return None

    def _normalize_openstates_data(self, bill_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize OpenStates bill data"""
        try:
            return {
                'bill_id': bill_data.get('id', ''),
                'state': bill_data.get('state', ''),
                'session': bill_data.get('session', ''),
                'bill_type': bill_data.get('bill_type', ''),
                'bill_number': bill_data.get('bill_number', ''),
                'title': bill_data.get('title', ''),
                'sponsor_name': bill_data.get('sponsor_name', ''),
                'introduced_date': bill_data.get('introduced_date', ''),
                'updated_date': bill_data.get('updated_date', ''),
                'url': bill_data.get('url', '')
            }
        except Exception as e:
            logger.error(f"OpenStates data normalization failed: {str(e)}")
            return None

    @_retry_on_failure
    def _fetch_congress_bills(self, congress: int, bill_type: str = None, limit: int = 20) -> List[Dict[str, Any]]:
        """Fetch bills from Congress.gov API"""
        try:
            params = {
                'congress': congress,
                'limit': limit,
                'offset': 0
            }

            if bill_type:
                params['type'] = bill_type.upper()

            url = f"{CONGRESS_API_BASE}/bill"
            if self.config.congress_api_key:
                params['api_key'] = self.config.congress_api_key

            logger.info(f"Fetching Congress bills: {url} with params {params}")
            response = self.session.get(url, params=params)
            response.raise_for_status()

            data = response.json()
            bills = data.get('bills', [])
            logger.info(f"Retrieved {len(bills)} bills from Congress.gov")
            return bills
        except Exception as e:
            logger.error(f"Failed to fetch Congress bills: {str(e)}")
            return []

    @_retry_on_failure
    def _fetch_govinfo_documents(self, collection: str, year: int = None) -> List[Dict[str, Any]]:
        """Fetch documents from GovInfo API"""
        try:
            url = f"{GOVINFO_API_BASE}/{collection}"
            if year:
                url = f"{url}/{year}"

            params = {}
            if self.config.govinfo_api_key:
                params['api_key'] = self.config.govinfo_api_key

            logger.info(f"Fetching GovInfo documents: {url}")
            response = self.session.get(url, params=params)
            response.raise_for_status()

            data = response.json()
            documents = data.get('documents', [])
            logger.info(f"Retrieved {len(documents)} documents from GovInfo")
            return documents
        except Exception as e:
            logger.error(f"Failed to fetch GovInfo documents: {str(e)}")
            return []

    @_retry_on_failure
    def _fetch_openstates_bills(self, state: str, session: str = None) -> List[Dict[str, Any]]:
        """Fetch bills from OpenStates API"""
        try:
            url = f"{OPENSTATES_API_BASE}/bills"
            params = {'state': state}
            if session:
                params['session'] = session
            if self.config.openstates_api_key:
                params['apikey'] = self.config.openstates_api_key

            logger.info(f"Fetching OpenStates bills: {url} with params {params}")
            response = self.session.get(url, params=params)
            response.raise_for_status()

            data = response.json()
            bills = data.get('results', [])
            logger.info(f"Retrieved {len(bills)} bills from OpenStates")
            return bills
        except Exception as e:
            logger.error(f"Failed to fetch OpenStates bills: {str(e)}")
            return []

    def _save_to_database(self, data: List[Dict[str, Any]], table_name: str) -> Tuple[int, int]:
        """Save data to database"""
        if not self._connect_to_database():
            return 0, 0

        try:
            successful = 0
            failed = 0

            for item in data:
                try:
                    if table_name == 'congress_bills':
                        query = """
                        INSERT INTO congress_bills
                        (bill_id, congress, bill_type, bill_number, title, sponsor_bioguide_id,
                         introduced_date, policy_area, subjects, url)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (bill_id) DO UPDATE SET
                        title = EXCLUDED.title,
                        sponsor_bioguide_id = EXCLUDED.sponsor_bioguide_id,
                        introduced_date = EXCLUDED.introduced_date,
                        policy_area = EXCLUDED.policy_area,
                        subjects = EXCLUDED.subjects,
                        url = EXCLUDED.url,
                        updated_at = CURRENT_TIMESTAMP
                        """
                        params = (
                            item['bill_id'], item['congress'], item['bill_type'], item['bill_number'],
                            item['title'], item['sponsor_bioguide_id'], item['introduced_date'],
                            item['policy_area'], item['subjects'], item['url']
                        )
                    elif table_name == 'govinfo_documents':
                        query = """
                        INSERT INTO govinfo_documents
                        (document_id, document_type, publication_date, title, download_url, file_size, pages)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (document_id) DO UPDATE SET
                        title = EXCLUDED.title,
                        download_url = EXCLUDED.download_url,
                        file_size = EXCLUDED.file_size,
                        pages = EXCLUDED.pages,
                        updated_at = CURRENT_TIMESTAMP
                        """
                        params = (
                            item['document_id'], item['document_type'], item['publication_date'],
                            item['title'], item['download_url'], item['file_size'], item['pages']
                        )
                    elif table_name == 'openstates_bills':
                        query = """
                        INSERT INTO openstates_bills
                        (bill_id, state, session, bill_type, bill_number, title, sponsor_name,
                         introduced_date, updated_date, url)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (bill_id) DO UPDATE SET
                        title = EXCLUDED.title,
                        sponsor_name = EXCLUDED.sponsor_name,
                        introduced_date = EXCLUDED.introduced_date,
                        updated_date = EXCLUDED.updated_date,
                        url = EXCLUDED.url,
                        updated_at = CURRENT_TIMESTAMP
                        """
                        params = (
                            item['bill_id'], item['state'], item['session'], item['bill_type'],
                            item['bill_number'], item['title'], item['sponsor_name'],
                            item['introduced_date'], item['updated_date'], item['url']
                        )
                    else:
                        logger.warning(f"Unknown table name: {table_name}")
                        continue

                    if self._execute_query(query, params):
                        successful += 1
                    else:
                        failed += 1

                except Exception as e:
                    logger.error(f"Failed to save {table_name} record: {str(e)}")
                    failed += 1

            logger.info(f"Database save completed: {successful} successful, {failed} failed")
            return successful, failed

        except Exception as e:
            logger.error(f"Database save operation failed: {str(e)}")
            return 0, len(data)

    def _save_to_file(self, data: List[Dict[str, Any]], source: str, file_type: str = 'json') -> bool:
        """Save data to file"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{source}_data_{timestamp}.{file_type}"
            filepath = os.path.join(self.config.data_directory, filename)

            if file_type == 'json':
                with open(filepath, 'w') as f:
                    json.dump(data, f, indent=2, default=str)
            elif file_type == 'csv':
                df = pd.DataFrame(data)
                df.to_csv(filepath, index=False)
            else:
                logger.warning(f"Unsupported file type: {file_type}")
                return False

            logger.info(f"Saved {len(data)} records to {filepath}")
            return True
        except Exception as e:
            logger.error(f"Failed to save data to file: {str(e)}")
            return False

    def _process_batch(self, data: List[Dict[str, Any]], source: str, table_name: str) -> IngestionResult:
        """Process a batch of data"""
        result = IngestionResult(source=source)
        result.start_time = time.time()

        try:
            # Normalize data
            normalized_data = []
            for item in data:
                if source == 'congress':
                    normalized = self._normalize_bill_data({'bill': item})
                elif source == 'govinfo':
                    normalized = self._normalize_govinfo_data(item)
                elif source == 'openstates':
                    normalized = self._normalize_openstates_data(item)
                else:
                    logger.warning(f"Unknown source: {source}")
                    continue

                if normalized:
                    normalized_data.append(normalized)

            result.records_processed = len(normalized_data)

            # Save to database
            if self.config.database_url:
                successful, failed = self._save_to_database(normalized_data, table_name)
                result.records_successful = successful
                result.records_failed = failed

            # Save to file as backup
            self._save_to_file(data, source)

            result.end_time = time.time()
            logger.info(f"Batch processing completed for {source}: {result.records_processed} records")
            return result

        except Exception as e:
            result.end_time = time.time()
            result.errors.append(f"Batch processing failed: {str(e)}")
            logger.error(f"Batch processing failed: {str(e)}")
            return result

    def _parallel_process(self, fetch_func, source: str, table_name: str, **kwargs) -> IngestionResult:
        """Process data in parallel"""
        result = IngestionResult(source=source)
        result.start_time = time.time()

        try:
            # Fetch data
            data = fetch_func(**kwargs)
            if not data:
                result.end_time = time.time()
                result.errors.append("No data fetched")
                return result

            # Process in batches
            batch_size = self.config.batch_size
            batches = [data[i:i + batch_size] for i in range(0, len(data), batch_size)]

            with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
                futures = []
                for batch in batches:
                    futures.append(executor.submit(
                        self._process_batch, batch, source, table_name
                    ))

                for future in as_completed(futures):
                    batch_result = future.result()
                    result.records_processed += batch_result.records_processed
                    result.records_successful += batch_result.records_successful
                    result.records_failed += batch_result.records_failed
                    result.errors.extend(batch_result.errors)

            result.end_time = time.time()
            logger.info(f"Parallel processing completed for {source}: {result.records_processed} records")
            return result

        except Exception as e:
            result.end_time = time.time()
            result.errors.append(f"Parallel processing failed: {str(e)}")
            logger.error(f"Parallel processing failed: {str(e)}")
            return result

    def ingest_congress_data(self, congress: int = 118, bill_type: str = None) -> IngestionResult:
        """Ingest Congress.gov data"""
        logger.info(f"Starting Congress data ingestion for congress {congress}")
        return self._parallel_process(
            self._fetch_congress_bills,
            source='congress',
            table_name='congress_bills',
            congress=congress,
            bill_type=bill_type
        )

    def ingest_govinfo_data(self, collection: str, year: int = None) -> IngestionResult:
        """Ingest GovInfo data"""
        logger.info(f"Starting GovInfo data ingestion for collection {collection}")
        return self._parallel_process(
            self._fetch_govinfo_documents,
            source='govinfo',
            table_name='govinfo_documents',
            collection=collection,
            year=year
        )

    def ingest_openstates_data(self, state: str, session: str = None) -> IngestionResult:
        """Ingest OpenStates data"""
        logger.info(f"Starting OpenStates data ingestion for state {state}")
        return self._parallel_process(
            self._fetch_openstates_bills,
            source='openstates',
            table_name='openstates_bills',
            state=state,
            session=session
        )

    def run_comprehensive_ingestion(self) -> List[IngestionResult]:
        """Run comprehensive ingestion of all data sources"""
        results = []

        # Setup database schema
        self._setup_database_schema()

        # Ingest Congress data
        congress_result = self.ingest_congress_data(congress=118)
        results.append(congress_result)

        # Ingest GovInfo data (example collections)
        govinfo_collections = ['BILLS', 'CONGREC', 'PLAW']
        for collection in govinfo_collections:
            govinfo_result = self.ingest_govinfo_data(collection=collection, year=2023)
            results.append(govinfo_result)

        # Ingest OpenStates data (example states)
        states = ['CA', 'TX', 'NY']
        for state in states:
            openstates_result = self.ingest_openstates_data(state=state)
            results.append(openstates_result)

        return results

    def generate_report(self, results: List[IngestionResult]) -> Dict[str, Any]:
        """Generate comprehensive ingestion report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_sources': len(results),
            'total_records_processed': sum(r.records_processed for r in results),
            'total_records_successful': sum(r.records_successful for r in results),
            'total_records_failed': sum(r.records_failed for r in results),
            'total_duration': sum(r.duration() for r in results),
            'sources': []
        }

        for result in results:
            source_report = {
                'source': result.source,
                'records_processed': result.records_processed,
                'records_successful': result.records_successful,
                'records_failed': result.records_failed,
                'success_rate': result.success_rate(),
                'duration': result.duration(),
                'errors': result.errors
            }
            report['sources'].append(source_report)

        # Calculate overall success rate
        total_processed = report['total_records_processed']
        total_successful = report['total_records_successful']
        report['overall_success_rate'] = (total_successful / total_processed * 100) if total_processed > 0 else 0

        return report

    def save_report(self, report: Dict[str, Any], format: str = 'json') -> bool:
        """Save ingestion report"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"ingestion_report_{timestamp}.{format}"
            filepath = os.path.join(self.config.data_directory, filename)

            if format == 'json':
                with open(filepath, 'w') as f:
                    json.dump(report, f, indent=2, default=str)
            elif format == 'yaml':
                with open(filepath, 'w') as f:
                    yaml.dump(report, f, default_flow_style=False)
            else:
                logger.warning(f"Unsupported report format: {format}")
                return False

            logger.info(f"Saved ingestion report to {filepath}")
            return True
        except Exception as e:
            logger.error(f"Failed to save ingestion report: {str(e)}")
            return False

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Comprehensive Data Ingestion for OpenDiscourse')
    parser.add_argument('--source', choices=['congress', 'govinfo', 'openstates', 'all'], default='all',
                       help='Data source to ingest')
    parser.add_argument('--congress', type=int, default=118, help='Congress number')
    parser.add_argument('--bill-type', help='Bill type (hr, s, hjres, etc.)')
    parser.add_argument('--collection', help='GovInfo collection')
    parser.add_argument('--year', type=int, help='Year for GovInfo data')
    parser.add_argument('--state', help='State for OpenStates data')
    parser.add_argument('--session', help='Session for OpenStates data')
    parser.add_argument('--config', help='Configuration file')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    parser.add_argument('--dry-run', action='store_true', help='Dry run (no database writes)')

    args = parser.parse_args()

    if args.debug:
        logger.setLevel(logging.DEBUG)

    # Load configuration
    config = None
    if args.config:
        try:
            with open(args.config, 'r') as f:
                config_data = yaml.safe_load(f)
                config = IngestionConfig(**config_data)
        except Exception as e:
            logger.error(f"Failed to load config file: {str(e)}")
            sys.exit(1)

    # Initialize ingestion manager
    manager = DataIngestionManager(config)

    # Run ingestion based on source
    results = []

    if args.source in ['congress', 'all']:
        result = manager.ingest_congress_data(
            congress=args.congress,
            bill_type=args.bill_type
        )
        results.append(result)

    if args.source in ['govinfo', 'all']:
        if not args.collection:
            logger.error("GovInfo collection required")
            sys.exit(1)
        result = manager.ingest_govinfo_data(
            collection=args.collection,
            year=args.year
        )
        results.append(result)

    if args.source in ['openstates', 'all']:
        if not args.state:
            logger.error("State required for OpenStates")
            sys.exit(1)
        result = manager.ingest_openstates_data(
            state=args.state,
            session=args.session
        )
        results.append(result)

    # Generate and save report
    report = manager.generate_report(results)
    manager.save_report(report)

    # Print summary
    print("\n" + "="*80)
    print("📊 INGESTION SUMMARY")
    print("="*80)
    print(f"📅 Timestamp: {report['timestamp']}")
    print(f"📦 Total Sources: {report['total_sources']}")
    print(f"📊 Records Processed: {report['total_records_processed']}")
    print(f"✅ Records Successful: {report['total_records_successful']}")
    print(f"❌ Records Failed: {report['total_records_failed']}")
    print(f"📈 Success Rate: {report['overall_success_rate']:.1f}%")
    print(f"⏱️ Total Duration: {report['total_duration']:.2f}s")

    for source_report in report['sources']:
        print(f"\n📋 {source_report['source'].upper()} INGESTION:")
        print(f"   Records: {source_report['records_processed']}")
        print(f"   Success: {source_report['records_successful']}")
        print(f"   Failed: {source_report['records_failed']}")
        print(f"   Rate: {source_report['success_rate']:.1f}%")
        print(f"   Time: {source_report['duration']:.2f}s")

    print("\n🎉 Ingestion completed successfully!")
    print("📄 Report saved to data directory")

if __name__ == "__main__":
    main()
