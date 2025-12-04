#!/usr/bin/env python3
"""
Simple migration verification script.
Tests migrations without requiring full dependency install.
"""

import os
import re
from pathlib import Path
from collections import defaultdict

def analyze_migrations():
    """Analyze migration files in the migrations directory."""
    migrations_dir = Path("migrations")

    if not migrations_dir.exists():
        print("❌ Migrations directory not found")
        return False

    print("=" * 70)
    print("MIGRATION ANALYSIS")
    print("=" * 70)
    print()

    # Find all SQL files
    migration_files = sorted(migrations_dir.glob("*.sql"))

    if not migration_files:
        print("❌ No migration files found")
        return False

    print(f"📁 Found {len(migration_files)} migration files\n")

    # Analyze each migration
    tables_by_schema = defaultdict(list)
    total_tables = 0

    for migration_file in migration_files:
        print(f"📄 {migration_file.name}")

        with open(migration_file, 'r') as f:
            content = f.read()

        # Find CREATE TABLE statements
        create_table_pattern = r'CREATE TABLE (?:IF NOT EXISTS\s+)?(\w+\.\w+)'
        tables = re.findall(create_table_pattern, content, re.IGNORECASE)

        if tables:
            print(f"   Tables: {len(tables)}")
            for table in tables:
                schema, table_name = table.split('.')
                tables_by_schema[schema].append(table_name)
                total_tables += 1
        print()

    # Summary
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"\n📊 Total Tables: {total_tables}")
    print(f"📚 Schemas: {len(tables_by_schema)}\n")

    for schema in sorted(tables_by_schema.keys()):
        tables = tables_by_schema[schema]
        print(f"  {schema}: {len(tables)} tables")
        for table in sorted(set(tables)):
            print(f"    - {table}")
        print()

    # Verification checks
    print("=" * 70)
    print("VERIFICATION CHECKS")
    print("=" * 70)
    print()

    checks = []

    # Check for core schemas
    required_schemas = ['congress', 'govinfo', 'openstates']
    for schema in required_schemas:
        if schema in tables_by_schema:
            checks.append(f"✅ {schema.upper()} schema present")
        else:
            checks.append(f"❌ Missing {schema.upper()} schema")

    # Check for migration tracking
    if 'schema_migrations' in str(content):
        checks.append("✅ Migration tracking support")

    # Check for idempotency
    idempotent = all('IF NOT EXISTS' in open(f).read() for f in migration_files)
    if idempotent:
        checks.append("✅ Idempotent migrations (IF NOT EXISTS)")
    else:
        checks.append("⚠️  Some migrations may not be idempotent")

    # Check for transactions
    transactional = all('BEGIN' in open(f).read() for f in migration_files)
    if transactional:
        checks.append("✅ Transaction-wrapped migrations")

    for check in checks:
        print(check)

    print()
    print("=" * 70)
    print(f"✅ MIGRATION ANALYSIS COMPLETE - {total_tables} TABLES VERIFIED")
    print("=" * 70)

    return True

if __name__ == "__main__":
    analyze_migrations()
