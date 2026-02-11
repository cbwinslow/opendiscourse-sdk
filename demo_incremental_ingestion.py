#!/usr/bin/env python3
"""
Demo Script: Incremental Ingestion System for Congress.gov Members
Demonstrates the complete trace flow with checkpoint tracking and fingerprinting
"""

import os
import sys

import psycopg2

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scripts.ingest_congress_incremental import IncrementalCongressIngestor


def demo_incremental_ingestion():
    """Demonstrate the complete incremental ingestion flow"""

    print("=" * 80)
    print("🚀 INCREMENTAL CONGRESS MEMBERS INGESTION DEMO")
    print("=" * 80)

    # Initialize ingestor
    try:
        ingestor = IncrementalCongressIngestor()
        print("✅ IncrementalCongressIngestor initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize ingestor: {e}")
        print("⚠️ Using demo mode without API key")
        return demo_without_api()

    # Step 1: Show initial checkpoint status
    print("\n📋 STEP 1: Initial Checkpoint Status")
    print("-" * 50)
    checkpoints = ingestor.get_checkpoint_status()

    # Step 2: Get ingestion parameters (demonstrates trace 1a)
    print("\n🔍 STEP 2: Get Next Ingestion Parameters (Trace 1a)")
    print("-" * 50)
    congress = 118
    params = ingestor.get_next_ingestion_params(congress)
    print(f"Congress {congress} parameters:")
    print(f"  Next offset: {params['next_offset']}")
    print(f"  Is completed: {params['is_completed']}")

    # Step 3: If already completed, reset to demonstrate flow
    if params['is_completed']:
        print("\n🔄 Congress 118 already completed, resetting checkpoint for demo...")
        reset_demo_checkpoint(ingestor, congress)
        params = ingestor.get_next_ingestion_params(congress)
        print(f"New parameters - Next offset: {params['next_offset']}")

    # Step 4: Demonstrate fingerprinting (trace 1d)
    print("\n🔐 STEP 3: Record Fingerprinting Demo (Trace 1d)")
    print("-" * 50)
    demo_fingerprinting(ingestor)

    # Step 5: Run incremental ingestion
    print("\n🚀 STEP 4: Running Incremental Ingestion")
    print("-" * 50)
    print("This will demonstrate the complete flow:")
    print("  1a. Get checkpoint parameters")
    print("  1b. Resume from checkpoint offset")
    print("  1c. Fetch batch from Congress API")
    print("  1d. Check SHA-256 fingerprint")
    print("  1e. Batch insert new members")
    print("  1f. Update checkpoint progress")

    try:
        result = ingestor.ingest_congress_members(congress)
        print("\n✅ Ingestion completed:")
        print(f"  Status: {result['status']}")
        print(f"  Records processed: {result['records_processed']}")
        print(f"  Records skipped: {result['records_skipped']}")
        if 'final_offset' in result:
            print(f"  Final offset: {result['final_offset']}")
    except Exception as e:
        print(f"❌ Ingestion failed: {e}")

    # Step 6: Show final checkpoint status
    print("\n📊 STEP 5: Final Checkpoint Status")
    print("-" * 50)
    ingestor.get_checkpoint_status()

    # Step 7: Show database statistics
    print("\n📈 STEP 6: Database Statistics")
    print("-" * 50)
    show_database_stats()

def reset_demo_checkpoint(ingestor, congress):
    """Reset checkpoint for demonstration"""
    cursor = ingestor.db_conn.cursor()
    try:
        cursor.execute("""
            DELETE FROM incremental.ingestion_checkpoints
            WHERE data_source = 'congress.gov'
            AND data_type = 'members'
            AND category = %s
        """, (str(congress),))

        cursor.execute("""
            DELETE FROM incremental.record_fingerprints
            WHERE data_source = 'congress.gov'
            AND data_type = 'members'
            AND record_id LIKE %s
        """, (f'%{congress}%',))

        ingestor.db_conn.commit()
        print(f"✅ Reset Congress {congress} checkpoint")
    finally:
        cursor.close()

def demo_fingerprinting(ingestor):
    """Demonstrate SHA-256 fingerprinting functionality"""
    # Sample member data
    sample_member = {
        'member': {
            'bioguideId': 'D000622',
            'firstName': 'Lauren',
            'lastName': 'Underwood',
            'birthDate': '1986-10-04',
            'gender': 'F'
        }
    }

    member_id = sample_member['member']['bioguideId']

    # First check - should be False (new record)
    is_processed_1 = ingestor.is_record_processed(member_id, sample_member)
    print(f"First fingerprint check for {member_id}: {is_processed_1}")

    # Second check with same data - should be True (duplicate)
    is_processed_2 = ingestor.is_record_processed(member_id, sample_member)
    print(f"Second fingerprint check (same data): {is_processed_2}")

    # Third check with modified data - should be False (changed)
    modified_member = sample_member.copy()
    modified_member['member']['lastName'] = 'Smith'
    is_processed_3 = ingestor.is_record_processed(member_id, modified_member)
    print(f"Third fingerprint check (modified data): {is_processed_3}")

def show_database_stats():
    """Show database statistics for the incremental system"""
    conn = psycopg2.connect(database='cbwinslow', user='cbwinslow')
    cursor = conn.cursor()

    try:
        # Checkpoint statistics
        cursor.execute("""
            SELECT
                data_source,
                data_type,
                COUNT(*) as total_checkpoints,
                SUM(CASE WHEN is_completed THEN 1 ELSE 0 END) as completed,
                SUM(total_processed) as total_records_processed
            FROM incremental.ingestion_checkpoints
            GROUP BY data_source, data_type
            ORDER BY data_source, data_type
        """)

        print("📊 Checkpoint Statistics:")
        print("Source\t\tType\tTotal\tCompleted\tRecords")
        print("-" * 60)
        for row in cursor.fetchall():
            print(f"{row[0]}\t{row[1]}\t{row[2]}\t{row[3]}\t\t{row[4]}")

        # Fingerprint statistics
        cursor.execute("""
            SELECT
                data_source,
                data_type,
                COUNT(*) as total_fingerprints
            FROM incremental.record_fingerprints
            GROUP BY data_source, data_type
            ORDER BY data_source, data_type
        """)

        print("\n🔐 Fingerprint Statistics:")
        print("Source\t\tType\tTotal Fingerprints")
        print("-" * 50)
        for row in cursor.fetchall():
            print(f"{row[0]}\t{row[1]}\t{row[2]}")

        # Session statistics
        cursor.execute("""
            SELECT
                status,
                COUNT(*) as count,
                MAX(started_at) as last_session
            FROM incremental.ingestion_sessions
            GROUP BY status
            ORDER BY status
        """)

        print("\n📋 Session Statistics:")
        print("Status\t\tCount\tLast Session")
        print("-" * 50)
        for row in cursor.fetchall():
            last_session = row[2].strftime('%Y-%m-%d %H:%M') if row[2] else 'Never'
            print(f"{row[0]}\t{row[1]}\t{last_session}")

    finally:
        cursor.close()
        conn.close()

def demo_without_api():
    """Demo without API key - show database structure only"""
    print("\n📋 Database Structure Demo (No API Key)")
    print("-" * 50)
    show_database_stats()

    print("\n🔧 Key Features of Incremental Ingestion System:")
    print("✅ Checkpoint tracking with offset-based pagination")
    print("✅ SHA-256 fingerprinting for duplicate detection")
    print("✅ Session tracking for audit trail")
    print("✅ Resume capability from interruption")
    print("✅ Progress monitoring and reporting")
    print("✅ Error handling and recovery")

    print("\n📝 Trace Flow (Congress.gov Members):")
    print("1a. get_next_ingestion_params() - Retrieve checkpoint")
    print("1b. Resume from checkpoint offset")
    print("1c. fetch_members_page() - Get batch from API")
    print("1d. is_record_processed() - SHA-256 fingerprint check")
    print("1e. insert_members_batch() - UPSERT to database")
    print("1f. update_checkpoint() - Save progress")

if __name__ == "__main__":
    demo_incremental_ingestion()
