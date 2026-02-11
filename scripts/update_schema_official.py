#!/usr/bin/env python3
"""Update Congress schema to support official API structure"""

import os

import psycopg2
from dotenv import load_dotenv

load_dotenv()

def update_schema_for_official_structure():
    """Update schema to support members per congress (official API structure)"""

    # Connect to database
    conn_params = {
        'database': os.getenv('DB_NAME', 'cbwinslow'),
        'user': os.getenv('DB_USER', 'cbwinslow')
    }

    conn = psycopg2.connect(**conn_params)
    cursor = conn.cursor()

    try:
        print("Updating Congress schema for official API structure...")

        # 1. Drop foreign key constraints temporarily
        print("Dropping foreign key constraints...")
        cursor.execute("ALTER TABLE congress.member_terms DROP CONSTRAINT IF EXISTS member_terms_bioguide_id_fkey")

        # 2. Create new members table that allows duplicates per congress
        print("Creating new members table...")
        cursor.execute("""
            CREATE TABLE congress.members_new (
                id SERIAL PRIMARY KEY,
                bioguide_id TEXT NOT NULL,
                congress_number INTEGER NOT NULL,
                first_name TEXT NOT NULL,
                middle_name TEXT,
                last_name TEXT NOT NULL,
                suffix TEXT,
                official_full_name TEXT,
                birthday DATE,
                gender TEXT,
                biography TEXT,
                birthplace TEXT,
                death_date DATE,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
                updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
                UNIQUE(bioguide_id, congress_number)
            )
        """)

        # 3. Migrate data from old table
        print("Migrating existing data...")
        cursor.execute("""
            INSERT INTO congress.members_new 
            (bioguide_id, congress_number, first_name, middle_name, last_name, suffix,
             official_full_name, birthday, gender, biography, birthplace, death_date, created_at, updated_at)
            SELECT m.bioguide_id, 
                   COALESCE(mt.congress_number, 118) as congress_number,
                   m.first_name, m.middle_name, m.last_name, m.suffix,
                   m.official_full_name, m.birthday, m.gender, m.biography, 
                   m.birthplace, m.death_date, m.created_at, m.updated_at
            FROM congress.members m
            LEFT JOIN congress.member_terms mt ON m.bioguide_id = mt.bioguide_id
            GROUP BY m.bioguide_id, mt.congress_number, m.first_name, m.middle_name, m.last_name, m.suffix,
                     m.official_full_name, m.birthday, m.gender, m.biography, m.birthplace, m.death_date, m.created_at, m.updated_at
        """)

        # 4. Drop old table and rename
        print("Replacing old table...")
        cursor.execute("DROP TABLE congress.members")
        cursor.execute("ALTER TABLE congress.members_new RENAME TO members")

        # 5. Update member_terms foreign key
        print("Updating foreign key constraints...")
        cursor.execute("""
            ALTER TABLE congress.member_terms 
            ADD CONSTRAINT member_terms_bioguide_id_fkey 
            FOREIGN KEY (bioguide_id) REFERENCES congress.members(bioguide_id)
        """)

        # 6. Add indexes for performance
        print("Adding indexes...")
        cursor.execute("CREATE INDEX idx_members_bioguide_id ON congress.members(bioguide_id)")
        cursor.execute("CREATE INDEX idx_members_congress_number ON congress.members(congress_number)")
        cursor.execute("CREATE INDEX idx_members_bioguide_congress ON congress.members(bioguide_id, congress_number)")

        conn.commit()

        # Verify results
        cursor.execute("SELECT COUNT(*) FROM congress.members")
        member_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM congress.member_terms")
        term_count = cursor.fetchone()[0]

        print("Migration complete!")
        print(f"Members: {member_count}")
        print(f"Member Terms: {term_count}")

    except Exception as e:
        conn.rollback()
        print(f"Error: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    update_schema_for_official_structure()