"""
================================================================================
File: test_deduplication.py
Author: OpenDiscourse Contributors
Created: 2025-12-04
Last Modified: 2025-12-04
Version: 1.0.0

Description:
    Comprehensive unit tests for the deduplication system.
    Tests fingerprint generation, duplicate detection, and all
    deduplication strategies.

Dependencies:
    - pytest: Testing framework
    - scripts.core.deduplication: Module under test

Test Coverage:
    - Fingerprint generation
    - Content hashing consistency
    - Duplicate detection
    - All deduplication strategies
    - Cache management
    - Statistics tracking

Usage:
    # Run all tests
    pytest tests/unit/test_deduplication.py

    # Run with coverage
    pytest --cov=scripts.core.deduplication tests/unit/test_deduplication.py

    # Run specific test
    pytest tests/unit/test_deduplication.py::test_fingerprint_generation

================================================================================
"""

import pytest
from datetime import datetime
from scripts.core.deduplication import (
    DeduplicationEngine,
    DeduplicationStrategy,
    Fingerprint
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def engine():
    """Create a fresh deduplication engine for each test."""
    return DeduplicationEngine(strategy=DeduplicationStrategy.UPDATE)


@pytest.fixture
def sample_bill_data():
    """Sample bill data for testing."""
    return {
        "congress": 118,
        "type": "hr",
        "number": 1,
        "title": "Test Bill for Healthcare",
        "introduced_date": "2023-01-01",
        "sponsor": {
            "name": "John Doe",
            "party": "D"
        }
    }


# ============================================================================
# Fingerprint Generation Tests
# ============================================================================

def test_fingerprint_generation(engine, sample_bill_data):
    """Test basic fingerprint generation."""
    fingerprint = engine.generate_fingerprint(
        data=sample_bill_data,
        record_type="bill",
        record_id="BILLS-118hr1"
    )

    assert isinstance(fingerprint, Fingerprint)
    assert fingerprint.record_type == "bill"
    assert fingerprint.record_id == "BILLS-118hr1"
    assert len(fingerprint.content_hash) == 64  # SHA256 length
    assert isinstance(fingerprint.created_at, datetime)


def test_fingerprint_consistency(engine, sample_bill_data):
    """Test that same data produces same hash."""
    fp1 = engine.generate_fingerprint(
        data=sample_bill_data,
        record_type="bill",
        record_id="BILLS-118hr1"
    )

    fp2 = engine.generate_fingerprint(
        data=sample_bill_data,
        record_type="bill",
        record_id="BILLS-118hr1"
    )

    assert fp1.content_hash == fp2.content_hash


def test_fingerprint_different_data(engine, sample_bill_data):
    """Test that different data produces different hash."""
    fp1 = engine.generate_fingerprint(
        data=sample_bill_data,
        record_type="bill",
        record_id="BILLS-118hr1"
    )

    # Modify data
    modified_data = sample_bill_data.copy()
    modified_data["title"] = "Different Title"

    fp2 = engine.generate_fingerprint(
        data=modified_data,
        record_type="bill",
        record_id="BILLS-118hr1"
    )

    assert fp1.content_hash != fp2.content_hash


def test_fingerprint_with_include_fields(engine, sample_bill_data):
    """Test fingerprint with field filtering."""
    # Only hash title field
    fp = engine.generate_fingerprint(
        data=sample_bill_data,
        record_type="bill",
        record_id="BILLS-118hr1",
        include_fields=["title"]
    )

    assert fp.metadata["has_include_filter"] == True
    assert fp.metadata["field_count"] == 1


def test_fingerprint_with_exclude_fields(engine, sample_bill_data):
    """Test fingerprint with field exclusion."""
    # Hash everything except sponsor
    fp = engine.generate_fingerprint(
        data=sample_bill_data,
        record_type="bill",
        record_id="BILLS-118hr1",
        exclude_fields=["sponsor"]
    )

    assert fp.metadata["has_exclude_filter"] == True
    # Should have all fields except sponsor
    assert fp.metadata["field_count"] == len(sample_bill_data) - 1


# ============================================================================
# Duplicate Detection Tests
# ============================================================================

def test_record_does_not_exist_initially(engine, sample_bill_data):
    """Test that new records don't exist."""
    exists = engine.record_exists(
        data=sample_bill_data,
        record_type="bill",
        record_id="BILLS-118hr1"
    )

    assert exists == False


def test_record_exists_after_marking(engine, sample_bill_data):
    """Test that marked records are detected as existing."""
    # Generate and mark fingerprint
    fp = engine.generate_fingerprint(
        data=sample_bill_data,
        record_type="bill",
        record_id="BILLS-118hr1"
    )
    engine.mark_processed(fp)

    # Check existence
    exists = engine.record_exists(
        data=sample_bill_data,
        record_type="bill",
        record_id="BILLS-118hr1"
    )

    assert exists == True


def test_modified_record_not_considered_duplicate(engine, sample_bill_data):
    """Test that modified records aren't considered duplicates."""
    # Mark original
    fp = engine.generate_fingerprint(
        data=sample_bill_data,
        record_type="bill",
        record_id="BILLS-118hr1"
    )
    engine.mark_processed(fp)

    # Modify data
    modified_data = sample_bill_data.copy()
    modified_data["title"] = "Updated Title"

    # Check - should not exist (content changed)
    exists = engine.record_exists(
        data=modified_data,
        record_type="bill",
        record_id="BILLS-118hr1"
    )

    assert exists == False


# ============================================================================
# Strategy Tests
# ============================================================================

def test_strategy_skip_new_record(engine, sample_bill_data):
    """Test SKIP strategy with new record."""
    should_process, reason = engine.should_process(
        data=sample_bill_data,
        record_type="bill",
        record_id="BILLS-118hr1",
        strategy=DeduplicationStrategy.SKIP
    )

    assert should_process == True
    assert reason == "new_record"


def test_strategy_skip_duplicate_record(engine, sample_bill_data):
    """Test SKIP strategy with duplicate record."""
    # Mark as processed
    fp = engine.generate_fingerprint(sample_bill_data, "bill", "BILLS-118hr1")
    engine.mark_processed(fp)

    # Check again
    should_process, reason = engine.should_process(
        data=sample_bill_data,
        record_type="bill",
        record_id="BILLS-118hr1",
        strategy=DeduplicationStrategy.SKIP
    )

    assert should_process == False
    assert reason == "duplicate_skipped"


def test_strategy_update_duplicate_record(engine, sample_bill_data):
    """Test UPDATE strategy with duplicate record."""
    # Mark as processed
    fp = engine.generate_fingerprint(sample_bill_data, "bill", "BILLS-118hr1")
    engine.mark_processed(fp)

    # Check with UPDATE strategy
    should_process, reason = engine.should_process(
        data=sample_bill_data,
        record_type="bill",
        record_id="BILLS-118hr1",
        strategy=DeduplicationStrategy.UPDATE
    )

    assert should_process == True
    assert reason == "duplicate_updated"


def test_strategy_error_duplicate_record(engine, sample_bill_data):
    """Test ERROR strategy with duplicate record."""
    # Mark as processed
    fp = engine.generate_fingerprint(sample_bill_data, "bill", "BILLS-118hr1")
    engine.mark_processed(fp)

    # Check with ERROR strategy
    should_process, reason = engine.should_process(
        data=sample_bill_data,
        record_type="bill",
        record_id="BILLS-118hr1",
        strategy=DeduplicationStrategy.ERROR
    )

    assert should_process == False
    assert reason == "duplicate_error"


def test_strategy_version_duplicate_record(engine, sample_bill_data):
    """Test VERSION strategy with duplicate record."""
    # Mark as processed
    fp = engine.generate_fingerprint(sample_bill_data, "bill", "BILLS-118hr1")
    engine.mark_processed(fp)

    # Check with VERSION strategy
    should_process, reason = engine.should_process(
        data=sample_bill_data,
        record_type="bill",
        record_id="BILLS-118hr1",
        strategy=DeduplicationStrategy.VERSION
    )

    assert should_process == True
    assert reason == "duplicate_versioned"


# ============================================================================
# Cache Management Tests
# ============================================================================

def test_cache_stores_fingerprints(engine, sample_bill_data):
    """Test that cache stores fingerprints."""
    assert len(engine.fingerprints) == 0

    fp = engine.generate_fingerprint(sample_bill_data, "bill", "BILLS-118hr1")
    engine.mark_processed(fp)

    assert len(engine.fingerprints) == 1
    assert "bill:BILLS-118hr1" in engine.fingerprints


def test_cache_eviction(sample_bill_data):
    """Test that cache evicts old entries when full."""
    # Create engine with small cache
    engine = DeduplicationEngine(cache_size=2)

    # Add 3 fingerprints
    for i in range(3):
        fp = engine.generate_fingerprint(
            data=sample_bill_data,
            record_type="bill",
            record_id=f"BILLS-118hr{i}"
        )
        engine.mark_processed(fp)

    # Should only have 2 (cache size limit)
    assert len(engine.fingerprints) == 2


def test_clear_cache(engine, sample_bill_data):
    """Test cache clearing."""
    fp = engine.generate_fingerprint(sample_bill_data, "bill", "BILLS-118hr1")
    engine.mark_processed(fp)

    assert len(engine.fingerprints) > 0

    engine.clear_cache()

    assert len(engine.fingerprints) == 0


# ============================================================================
# Statistics Tests
# ============================================================================

def test_get_stats_empty(engine):
    """Test stats for empty engine."""
    stats = engine.get_stats()

    assert stats["total_fingerprints"] == 0
    assert stats["cache_utilization"] == 0
    assert stats["by_record_type"] == {}
    assert stats["strategy"] == "update"


def test_get_stats_with_data(engine, sample_bill_data):
    """Test stats with data."""
    # Add some fingerprints
    for i in range(5):
        fp = engine.generate_fingerprint(
            data=sample_bill_data,
            record_type="bill",
            record_id=f"BILLS-118hr{i}"
        )
        engine.mark_processed(fp)

    stats = engine.get_stats()

    assert stats["total_fingerprints"] == 5
    assert stats["by_record_type"]["bill"] == 5
    assert stats["cache_utilization"] > 0


# ============================================================================
# Conflict Detection Tests
# ============================================================================

def test_get_conflicts_none(engine, sample_bill_data):
    """Test getting conflicts when none exist."""
    fp = engine.generate_fingerprint(sample_bill_data, "bill", "BILLS-118hr1")

    conflicts = engine.get_conflicts("bill", fp.content_hash)

    assert len(conflicts) == 0


def test_get_conflicts_found(engine, sample_bill_data):
    """Test finding conflicts."""
    # Add a fingerprint
    fp = engine.generate_fingerprint(sample_bill_data, "bill", "BILLS-118hr1")
    engine.mark_processed(fp)

    # Search for conflicts
    conflicts = engine.get_conflicts("bill", fp.content_hash)

    assert len(conflicts) == 1
    assert conflicts[0].record_id == "BILLS-118hr1"


# ============================================================================
# Integration Tests
# ============================================================================

def test_full_workflow(engine, sample_bill_data):
    """Test complete deduplication workflow."""
    record_id = "BILLS-118hr1"

    # 1. Check if exists (should not)
    exists = engine.record_exists(sample_bill_data, "bill", record_id)
    assert exists == False

    # 2. Should process (new record)
    should_process, reason = engine.should_process(
        sample_bill_data, "bill", record_id
    )
    assert should_process == True
    assert reason == "new_record"

    # 3. Generate fingerprint and mark as processed
    fp = engine.generate_fingerprint(sample_bill_data, "bill", record_id)
    engine.mark_processed(fp, database_id=12345)

    # 4. Check again (should exist now)
    exists = engine.record_exists(sample_bill_data, "bill", record_id)
    assert exists == True

    # 5. Should still process with UPDATE strategy
    should_process, reason = engine.should_process(
        sample_bill_data,
        "bill",
        record_id,
        strategy=DeduplicationStrategy.UPDATE
    )
    assert should_process == True
    assert reason == "duplicate_updated"

    # 6. Should not process with SKIP strategy
    should_process, reason = engine.should_process(
        sample_bill_data,
        "bill",
        record_id,
        strategy=DeduplicationStrategy.SKIP
    )
    assert should_process == False
    assert reason == "duplicate_skipped"
