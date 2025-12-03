#!/usr/bin/env python3
"""
Simple Congress Bills Ingestion
Works with simplified database connection
"""

import os
import requests
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

def get_db_connection():
    """Get database connection with Unix socket"""
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME", "opendiscourse"),
        user=os.getenv("DB_USER", "cbwinslow"),
        host="/var/run/postgresql"
    )

def ingest_congress_bills(congress_number, limit=100):
    """Ingest bills for a specific congress"""
    api_key = os.getenv("CONGRESS_API_KEY")
    if not api_key:
        raise ValueError("CONGRESS_API_KEY required")

    base_url = "https://api.congress.gov/v3"
    headers = {"X-API-Key": api_key, "Accept": "application/json"}

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        logger.info(f"🚀 Starting bills ingestion for Congress {congress_number}")

        # Fetch bills with offset pagination
        offset = 0
        total_processed = 0

        while total_processed < limit:
            url = f"{base_url}/bill/{congress_number}?limit=50&offset={offset}"
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()

            bills = data.get("bills", [])
            if not bills:
                break

            # Prepare data for insertion
            rows = []
            for bill in bills:
                rows.append((
                    bill.get("congress", congress_number),
                    bill.get("type", ""),
                    int(bill.get("number", 0)),
                    bill.get("originChamber", ""),
                    bill.get("introducedDate"),
                    bill.get("latestAction", {}).get("actionDate"),
                    bill.get("latestAction", {}).get("text"),
                    bill.get("policyArea", {}).get("name") if bill.get("policyArea") else "",
                    bill.get("title", ""),
                    bill.get("sponsor", {}).get("bioguideId"),
                    datetime.now()
                ))

            # Insert data
            query = """
            INSERT INTO congress.bills
            (congress, type, number, title, introduced_date, latest_action_date,
             latest_action_text, sponsor_bioguide_id, sponsor_name, policy_area,
             subjects, summaries, url, created_at)
            VALUES %s
            ON CONFLICT (congress, type, number) DO UPDATE SET
                title = EXCLUDED.title,
                introduced_date = EXCLUDED.introduced_date,
                latest_action_date = EXCLUDED.latest_action_date,
                latest_action_text = EXCLUDED.latest_action_text,
                sponsor_bioguide_id = EXCLUDED.sponsor_bioguide_id,
                sponsor_name = EXCLUDED.sponsor_name,
                policy_area = EXCLUDED.policy_area,
                subjects = EXCLUDED.subjects,
                summaries = EXCLUDED.summaries,
                url = EXCLUDED.url,
                updated_at = now()
            """

            execute_values(cursor, query, rows)
            conn.commit()

            batch_count = len(bills)
            total_processed += batch_count
            offset += 50

            logger.info(f"✅ Processed {batch_count} bills (total: {total_processed})")

            if len(bills) < 50:  # Last page
                break

        logger.info(f"🎉 Congress {congress_number} bills ingestion complete: {total_processed} bills")

    except Exception as e:
        logger.error(f"❌ Error: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    import json
    ingest_congress_bills(118, limit=200)
