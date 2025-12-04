"""
================================================================================
File: test_worker_pool.py
Author: OpenDiscourse Contributors
Created: 2025-12-04
Version: 1.0.0

Description:
    Comprehensive tests for worker pool system including job submission,
    parallel processing, rate limiting, and error handling.

================================================================================
"""

import pytest
import time
from scripts.core.worker_pool import (
    WorkerPool,
    Job,
    JobResult,
    WorkerStatus,
    JobStatus
)


# ============================================================================
# Test Functions (Simulated Work)
# ============================================================================

def simple_task(job: Job) -> dict:
    """Simple test task that returns job data."""
    return {"processed": job.data}


def slow_task(job: Job) -> dict:
    """Task that takes time to complete."""
    time.sleep(0.1)
    return {"processed": job.data}


def failing_task(job: Job) -> dict:
    """Task that always fails."""
    raise ValueError("Intentional failure")


def conditional_failing_task(job: Job) -> dict:
    """Task that fails on specific condition."""
    if job.data.get("should_fail"):
        raise ValueError("Conditional failure")
    return {"processed": job.data}


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def worker_pool():
    """Create worker pool for testing."""
    pool = WorkerPool(num_workers=2, rate_limit=0)  # No rate limit for tests
    yield pool
    pool.shutdown()


# ============================================================================
# Basic Functionality Tests
# ============================================================================

def test_worker_pool_creation():
    """Test creating a worker pool."""
    pool = WorkerPool(num_workers=4, rate_limit=10)

    assert pool.num_workers == 4
    assert pool.rate_limit == 10
    assert pool.stats["jobs_submitted"] == 0

    pool.shutdown()


def test_job_submission(worker_pool):
    """Test submitting jobs to the pool."""
    job = Job(task_func=simple_task, data={"id": 1})

    worker_pool.submit(job)

    assert worker_pool.stats["jobs_submitted"] == 1
    assert worker_pool.job_queue.qsize() == 1


def test_batch_submission(worker_pool):
    """Test submitting multiple jobs at once."""
    jobs = [
        Job(task_func=simple_task, data={"id": i})
        for i in range(10)
    ]

    worker_pool.submit_batch(jobs)

    assert worker_pool.stats["jobs_submitted"] == 10
    assert worker_pool.job_queue.qsize() == 10


def test_single_job_processing(worker_pool):
    """Test processing a single job."""
    job = Job(task_func=simple_task, data={"id": 123})
    worker_pool.submit(job)

    results = worker_pool.run()

    assert len(results) == 1
    assert results[0].success == True
    assert results[0].result["processed"]["id"] == 123


def test_multiple_job_processing(worker_pool):
    """Test processing multiple jobs."""
    jobs = [
        Job(task_func=simple_task, data={"id": i})
        for i in range(20)
    ]
    worker_pool.submit_batch(jobs)

    results = worker_pool.run()

    assert len(results) == 20
    assert all(r.success for r in results)
    assert worker_pool.stats["jobs_completed"] == 20


# ============================================================================
# Parallel Processing Tests
# ============================================================================

def test_parallel_processing():
    """Test that jobs are processed in parallel."""
    pool = WorkerPool(num_workers=4, rate_limit=0)

    # Submit jobs that take 0.1s each
    jobs = [Job(task_func=slow_task, data={"id": i}) for i in range(8)]
    pool.submit_batch(jobs)

    start_time = time.time()
    results = pool.run()
    duration = time.time() - start_time

    # With 4 workers, 8 jobs should take ~0.2s (2 batches)
    # Sequential would take 0.8s
    assert duration < 0.5, f"Took {duration}s, expected parallel execution"
    assert all(r.success for r in results)

    pool.shutdown()


# ============================================================================
# Error Handling Tests
# ============================================================================

def test_job_failure_handling(worker_pool):
    """Test handling of failing jobs."""
    job = Job(task_func=failing_task, data={"id": 1})
    worker_pool.submit(job)

    results = worker_pool.run()

    assert len(results) == 1
    assert results[0].success == False
    assert results[0].error is not None
    assert "Intentional failure" in results[0].error


def test_mixed_success_and_failure(worker_pool):
    """Test processing mix of successful and failing jobs."""
    jobs = [
        Job(task_func=conditional_failing_task, data={"id": i, "should_fail": i % 2 == 0})
        for i in range(10)
    ]
    worker_pool.submit_batch(jobs)

    results = worker_pool.run()

    successful = [r for r in results if r.success]
    failed = [r for r in results if not r.success]

    assert len(successful) == 5  # IDs 1,3,5,7,9
    assert len(failed) == 5      # IDs 0,2,4,6,8


def test_job_retry_on_failure():
    """Test that jobs are retried on failure."""
    pool = WorkerPool(num_workers=1, rate_limit=0)

    # Job that fails with max_retries set
    job = Job(
        task_func=failing_task,
        data={"id": 1},
        max_retries=2
    )
    pool.submit(job)

    results = pool.run()

    # Should have attempted 1 initial + 2 retries = 3 attempts
    # But only one result in the end
    assert len(results) == 1
    assert results[0].success == False

    pool.shutdown()


# ============================================================================
# Rate Limiting Tests
# ============================================================================

def test_rate_limiting():
    """Test that rate limiting is enforced."""
    rate_limit = 10  # 10 requests per second
    pool = WorkerPool(num_workers=1, rate_limit=rate_limit)

    # Submit 5 quick jobs
    jobs = [Job(task_func=simple_task, data={"id": i}) for i in range(5)]
    pool.submit_batch(jobs)

    start_time = time.time()
    results = pool.run()
    duration = time.time() - start_time

    # With rate limit of 10/s, 5 jobs should take ~0.4-0.5s
    expected_min_duration = 4 / rate_limit  # 0.4s
    assert duration >= expected_min_duration, f"Rate limiting not enforced: {duration}s"

    pool.shutdown()


# ============================================================================
# Queue Management Tests
# ============================================================================

def test_queue_size_limit():
    """Test queue size limitation."""
    pool = WorkerPool(num_workers=1, queue_size=5)

    # Submit 5 jobs (should succeed)
    for i in range(5):
        pool.submit(Job(task_func=simple_task, data={"id": i}))

    # 6th job should raise Full exception
    from queue import Full
    with pytest.raises(Full):
        pool.submit(
            Job(task_func=simple_task, data={"id": 6}),
            block=False
        )

    pool.shutdown()


def test_clear_queue(worker_pool):
    """Test clearing the job queue."""
    # Submit jobs
    jobs = [Job(task_func=simple_task, data={"id": i}) for i in range(10)]
    worker_pool.submit_batch(jobs)

    assert worker_pool.job_queue.qsize() == 10

    # Clear queue
    worker_pool.clear_queue()

    assert worker_pool.job_queue.qsize() == 0


# ============================================================================
# Statistics Tests
# ============================================================================

def test_statistics_tracking(worker_pool):
    """Test that statistics are tracked correctly."""
    # Submit and process jobs
    jobs = [
        Job(task_func=conditional_failing_task, data={"id": i, "should_fail": i >= 5})
        for i in range(10)
    ]
    worker_pool.submit_batch(jobs)

    results = worker_pool.run()
    stats = worker_pool.get_stats()

    assert stats["jobs_submitted"] == 10
    assert stats["jobs_completed"] == 5
    assert stats["jobs_failed"] == 5
    assert stats["success_rate"] == 0.5


def test_print_stats(worker_pool, capsys):
    """Test printing statistics."""
    # Process some jobs
    jobs = [Job(task_func=simple_task, data={"id": i}) for i in range(5)]
    worker_pool.submit_batch(jobs)
    worker_pool.run()

    # Print stats
    worker_pool.print_stats()

    captured = capsys.readouterr()
    assert "WORKER POOL STATISTICS" in captured.out
    assert "Jobs Completed: 5" in captured.out


# ============================================================================
# Job Result Tests
# ============================================================================

def test_job_result_contains_timing_info(worker_pool):
    """Test that results include timing information."""
    job = Job(task_func=slow_task, data={"id": 1})
    worker_pool.submit(job)

    results = worker_pool.run()
    result = results[0]

    assert result.started_at is not None
    assert result.completed_at is not None
    assert result.duration_seconds is not None
    assert result.duration_seconds >= 0.1  # Task sleeps for 0.1s


def test_job_result_contains_worker_id(worker_pool):
    """Test that results include worker ID."""
    job = Job(task_func=simple_task, data={"id": 1})
    worker_pool.submit(job)

    results = worker_pool.run()
    result = results[0]

    assert result.worker_id is not None


# ============================================================================
# Shutdown Tests
# ============================================================================

def test_graceful_shutdown():
    """Test graceful shutdown of worker pool."""
    pool = WorkerPool(num_workers=2)

    # Submit jobs
    jobs = [Job(task_func=slow_task, data={"id": i}) for i in range(5)]
    pool.submit_batch(jobs)

    # Start processing
    results = pool.run()

    # Shutdown
    pool.shutdown(wait=True)

    # Should have processed all jobs
    assert len(results) == 5


def test_shutdown_with_timeout():
    """Test shutdown with timeout."""
    pool = WorkerPool(num_workers=1)

    # Submit a long-running job
    def very_slow_task(job):
        time.sleep(10)
        return {}

    pool.submit(Job(task_func=very_slow_task, data={}))

    # Start in background (would need threading for real test)
    # For now, just test that shutdown accepts timeout
    pool.shutdown(wait=False, timeout=1)

    # Pool should be shutdown
    assert pool.executor is None


# ============================================================================
# Integration Tests
# ============================================================================

def test_full_workflow():
    """Test complete workflow from submission to results."""
    pool = WorkerPool(num_workers=4, rate_limit=20)

    # Create varied jobs
    jobs = []
    for i in range(100):
        if i % 10 == 0:
            # Some failing jobs
            job = Job(task_func=failing_task, data={"id": i})
        else:
            # Mostly successful jobs
            job = Job(task_func=simple_task, data={"id": i})
        jobs.append(job)

    # Submit batch
    pool.submit_batch(jobs)

    # Process
    results = pool.run()

    # Verify results
    assert len(results) == 100
    successful = [r for r in results if r.success]
    failed = [r for r in results if not r.success]

    assert len(successful) == 90
    assert len(failed) == 10

    # Check stats
    stats = pool.get_stats()
    assert stats["success_rate"] == 0.9

    # Shutdown
    pool.shutdown()
