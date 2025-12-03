"""Basic data validation helpers for ingestion."""

from typing import Any, Dict, Iterable

REQUIRED_FIELDS = {"id", "source", "content"}


def validate_record(record: Dict[str, Any]) -> bool:
    """Validate a single ingestion record.

    Ensures all required fields exist and are non-empty.
    """
    missing = [field for field in REQUIRED_FIELDS if not record.get(field)]
    if missing:
        return False
    return True


def validate_records(records: Iterable[Dict[str, Any]]) -> bool:
    """Validate multiple records."""
    return all(validate_record(rec) for rec in records)
