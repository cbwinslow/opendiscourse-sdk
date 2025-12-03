#!/usr/bin/env python3
"""
OpenStates Jurisdictions Ingestion System
Complete jurisdictions data ingestion with details
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
# JURISDICTIONS DATA MODELS
# ============================================================================

class JurisdictionDivisionModel(BaseModel):
    """Pydantic model for jurisdiction division data"""
    division_id: str
    name: str
    country: str
    classification: Optional[str] = None
    parent_id: Optional[str] = None
    geometry: Optional[Dict[str, Any]] = None
    created_at: datetime = field(default_factory=datetime.now)


class JurisdictionLinkModel(BaseModel):
    """Pydantic model for jurisdiction link data"""
    link_id: str
    jurisdiction_id: str
    url: str
    note: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)


# ============================================================================
# JURISDICTIONS DATA VALIDATOR
# ============================================================================

class JurisdictionsDataValidator(OpenStatesDataValidator):
    """Extended data validator for jurisdictions-specific data"""

    def validate_jurisdiction_division_data(self, division_data: Dict[str, Any]) -> Optional[JurisdictionDivisionModel]:
        """Validate jurisdiction division data"""
        try:
            normalized_data = self._normalize_division_fields(division_data)
            division = JurisdictionDivisionModel(**normalized_data)
            return division
        except ValidationError as e:
            self.logger.warning(f"Jurisdiction division validation failed: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error validating jurisdiction division data: {e}")
            return None

    def validate_jurisdiction_link_data(self, link_data: Dict[str, Any]) -> Optional[JurisdictionLinkModel]:
        """Validate jurisdiction link data"""
        try:
            normalized_data = self._normalize_link_fields(link_data)
            link = JurisdictionLinkModel(**normalized_data)
            return link
        except ValidationError as e:
            self.logger.warning(f"Jurisdiction link validation failed: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error validating jurisdiction link data: {e}")
            return None

    def _normalize_division_fields(self, division_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize jurisdiction division data fields"""
        return {
            'division_id': division_data.get('id', ''),
            'name': division_data.get('name', ''),
            'country': division_data.get('country', ''),
            'classification': division_data.get('classification', ''),
            'parent_id': division_data.get('parent', ''),
            'geometry': division_data.get('geometry', {})
        }

    def _normalize_link_fields(self, link_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize jurisdiction link data fields"""
        return {
            'link_id': link_data.get('id', f"{link_data.get('jurisdiction_id', '')}_{hash(link_data.get('url', ''))}"),
            'jurisdiction_id': link_data.get('jurisdiction_id', ''),
            'url': link_data.get('url', ''),
            'note': link_data.get('note', '')
        }


# ============================================================================
# JURISDICTIONS INGESTOR
# ============================================================================

class OpenStatesJurisdictionsIngestor:
    """Complete jurisdictions data ingestion with details"""

    def __init__(self, db_conn, rate_manager: OpenStatesRateLimitManager,
                 pagination_manager: OpenStatesPaginationManager,
                 progress_monitor: OpenStatesProgressMonitor):
        self.db_conn = db_conn
        self.rate_manager = rate_manager
        self.pagination_manager = pagination_manager
        self.progress_monitor = progress_monitor
        self.validator = JurisdictionsDataValidator()
        self.logger = logging.getLogger(__name__)

        # API configuration
        self.api_key = get_optional_env_var('OPENSTATES_API_KEY')
        self.base_url = "https://v3.openstates.org"
        self.batch_size = 50
        self.max_retries = 3

    def ingest_all_jurisdictions(self) -> Dict[str, Any]:
        """Ingest all jurisdictions with complete details"""
        self.logger.info("Starting comprehensive jurisdictions ingestion")

        results = {}

        # Phase 1: Basic jurisdictions data
        try:
            basic_result = self.ingest_jurisdictions()
            results['basic_jurisdictions'] = basic_result
            self.logger.info(f"✅ Basic jurisdictions completed: {basic_result.get('records_processed', 0)} records")
        except Exception as e:
            self.logger.error(f"❌ Basic jurisdictions failed: {e}")
            results['basic_jurisdictions'] = {'error': str(e), 'success': False}

        # Phase 2: Jurisdiction details enrichment (parallel safe)
        if basic_result.get('records_processed', 0) > 0:
            try:
                details_result = self.ingest_jurisdiction_details()
                results['details_enrichment'] = details_result
                self.logger.info(f"✅ Jurisdiction details completed: {details_result.get('records_processed', 0)} records")
            except Exception as e:
                self.logger.error(f"❌ Jurisdiction details failed: {e}")
                results['details_enrichment'] = {'error': str(e), 'success': False}

        # Phase 3: Jurisdiction divisions
        try:
            divisions_result = self.ingest_jurisdiction_divisions()
            results['divisions'] = divisions_result
            self.logger.info(f"✅ Jurisdiction divisions completed: {divisions_result.get('records_processed', 0)} records")
        except Exception as e:
            self.logger.error(f"❌ Jurisdiction divisions failed: {e}")
            results['divisions'] = {'error': str(e), 'success': False}

        # Phase 4: Jurisdiction links
        try:
            links_result = self.ingest_jurisdiction_links()
            results['links'] = links_result
            self.logger.info(f"✅ Jurisdiction links completed: {links_result.get('records_processed', 0)} records")
        except Exception as e:
            self.logger.error(f"❌ Jurisdiction links failed: {e}")
            results['links'] = {'error': str(e), 'success': False}

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
            'total_processed': total_processed,
            'phases_completed': success_count,
            'phases_total': len(results),
            'success_rate': (success_count / len(results)) * 100,
            'results': results
        }

        self.logger.info(f"🎉 Comprehensive jurisdictions ingestion completed: {total_processed} total records")
        return summary

    def ingest_jurisdictions(self) -> Dict[str, Any]:
        """Ingest basic jurisdictions data with enhanced pagination and rate limiting"""
        self.logger.info("Ingesting basic jurisdictions data")

        total_processed = 0
        total_skipped = 0
        page = 1
        empty_page_count = 0

        while True:
            # Rate limiting
            self.rate_manager.wait_if_needed()

            # Fetch jurisdictions
            jurisdictions_data = self.fetch_jurisdictions_batch(page)
            jurisdictions = jurisdictions_data.get('results', [])

            if not jurisdictions:
                empty_page_count += 1
                if not self.pagination_manager.should_continue_pagination(jurisdictions_data, empty_page_count):
                    break
                continue

            self.logger.info(f"📦 Processing page {page} - {len(jurisdictions)} jurisdictions...")

            # Process jurisdictions with validation
            new_jurisdictions = []
            skipped_in_batch = 0

            for jurisdiction_data in jurisdictions:
                jurisdiction_id = jurisdiction_data.get('id')

                if not jurisdiction_id:
                    skipped_in_batch += 1
                    continue

                # Validate with Pydantic
                validated_jurisdiction = self.validator.validate_jurisdiction_data(jurisdiction_data)
                if not validated_jurisdiction:
                    skipped_in_batch += 1
                    continue

                # Check if already processed (fingerprinting)
                if self.is_jurisdiction_processed(jurisdiction_id, jurisdiction_data):
                    skipped_in_batch += 1
                    continue

                new_jurisdictions.append(validated_jurisdiction.dict())

            # Insert batch
            if new_jurisdictions:
                inserted = self.insert_jurisdictions_batch(new_jurisdictions)
                total_processed += inserted
                self.logger.info(f"   ✅ Inserted {inserted} new jurisdictions")
                self.rate_manager.handle_success()

            total_skipped += skipped_in_batch

            # Update progress
            self.progress_monitor.update_progress('jurisdictions', 'all', total_processed, total_processed + total_skipped)

            # Check pagination
            if not self.pagination_manager.should_continue_pagination(jurisdictions_data, 0):
                break

            page += 1
            empty_page_count = 0

        self.logger.info(f"🎉 Jurisdictions ingestion completed: {total_processed} processed, {total_skipped} skipped")

        return {
            'records_processed': total_processed,
            'records_skipped': total_skipped,
            'final_page': page
        }

    def fetch_jurisdictions_batch(self, page: int = 1) -> Dict[str, Any]:
        """Fetch a batch of jurisdictions from OpenStates API"""
        url = f"{self.base_url}/jurisdictions"
        params = {
            'apikey': self.api_key,
            'per_page': min(self.batch_size, 50),
            'page': page
        }

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

    def is_jurisdiction_processed(self, jurisdiction_id: str, jurisdiction_data: Dict[str, Any]) -> bool:
        """Check if jurisdiction was already processed using fingerprinting"""
        cursor = self.db_conn.cursor()

        try:
            # Create content hash for fingerprinting
            content_hash = hashlib.sha256(
                json.dumps(jurisdiction_data, sort_keys=True).encode('utf-8')
            ).hexdigest()

            cursor.execute("""
                SELECT incremental.is_record_processed(
                    %s, %s, %s, %s::jsonb
                )
            """, ('openstates.org', 'jurisdictions', jurisdiction_id, json.dumps(jurisdiction_data)))

            result = cursor.fetchone()
            return result[0] if result else False
        finally:
            cursor.close()

    def insert_jurisdictions_batch(self, jurisdictions: List[Dict[str, Any]]) -> int:
        """Insert a batch of jurisdictions into the database"""
        if not jurisdictions:
            return 0

        cursor = self.db_conn.cursor()

        try:
            query = """
                INSERT INTO openstates.jurisdictions (
                    jurisdiction_id, name, classification, url, feature_flags,
                    divisions, links, created_at, updated_at
                ) VALUES %s
                ON CONFLICT (jurisdiction_id) DO UPDATE SET
                    name = EXCLUDED.name,
                    classification = EXCLUDED.classification,
                    url = EXCLUDED.url,
                    feature_flags = EXCLUDED.feature_flags,
                    divisions = EXCLUDED.divisions,
                    links = EXCLUDED.links,
                    updated_at = EXCLUDED.updated_at
            """

            values = [
                (
                    j['jurisdiction_id'], j['name'], j['classification'],
                    j['url'], Json(j['feature_flags']),
                    Json(j['divisions']), Json(j['links']),
                    j['created_at'], j['updated_at']
                )
                for j in jurisdictions
            ]

            execute_values(cursor, query, values)
            self.db_conn.commit()
            return len(jurisdictions)

        except Exception as e:
            self.db_conn.rollback()
            self.logger.error(f"Error inserting jurisdictions batch: {e}")
            raise
        finally:
            cursor.close()

    def ingest_jurisdiction_details(self) -> Dict[str, Any]:
        """Enrich jurisdictions with detailed information"""
        self.logger.info("Ingesting jurisdiction details")

        # Get all jurisdiction IDs
        jurisdiction_ids = self.get_jurisdiction_ids()

        if not jurisdiction_ids:
            self.logger.info("No jurisdictions found for details enrichment")
            return {'records_processed': 0, 'message': 'No jurisdictions found'}

        total_processed = 0
        total_skipped = 0

        # Process jurisdictions in batches
        for i in range(0, len(jurisdiction_ids), self.batch_size):
            batch_ids = jurisdiction_ids[i:i + self.batch_size]

            for jurisdiction_id in batch_ids:
                # Rate limiting
                self.rate_manager.wait_if_needed()

                try:
                    # Fetch jurisdiction details
                    jurisdiction_details = self.fetch_jurisdiction_details(jurisdiction_id)

                    if jurisdiction_details:
                        # Validate and insert
                        validated_jurisdiction = self.validator.validate_jurisdiction_data(jurisdiction_details)
                        if validated_jurisdiction:
                            self.insert_jurisdiction_details(validated_jurisdiction.dict())
                            total_processed += 1
                            self.rate_manager.handle_success()
                        else:
                            total_skipped += 1
                    else:
                        total_skipped += 1

                except Exception as e:
                    self.logger.error(f"Error processing jurisdiction details for {jurisdiction_id}: {e}")
                    total_skipped += 1

            # Update progress
            self.progress_monitor.update_progress('jurisdiction_details', 'all', total_processed, len(jurisdiction_ids))

        self.logger.info(f"🎉 Jurisdiction details completed: {total_processed} processed, {total_skipped} skipped")

        return {
            'records_processed': total_processed,
            'records_skipped': total_skipped
        }

    def fetch_jurisdiction_details(self, jurisdiction_id: str) -> Optional[Dict[str, Any]]:
        """Fetch detailed information for a specific jurisdiction"""
        url = f"{self.base_url}/jurisdictions/{jurisdiction_id}"
        params = {'apikey': self.api_key}

        try:
            response = requests.get(url, params=params, timeout=30)

            if response.status_code == 429:
                self.rate_manager.handle_rate_limit_error()
                return None

            response.raise_for_status()
            return response.json()

        except Exception as e:
            self.logger.error(f"Error fetching jurisdiction details for {jurisdiction_id}: {e}")
            return None

    def insert_jurisdiction_details(self, jurisdiction_data: Dict[str, Any]):
        """Insert enriched jurisdiction details"""
        cursor = self.db_conn.cursor()

        try:
            query = """
                UPDATE openstates.jurisdictions SET
                    name = %s,
                    classification = %s,
                    url = %s,
                    feature_flags = %s,
                    divisions = %s,
                    links = %s,
                    updated_at = %s
                WHERE jurisdiction_id = %s
            """

            cursor.execute(query, (
                jurisdiction_data.get('name'),
                jurisdiction_data.get('classification'),
                jurisdiction_data.get('url'),
                Json(jurisdiction_data.get('feature_flags', {})),
                Json(jurisdiction_data.get('divisions', [])),
                Json(jurisdiction_data.get('links', [])),
                datetime.now(),
                jurisdiction_data['jurisdiction_id']
            ))

            self.db_conn.commit()

        except Exception as e:
            self.db_conn.rollback()
            self.logger.error(f"Error inserting jurisdiction details: {e}")
            raise
        finally:
            cursor.close()

    def ingest_jurisdiction_divisions(self) -> Dict[str, Any]:
        """Ingest jurisdiction divisions"""
        self.logger.info("Ingesting jurisdiction divisions")

        # Get all jurisdiction IDs
        jurisdiction_ids = self.get_jurisdiction_ids()

        if not jurisdiction_ids:
            self.logger.info("No jurisdictions found for divisions ingestion")
            return {'records_processed': 0, 'message': 'No jurisdictions found'}

        total_processed = 0
        total_skipped = 0

        for jurisdiction_id in jurisdiction_ids:
            # Rate limiting
            self.rate_manager.wait_if_needed()

            try:
                # Fetch jurisdiction divisions
                divisions_data = self.fetch_jurisdiction_divisions(jurisdiction_id)

                if divisions_data:
                    # Process divisions
                    for division_data in divisions_data:
                        # Validate
                        validated_division = self.validator.validate_jurisdiction_division_data(division_data)
                        if validated_division:
                            self.insert_jurisdiction_division(validated_division.dict())
                            total_processed += 1
                        else:
                            total_skipped += 1

                    self.rate_manager.handle_success()
                else:
                    total_skipped += 1

            except Exception as e:
                self.logger.error(f"Error processing divisions for jurisdiction {jurisdiction_id}: {e}")
                total_skipped += 1

        self.logger.info(f"🎉 Jurisdiction divisions completed: {total_processed} processed, {total_skipped} skipped")

        return {
            'records_processed': total_processed,
            'records_skipped': total_skipped
        }

    def fetch_jurisdiction_divisions(self, jurisdiction_id: str) -> Optional[List[Dict[str, Any]]]:
        """Fetch divisions for a specific jurisdiction"""
        url = f"{self.base_url}/jurisdictions/{jurisdiction_id}"
        params = {'apikey': self.api_key, 'include': 'divisions'}

        try:
            response = requests.get(url, params=params, timeout=30)

            if response.status_code == 429:
                self.rate_manager.handle_rate_limit_error()
                return None

            response.raise_for_status()
            data = response.json()
            return data.get('divisions', [])

        except Exception as e:
            self.logger.error(f"Error fetching jurisdiction divisions for {jurisdiction_id}: {e}")
            return None

    def insert_jurisdiction_division(self, division_data: Dict[str, Any]):
        """Insert jurisdiction division into database"""
        cursor = self.db_conn.cursor()

        try:
            query = """
                INSERT INTO openstates.jurisdiction_divisions (
                    division_id, name, country, classification, parent_id,
                    geometry, created_at
                ) VALUES %s
                ON CONFLICT (division_id) DO UPDATE SET
                    name = EXCLUDED.name,
                    country = EXCLUDED.country,
                    classification = EXCLUDED.classification,
                    parent_id = EXCLUDED.parent_id,
                    geometry = EXCLUDED.geometry
            """

            values = [(
                division_data['division_id'], division_data['name'],
                division_data['country'], division_data['classification'],
                division_data['parent_id'], Json(division_data['geometry']),
                division_data['created_at']
            )]

            execute_values(cursor, query, values)
            self.db_conn.commit()

        except Exception as e:
            self.db_conn.rollback()
            self.logger.error(f"Error inserting jurisdiction division: {e}")
            raise
        finally:
            cursor.close()

    def ingest_jurisdiction_links(self) -> Dict[str, Any]:
        """Ingest jurisdiction links"""
        self.logger.info("Ingesting jurisdiction links")

        # Get all jurisdiction IDs
        jurisdiction_ids = self.get_jurisdiction_ids()

        if not jurisdiction_ids:
            self.logger.info("No jurisdictions found for links ingestion")
            return {'records_processed': 0, 'message': 'No jurisdictions found'}

        total_processed = 0
        total_skipped = 0

        for jurisdiction_id in jurisdiction_ids:
            # Rate limiting
            self.rate_manager.wait_if_needed()

            try:
                # Fetch jurisdiction links
                links_data = self.fetch_jurisdiction_links(jurisdiction_id)

                if links_data:
                    # Process links
                    for link_data in links_data:
                        link_data['jurisdiction_id'] = jurisdiction_id

                        # Validate
                        validated_link = self.validator.validate_jurisdiction_link_data(link_data)
                        if validated_link:
                            self.insert_jurisdiction_link(validated_link.dict())
                            total_processed += 1
                        else:
                            total_skipped += 1

                    self.rate_manager.handle_success()
                else:
                    total_skipped += 1

            except Exception as e:
                self.logger.error(f"Error processing links for jurisdiction {jurisdiction_id}: {e}")
                total_skipped += 1

        self.logger.info(f"🎉 Jurisdiction links completed: {total_processed} processed, {total_skipped} skipped")

        return {
            'records_processed': total_processed,
            'records_skipped': total_skipped
        }

    def fetch_jurisdiction_links(self, jurisdiction_id: str) -> Optional[List[Dict[str, Any]]]:
        """Fetch links for a specific jurisdiction"""
        url = f"{self.base_url}/jurisdictions/{jurisdiction_id}"
        params = {'apikey': self.api_key, 'include': 'links'}

        try:
            response = requests.get(url, params=params, timeout=30)

            if response.status_code == 429:
                self.rate_manager.handle_rate_limit_error()
                return None

            response.raise_for_status()
            data = response.json()
            return data.get('links', [])

        except Exception as e:
            self.logger.error(f"Error fetching jurisdiction links for {jurisdiction_id}: {e}")
            return None

    def insert_jurisdiction_link(self, link_data: Dict[str, Any]):
        """Insert jurisdiction link into database"""
        cursor = self.db_conn.cursor()

        try:
            query = """
                INSERT INTO openstates.jurisdiction_links (
                    link_id, jurisdiction_id, url, note, created_at
                ) VALUES %s
                ON CONFLICT (link_id) DO UPDATE SET
                    jurisdiction_id = EXCLUDED.jurisdiction_id,
                    url = EXCLUDED.url,
                    note = EXCLUDED.note
            """

            values = [(
                link_data['link_id'], link_data['jurisdiction_id'],
                link_data['url'], link_data['note'], link_data['created_at']
            )]

            execute_values(cursor, query, values)
            self.db_conn.commit()

        except Exception as e:
            self.db_conn.rollback()
            self.logger.error(f"Error inserting jurisdiction link: {e}")
            raise
        finally:
            cursor.close()

    def get_jurisdiction_ids(self) -> List[str]:
        """Get all jurisdiction IDs"""
        cursor = self.db_conn.cursor()

        try:
            query = "SELECT jurisdiction_id FROM openstates.jurisdictions"
            cursor.execute(query)
            results = cursor.fetchall()
            return [row[0] for row in results]

        finally:
            cursor.close()


# ============================================================================
# MAIN EXECUTION FOR JURISDICTIONS
# ============================================================================

def main():
    """Main function for jurisdictions ingestion"""
    print("🚀 OpenStates Jurisdictions Ingestion System")
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

        # Initialize jurisdictions ingestor
        jurisdictions_ingestor = OpenStatesJurisdictionsIngestor(
            db_conn, rate_manager, pagination_manager, progress_monitor
        )

        # Ingest all jurisdictions
        print("\n📍 Ingesting all jurisdictions with complete details...")
        result = jurisdictions_ingestor.ingest_all_jurisdictions()
        print(f"✅ Jurisdictions completed: {result['total_processed']} records")

        print(f"\n🎉 All jurisdictions ingestion completed: {result['total_processed']} total records")

        # Display progress summary
        progress_summary = progress_monitor.get_summary()
        print(f"\n📊 Progress Summary:")
        print(f"   Total elapsed: {progress_summary.get('total_elapsed_seconds', 0):.1f}s")
        print(f"   Average rate: {progress_summary.get('average_rate', 0):.1f} records/s")

        db_conn.close()

    except Exception as e:
        print(f"❌ Fatal error: {e}")
        logging.error(f"Fatal error in jurisdictions ingestion: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
