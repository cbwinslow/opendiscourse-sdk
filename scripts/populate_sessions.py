#!/usr/bin/env python3
"""Populate Congress sessions table"""

import os
from datetime import date, datetime

import psycopg2
from dotenv import load_dotenv

load_dotenv()

def populate_sessions():
    """Populate congress.sessions table with Congress 101-118"""

    # Connect to database
    conn_params = {
        'database': os.getenv('DB_NAME', 'cbwinslow'),
        'user': os.getenv('DB_USER', 'cbwinslow')
    }

    conn = psycopg2.connect(**conn_params)

    cursor = conn.cursor()

    # Congress sessions data (101-118)
    congress_sessions = [
        # Congress, Start Date, End Date, Odd Year, Even Year
        (101, date(1989, 1, 3), date(1991, 1, 3), 1989, 1990),
        (102, date(1991, 1, 3), date(1993, 1, 3), 1991, 1992),
        (103, date(1993, 1, 3), date(1995, 1, 3), 1993, 1994),
        (104, date(1995, 1, 3), date(1997, 1, 3), 1995, 1996),
        (105, date(1997, 1, 3), date(1999, 1, 3), 1997, 1998),
        (106, date(1999, 1, 3), date(2001, 1, 3), 1999, 2000),
        (107, date(2001, 1, 3), date(2003, 1, 3), 2001, 2002),
        (108, date(2003, 1, 3), date(2005, 1, 3), 2003, 2004),
        (109, date(2005, 1, 3), date(2007, 1, 3), 2005, 2006),
        (110, date(2007, 1, 3), date(2009, 1, 3), 2007, 2008),
        (111, date(2009, 1, 3), date(2011, 1, 3), 2009, 2010),
        (112, date(2011, 1, 3), date(2013, 1, 3), 2011, 2012),
        (113, date(2013, 1, 3), date(2015, 1, 3), 2013, 2014),
        (114, date(2015, 1, 3), date(2017, 1, 3), 2015, 2016),
        (115, date(2017, 1, 3), date(2019, 1, 3), 2017, 2018),
        (116, date(2019, 1, 3), date(2021, 1, 3), 2019, 2020),
        (117, date(2021, 1, 3), date(2023, 1, 3), 2021, 2022),
        (118, date(2023, 1, 3), date(2025, 1, 3), 2023, 2024),
    ]

    try:
        # Insert sessions
        insert_query = """
            INSERT INTO congress.sessions (
                congress_number, start_date, end_date, odd_year, even_year, created_at, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (congress_number) DO UPDATE SET
                start_date = EXCLUDED.start_date,
                end_date = EXCLUDED.end_date,
                odd_year = EXCLUDED.odd_year,
                even_year = EXCLUDED.even_year,
                updated_at = EXCLUDED.updated_at
        """

        for session in congress_sessions:
            cursor.execute(insert_query, (*session, datetime.now(), datetime.now()))

        conn.commit()
        print(f"Successfully inserted {len(congress_sessions)} congress sessions")

        # Verify
        cursor.execute("SELECT COUNT(*) FROM congress.sessions")
        count = cursor.fetchone()[0]
        print(f"Total sessions in database: {count}")

    except Exception as e:
        conn.rollback()
        print(f"Error: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    populate_sessions()
