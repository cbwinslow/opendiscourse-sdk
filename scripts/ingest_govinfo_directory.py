#!/usr/bin/env python3
"""
GovInfo Congressional Directory Ingestion
Ingests member data from GovInfo.gov Congressional Directory packages
"""

import os
import sys
import requests
import time
import json
import re
from datetime import datetime
from typing import Dict, List, Any, Optional
import psycopg2
from psycopg2.extras import execute_values, DictCursor
from dotenv import load_dotenv
import argparse
import logging

load_dotenv()

class GovInfoDirectoryIngestor:
    """Ingests member data from GovInfo.gov Congressional Directory"""
    
    def __init__(self, db_connection_params: Dict[str, Any]):
        self.db_connection_params = db_connection_params
        self.api_key = os.getenv('GOVINFO_API_KEY')
        if not self.api_key:
            raise ValueError("GOVINFO_API_KEY environment variable is required")
        
        self.base_url = "https://api.govinfo.gov"
        self.request_delay = 1.0
        self.max_retries = 3
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def fetch_congressional_directories(self, congress: int) -> List[Dict[str, Any]]:
        """Fetch Congressional Directory packages for a congress"""
        # Approximate start date for the requested congress (Congress 118 began 2023-01-03).
        # Adjust as needed if you have an authoritative mapping elsewhere.
        congress_start_year = 1789 + (congress - 1) * 2
        start_date = f"{congress_start_year}-01-01T00:00:00Z"
        
        url = f"{self.base_url}/collections/CDIR/{start_date}"
        params = {
            'api_key': self.api_key,
            'congress': congress,
            'offset': 0,
            'pageSize': 100
        }
        
        for attempt in range(self.max_retries):
            try:
                response = requests.get(url, params=params, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                packages = data.get('packages', [])
                
                # Filter for the most recent directory
                if packages:
                    return packages
                
                return []
                
            except requests.exceptions.RequestException as e:
                if attempt == self.max_retries - 1:
                    raise
                wait_time = 2 ** attempt
                self.logger.warning(f"Request failed (attempt {attempt + 1}), retrying in {wait_time}s: {e}")
                time.sleep(wait_time)
    
    def fetch_directory_content(self, package_id: str) -> str:
        """Fetch the text content of a Congressional Directory"""
        url = f"{self.base_url}/packages/{package_id}/txt"
        params = {'api_key': self.api_key}
        
        for attempt in range(self.max_retries):
            try:
                response = requests.get(url, params=params, timeout=60)
                response.raise_for_status()
                return response.text
                
            except requests.exceptions.RequestException as e:
                if attempt == self.max_retries - 1:
                    raise
                wait_time = 2 ** attempt
                self.logger.warning(f"Request failed (attempt {attempt + 1}), retrying in {wait_time}s: {e}")
                time.sleep(wait_time)
    
    def parse_member_from_text(self, text: str) -> List[Dict[str, Any]]:
        """Parse member information from Congressional Directory text"""
        members = []
        
        # This is a simplified parser - in production, you'd want more sophisticated parsing
        # Look for member patterns like "Senator John Smith (R-CA)"
        
        # Senate patterns
        senate_pattern = r'(?:Senator|Sen\.)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+\(([A-Z]+)-([A-Z]{2})\)'
        senate_matches = re.findall(senate_pattern, text)
        
        for match in senate_matches:
            name, party, state = match
            name_parts = name.split()
            
            members.append({
                'member_id': f"sen_{state.lower()}_{name.lower().replace(' ', '_')}",
                'bioguide_id': None,  # Would need cross-reference
                'first_name': name_parts[0] if len(name_parts) > 0 else '',
                'middle_name': ' '.join(name_parts[1:-1]) if len(name_parts) > 2 else '',
                'last_name': name_parts[-1] if len(name_parts) > 0 else '',
                'suffix': '',
                'full_name': name,
                'preferred_name': '',
                'birthday': None,
                'gender': '',
                'party_code': party,
                'state': state,
                'district': '',
                'url': '',
                'twitter_handle': '',
                'youtube_handle': '',
                'facebook_handle': '',
                'biography_text': '',
                'photo_url': '',
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            })
        
        # House patterns  
        house_pattern = r'(?:Representative|Rep\.)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+\(([A-Z]+)-([A-Z]{2})(?:-(\d+))?\)'
        house_matches = re.findall(house_pattern, text)
        
        for match in house_matches:
            name, party, state, district = match
            name_parts = name.split()
            
            members.append({
                'member_id': f"rep_{state.lower()}_{district or 'at-large'}_{name.lower().replace(' ', '_')}",
                'bioguide_id': None,  # Would need cross-reference
                'first_name': name_parts[0] if len(name_parts) > 0 else '',
                'middle_name': ' '.join(name_parts[1:-1]) if len(name_parts) > 2 else '',
                'last_name': name_parts[-1] if len(name_parts) > 0 else '',
                'suffix': '',
                'full_name': name,
                'preferred_name': '',
                'birthday': None,
                'gender': '',
                'party_code': party,
                'state': state,
                'district': district or '',
                'url': '',
                'twitter_handle': '',
                'youtube_handle': '',
                'facebook_handle': '',
                'biography_text': '',
                'photo_url': '',
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            })
        
        return members
    
    def insert_members_batch(self, members: List[Dict[str, Any]]) -> int:
        """Insert a batch of members into the database"""
        if not members:
            return 0
        
        cursor = self.db_conn.cursor()
        
        try:
            # Use UPSERT to handle duplicates by member_id
            query = """
                INSERT INTO govinfo.members (
                    member_id, bioguide_id, first_name, middle_name, last_name, suffix,
                    full_name, preferred_name, birthday, gender, party_code, state,
                    district, url, twitter_handle, youtube_handle, facebook_handle,
                    biography_text, photo_url, created_at, updated_at
                ) VALUES %s
                ON CONFLICT (member_id) DO UPDATE SET
                    bioguide_id = EXCLUDED.bioguide_id,
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
    
    def ingest_congress_directory(self, congress: int) -> Dict[str, Any]:
        """Ingest members from Congressional Directory for a congress"""
        
        # Initialize database connection
        self.db_conn = psycopg2.connect(**self.db_connection_params)
        
        print(f"🚀 Starting GovInfo Congressional Directory ingestion for Congress {congress}")
        
        try:
            # Get Congressional Directory packages
            packages = self.fetch_congressional_directories(congress)
            
            if not packages:
                print("❌ No Congressional Directory packages found")
                return {'total_processed': 0, 'total_failed': 0, 'success_rate': 0}
            
            total_processed = 0
            total_failed = 0
            
            for package in packages:
                package_id = package.get('packageId')
                title = package.get('title', '')
                
                print(f"📄 Processing directory: {title}")
                
                try:
                    # Fetch directory content
                    content = self.fetch_directory_content(package_id)
                    
                    # Parse members from text
                    members = self.parse_member_from_text(content)
                    
                    if members:
                        # Insert members
                        inserted = self.insert_members_batch(members)
                        total_processed += inserted
                        print(f"   ✅ Inserted {inserted} members")
                    else:
                        print(f"   ⚠️  No members found in directory")
                    
                    time.sleep(self.request_delay)
                    
                except Exception as e:
                    total_failed += 1
                    self.logger.error(f"Error processing directory {package_id}: {e}")
                    print(f"   ❌ Failed to process directory: {e}")
            
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
    parser = argparse.ArgumentParser(description="Ingest GovInfo Congressional Directory data")
    parser.add_argument('--congress', type=int, default=118, help='Congress number (default: 118)')
    parser.add_argument('--request-delay', type=float, default=1.0, help='Delay between requests (seconds)')
    parser.add_argument('--dry-run', action='store_true', help='Test without actual ingestion')
    
    args = parser.parse_args()
    
    # Database connection parameters
    db_params = {
        'database': os.getenv('DB_NAME', 'cbwinslow'),
        'user': os.getenv('DB_USER', 'cbwinslow')
    }
    
    if args.dry_run:
        print(f"DRY RUN: Would ingest GovInfo Congressional Directory for Congress {args.congress}")
        return
    
    # Create ingestor and run ingestion
    ingestor = GovInfoDirectoryIngestor(db_params)
    ingestor.request_delay = args.request_delay
    
    try:
        stats = ingestor.ingest_congress_directory(args.congress)
        print(f"\n🎉 Ingestion completed!")
        print(f"   ✅ Processed: {stats['total_processed']} members")
        print(f"   ❌ Failed: {stats['total_failed']} directories")
        print(f"   📊 Success rate: {stats['success_rate']:.1f}%")
        
    except KeyboardInterrupt:
        print("\n⚠️  Ingestion interrupted by user")
    except Exception as e:
        print(f"\n❌ Ingestion failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()