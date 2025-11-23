"""
Universal progress monitoring system for bulk data ingestion.
"""

import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

import psycopg2
from psycopg2.extras import RealDictCursor


@dataclass
class IngestionContext:
    """Context passed to delegate functions"""
    job_id: int
    data_source: str
    table_name: str
    record_type: str
    current_record_id: Optional[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class UniversalProgressMonitor:
    def __init__(self, db_connection, display_mode: str = 'tui'):
        self.db = db_connection
        self.display_mode = display_mode
        self.console = Console()
        self.delegates = {}
        self.active_jobs = {}
        self.live_display = None

    def register_delegate(self, data_source: str, table_name: str,
                         delegate_func: Callable[[IngestionContext, Dict[str, Any]], None]):
        """Register a delegate function for specific data source + table combination"""
        key = f"{data_source}:{table_name}"
        self.delegates[key] = delegate_func

    def start_job(self, job_name: str, data_source: str, table_name: str,
                  record_type: str, total_estimated: Optional[int] = None,
                  metadata: Dict[str, Any] = None) -> int:
        """Start a new ingestion job with progress tracking"""
        cursor = self.db.cursor()

        # Create job record
        cursor.execute("""
            INSERT INTO ingestion_jobs (
                job_name, data_source, table_name, record_type,
                total_records, metadata, status
            ) VALUES (%s, %s, %s, %s, %s, %s, 'running')
            RETURNING id
        """, (job_name, data_source, table_name, record_type,
              total_estimated, psycopg2.extras.Json(metadata or {})))

        job_id = cursor.fetchone()[0]
        self.db.commit()

        # Initialize job tracking
        context = IngestionContext(
            job_id=job_id,
            data_source=data_source,
            table_name=table_name,
            record_type=record_type,
            metadata=metadata or {}
        )

        self.active_jobs[job_id] = {
            'context': context,
            'start_time': time.time(),
            'processed': 0,
            'failed': 0
        }

        # Start TUI display if enabled
        if self.display_mode == 'tui':
            self._start_tui_display(job_id)

        return job_id

    def update_progress(self, job_id: int, success: bool,
                       record_id: Optional[str] = None,
                       error_details: Optional[Dict] = None):
        """Update progress for a job"""
        if job_id not in self.active_jobs:
            return

        job_data = self.active_jobs[job_id]
        context = job_data['context']
        context.current_record_id = record_id

        # Update counters
        if success:
            job_data['processed'] += 1
        else:
            job_data['failed'] += 1

        # Log error if any
        if error_details:
            self._log_error(job_id, error_details)

        # Call delegate function
        delegate_key = f"{context.data_source}:{context.table_name}"
        if delegate_key in self.delegates:
            delegate_context = {
                'success': success,
                'error_details': error_details,
                'processed_count': job_data['processed'],
                'failed_count': job_data['failed'],
                'elapsed_time': time.time() - job_data['start_time']
            }
            self.delegates[delegate_key](context, delegate_context)

        # Update database
        self._update_db_progress(job_id, job_data['processed'], job_data['failed'])

        # Update display
        if self.display_mode == 'tui':
            self._update_tui_display(job_id, job_data)

    def complete_job(self, job_id: int):
        """Mark a job as completed"""
        if job_id not in self.active_jobs:
            return

        cursor = self.db.cursor()
        cursor.execute("""
            UPDATE ingestion_jobs
            SET status = 'completed', completed_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (job_id,))
        self.db.commit()

        # Clean up
        if job_id in self.active_jobs:
            del self.active_jobs[job_id]

        if self.live_display:
            self.live_display.stop()

    def _log_error(self, job_id: int, error_details: Dict):
        """Log error to database"""
        cursor = self.db.cursor()
        cursor.execute("""
            INSERT INTO ingestion_errors (
                job_id, error_type, error_message, record_id,
                error_metadata
            ) VALUES (%s, %s, %s, %s, %s)
        """, (
            job_id,
            error_details.get('error_type', 'unknown_error'),
            error_details.get('error_message', 'Unknown error'),
            error_details.get('record_id'),
            psycopg2.extras.Json(error_details.get('metadata', {}))
        ))
        self.db.commit()

    def _update_db_progress(self, job_id: int, processed: int, failed: int):
        """Update progress in database"""
        cursor = self.db.cursor()

        # Calculate throughput
        job_data = self.active_jobs.get(job_id)
        if job_data:
            elapsed = time.time() - job_data['start_time']
            throughput = processed / max(elapsed / 60, 0.01) if elapsed > 0 else 0

            # Calculate ETA
            eta = None
            if job_data['context'].metadata.get('total_estimated') and throughput > 0:
                remaining = job_data['context'].metadata['total_estimated'] - processed
                eta_seconds = remaining / throughput * 60
                eta = datetime.now() + timedelta(seconds=eta_seconds)

            cursor.execute("""
                UPDATE ingestion_jobs
                SET processed_records = %s, failed_records = %s,
                    throughput_per_minute = %s, eta_timestamp = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (processed, failed, throughput, eta, job_id))

        self.db.commit()

    def _start_tui_display(self, job_id: int):
        """Initialize TUI display"""
        if self.live_display:
            self.live_display.stop()

        self.live_display = Live(console=self.console, refresh_per_second=2)
        self.live_display.start()
        self._update_tui_display(job_id, self.active_jobs[job_id])

    def _update_tui_display(self, job_id: int, job_data: Dict):
        """Update the TUI display"""
        if not self.live_display:
            return

        context = job_data['context']
        processed = job_data['processed']
        failed = job_data['failed']
        elapsed = time.time() - job_data['start_time']

        # Calculate metrics
        throughput = processed / max(elapsed / 60, 0.01)
        total_estimated = context.metadata.get('total_estimated')
        progress_percent = (processed / max(total_estimated or processed, 1)) * 100

        # Calculate ETA
        eta_str = "Unknown"
        if total_estimated and throughput > 0:
            remaining = total_estimated - processed
            eta_seconds = remaining / throughput * 60
            eta_str = f"{int(eta_seconds // 3600):02d}:{int((eta_seconds % 3600) // 60):02d}:{int(eta_seconds % 60):02d}"

        # Create display table
        table = Table(show_header=False, box=None)
        table.add_row("📊 Job:", f"{context.metadata.get('job_name', f'Job {job_id}')}")
        table.add_row("🔗 Source:", f"{context.data_source}")
        table.add_row("📋 Table:", f"{context.table_name}")
        table.add_row("👤 Type:", f"{context.record_type}")
        table.add_row("📈 Progress:", f"{processed}/{total_estimated or processed} ({progress_percent:.1f}%)")
        table.add_row("⚡ Throughput:", f"{throughput:.1f} records/min")
        table.add_row("⏰ ETA:", eta_str)
        table.add_row("❌ Failed:", f"{failed}")
        table.add_row("🔄 Current:", context.current_record_id or "Processing...")

        panel = Panel(table, title="🔥 Bulk Data Ingestion Monitor", border_style="blue")
        self.live_display.update(panel)

    def get_job_status(self, job_id: int) -> Optional[Dict]:
        """Get current status of a job"""
        cursor = self.db.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
            SELECT id, job_name, data_source, table_name, record_type, status,
                   total_records, processed_records, failed_records,
                   throughput_per_minute, eta_timestamp, started_at, completed_at
            FROM ingestion_jobs WHERE id = %s
        """, (job_id,))

        result = cursor.fetchone()
        return dict(result) if result else None
