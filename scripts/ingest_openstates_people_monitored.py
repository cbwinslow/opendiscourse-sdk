#!/usr/bin/env python3
"""
OpenStates People Ingestion with Real-Time Monitoring
Ingests people data from OpenStates.org API with comprehensive progress monitoring
"""

import os
import sys
import requests
import time
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
import psycopg2
from psycopg2.extras import execute_values, DictCursor
from dotenv import load_dotenv
import argparse
import logging

# Add monitoring path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from monitoring.progress_monitor import UniversalProgressMonitor, IngestionContext

load_dotenv()

class OpenStatesPeopleIngestor:
    """Ingests people data from OpenStates.org API with monitoring"""
    
    def __init__(self, db_connection_params: Dict[str, Any]):
        self.db_connection_params = db_connection_params
        self.api_key = os.getenv('OPENSTATES_API_KEY')
        if not self.api_key:
            raise ValueError("OPENSTATES_API_KEY environment variable is required")
        
        self.base_url = "https://v3.openstates.org"
        self.batch_size = 50
        self.request_delay = 0.5
        self.max_retries = 3
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def fetch_people_batch(self, jurisdiction: str = None, page: int = 1) -> Dict[str, Any]:
        """Fetch a batch of people from OpenStates API"""
        url = f"{self.base_url}/people"
        params = {
            'apikey': self.api_key,
            'per_page': min(self.batch_size, 50),  # OpenStates max is 50
            'page': page
        }
        
        if jurisdiction:
            params['jurisdiction'] = jurisdiction
        
        for attempt in range(self.max_retries):
            try:
                response = requests.get(url, params=params, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                
                if 'results' not in data:
                    self.logger.warning("No 'results' key in API response")
                    return {'results': [], 'pagination': {}}
                
                return data
                
            except requests.exceptions.RequestException as e:
                if attempt == self.max_retries - 1:
                    raise
                wait_time = 2 ** attempt
                self.logger.warning(f"Request failed (attempt {attempt + 1}), retrying in {wait_time}s: {e}")
                time.sleep(wait_time)
    
    def normalize_person_data(self, person_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize OpenStates person data for database insertion"""
        # Handle different name formats
        name = person_data.get('name', '')
        family_name = person_data.get('family_name', '')
        given_name = person_data.get('given_name', '')
        
        # If given_name/family_name not provided, try to parse from name
        if not family_name and name:
            name_parts = name.split()
            family_name = name_parts[-1] if name_parts else ''
            given_name = ' '.join(name_parts[:-1]) if len(name_parts) > 1 else ''
        
        # Parse dates
        birth_date = self.parse_date(person_data.get('birth_date'))
        death_date = self.parse_date(person_data.get('death_date'))
        
        # Current role data (JSONB)
        current_role_data = person_data.get('current_role', {})
        if isinstance(current_role_data, dict):
            # Clean up the role data for JSONB storage
            current_role_data = {
                k: v for k, v in current_role_data.items() 
                if v is not None and v != ''
            }
        
        # Image URL
        image = person_data.get('image', '')
        
        # Gender and biography
        gender = person_data.get('gender', '')
        biography = person_data.get('biography', '')
        
        # Party and jurisdiction
        primary_party = person_data.get('primary_party', '')
        jurisdiction_id = person_data.get('jurisdiction', '')
        
        return {
            'person_id': person_data.get('id', ''),
            'name': name,
            'family_name': family_name,
            'given_name': given_name,
            'image': image,
            'gender': gender,
            'biography': biography,
            'birth_date': birth_date,
            'death_date': death_date,
            'primary_party': primary_party,
            'jurisdiction_id': jurisdiction_id,
            'current_role_data': json.dumps(current_role_data) if current_role_data else '{}',
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
    
    def parse_date(self, date_str: Optional[str]) -> Optional[str]:
        """Parse date string in various formats"""
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
            
            # If no format matches, return None
            self.logger.warning(f"Could not parse date: {date_str}")
            return None
            
        except Exception as e:
            self.logger.warning(f"Error parsing date '{date_str}': {e}")
            return None
    
    def insert_people_batch(self, people: List[Dict[str, Any]]) -> int:
        """Insert a batch of people into the database"""
        if not people:
            return 0
        
        cursor = self.db_conn.cursor()
        
        try:
            # Use UPSERT to handle duplicates by person_id
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
                    p['current_role_data'], p['created_at'], p['updated_at']
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
    
    def ingest_people(self, jurisdiction: str = None, monitor_mode: str = 'tui') -> Dict[str, Any]:
        """Ingest people data with monitoring"""
        
        # Initialize database connection
        self.db_conn = psycopg2.connect(**self.db_connection_params)
        
        # Initialize monitoring
        monitor = UniversalProgressMonitor(self.db_conn, display_mode=monitor_mode)
        
        # Start monitoring job
        job_id = monitor.start_job(
            job_name=f"OpenStates People {jurisdiction or 'All'}",
            data_source="openstates.org",
            table_name="openstates.people",
            record_type="people",
            total_estimated=1000,  # Estimate
            metadata={'jurisdiction': jurisdiction}
        )
        
        try:
            # Fetch and process people
            page = 1
            total_processed = 0
            total_failed = 0
            
            while True:
                # Fetch batch
                batch_data = self.fetch_people_batch(jurisdiction, page)
                people = batch_data.get('results', [])
                
                if not people:
                    break
                
                # Process batch
                batch_start_time = time.time()
                successful_in_batch = 0
                failed_in_batch = 0
                
                for person_data in people:
                    try:
                        # Normalize data
                        normalized = self.normalize_person_data(person_data)
                        
                        # Update progress for monitoring
                        monitor.update_progress(
                            job_id=job_id,
                            success=True,
                            record_id=normalized.get('person_id', 'unknown')
                        )
                        successful_in_batch += 1
                        
                    except Exception as e:
                        failed_in_batch += 1
                        monitor.update_progress(
                            job_id=job_id,
                            success=False,
                            record_id=person_data.get('id', 'unknown'),
                            error_details={'error': str(e)}
                        )
                        self.logger.error(f"Error processing person: {e}")
                
                # Insert batch
                if successful_in_batch > 0:
                    try:
                        # Filter successful people for insertion
                        successful_people = []
                        for person_data in people:
                            try:
                                normalized = self.normalize_person_data(person_data)
                                if normalized['person_id']:  # Only insert if person_id exists
                                    successful_people.append(normalized)
                            except:
                                continue
                        
                        inserted = self.insert_people_batch(successful_people)
                        total_processed += inserted
                        
                    except Exception as e:
                        # Mark all as failed if batch insert fails
                        failed_in_batch = successful_in_batch
                        self.logger.error(f"Batch insert failed: {e}")
                
                total_failed += failed_in_batch
                
                # Check if we're done
                pagination = batch_data.get('pagination', {})
                if not pagination.get('next_page') or len(people) < self.batch_size:
                    break
                
                page += 1
                time.sleep(self.request_delay)
            
            # Complete job
            monitor.complete_job(job_id)
            
            final_stats = {
                'total_processed': total_processed,
                'total_failed': total_failed,
                'success_rate': (total_processed / (total_processed + total_failed) * 100) if (total_processed + total_failed) > 0 else 0
            }
            
            return final_stats
            
        except Exception as e:
            self.logger.error(f"Ingestion failed: {e}")
            raise
        
        finally:
            if hasattr(self, 'db_conn') and self.db_conn:
                self.db_conn.close()


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Ingest OpenStates people data with monitoring")
    parser.add_argument('--jurisdiction', type=str, help='Jurisdiction code (e.g., "ca", "ny")')
    parser.add_argument('--batch-size', type=int, default=50, help='Batch size for API requests')
    parser.add_argument('--request-delay', type=float, default=0.5, help='Delay between requests (seconds)')
    parser.add_argument('--monitor-mode', choices=['tui', 'simple', 'silent'], default='tui', 
                       help='Monitoring display mode')
    parser.add_argument('--dry-run', action='store_true', help='Test without actual ingestion')
    
    args = parser.parse_args()
    
    # Database connection parameters
    db_params = {
        'database': os.getenv('DB_NAME', 'cbwinslow'),
        'user': os.getenv('DB_USER', 'cbwinslow')
    }
    
    if args.dry_run:
        print(f"DRY RUN: Would ingest OpenStates people {f'for {args.jurisdiction}' if args.jurisdiction else 'for all jurisdictions'}")
        print(f"Batch size: {args.batch_size}")
        print(f"Monitor mode: {args.monitor_mode}")
        return
    
    # Create ingestor and run ingestion
    ingestor = OpenStatesPeopleIngestor(db_params)
    ingestor.batch_size = args.batch_size
    ingestor.request_delay = args.request_delay
    
    try:
        stats = ingestor.ingest_people(args.jurisdiction, args.monitor_mode)
        print(f"\n✅ Ingestion completed!")
        print(f"   Processed: {stats['total_processed']} people")
        print(f"   Failed: {stats['total_failed']} people")
        print(f"   Success rate: {stats['success_rate']:.1f}%")
        
    except KeyboardInterrupt:
        print("\n⚠️  Ingestion interrupted by user")
    except Exception as e:
        print(f"\n❌ Ingestion failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()