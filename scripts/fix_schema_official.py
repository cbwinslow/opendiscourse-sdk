#!/usr/bin/env python3
"""Fix Congress schema to support official API structure"""

import os

import psycopg2
from dotenv import load_dotenv

load_dotenv()

def fix_schema_for_official_structure():
    """Fix schema to support members per congress (official API structure)"""

    # Connect to database
    conn_params = {
        'database': os.getenv('DB_NAME', 'cbwinslow'),
        'user': os.getenv('DB_USER', 'cbwinslow')
    }

    conn = psycopg2.connect(**conn_params)
    cursor = conn.cursor()

    try:
        print("Fixing Congress schema for official API structure...")

        # 1. Add congress_number column to members table
        print("Adding congress_number column...")
        cursor.execute("""
            ALTER TABLE congress.members 
            ADD COLUMN IF NOT EXISTS congress_number INTEGER
        """)

        # 2. Update existing records with congress numbers from member_terms
        print("Updating congress numbers from member_terms...")
        cursor.execute("""
            UPDATE congress.members m
            SET congress_number = sub.congress_number
            FROM (
                SELECT DISTINCT bioguide_id, congress_number
                FROM congress.member_terms
                WHERE congress_number IS NOT NULL
            ) sub
            WHERE m.bioguide_id = sub.bioguide_id
        """)

        # 3. For any remaining records without congress_number, set to 118 (default)
        print("Setting default congress number for remaining records...")
        cursor.execute("""
            UPDATE congress.members 
            SET congress_number = 118 
            WHERE congress_number IS NULL
        """)

        # 4. Drop the old primary key
        print("Dropping old primary key...")
        cursor.execute("ALTER TABLE congress.members DROP CONSTRAINT members_pkey")

        # 5. Add new composite primary key
        print("Adding composite primary key...")
        cursor.execute("""
            ALTER TABLE congress.members 
            ADD CONSTRAINT members_pkey PRIMARY KEY (bioguide_id, congress_number)
        """)

        # 6. Add congress_number to NOT NULL constraint
        print("Adding NOT NULL constraint to congress_number...")
        cursor.execute("""
            ALTER TABLE congress.members 
            ALTER COLUMN congress_number SET NOT NULL
        """)

        # 7. Add indexes for performance
        print("Adding indexes...")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_members_congress_number ON congress.members(congress_number)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_members_bioguide_congress ON congress.members(bioguide_id, congress_number)")

        conn.commit()

        # Verify results
        cursor.execute("SELECT COUNT(*) FROM congress.members")
        member_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(DISTINCT bioguide_id) FROM congress.members")
        unique_members = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM congress.member_terms")
        term_count = cursor.fetchone()[0]

        print("Schema fix complete!")
        print(f"Total member records: {member_count}")
        print(f"Unique bioguide IDs: {unique_members}")
        print(f"Member terms: {term_count}")

        # Show sample data
        print("\nSample data:")
        cursor.execute("""
            SELECT bioguide_id, congress_number, first_name, last_name 
            FROM congress.members 
            ORDER BY bioguide_id, congress_number 
            LIMIT 10
        """)
        for row in cursor.fetchall():
            print(f"  {row[0]} - Congress {row[1]}: {row[2]} {row[3]}")

    except Exception as e:
        conn.rollback()
        print(f"Error: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    fix_schema_for_official_structure()