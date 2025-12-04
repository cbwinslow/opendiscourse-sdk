#!/usr/bin/env python3
"""
Database Query Script - Show Actual Ingestion Progress
Queries all tables to show current row counts and ingestion status
"""

import psycopg2
import os
from datetime import datetime
import json
from typing import Dict, List, Any

def get_db_connection():
    """Establish database connection with retry logic"""
    max_retries = 3
    retry_delay = 2

    for attempt in range(max_retries):
        try:
            # Use Unix socket connection for local development
            conn = psycopg2.connect(
                dbname=os.getenv('DB_NAME', 'opendiscourse'),
                user=os.getenv('DB_USER', 'postgres'),
                password=os.getenv('DB_PASSWORD', ''),
                host=os.getenv('DB_HOST', '/var/run/postgresql'),
                port=os.getenv('DB_PORT', '5432')
            )
            return conn
        except psycopg2.OperationalError as e:
            if attempt == max_retries - 1:
                raise
            print(f"Connection attempt {attempt + 1} failed: {e}")
            time.sleep(retry_delay)

    return None

def query_table_row_counts(conn) -> Dict[str, Any]:
    """Query all relevant tables and return row counts"""
    results = {}

    # Congress tables
    congress_tables = [
        'congress.bills', 'congress.members', 'congress.committees',
        'congress.committee_membership', 'congress.legislative_actions'
    ]

    # OpenStates tables
    openstates_tables = [
        'openstates.people', 'openstates.bills', 'openstates.organizations',
        'openstates.memberships', 'openstates.posts'
    ]

    # GovInfo tables
    govinfo_tables = [
        'govinfo.packages', 'govinfo.granules', 'govinfo.versions'
    ]

    all_tables = congress_tables + openstates_tables + govinfo_tables

    with conn.cursor() as cursor:
        for table in all_tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                results[table] = count
            except Exception as e:
                results[table] = f"Error: {str(e)}"

    return results

def query_recent_ingestion(conn) -> List[Dict[str, Any]]:
    """Query recent ingestion records"""
    recent_ingestions = []

    with conn.cursor() as cursor:
        try:
            cursor.execute("""
                SELECT source, table_name, records_ingested, timestamp
                FROM ingestion_logs
                ORDER BY timestamp DESC
                LIMIT 20
            """)
            for row in cursor.fetchall():
                recent_ingestions.append({
                    'source': row[0],
                    'table': row[1],
                    'records': row[2],
                    'timestamp': row[3].isoformat() if row[3] else None
                })
        except Exception as e:
            print(f"Error querying recent ingestions: {e}")

    return recent_ingestions

def main():
    """Main execution function"""
    print("🔍 DATABASE INGESTION STATUS QUERY")
    print("=" * 50)

    try:
        conn = get_db_connection()
        if not conn:
            print("❌ Failed to establish database connection")
            return

        print("✅ Database connection established")
        print(f"📊 Querying table row counts...")

        # Query row counts
        row_counts = query_table_row_counts(conn)

        # Query recent ingestions
        recent_ingestions = query_recent_ingestion(conn)

        print("\n" + "=" * 60)
        print("📈 CURRENT TABLE ROW COUNTS")
        print("=" * 60)

        # Display Congress tables
        print("\n🏛️ CONGRESS DATA:")
        for table in ['congress.bills', 'congress.members', 'congress.committees']:
            if table in row_counts:
                print(f"  {table}: {row_counts[table]:,} rows")

        # Display OpenStates tables
        print("\n🗳️ OPENSTATES DATA:")
        for table in ['openstates.people', 'openstates.bills', 'openstates.organizations']:
            if table in row_counts:
                count = row_counts[table]
                if isinstance(count, int):
                    print(f"  {table}: {count:,} rows")
                else:
                    print(f"  {table}: {count}")

        # Display GovInfo tables
        print("\n📚 GOVINFO DATA:")
        for table in ['govinfo.packages', 'govinfo.granules']:
            if table in row_counts:
                print(f"  {table}: {row_counts[table]:,} rows")

        print("\n" + "=" * 60)
        print("📋 RECENT INGESTION ACTIVITY")
        print("=" * 60)

        if recent_ingestions:
            for ingestion in recent_ingestions:
                print(f"  {ingestion['timestamp']} - {ingestion['source']} → {ingestion['table']}: {ingestion['records']:,} records")
        else:
            print("  No recent ingestion records found")

        # Calculate totals
        total_congress = sum(row_counts.get(table, 0) for table in ['congress.bills', 'congress.members', 'congress.committees'])
        total_openstates = sum(row_counts.get(table, 0) for table in ['openstates.people', 'openstates.bills', 'openstates.organizations'])
        total_govinfo = sum(row_counts.get(table, 0) for table in ['govinfo.packages', 'govinfo.granules'])

        print("\n" + "=" * 60)
        print("📊 TOTAL INGESTION SUMMARY")
        print("=" * 60)
        print(f"  🏛️  Congress Data: {total_congress:,} records")
        print(f"  🗳️  OpenStates Data: {total_openstates:,} records")
        print(f"  📚 GovInfo Data: {total_govinfo:,} records")
        print(f"  🔢  TOTAL: {total_congress + total_openstates + total_govinfo:,} records")

        # Save results to file
        results = {
            'timestamp': datetime.now().isoformat(),
            'row_counts': row_counts,
            'recent_ingestions': recent_ingestions,
            'totals': {
                'congress': total_congress,
                'openstates': total_openstates,
                'govinfo': total_govinfo,
                'total': total_congress + total_openstates + total_govinfo
            }
        }

        with open('ingestion_status_results.json', 'w') as f:
            json.dump(results, f, indent=2)

        print(f"\n✅ Results saved to ingestion_status_results.json")

    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"Error type: {type(e).__name__}")

    finally:
        if 'conn' in locals() and conn:
            conn.close()
            print("🔌 Database connection closed")

if __name__ == "__main__":
    import time
    main()
