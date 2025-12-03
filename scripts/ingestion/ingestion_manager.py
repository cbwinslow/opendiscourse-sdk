import os
import sys
import time
import json
import hashlib
import argparse
import psycopg2
from psycopg2.extras import execute_values, RealDictCursor
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

class IngestionManager:
    def __init__(self, db_config: Dict, dry_run: bool = False):
        self.db_config = db_config
        self.dry_run = dry_run
        self.conn = None
        self.job_id = None

    def connect(self):
        """Establish database connection"""
        try:
            self.conn = psycopg2.connect(**self.db_config)
            self.conn.autocommit = False # Use transactions
            return True
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return False

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()

    def run_migrations(self, migration_files: List[str]):
        """Run SQL migration files"""
        if not self.connect():
            return

        print("🔄 Running migrations...")
        cursor = self.conn.cursor()
        try:
            for file_path in migration_files:
                print(f"  - Applying {os.path.basename(file_path)}...")
                with open(file_path, 'r') as f:
                    sql = f.read()
                    cursor.execute(sql)
            self.conn.commit()
            print("✅ All migrations applied successfully")
        except Exception as e:
            self.conn.rollback()
            print(f"❌ Migration failed: {e}")
            raise
        finally:
            cursor.close()
            self.close()

    def start_job(self, job_name: str, data_source: str, record_type: str, total_estimated: int = None) -> int:
        """Start a new ingestion job"""
        if self.dry_run:
            print(f"🔍 DRY RUN: Starting job {job_name} for {data_source}/{record_type}")
            return 0

        if not self.conn:
            self.connect()

        cursor = self.conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO ingestion.ingestion_jobs
                (job_name, data_source, record_type, total_estimated, status)
                VALUES (%s, %s, %s, %s, 'running')
                RETURNING id
            """, (job_name, data_source, record_type, total_estimated))
            self.job_id = cursor.fetchone()[0]
            self.conn.commit()
            print(f"🚀 Started ingestion job #{self.job_id}: {job_name}")
            return self.job_id
        except Exception as e:
            self.conn.rollback()
            print(f"❌ Failed to start job: {e}")
            return -1
        finally:
            cursor.close()

    def complete_job(self, status: str = 'completed', metadata: Dict = None):
        """Complete the current ingestion job"""
        if self.dry_run or not self.job_id:
            return

        cursor = self.conn.cursor()
        try:
            cursor.execute("""
                UPDATE ingestion.ingestion_jobs
                SET status = %s,
                    completed_at = CURRENT_TIMESTAMP,
                    metadata = COALESCE(metadata, '{}'::jsonb) || %s::jsonb
                WHERE id = %s
            """, (status, json.dumps(metadata or {}), self.job_id))
            self.conn.commit()
            print(f"🏁 Job #{self.job_id} finished with status: {status}")
        except Exception as e:
            self.conn.rollback()
            print(f"❌ Failed to complete job: {e}")
        finally:
            cursor.close()

    def is_record_processed(self, data_source: str, record_type: str, record_id: str, content: Dict = None) -> bool:
        """Check if record is already processed using incremental schema"""
        if self.dry_run:
            return False

        cursor = self.conn.cursor()
        try:
            # Calculate hash if content provided
            # Note: The SQL function handles hash calculation if we pass JSON,
            # but we can also rely on the function to do it.
            # Let's call the function directly.
            cursor.execute("""
                SELECT incremental.is_record_processed(%s, %s, %s, %s)
            """, (data_source, record_type, record_id, json.dumps(content) if content else None))
            result = cursor.fetchone()[0]
            # We need to commit because the function might update the fingerprint timestamp
            self.conn.commit()
            return result
        except Exception as e:
            self.conn.rollback()
            print(f"⚠️ Error checking record fingerprint: {e}")
            return False
        finally:
            cursor.close()

    def update_progress(self, processed: int, failed: int = 0, current_id: str = None):
        """Update job progress"""
        if self.dry_run or not self.job_id:
            return

        cursor = self.conn.cursor()
        try:
            cursor.execute("""
                UPDATE ingestion.ingestion_jobs
                SET processed_records = processed_records + %s,
                    failed_records = failed_records + %s,
                    current_record_id = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (processed, failed, current_id, self.job_id))
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            # Don't fail the whole run just because progress update failed
            print(f"⚠️ Failed to update progress: {e}")
        finally:
            cursor.close()

def main():
    parser = argparse.ArgumentParser(description="Ingestion Manager")
    parser.add_argument('command', choices=['migrate', 'status'], help='Command to run')
    parser.add_argument('--dry-run', action='store_true', help='Dry run mode')

    args = parser.parse_args()

    # DB Config - defaults for local socket connection
    db_config = {
        'database': os.getenv('DB_NAME', 'opendiscourse'),
        'user': os.getenv('DB_USER', 'cbwinslow'),
        'password': os.getenv('DB_PASSWORD', ''),
        'host': os.getenv('DB_HOST', ''), # Empty for local socket
        'port': os.getenv('DB_PORT', '')  # Empty for default
    }

    # Filter out empty values to let libpq use defaults
    db_config = {k: v for k, v in db_config.items() if v}

    manager = IngestionManager(db_config, args.dry_run)

    if args.command == 'migrate':
        migrations = [
            'migrations/001_congress_schema.sql',
            # 'migrations/002_govinfo_schema.sql', # Skipping as file path uncertain/not found in list
            'migrations/003_openstates_schema_optimized.sql',
            'migrations/011_ingestion_tables.sql',
            'migrations/014_incremental_ingestion_tracking.sql'
        ]
        # Adjust paths to be absolute or relative to script execution
        base_path = Path(__file__).parent.parent.parent
        abs_migrations = [str(base_path / m) for m in migrations]

        manager.run_migrations(abs_migrations)

    elif args.command == 'status':
        if manager.connect():
            cursor = manager.conn.cursor()
            cursor.execute("SELECT * FROM ingestion.ingestion_jobs ORDER BY created_at DESC LIMIT 5")
            jobs = cursor.fetchall()
            print("\nRecent Ingestion Jobs:")
            for job in jobs:
                print(job)
            manager.close()

if __name__ == "__main__":
    main()
