from fastapi import APIRouter, HTTPException, Body
from typing import Optional, List
import os
import psycopg2
from psycopg2.extras import Json
from diagnostic_tools.linux_system_diagnostics.python.collector import LinuxDiagnosticCollector

router = APIRouter()

DB_URL = os.environ.get(
    "RAG_DB_URL", "postgresql://user:password@localhost:5432/opendiscourse"
)

def insert_diagnostics_report(
    report: dict,
    host: Optional[str] = None,
    tags: Optional[List[str]] = None,
    notes: Optional[str] = None,
):
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO diagnostics_reports (report, host, tags, notes)
            VALUES (%s, %s, %s, %s)
            RETURNING id;
            """,
            (Json(report), host, tags, notes)
        )
        report_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        return report_id
    except Exception as e:
        print(f"DB insert error: {e}")
        return None

@router.get("/diagnostics/linux")
def get_linux_diagnostics():
    collector = LinuxDiagnosticCollector()
    try:
        report = collector.collect_full_report()
        return report.dict() if hasattr(report, "dict") else report
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Diagnostics collection failed: {str(e)}"
        )

@router.post("/ingest/diagnostics")
def ingest_diagnostics(
    report: dict = Body(...),
    host: Optional[str] = None,
    tags: Optional[List[str]] = None,
    notes: Optional[str] = None,
):
    report_id = insert_diagnostics_report(report, host, tags, notes)
    if report_id is None:
        raise HTTPException(
            status_code=500,
            detail="Failed to insert diagnostics report into DB"
        )
    return {"report_id": report_id, "status": "ingested into DB"}
