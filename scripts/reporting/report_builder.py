#!/usr/bin/env python3
"""Simple report builder for entities."""
import csv
import os
import psycopg2

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://localhost/opendiscourse")

QUERY = "SELECT entity_type, COUNT(*) FROM entities GROUP BY entity_type ORDER BY COUNT(*) DESC"

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()
cur.execute(QUERY)
rows = cur.fetchall()

with open("entity_report.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["entity_type", "count"])
    writer.writerows(rows)

print("Report written to entity_report.csv")
