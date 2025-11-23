#!/usr/bin/env python3
"""
GovInfo Members Ingestion with Real-Time Monitoring
Ingests member data from GovInfo.gov API with comprehensive progress monitoring
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

class GovInfoMembersIngestor:
    """Ingests member data from GovInfo.gov API with monitoring"""
    
    def __init__(self, db_connection_params: Dict[str, Any]):
        self.db_connection_params = db_connection_params
        self.api_key = os.getenv('GOVINFO_API_KEY')
        if not self.api_key:
            raise ValueError("GOVINFO_API_KEY environment variable is required")
        
        self.base_url = "https://api.govinfo.gov"
        self.batch_size = 50
        self.request_delay = 0.5
        self.max_retries = 3
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def fetch_members_batch(self, congress: int, offset: int = 0) -> Dict[str, Any]:
        """Fetch a batch of members from GovInfo API"""
        url = f"{self.base_url}/members"
        params = {
            'api_key': self.api_key,
            'offset': offset,
            'pageSize': min(self.batch_size, 100),  # GovInfo max is 100
            'congress': congress
        }
        
        for attempt in range(self.max_retries):
            try:
                response = requests.get(url, params=params, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                
                if 'members' not in data:
                    self.logger.warning("No 'members' key in API response")
                    return {'members': [], 'count': 0}
                
                return data
                
            except requests.exceptions.RequestException as e:
                if attempt == self.max_retries - 1:
                    raise
                wait_time = 2 ** attempt
                self.logger.warning(f"Request failed (attempt {attempt + 1}), retrying in {wait_time}s: {e}")
                time.sleep(wait_time)
    
    def normalize_member_data(self, member_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize GovInfo member data for database insertion"""
        # GovInfo API structure may vary, handle common patterns
        member_info = member_data.get('member', member_data)
        
        # Handle different name formats
        name_parts = member_info.get('name', {})
        if isinstance(name_parts, str):
            # If name is a string, parse it
            name_str = name_parts
            name_parts = {'fullName': name_str}
        
        first_name = name_parts.get('first', name_parts.get('givenName', ''))
        last_name = name_parts.get('last', name_parts.get('familyName', ''))
        middle_name = name_parts.get('middle', '')
        suffix = name_parts.get('suffix', '')
        full_name = name_parts.get('fullName', f"{first_name} {last_name}".strip())
        
        # Parse dates
        birthday = self.parse_date(member_info.get('birthDate'))
        death_date = self.parse_date(member_info.get('deathDate'))
        
        # Handle party and state
        party_code = member_info.get('party', member_info.get('partyCode', ''))
        state = member_info.get('state', member_info.get('stateCode', ''))
        district = member_info.get('district', '')
        
        # Social media handles
        twitter_handle = member_info.get('twitter', '')
        youtube_handle = member_info.get('youtube', '')
        facebook_handle = member_info.get('facebook', '')
        
        # URLs
        url = member_info.get('url', '')
        photo_url = member_info.get('photoUrl', '')
        
        # Biography
        biography_text = member_info.get('biography', member_info.get('bio', ''))
        
        return {
            'member_id': member_info.get('memberId', member_info.get('id', '')),
            'bioguide_id': member_info.get('bioguideId', ''),
            'first_name': first_name,
            'middle_name': middle_name,
            'last_name': last_name,
            'suffix': suffix,
            'full_name': full_name,
            'preferred_name': name_parts.get('preferredName', ''),
            'birthday': birthday,
            'gender': member_info.get('gender', ''),
            'party_code': party_code,
            'state': state,
            'district': str(district) if district else '',
            'url': url,
            'twitter_handle': twitter_handle,
            'youtube_handle': youtube_handle,
            'facebook_handle': facebook_handle,
            'biography_text': biography_text,
            'photo_url': photo_url,
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
    
    def parse_date(self, date_str: Optional[str]) -> Optional[str]:
        """Parse date string in various formats"""
        if not date_str:
            return None
        
        try:
            # Try common date formats
            for fmt in ['%Y-%m-%d', '%Y/%m/%d', '%m/%d/%Y']:
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
    
    def insert_members_batch(self, members: List[Dict[str, Any]]) -> int:
        """Insert a batch of members into the database"""
        if not members:
            return 0
        
        cursor = self.db_conn.cursor()
        
        try:
            # Use UPSERT to handle duplicates by bioguide_id
            query = """
                INSERT INTO govinfo.members (
                    member_id, bioguide_id, first_name, middle_name, last_name, suffix,
                    full_name, preferred_name, birthday, gender, party_code, state,
                    district, url, twitter_handle, youtube_handle, facebook_handle,
                    biography_text, photo_url, created_at, updated_at
                ) VALUES %s
                ON CONFLICT (bioguide_id) DO UPDATE SET
                    member_id = EXCLUDED.member_id,
                    first_name = EXCLUDED.first_name,
                    middle_name = EXCLUDED.middle_name,
                    last_name = EXCLUDED.last_name,
                    suffix = EXCLUDED.suffix,
                    full_name = EXCLUDED.full_name,
                    preferred_name = EXCLUDED.preferred_name,
                    birthday = EXCLUDED.birthday,
                    gender = EXCLUDED.gender,
                    party_code = EXCLUDED.party_code,
                    state = EXCLUDED.state,
                    district = EXCLUDED.district,
                    url = EXCLUDED.url,
                    twitter_handle = EXCLUDED.twitter_handle,
                    youtube_handle = EXCLUDED.youtube_handle,
                    facebook_handle = EXCLUDED.facebook_handle,
                    biography_text = EXCLUDED.biography_text,
                    photo_url = EXCLUDED.photo_url,
                    updated_at = EXCLUDED.updated_at
            """
            
            values = [
                (
                    m['member_id'], m['bioguide_id'], m['first_name'], m['middle_name'],
                    m['last_name'], m['suffix'], m['full_name'], m['preferred_name'],
                    m['birthday'], m['gender'], m['party_code'], m['state'], m['district'],
                    m['url'], m['twitter_handle'], m['youtube_handle'], m['facebook_handle'],
                    m['biography_text'], m['photo_url'], m['created_at'], m['updated_at']
                )
                for m in members
            ]
            
            execute_values(cursor, query, values)
            self.db_conn.commit()
            
            return len(members)
            
        except Exception as e:
            self.db_conn.rollback()
            self.logger.error(f"Error inserting members batch: {e}")
            raise
    
    def ingest_congress_members(self, congress: int, monitor_mode: str = 'tui') -> Dict[str, Any]:
        """Ingest members for a specific congress with monitoring"""
        
        # Initialize database connection
        self.db_conn = psycopg2.connect(**self.db_connection_params)
        
        # Initialize monitoring
        monitor = UniversalProgressMonitor(self.db_conn, display_mode=monitor_mode)
        
        # Start monitoring job
        job_id = monitor.start_job(
            job_name=f"GovInfo Members Congress {congress}",
            data_source="govinfo.gov",
            table_name="govinfo.members",
            record_type="members",
            total_estimated=1000,  # Estimate
            metadata={'congress': congress}
        )
        
        try:
            # Fetch and process members
            offset = 0
            total_processed = 0
            total_failed = 0
            
            while True:
                # Fetch batch
                batch_data = self.fetch_members_batch(congress, offset)
                members = batch_data.get('members', [])
                
                if not members:
                    break
                
                # Process batch
                batch_start_time = time.time()
                successful_in_batch = 0
                failed_in_batch = 0
                
                for member_data in members:
                    try:
                        # Normalize data
                        normalized = self.normalize_member_data(member_data)
                        
                        # Update progress for monitoring
                        monitor.update_progress(
                            job_id=job_id,
                            success=True,
                            record_id=normalized.get('bioguide_id', 'unknown')
                        )
                        successful_in_batch += 1
                        
                    except Exception as e:
                        failed_in_batch += 1
                        monitor.update_progress(
                            job_id=job_id,
                            success=False,
                            record_id=member_data.get('memberId', 'unknown'),
                            error_details={'error': str(e)}
                        )
                        self.logger.error(f"Error processing member: {e}")
                
                # Insert batch
                if successful_in_batch > 0:
                    try:
                        # Filter successful members for insertion
                        successful_members = []
                        for member_data in members:
                            try:
                                normalized = self.normalize_member_data(member_data)
                                if normalized['bioguide_id']:  # Only insert if bioguide_id exists
                                    successful_members.append(normalized)
                            except:
                                continue
                        
                        inserted = self.insert_members_batch(successful_members)
                        total_processed += inserted
                        
                    except Exception as e:
                        # Mark all as failed if batch insert fails
                        failed_in_batch = successful_in_batch
                        self.logger.error(f"Batch insert failed: {e}")
                
                total_failed += failed_in_batch
                
                # Check if we're done
                if len(members) < self.batch_size or offset + len(members) >= batch_data.get('count', float('inf')):
                    break
                
                offset += len(members)
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
    parser = argparse.ArgumentParser(description="Ingest GovInfo members data with monitoring")
    parser.add_argument('--congress', type=int, default=118, help='Congress number (default: 118)')
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
        print(f"DRY RUN: Would ingest GovInfo members for Congress {args.congress}")
        print(f"Batch size: {args.batch_size}")
        print(f"Monitor mode: {args.monitor_mode}")
        return
    
    # Create ingestor and run ingestion
    ingestor = GovInfoMembersIngestor(db_params)
    ingestor.batch_size = args.batch_size
    ingestor.request_delay = args.request_delay
    
    try:
        stats = ingestor.ingest_congress_members(args.congress, args.monitor_mode)
        print(f"\n✅ Ingestion completed!")
        print(f"   Processed: {stats['total_processed']} members")
        print(f"   Failed: {stats['total_failed']} members")
        print(f"   Success rate: {stats['success_rate']:.1f}%")
        
    except KeyboardInterrupt:
        print("\n⚠️  Ingestion interrupted by user")
    except Exception as e:
        print(f"\n❌ Ingestion failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()