#!/usr/bin/env python3
"""Basic vector database stats."""
import os
import psycopg2

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://localhost/opendiscourse")

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()
cur.execute("SELECT COUNT(*) FROM document_vectors")
count = cur.fetchone()[0]
print("Vector count:", count)
