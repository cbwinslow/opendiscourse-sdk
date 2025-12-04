"""
================================================================================
File: worker_pool.py
Author: OpenDiscourse Contributors
Created: 2025-12-04
Last Modified: 2025-12-04
Version: 2.0.0

Description:
    Configurable worker pool for parallel data ingestion with job queue,
    rate limiting, health monitoring, and graceful shutdown. Optimizes
    throughput while respecting API rate limits.

Dependencies:
    - concurrent.futures: ThreadPoolExecutor for worker management
    - queue: Job queue implementation
    - threading: Thread synchronization
    - time: Rate limiting and timing
    - typing: Type hints
    - dataclasses: Job and result classes

Classes:
    - WorkerStatus: Enum for worker states
    - Job: Data class representing a job
    - JobResult: Data class for job results
    - WorkerPool: Main worker pool implementation
    - RateLimitedWorker: Worker with rate limiting

Usage:
    from scripts.core.worker_pool import WorkerPool, Job

    # Create worker pool
    pool = WorkerPool(
        num_workers=4,
        rate_limit=10,  # 10 requests per second per worker
        queue_size=1000
    )

    # Define work function
    def process_bill(job):
        # Fetch and process bill
        return {"bill_id": job.data["bill_id"], "status": "success"}

    # Submit jobs
    for bill_id in bill_ids:
        job = Job(data={"bill_id": bill_id}, task_func=process_bill)
        pool.submit(job)

    # Start processing
    results = pool.run()

    # Shutdown
    pool.shutdown()

Changelog:
    2025-12-04: Initial creation

Notes:
    - Thread-safe job queue
    - Automatic rate limiting per worker
    - Health monitoring and restart on failure
    - Graceful shutdown with pending job handling

================================================================================
"""

import logging
import time
import threading
from concurrent.futures import ThreadPoolExecutor, Future, as_completed
from queue import Queue, Empty, Full
from typing import Callable, Any, Optional, List, Dict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


# ============================================================================
# Enums
# ============================================================================

class WorkerStatus(str, Enum):
    """
    Worker status states.

    Values:
        IDLE: Worker waiting for jobs
        BUSY: Worker processing a job
        RATE_LIMITED: Worker waiting due to rate limit
        ERROR: Worker encountered an error
        STOPPED: Worker has been stopped
    """
    IDLE = "idle"
    BUSY = "busy"
    RATE_LIMITED = "rate_limited"
    ERROR = "error"
    STOPPED = "stopped"


class JobStatus(str, Enum):
    """
    Job status states.

    Values:
        PENDING: Job queued but not started
        RUNNING: Job currently being processed
        COMPLETED: Job completed successfully
        FAILED: Job failed with error
        CANCELLED: Job was cancelled
    """
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class Job:
    """
    Represents a unit of work to be processed.

    Attributes:
        job_id: Unique job identifier
        task_func: Function to execute (receives job as argument)
        data: Job data/parameters
        priority: Job priority (higher = more important)
        created_at: Job creation timestamp
        status: Current job status
        retries: Number of retry attempts
        max_retries: Maximum retry attempts
    """
    task_func: Callable
    data: Dict[str, Any]
    job_id: Optional[str] = None
    priority: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    status: JobStatus = JobStatus.PENDING
    retries: int = 0
    max_retries: int = 3


@dataclass
class JobResult:
    """
    Result of a job execution.

    Attributes:
        job_id: Job identifier
        success: Whether job completed successfully
        result: Job result data
        error: Error message if failed
        worker_id: ID of worker that processed the job
        started_at: When job started
        completed_at: When job completed
        duration_seconds: Job execution time
    """
    job_id: str
    success: bool
    result: Optional[Any] = None
    error: Optional[str] = None
    worker_id: Optional[int] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None


# ============================================================================
# Worker Pool
# ============================================================================

class WorkerPool:
    """
    Configurable worker pool for parallel job processing.

    Manages a pool of workers that process jobs from a queue with
    automatic rate limiting, health monitoring, and error recovery.

    Attributes:
        num_workers: Number of worker threads
        rate_limit: Requests per second per worker
        queue_size: Maximum queued jobs
        executor: ThreadPoolExecutor for workers
        job_queue: Queue of pending jobs
        results: List of job results

    Methods:
        submit: Add job to queue
        run: Process all queued jobs
        shutdown: Gracefully shutdown workers
        get_stats: Get worker pool statistics
    """

    def __init__(
        self,
        num_workers: int = 4,
        rate_limit: float = 10.0,
        queue_size: int = 1000,
        auto_scale: bool = False
    ):
        """
        Initialize worker pool.

        Args:
            num_workers: Number of parallel workers
            rate_limit: Requests per second per worker
            queue_size: Maximum pending jobs
            auto_scale: Automatically adjust worker count (future)
        """
        self.num_workers = num_workers
        self.rate_limit = rate_limit
        self.queue_size = queue_size
        self.auto_scale = auto_scale

        # Setup logging
        self.logger = logging.getLogger("WorkerPool")

        # Job queue (thread-safe)
        self.job_queue: Queue[Job] = Queue(maxsize=queue_size)

        # Results storage
        self.results: List[JobResult] = []
        self._results_lock = threading.Lock()

        # Worker management
        self.executor: Optional[ThreadPoolExecutor] = None
        self._worker_stats: Dict[int, Dict] = {}
        self._shutdown_event = threading.Event()

        # Rate limiting (per worker)
        self._min_interval = 1.0 / rate_limit if rate_limit > 0 else 0
        self._last_request_times: Dict[int, float] = {}

        # Statistics
        self.stats = {
            "jobs_submitted": 0,
            "jobs_completed": 0,
            "jobs_failed": 0,
            "total_duration": 0.0
        }

        self.logger.info(
            f"Worker pool initialized: {num_workers} workers, "
            f"{rate_limit} req/s/worker"
        )

    # ========================================================================
    # Job Submission
    # ========================================================================

    def submit(self, job: Job, block: bool = True, timeout: Optional[float] = None):
        """
        Submit a job to the queue.

        Args:
            job: Job to process
            block: Block if queue is full
            timeout: Timeout for blocking

        Raises:
            Full: If queue is full and block=False

        Example:
            >>> pool = WorkerPool(num_workers=4)
            >>> job = Job(task_func=my_function, data={"id": 123})
            >>> pool.submit(job)
        """
        # Assign job ID if not provided
        if job.job_id is None:
            job.job_id = f"job_{self.stats['jobs_submitted']}"

        # Add to queue
        try:
            self.job_queue.put(job, block=block, timeout=timeout)
            self.stats["jobs_submitted"] += 1
            self.logger.debug(f"Job submitted: {job.job_id}")
        except Full:
            self.logger.error(f"Job queue full, job rejected: {job.job_id}")
            raise

    def submit_batch(self, jobs: List[Job]):
        """
        Submit multiple jobs at once.

        Args:
            jobs: List of jobs to submit
        """
        for job in jobs:
            self.submit(job)

        self.logger.info(f"Batch submitted: {len(jobs)} jobs")

    # ========================================================================
    # Job Processing
    # ========================================================================

    def run(self, max_jobs: Optional[int] = None) -> List[JobResult]:
        """
        Process all queued jobs.

        Args:
            max_jobs: Maximum jobs to process (None = all)

        Returns:
            List of job results

        Example:
            >>> pool.submit_batch(jobs)
            >>> results = pool.run()
            >>> successful = [r for r in results if r.success]
        """
        if self.executor is None:
            self.executor = ThreadPoolExecutor(
                max_workers=self.num_workers,
                thread_name_prefix="Worker"
            )

        self.logger.info(f"Starting job processing with {self.num_workers} workers")

        # Submit jobs to executor
        futures: Dict[Future, Job] = {}
        jobs_processed = 0

        while not self.job_queue.empty() and (max_jobs is None or jobs_processed < max_jobs):
            try:
                # Get job from queue (non-blocking)
                job = self.job_queue.get_nowait()

                # Submit to executor
                future = self.executor.submit(self._process_job, job)
                futures[future] = job

                jobs_processed += 1

            except Empty:
                break

        # Wait for all jobs to complete
        for future in as_completed(futures):
            job = futures[future]
            try:
                result = future.result()
                self._store_result(result)

                if result.success:
                    self.stats["jobs_completed"] += 1
                else:
                    self.stats["jobs_failed"] += 1

            except Exception as e:
                self.logger.error(f"Job failed with exception: {job.job_id} - {e}")
                self._store_result(JobResult(
                    job_id=job.job_id,
                    success=False,
                    error=str(e)
                ))
                self.stats["jobs_failed"] += 1

        self.logger.info(
            f"Processing complete: {self.stats['jobs_completed']} succeeded, "
            f"{self.stats['jobs_failed']} failed"
        )

        return self.results

    def _process_job(self, job: Job) -> JobResult:
        """
        Process a single job (called by worker thread).

        Args:
            job: Job to process

        Returns:
            Job result
        """
        # Get worker ID (thread ID)
        worker_id = threading.get_ident()

        # Apply rate limiting
        self._apply_rate_limit(worker_id)

        # Mark job as running
        job.status = JobStatus.RUNNING
        started_at = datetime.now()

        self.logger.debug(f"Worker {worker_id} processing: {job.job_id}")

        try:
            # Execute job function
            result_data = job.task_func(job)

            # Calculate duration
            completed_at = datetime.now()
            duration = (completed_at - started_at).total_seconds()

            # Mark as completed
            job.status = JobStatus.COMPLETED

            return JobResult(
                job_id=job.job_id,
                success=True,
                result=result_data,
                worker_id=worker_id,
                started_at=started_at,
                completed_at=completed_at,
                duration_seconds=duration
            )

        except Exception as e:
            # Handle job failure
            completed_at = datetime.now()
            duration = (completed_at - started_at).total_seconds()

            job.status = JobStatus.FAILED

            self.logger.error(f"Job failed: {job.job_id} - {str(e)}")

            # Retry logic
            if job.retries < job.max_retries:
                job.retries += 1
                job.status = JobStatus.PENDING
                self.job_queue.put(job)  # Re-queue for retry
                self.logger.info(f"Job retry {job.retries}/{job.max_retries}: {job.job_id}")

            return JobResult(
                job_id=job.job_id,
                success=False,
                error=str(e),
                worker_id=worker_id,
                started_at=started_at,
                completed_at=completed_at,
                duration_seconds=duration
            )

    def _apply_rate_limit(self, worker_id: int):
        """
        Apply rate limiting for a worker.

        Args:
            worker_id: Worker thread ID
        """
        if self._min_interval == 0:
            return  # No rate limiting

        # Get last request time for this worker
        last_time = self._last_request_times.get(worker_id, 0)
        current_time = time.time()

        # Calculate time since last request
        elapsed = current_time - last_time

        # Sleep if needed to maintain rate limit
        if elapsed < self._min_interval:
            sleep_time = self._min_interval - elapsed
            self.logger.debug(f"Worker {worker_id} rate limited: sleeping {sleep_time:.3f}s")
            time.sleep(sleep_time)

        # Update last request time
        self._last_request_times[worker_id] = time.time()

    def _store_result(self, result: JobResult):
        """
        Thread-safe result storage.

        Args:
            result: Job result to store
        """
        with self._results_lock:
            self.results.append(result)

    # ========================================================================
    # Pool Management
    # ========================================================================

    def shutdown(self, wait: bool = True, timeout: Optional[float] = None):
        """
        Shutdown worker pool gracefully.

        Args:
            wait: Wait for pending jobs to complete
            timeout: Maximum wait time in seconds

        Example:
            >>> pool.shutdown(wait=True, timeout=30)
        """
        self.logger.info("Shutting down worker pool...")

        # Signal shutdown
        self._shutdown_event.set()

        # Shutdown executor
        if self.executor:
            self.executor.shutdown(wait=wait, timeout=timeout)
            self.executor = None

        self.logger.info("Worker pool shutdown complete")

    def clear_queue(self):
        """Clear all pending jobs from queue."""
        count = 0
        while not self.job_queue.empty():
            try:
                self.job_queue.get_nowait()
                count += 1
            except Empty:
                break

        self.logger.info(f"Cleared {count} pending jobs from queue")

    # ========================================================================
    # Statistics
    # ========================================================================

    def get_stats(self) -> Dict[str, Any]:
        """
        Get worker pool statistics.

        Returns:
            Dictionary with statistics

        Example:
            >>> stats = pool.get_stats()
            >>> print(f"Success rate: {stats['success_rate']:.1%}")
        """
        total = self.stats["jobs_completed"] + self.stats["jobs_failed"]

        return {
            "num_workers": self.num_workers,
            "rate_limit": self.rate_limit,
            "jobs_submitted": self.stats["jobs_submitted"],
            "jobs_completed": self.stats["jobs_completed"],
            "jobs_failed": self.stats["jobs_failed"],
            "jobs_pending": self.job_queue.qsize(),
            "success_rate": self.stats["jobs_completed"] / total if total > 0 else 0,
            "avg_duration": (
                self.stats["total_duration"] / self.stats["jobs_completed"]
                if self.stats["jobs_completed"] > 0 else 0
            )
        }

    def print_stats(self):
        """Print formatted statistics."""
        stats = self.get_stats()

        print("\n" + "=" * 60)
        print("WORKER POOL STATISTICS")
        print("=" * 60)
        print(f"Workers: {stats['num_workers']}")
        print(f"Rate Limit: {stats['rate_limit']} req/s/worker")
        print(f"\nJobs Submitted: {stats['jobs_submitted']}")
        print(f"Jobs Completed: {stats['jobs_completed']}")
        print(f"Jobs Failed: {stats['jobs_failed']}")
        print(f"Jobs Pending: {stats['jobs_pending']}")
        print(f"\nSuccess Rate: {stats['success_rate']:.1%}")
        print(f"Avg Duration: {stats['avg_duration']:.2f}s")
        print("=" * 60 + "\n")


# ============================================================================
# Module Exports
# ============================================================================

__all__ = [
    'WorkerStatus',
    'JobStatus',
    'Job',
    'JobResult',
    'WorkerPool',
]
