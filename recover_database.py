#!/usr/bin/env python3
"""Simple database recovery script for OpenDiscourse.

This script recreates the basic database schema without requiring
complex dependencies or service restarts.
"""

import subprocess
import sys
from pathlib import Path


def run_sql_file(sql_file: Path, database: str = "opendiscourse") -> bool:
    """Run an SQL file against the database using Unix socket connection."""
    try:
        cmd = ["psql", "-d", database, "-f", str(sql_file)]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(f"✅ Successfully applied {sql_file.name}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error applying {sql_file.name}: {e}")
        print(f"STDERR: {e.stderr}")
        return False

def main():
    """Recover the database schema."""
    print("🔧 OpenDiscourse Database Recovery")
    print("=" * 40)

    # Check if database exists
    try:
        result = subprocess.run(
            ["psql", "-d", "postgres", "-c", "SELECT 1 FROM pg_database WHERE datname = 'opendiscourse'"],
            capture_output=True, text=True, check=True
        )
        print("✅ Database 'opendiscourse' exists")
    except subprocess.CalledProcessError:
        print("❌ Database 'opendiscourse' does not exist")
        return 1

    # Get migration files
    migrations_dir = Path("migrations")
    if not migrations_dir.exists():
        print("❌ Migrations directory not found")
        return 1

    migration_files = sorted(migrations_dir.glob("*.sql"))
    if not migration_files:
        print("❌ No migration files found")
        return 1

    print(f"📁 Found {len(migration_files)} migration files")

    # Apply migrations
    success_count = 0
    for migration_file in migration_files:
        if run_sql_file(migration_file):
            success_count += 1

    print(f"\n📊 Recovery Complete: {success_count}/{len(migration_files)} migrations applied")

    # Verify tables were created
    try:
        result = subprocess.run(
            ["psql", "-d", "opendiscourse", "-c", "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public'"],
            capture_output=True, text=True, check=True
        )
        table_count = result.stdout.strip().split('\n')[-1]
        print(f"📋 Tables created: {table_count}")
    except subprocess.CalledProcessError:
        print("⚠️  Could not verify table count")

    return 0 if success_count == len(migration_files) else 1

if __name__ == "__main__":
    sys.exit(main())
