#!/usr/bin/env python3
"""
Apply the RAG database schema (rag_db_schema.sql) to a PostgreSQL database.

Usage:
  python migrate_rag_db.py --db-url postgresql://user:pass@host:port/dbname
  # Or set DATABASE_URL env var

This script requires psycopg2 to be installed.
"""
import argparse
import os
import sys

import psycopg2

SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "rag_db_schema.sql")

def main():
    parser = argparse.ArgumentParser(description="Apply RAG DB schema to PostgreSQL.")
    parser.add_argument("--db-url", help="PostgreSQL connection URL (overrides DATABASE_URL env var)")
    args = parser.parse_args()

    db_url = args.db_url or os.environ.get("DATABASE_URL")
    if not db_url:
        print("Error: Provide --db-url or set DATABASE_URL environment variable.")
        sys.exit(1)

    with open(SCHEMA_PATH, "r") as f:
        schema_sql = f.read()

    try:
        conn = psycopg2.connect(db_url)
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute(schema_sql)
        print("RAG DB schema applied successfully.")
    except Exception as e:
        print(f"Error applying schema: {e}")
        sys.exit(1)
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    main()
