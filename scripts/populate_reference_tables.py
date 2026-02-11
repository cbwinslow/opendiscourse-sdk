#!/usr/bin/env python3
"""Populate reference tables for Congress schema"""

import os
from datetime import datetime

import psycopg2
from dotenv import load_dotenv

load_dotenv()

def populate_reference_tables():
    """Populate reference tables (parties, states)"""

    # Connect to database
    conn_params = {
        'database': os.getenv('DB_NAME', 'cbwinslow'),
        'user': os.getenv('DB_USER', 'cbwinslow')
    }

    conn = psycopg2.connect(**conn_params)
    cursor = conn.cursor()

    try:
        # Populate parties
        parties = [
            ('D', 'Democratic Party'),
            ('R', 'Republican Party'),
            ('I', 'Independent'),
            ('L', 'Libertarian Party'),
            ('G', 'Green Party'),
            ('O', 'Other')
        ]

        party_query = """
            INSERT INTO congress.parties (party_code, display_name, created_at, updated_at)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (party_code) DO UPDATE SET
                display_name = EXCLUDED.display_name,
                updated_at = EXCLUDED.updated_at
        """

        for party in parties:
            cursor.execute(party_query, (*party, datetime.now(), datetime.now()))

        print(f"Inserted {len(parties)} parties")

        # Populate states
        states = [
            ('AL', 'Alabama', '01', False),
            ('AK', 'Alaska', '02', False),
            ('AZ', 'Arizona', '04', False),
            ('AR', 'Arkansas', '05', False),
            ('CA', 'California', '06', False),
            ('CO', 'Colorado', '08', False),
            ('CT', 'Connecticut', '09', False),
            ('DE', 'Delaware', '10', False),
            ('FL', 'Florida', '12', False),
            ('GA', 'Georgia', '13', False),
            ('HI', 'Hawaii', '15', True),
            ('ID', 'Idaho', '16', False),
            ('IL', 'Illinois', '17', False),
            ('IN', 'Indiana', '18', False),
            ('IA', 'Iowa', '19', False),
            ('KS', 'Kansas', '20', False),
            ('KY', 'Kentucky', '21', False),
            ('LA', 'Louisiana', '22', False),
            ('ME', 'Maine', '23', False),
            ('MD', 'Maryland', '24', False),
            ('MA', 'Massachusetts', '25', False),
            ('MI', 'Michigan', '26', False),
            ('MN', 'Minnesota', '27', False),
            ('MS', 'Mississippi', '28', False),
            ('MO', 'Missouri', '29', False),
            ('MT', 'Montana', '30', False),
            ('NE', 'Nebraska', '31', False),
            ('NV', 'Nevada', '32', False),
            ('NH', 'New Hampshire', '33', False),
            ('NJ', 'New Jersey', '34', False),
            ('NM', 'New Mexico', '35', False),
            ('NY', 'New York', '36', False),
            ('NC', 'North Carolina', '37', False),
            ('ND', 'North Dakota', '38', False),
            ('OH', 'Ohio', '39', False),
            ('OK', 'Oklahoma', '40', False),
            ('OR', 'Oregon', '41', False),
            ('PA', 'Pennsylvania', '42', False),
            ('RI', 'Rhode Island', '44', False),
            ('SC', 'South Carolina', '45', False),
            ('SD', 'South Dakota', '46', False),
            ('TN', 'Tennessee', '47', False),
            ('TX', 'Texas', '48', False),
            ('UT', 'Utah', '49', False),
            ('VT', 'Vermont', '50', False),
            ('VA', 'Virginia', '51', False),
            ('WA', 'Washington', '53', False),
            ('WV', 'West Virginia', '54', False),
            ('WI', 'Wisconsin', '55', False),
            ('WY', 'Wyoming', '56', False),
            ('DC', 'District of Columbia', '11', True),
            ('PR', 'Puerto Rico', '72', True),
            ('GU', 'Guam', '66', True),
            ('VI', 'Virgin Islands', '78', True),
            ('AS', 'American Samoa', '60', True),
            ('MP', 'Northern Mariana Islands', '69', True)
        ]

        state_query = """
            INSERT INTO congress.states (state_code, name, fips_code, is_territory, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (state_code) DO UPDATE SET
                name = EXCLUDED.name,
                fips_code = EXCLUDED.fips_code,
                is_territory = EXCLUDED.is_territory,
                updated_at = EXCLUDED.updated_at
        """

        for state in states:
            cursor.execute(state_query, (*state, datetime.now(), datetime.now()))

        print(f"Inserted {len(states)} states and territories")

        conn.commit()

        # Verify
        cursor.execute("SELECT COUNT(*) FROM congress.parties")
        party_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM congress.states")
        state_count = cursor.fetchone()[0]

        print(f"Total parties: {party_count}")
        print(f"Total states: {state_count}")

    except Exception as e:
        conn.rollback()
        print(f"Error: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    populate_reference_tables()