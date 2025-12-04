#!/usr/bin/env python3
"""
GovInfo CLI Tool
Focused CLI for ingesting GovInfo collections, packages, granules, and committees.
"""

import argparse
import sys
import os
import time
import json
import psycopg2
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import requests
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))
# Add script directory to path to allow importing rate_limiter
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from rate_limiter import rate_limiter
try:
    from utils import resource_manager
except ImportError:
    sys.path.append(os.path.join(os.path.dirname(__file__), '../utils'))
    import resource_manager

class GovInfoCLI:
    def __init__(self, api_key: str, db_config: Dict, batch_size: int = 50, dry_run: bool = False):
        self.api_key = api_key
        self.db_config = db_config
        self.batch_size = batch_size
        self.dry_run = dry_run
        self.base_url = "https://api.govinfo.gov"
        self.session = requests.Session()
        self.conn = None

class GovInfoCLI:
    """
    GovInfo CLI Tool

    A comprehensive command-line interface for ingesting GovInfo (Government Publishing Office)
    data into a PostgreSQL database. This class provides ETL functionality for various
    types of government documents and publications including:

    - Collections (document collections)
    - Packages (document packages)
    - Granules (individual documents within packages)
    - Committee information

    The class handles API rate limiting, error handling, batch processing, and
    database schema management automatically. GovInfo provides official government
    documents including bills, laws, regulations, hearings, and more.

    Attributes:
        api_key (str): GovInfo API key for authentication
        db_config (dict): PostgreSQL database connection configuration
        batch_size (int): Number of records to process per batch (default: 50)
        dry_run (bool): If True, simulates operations without making database changes
        base_url (str): Base URL for GovInfo API
        session (requests.Session): Configured HTTP session with authentication
        conn (psycopg2.connection): Database connection object

    Example:
        List available collections:
        >>> cli = GovInfoCLI(api_key="your_key", db_config=config)
        >>> cli.ingest_collections()
    """
    def transform_collection(self, collection_data: dict) -> tuple:
        """Transform GovInfo collection data into DB tuple.
        Returns: (code, name, package_count, granule_count, created_at)
        """
        return (
            collection_data.get('collectionCode'),
            collection_data.get('collectionName'),
            collection_data.get('packageCount'),
            collection_data.get('granuleCount'),
            datetime.now()
        )

    def transform_package(self, package_data: dict) -> tuple:
        """Transform GovInfo package data into DB tuple.
        Returns: (package_id, collection_code, title, congress_number, chamber_code,
                  bill_type, bill_number, doc_class, granule_count, date_issued,
                  last_modified, created_at)
        """
        return (
            package_data.get('packageId'),
            package_data.get('collectionCode'),
            package_data.get('title'),
            package_data.get('congressNumber'),
            package_data.get('chamberCode'),
            package_data.get('billType'),
            package_data.get('billNumber'),
            package_data.get('docClass'),
            package_data.get('granuleCount'),
            package_data.get('dateIssued'),
            package_data.get('lastModified'),
            datetime.now()
        )

    def transform_granule(self, granule_data: dict) -> tuple:
        """Transform GovInfo granule data into DB tuple.
        Returns: (granule_id, package_id, granule_class, title, sequence_number,
                  granule_date, last_modified, created_at)
        """
        return (
            granule_data.get('granuleId'),
            granule_data.get('packageId'),
            granule_data.get('granuleClass'),
            granule_data.get('title'),
            granule_data.get('sequenceNumber'),
            granule_data.get('granuleDate'),
            granule_data.get('lastModified'),
            datetime.now()
        )

    def transform_committee(self, committee_data: dict) -> tuple:
        """Transform GovInfo committee data into DB tuple.
        Returns: (committee_code, committee_name, chamber_code, parent_committee_code,
                  type, established_date, terminated_date, url, jurisdiction, created_at)
        """
        return (
            committee_data.get('committeeCode'),
            committee_data.get('committeeName'),
            committee_data.get('chamberCode'),
            committee_data.get('parentCommitteeCode'),
            committee_data.get('type'),
            committee_data.get('establishedDate'),
            committee_data.get('terminatedDate'),
            committee_data.get('url'),
            committee_data.get('jurisdiction'),
            datetime.now()
        )

    def connect_db(self):
        """Establish database connection"""
        try:
            self.conn = psycopg2.connect(**self.db_config)
            return True
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return False

    def close_db(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()

    def get(self, endpoint: str, params: dict = None) -> Optional[Dict]:
        """Make GET request with error handling and exponential backoff"""
        url = f"{self.base_url}{endpoint}"
        if params is None:
            params = {}
        params['api_key'] = self.api_key

        max_retries = 3
        base_delay = 2.0

        for attempt in range(max_retries + 1):
            try:
                # Rate limiting
                rate_limiter.wait("govinfo.gov")
                response = self.session.get(url, params=params)

                if response.status_code == 429:
                    if attempt < max_retries:
                        delay = base_delay * (2 ** attempt)
                        print(f"⏳ Rate limited (429), retry {attempt + 1}/{max_retries} after {delay}s...")
                        time.sleep(delay)
                        continue
                    else:
                        print(f"❌ Max retries exceeded for rate limit")
                        return None

                response.raise_for_status()
                return response.json()

            except requests.exceptions.RequestException as e:
                if attempt < max_retries:
                    delay = base_delay * (2 ** attempt)
                    print(f"⚠️ API request failed (attempt {attempt + 1}/{max_retries}): {e}")
                    print(f"⏳ Retrying in {delay}s...")
                    time.sleep(delay)
                else:
                    print(f"❌ API request failed after {max_retries} retries: {e}")
                    return None

        return None

    def ingest_collections(self):
        """Ingest available collections"""
        print("🚀 Starting GovInfo collections ingestion")

        if not self.connect_db():
            return

        data = self.get("/collections")
        if not data or not data.get('collections'):
            print("❌ No collections found")
            return

        collections = []
        for c in data['collections']:
            collections.append((
                c.get('collectionCode'),
                c.get('collectionName'),
                c.get('packageCount'),
                c.get('granuleCount'),
                datetime.now()
            ))

        if collections:
            query = """
            INSERT INTO govinfo.collections
            (code, name, package_count, granule_count, last_updated)
            VALUES %s
            ON CONFLICT (code) DO UPDATE SET
                name = EXCLUDED.name,
                package_count = EXCLUDED.package_count,
                granule_count = EXCLUDED.granule_count,
                last_updated = now()
            """

            if self.dry_run:
                print(f"🔍 DRY RUN: Would insert {len(collections)} collections")
            else:
                cursor = self.conn.cursor()
                try:
                    from psycopg2.extras import execute_values
                    execute_values(cursor, query, collections)
                    self.conn.commit()
                    print(f"✅ Processed {len(collections)} collections")
                except Exception as e:
                    print(f"❌ Batch insert failed: {e}")
                    self.conn.rollback()
                finally:
                    cursor.close()

        self.close_db()

    def ingest_packages(self, collection: str, start_date: str, end_date: str = None):
        """Ingest packages for a collection"""
        print(f"🚀 Starting GovInfo packages ingestion for {collection}")

        if not self.connect_db():
            return

        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')

        start_dt = f"{start_date}T00:00:00Z"
        end_dt = f"{end_date}T23:59:59Z"

        offset = 0
        total_processed = 0

        while True:
            endpoint = f"/collections/{collection}/{start_dt}/{end_dt}"
            params = {'pageSize': self.batch_size, 'offset': offset}

            data = self.get(endpoint, params)

            if not data or not data.get('packages'):
                break

            packages = []
            for pkg in data['packages']:
                packages.append((
                    pkg.get('packageId'),
                    pkg.get('title'),
                    pkg.get('collectionCode'),
                    pkg.get('docClass'),
                    pkg.get('dateIssued'),
                    pkg.get('lastModified'),
                    pkg.get('packageLink'),
                    datetime.now()
                ))

            if packages:
                query = """
                INSERT INTO govinfo.packages
                (package_id, title, collection_code, doc_class, date_issued, last_modified, package_link, created_at)
                VALUES %s
                ON CONFLICT (package_id) DO UPDATE SET
                    title = EXCLUDED.title,
                    last_modified = EXCLUDED.last_modified,
                    package_link = EXCLUDED.package_link,
                    updated_at = now()
                """

                if self.dry_run:
                    print(f"🔍 DRY RUN: Would insert {len(packages)} packages")
                    total_processed += len(packages)
                else:
                    cursor = self.conn.cursor()
                    try:
                        from psycopg2.extras import execute_values
                        execute_values(cursor, query, packages)
                        self.conn.commit()
                        total_processed += len(packages)
                        print(f"✅ Processed {total_processed} packages")
                    except Exception as e:
                        print(f"❌ Batch insert failed: {e}")
                        self.conn.rollback()
                        break
                    finally:
                        cursor.close()

            if not data.get('nextPage'):
                break

            offset += self.batch_size
            time.sleep(0.2)

        self.close_db()
        print(f"🎉 Completed: {total_processed} GovInfo packages")

    def ingest_granules(self, package_id: str):
        """Ingest granules for a package"""
        print(f"🚀 Starting GovInfo granules ingestion for package {package_id}")

        if not self.connect_db():
            return

        # Ensure table exists
        create_table_query = """
        CREATE TABLE IF NOT EXISTS govinfo.granules (
            id TEXT PRIMARY KEY,
            title TEXT,
            package_id TEXT,
            granule_link TEXT,
            granule_class TEXT,
            created_at TIMESTAMP,
            updated_at TIMESTAMP
        );
        """
        if not self.dry_run:
            cursor = self.conn.cursor()
            cursor.execute(create_table_query)
            self.conn.commit()
            cursor.close()

        offset = 0
        total_processed = 0

        while True:
            endpoint = f"/packages/{package_id}/granules"
            params = {'pageSize': self.batch_size, 'offset': offset}

            data = self.get(endpoint, params)

            if not data or not data.get('granules'):
                break

            granules = []
            for gran in data['granules']:
                granules.append((
                    gran.get('granuleId'),
                    gran.get('title'),
                    package_id,
                    gran.get('granuleLink'),
                    gran.get('granuleClass'),
                    datetime.now()
                ))

            if granules:
                query = """
                INSERT INTO govinfo.granules
                (id, title, package_id, granule_link, granule_class, created_at)
                VALUES %s
                ON CONFLICT (id) DO UPDATE SET
                    title = EXCLUDED.title,
                    package_id = EXCLUDED.package_id,
                    granule_link = EXCLUDED.granule_link,
                    granule_class = EXCLUDED.granule_class,
                    updated_at = now()
                """

                if self.dry_run:
                    print(f"🔍 DRY RUN: Would insert {len(granules)} granules")
                    total_processed += len(granules)
                else:
                    cursor = self.conn.cursor()
                    try:
                        from psycopg2.extras import execute_values
                        execute_values(cursor, query, granules)
                        self.conn.commit()
                        total_processed += len(granules)
                        print(f"✅ Processed {total_processed} granules")
                    except Exception as e:
                        print(f"❌ Batch insert failed: {e}")
                        self.conn.rollback()
                        break
                    finally:
                        cursor.close()

            if not data.get('nextPage'):
                break

            offset += self.batch_size
            time.sleep(0.2)

        self.close_db()
        print(f"🎉 Completed: {total_processed} GovInfo granules")

    def ingest_committees(self, start_date: str, end_date: str = None):
        """Ingest committee packages (shortcut for ingest-packages with collection=COMMITTEE)"""
        print("🚀 Starting GovInfo committees ingestion")
        self.ingest_packages('COMMITTEE', start_date, end_date)

    def status(self):
        """Show GovInfo data status"""
        if not self.connect_db():
            return

        cursor = self.conn.cursor()
        try:
            tables = [
                ("govinfo.collections", "Collections"),
                ("govinfo.packages", "Packages"),
                ("govinfo.granules", "Granules")
            ]

            print("📊 GovInfo Data Status:")
            for table, label in tables:
                try:
                    cursor.execute(f"SELECT count(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    print(f"  {label:<15}: {count}")
                except psycopg2.errors.UndefinedTable:
                    print(f"  {label:<15}: Not initialized")
                    self.conn.rollback()

        except Exception as e:
            print(f"❌ Status check failed: {e}")
        finally:
            cursor.close()
            self.close_db()

def main():
    parser = argparse.ArgumentParser(description="GovInfo Ingestion CLI")
    parser.add_argument('--dry-run', action='store_true', help='Run without making changes')
    parser.add_argument('--batch-size', type=int, default=50, help='Batch size')

    subparsers = parser.add_subparsers(dest='command', required=True)

    # Ingest Collections
    subparsers.add_parser('ingest-collections', help='Ingest collections')

    # Ingest Packages
    pkg_parser = subparsers.add_parser('ingest-packages', help='Ingest packages')
    pkg_parser.add_argument('collection', help='Collection code (e.g., BILLS, CREC)')
    pkg_parser.add_argument('start_date', help='Start date (YYYY-MM-DD)')
    pkg_parser.add_argument('--end-date', help='End date (YYYY-MM-DD)')

    # Ingest Granules
    gran_parser = subparsers.add_parser('ingest-granules', help='Ingest granules')
    gran_parser.add_argument('package_id', help='Package ID')

    # Ingest Committees
    comm_parser = subparsers.add_parser('ingest-committees', help='Ingest committee packages')
    comm_parser.add_argument('start_date', help='Start date (YYYY-MM-DD)')
    comm_parser.add_argument('--end-date', help='End date (YYYY-MM-DD)')

    # Ingest Collection (bulk packages)
    coll_parser = subparsers.add_parser('ingest-collection', help='Ingest all packages from a collection')
    coll_parser.add_argument('collection', help='Collection code (e.g., BILLS, FR)')
    coll_parser.add_argument('--start-date', help='Start date (YYYY-MM-DD)', default='2005-01-01')
    coll_parser.add_argument('--end-date', help='End date (YYYY-MM-DD)')

    # Status
    subparsers.add_parser('status', help='Show status')

    args = parser.parse_args()

    api_key = resource_manager.GOVINFO_API_KEY
    if not api_key:
        print("❌ GOVINFO_API_KEY environment variable required")
        return

    db_config = {
        'database': 'opendiscourse',
        'user': 'cbwinslow',
        'host': '/var/run/postgresql'
    }

    cli = GovInfoCLI(api_key, db_config, args.batch_size, args.dry_run)

    if args.command == 'ingest-collections':
        cli.ingest_collections()
    elif args.command == 'ingest-collection':
        cli.ingest_packages(args.collection, args.start_date, args.end_date)
    elif args.command == 'ingest-packages':
        cli.ingest_packages(args.collection, args.start_date, args.end_date)
    elif args.command == 'ingest-granules':
        cli.ingest_granules(args.package_id)
    elif args.command == 'ingest-committees':
        cli.ingest_committees(args.start_date, args.end_date)
    elif args.command == 'status':
        cli.status()
        cli.status()

if __name__ == "__main__":
    main()
