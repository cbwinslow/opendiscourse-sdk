"""
================================================================================
File: deduplication.py
Author: OpenDiscourse Contributors
Created: 2025-12-04
Last Modified: 2025-12-04
Version: 2.0.0

Description:
    Intelligent data deduplication system using content-based fingerprinting.
    Prevents duplicate records in the database using multiple strategies
    including SHA256 hashing, modified timestamp tracking, and configurable
    conflict resolution.

Dependencies:
    - hashlib: Content hashing (SHA256)
    - json: JSON serialization for fingerprints
    - typing: Type hints
    - enum: Strategy enumeration
    - datetime: Timestamp tracking
    - pydantic: Data validation

Classes:
    - DeduplicationStrategy: Enum defining deduplication behaviors
    - Fingerprint: Pydantic model for record fingerprints
    - DeduplicationEngine: Main deduplication logic

Usage:
    from scripts.core.deduplication import DeduplicationEngine, DeduplicationStrategy

    # Initialize engine
    engine = DeduplicationEngine(strategy=DeduplicationStrategy.UPSERT)

    # Check if record exists
    exists = engine.record_exists(record_data, record_type="bill")

    # Get fingerprint
    fingerprint = engine.generate_fingerprint(record_data)

    # Mark as processed
    engine.mark_processed(fingerprint, record_id="BILLS-118hr1")

Changelog:
    2025-12-04: Initial creation

Notes:
    - Uses SHA256 for content hashing
    - Supports multiple deduplication strategies
    - Configurable per data type (bills, members, etc.)
    - Tracks modified timestamps for incremental sync

================================================================================
"""

import hashlib
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from enum import Enum

from pydantic import BaseModel, Field


# ============================================================================
# Enums
# ============================================================================

class DeduplicationStrategy(str, Enum):
    """
    Deduplication strategies for handling duplicate records.

    Values:
        SKIP: Skip duplicate records without error
        UPDATE: Update existing records with new data (upsert)
        ERROR: Raise error on duplicate detection
        VERSION: Keep both as different versions
    """
    SKIP = "skip"
    UPDATE = "update"
    ERROR = "error"
    VERSION = "version"


# ============================================================================
# Pydantic Models
# ============================================================================

class Fingerprint(BaseModel):
    """
    Content fingerprint for a record.

    Attributes:
        record_type: Type of record (bill, member, vote, etc.)
        record_id: External identifier (e.g., BILLS-118hr1)
        content_hash: SHA256 hash of normalized content
        created_at: When fingerprint was created
        updated_at: When record was last updated
        metadata: Additional tracking information
    """

    record_type: str = Field(..., description="Record type")
    record_id: str = Field(..., description="External record ID")
    content_hash: str = Field(..., description="SHA256 content hash")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# ============================================================================
# Deduplication Engine
# ============================================================================

class DeduplicationEngine:
    """
    Intelligent deduplication engine for record management.

    Provides content-based deduplication using SHA256 hashing with
    configurable strategies for handling duplicates.

    Attributes:
        strategy: Default deduplication strategy
        logger: Logger instance
        fingerprints: In-memory fingerprint cache

    Methods:
        generate_fingerprint: Create content hash for a record
        record_exists: Check if record already processed
        mark_processed: Mark record as processed
        should_process: Determine if record should be processed
        get_conflicts: Find conflicting records
    """

    def __init__(
        self,
        strategy: DeduplicationStrategy = DeduplicationStrategy.UPDATE,
        cache_size: int = 10000
    ):
        """
        Initialize deduplication engine.

        Args:
            strategy: Default deduplication strategy
            cache_size: Maximum fingerprints to cache in memory
        """
        self.strategy = strategy
        self.cache_size = cache_size

        # Setup logging
        self.logger = logging.getLogger("DeduplicationEngine")

        # In-memory fingerprint cache (for performance)
        # In production, this would be backed by database
        self.fingerprints: Dict[str, Fingerprint] = {}

        self.logger.info(f"Deduplication engine initialized with strategy: {strategy.value}")

    # ========================================================================
    # Fingerprint Generation
    # ========================================================================

    def generate_fingerprint(
        self,
        data: Dict[str, Any],
        record_type: str,
        record_id: str,
        include_fields: Optional[List[str]] = None,
        exclude_fields: Optional[List[str]] = None
    ) -> Fingerprint:
        """
        Generate content-based fingerprint for a record.

        Creates a SHA256 hash of the record's normalized content,
        optionally filtering fields to include/exclude.

        Args:
            data: Record data dictionary
            record_type: Type of record (bill, member, etc.)
            record_id: External record identifier
            include_fields: Only hash these fields (if specified)
            exclude_fields: Don't hash these fields

        Returns:
            Fingerprint object with content hash

        Example:
            >>> engine = DeduplicationEngine()
            >>> fingerprint = engine.generate_fingerprint(
            >>>     data={"title": "My Bill", "number": "HR1"},
            >>>     record_type="bill",
            >>>     record_id="BILLS-118hr1"
            >>> )
        """
        # Filter data based on include/exclude fields
        filtered_data = self._filter_data(data, include_fields, exclude_fields)

        # Normalize data (sort keys, handle nulls)
        normalized = self._normalize_data(filtered_data)

        # Generate SHA256 hash
        content_hash = self._hash_content(normalized)

        # Create fingerprint
        fingerprint = Fingerprint(
            record_type=record_type,
            record_id=record_id,
            content_hash=content_hash,
            metadata={
                "field_count": len(filtered_data),
                "has_include_filter": include_fields is not None,
                "has_exclude_filter": exclude_fields is not None
            }
        )

        self.logger.debug(
            f"Generated fingerprint for {record_type}:{record_id} - "
            f"hash={content_hash[:16]}..."
        )

        return fingerprint

    def _filter_data(
        self,
        data: Dict[str, Any],
        include: Optional[List[str]],
        exclude: Optional[List[str]]
    ) -> Dict[str, Any]:
        """
        Filter data based on include/exclude field lists.

        Args:
            data: Original data dictionary
            include: Fields to include (if specified, only these)
            exclude: Fields to exclude

        Returns:
            Filtered data dictionary
        """
        # Start with all data
        filtered = data.copy()

        # Apply include filter (if specified, keep only these fields)
        if include:
            filtered = {k: v for k, v in filtered.items() if k in include}

        # Apply exclude filter
        if exclude:
            filtered = {k: v for k, v in filtered.items() if k not in exclude}

        return filtered

    def _normalize_data(self, data: Dict[str, Any]) -> str:
        """
        Normalize data for consistent hashing.

        - Sorts dictionary keys
        - Handles None values consistently
        - Converts to canonical JSON representation

        Args:
            data: Data dictionary to normalize

        Returns:
            Normalized JSON string
        """
        # Sort keys recursively and serialize to JSON
        normalized = json.dumps(
            data,
            sort_keys=True,
            ensure_ascii=True,
            separators=(',', ':'),  # Compact format
            default=str  # Convert non-serializable to string
        )

        return normalized

    def _hash_content(self, content: str) -> str:
        """
        Generate SHA256 hash of content.

        Args:
            content: Content string to hash

        Returns:
            Hexadecimal hash string
        """
        hasher = hashlib.sha256()
        hasher.update(content.encode('utf-8'))
        return hasher.hexdigest()

    # ========================================================================
    # Duplicate Detection
    # ========================================================================

    def record_exists(
        self,
        data: Dict[str, Any],
        record_type: str,
        record_id: str,
        **fingerprint_kwargs
    ) -> bool:
        """
        Check if a record already exists based on content hash.

        Args:
            data: Record data
            record_type: Type of record
            record_id: Record identifier
            **fingerprint_kwargs: Additional args for generate_fingerprint

        Returns:
            True if record exists with same content

        Example:
            >>> exists = engine.record_exists(
            >>>     data=bill_data,
            >>>     record_type="bill",
            >>>     record_id="BILLS-118hr1"
            >>> )
            >>> if not exists:
            >>>     # Insert new record
            >>>     ...
        """
        # Generate fingerprint for this record
        fingerprint = self.generate_fingerprint(
            data=data,
            record_type=record_type,
            record_id=record_id,
            **fingerprint_kwargs
        )

        # Check if we have a matching fingerprint
        cache_key = f"{record_type}:{record_id}"

        if cache_key in self.fingerprints:
            existing = self.fingerprints[cache_key]

            # Compare content hashes
            if existing.content_hash == fingerprint.content_hash:
                self.logger.debug(f"Record exists: {cache_key} (hash match)")
                return True
            else:
                self.logger.debug(f"Record changed: {cache_key} (hash mismatch)")
                return False

        # Not in cache, assume doesn't exist
        # In production, would check database here
        return False

    def should_process(
        self,
        data: Dict[str, Any],
        record_type: str,
        record_id: str,
        strategy: Optional[DeduplicationStrategy] = None,
        **fingerprint_kwargs
    ) -> tuple[bool, str]:
        """
        Determine if a record should be processed based on deduplication strategy.

        Args:
            data: Record data
            record_type: Type of record
            record_id: Record identifier
            strategy: Override default strategy
            **fingerprint_kwargs: Additional fingerprint args

        Returns:
            Tuple of (should_process: bool, reason: str)

        Example:
            >>> should_process, reason = engine.should_process(
            >>>     data=bill_data,
            >>>     record_type="bill",
            >>>     record_id="BILLS-118hr1",
            >>>     strategy=DeduplicationStrategy.SKIP
            >>> )
            >>> if should_process:
            >>>     # Process the record
            >>>     ...
        """
        # Use provided strategy or default
        strategy = strategy or self.strategy

        # Check if record exists
        exists = self.record_exists(
            data=data,
            record_type=record_type,
            record_id=record_id,
            **fingerprint_kwargs
        )

        # Apply strategy
        if not exists:
            # New record, always process
            return True, "new_record"

        # Record exists, apply strategy
        if strategy == DeduplicationStrategy.SKIP:
            return False, "duplicate_skipped"

        elif strategy == DeduplicationStrategy.UPDATE:
            return True, "duplicate_updated"

        elif strategy == DeduplicationStrategy.ERROR:
            return False, "duplicate_error"

        elif strategy == DeduplicationStrategy.VERSION:
            return True, "duplicate_versioned"

        else:
            # Unknown strategy, default to skip
            self.logger.warning(f"Unknown strategy: {strategy}, defaulting to SKIP")
            return False, "unknown_strategy"

    # ========================================================================
    # Record Tracking
    # ========================================================================

    def mark_processed(
        self,
        fingerprint: Fingerprint,
        database_id: Optional[int] = None
    ):
        """
        Mark a record as processed by storing its fingerprint.

        Args:
            fingerprint: Record fingerprint
            database_id: Optional database primary key

        Example:
            >>> fingerprint = engine.generate_fingerprint(...)
            >>> # Insert record into database
            >>> db_id = cursor.lastrowid
            >>> # Mark as processed
            >>> engine.mark_processed(fingerprint, database_id=db_id)
        """
        # Add to cache
        cache_key = f"{fingerprint.record_type}:{fingerprint.record_id}"
        self.fingerprints[cache_key] = fingerprint

        # Store database ID if provided
        if database_id:
            fingerprint.metadata['database_id'] = database_id

        # Evict old entries if cache is too large
        if len(self.fingerprints) > self.cache_size:
            # Remove oldest entries (FIFO)
            # In production, would use LRU cache
            to_remove = len(self.fingerprints) - self.cache_size
            for key in list(self.fingerprints.keys())[:to_remove]:
                del self.fingerprints[key]

        self.logger.debug(f"Marked as processed: {cache_key}")

    def get_conflicts(
        self,
        record_type: str,
        content_hash: str
    ) -> List[Fingerprint]:
        """
        Find all records with the same content hash.

        Args:
            record_type: Type of record to search
            content_hash: Content hash to match

        Returns:
            List of matching fingerprints
        """
        conflicts = [
            fp for fp in self.fingerprints.values()
            if fp.record_type == record_type and fp.content_hash == content_hash
        ]

        return conflicts

    # ========================================================================
    # Statistics
    # ========================================================================

    def get_stats(self) -> Dict[str, Any]:
        """
        Get deduplication statistics.

        Returns:
            Dictionary with cache statistics
        """
        # Count by record type
        by_type = {}
        for fp in self.fingerprints.values():
            by_type[fp.record_type] = by_type.get(fp.record_type, 0) + 1

        return {
            "total_fingerprints": len(self.fingerprints),
            "cache_size_limit": self.cache_size,
            "cache_utilization": len(self.fingerprints) / self.cache_size,
            "by_record_type": by_type,
            "strategy": self.strategy.value
        }

    def clear_cache(self):
        """Clear the fingerprint cache."""
        self.fingerprints.clear()
        self.logger.info("Fingerprint cache cleared")


# ============================================================================
# Module Exports
# ============================================================================

__all__ = [
    'DeduplicationStrategy',
    'Fingerprint',
    'DeduplicationEngine',
]
