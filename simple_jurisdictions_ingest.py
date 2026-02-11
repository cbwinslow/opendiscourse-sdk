#!/usr/bin/env python3
"""
Simple OpenStates Jurisdictions Ingestion
Works with the existing schema without feature_flags
"""

import logging
import os

import psycopg2
import requests
from dotenv import load_dotenv
from psycopg2.extras import execute_values

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

def get_db_connection():
    """Get database connection"""
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME", "opendiscourse"),
        user=os.getenv("DB_USER", "cbwinslow"),
        host=os.getenv("DB_HOST", "/var/run/postgresql")
    )

def ingest_jurisdictions():
    """Ingest OpenStates jurisdictions"""
    api_key = os.getenv("OPENSTATES_API_KEY")
    if not api_key:
        raise ValueError("OPENSTATES_API_KEY required")

    base_url = "https://v3.openstates.org"
    headers = {"X-API-Key": api_key, "Accept": "application/json"}

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Fetch jurisdictions
        url = f"{base_url}/jurisdictions"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()

        jurisdictions = data.get("results", [])
        logger.info(f"Found {len(jurisdictions)} jurisdictions")

        # Prepare data for insertion
        rows = []
        for jur in jurisdictions:
            rows.append((
                jur["id"],
                jur["name"],
                jur["classification"],
                jur.get("division_id", "").split(":")[-1] if jur.get("division_id") else "",
                jur.get("url"),
                jur.get("latest_bill_update"),
                jur.get("latest_people_update")
            ))

        # Insert data
        query = """
        INSERT INTO openstates.jurisdictions
        (jurisdiction_id, name, classification, state_code, url, latest_bill_update, latest_people_update)
        VALUES %s
        ON CONFLICT (jurisdiction_id) DO UPDATE SET
            name = EXCLUDED.name,
            classification = EXCLUDED.classification,
            state_code = EXCLUDED.state_code,
            url = EXCLUDED.url,
            latest_bill_update = EXCLUDED.latest_bill_update,
            latest_people_update = EXCLUDED.latest_people_update,
            updated_at = now()
        """

        execute_values(cursor, query, rows)
        conn.commit()

        logger.info(f"✅ Successfully processed {len(rows)} jurisdictions")

    except Exception as e:
        logger.error(f"❌ Error: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    ingest_jurisdictions()
