#!/usr/bin/env python3
"""
Paralleltes Ingestion with Detailed Bill Information
Optimized for maximum throughput using concurrent processing
"""

import os
import sys
import json
import time
import logging
import requests
import psycopg2
from psycopg2 import pool
from psycopg2.extras import execute_values
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

# Add project root to path
sys.path.append('/home/cbwinslow/Videos/opendiscourse')

from rate_limiter import adaptive_limiters
from env_config import get_optional_env_var, validate_api_keys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/parallel_bills_votes_ingestion.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class IngestionStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class BillIngestionJob:
    """Represents a single bill ingestion job"""
    job_id: str
    source: str
    congress: Optional[int] = None
    jurisdiction: Optional[str] = None
    status: IngestionStatus = IngestionStatus.PENDING
    records_processed: int = 0
    records_skipped: int = 0
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

class ParallelBillsVotesIngestor:
    """Parallel ingestion of bills and votes with detailed information"""

    def __init__(self, max_workers: int = 10):
        self.max_workers = max_workers
        self.base_url_congress = "https://api.congress.gov/v3"
        self.base_url_openstates = "https://v3.openstates.org"

        # Validate and get API keys
        api_keys = validate_api_k
     self.congress_api_key = get_optional_env_var('CONGRESS_API_KEY')
self.openstates_api_key = get_optional_env_var('OPENSTATES_API_KEY')

        # Setup database connection pool
        self.db_pool = psycopg2.pool.ThreadedConnectionPool(
            minconn=5,
            maxconn=max_workers + 5,
            database='opendiscourse',
            user='cbwinslow',
            host='/var/run/postgresql'
        )

        self.batch_size = 50
        self.jobs: List[BillIngestionJob] = []

        logger.info(f"✅ Initialized with {max_workers} parallel workers")

    def fetch_bill_details(self, bill_id: str, congress: int) -> Optional[Dict[str, Any]]:
        """Fetch detailed bill information including text, actions, cosponsors, etc."""
        adaptive_limiters['congress.gov'].wait_for_token()

        url = f"{self.base_url_congress}/bill/{congress}/{bill_id}"
        params = {'api_key': self.congress_api_key}
        headers = {'Accept': 'application/json'}

        try:
            response = requests.get(url, params=params, headers=headers, timeout=30)
            adaptive_limiters['congress.gov'].update_from_response(response.headers)
            response.raise_for_status()

            bill_data = response.json().get('bill', {})

            # Fetch additional details
            details = {
                'bill_data': bill_data,
                'actions': self._fetch_bill_actions(bill_id, congress),
                'cosponsors': self._fetch_bill_cosponsors(bill_id, congress),
                'subjects': self._fetch_bill_subjects(bill_id, congress),
                'summaries': self._fetch_bill_summaries(bill_id, congress),
                'text_versions': self._fetch_bill_text_versions(bill_id, congress),
                'amendments': self._fetch_bill_amendments(bill_id, congress),
                'related_bills': self._fetch_related_bills(bill_id, congress)
            }

            return details

        except Exception as e:
            logger.error(f"Error fetching bill details for {bill_id}: {e}")
            return None

    def _fetch_bill_actions(self, bill_id: str, congress: int) -> List[Dict]:
        """Fetch all actions for a bill"""
        try:
            adaptive_limiters['congress.gov'].wait_for_token()
            url = f"{self.base_url_congress}/bill/{congress}/{bill_id}/actions"
            params = {'api_key': self.congress_api_key, 'limit': 250}
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json().get('actions', [])
        except:
            return []

    def _fetch_bill_cosponsors(self, bill_id: str, congress: int) -> List[Dict]:
        """Fetch all cosponsors for a bill"""
        try:
            adaptive_limiters['congress.gov'].wait_for_token()
            url = f"{self.base_url_congress}/bill/{congress}/{bill_id}/cosponsors"
            params = {'api_key': self.congress_api_key, 'limit': 250}
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json().get('cosponsors', [
()
   for_statusse_rairesponse.           ut=30)
  timeo=params,l, params.get(urrequestsnse = po         res
   ess_api_key}.congr_key': se= {'apiams ar  p          jects"
ub}/sill_idgress}/{bll/{conngress}/birl_co.base_u= f"{self    url        r_token()
 ov'].wait_fo['congress.giterse_limtiv  adap
                try:""
  ll"cs for a biubjects/topi"Fetch s    ""t]:
     List[Dic ->ess: int)r, congrbill_id: stf, s(selsubject_fetch_bill_
    def urn []
    ret:
              except
