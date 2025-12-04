"""
================================================================================
File: congress_error_handler.py
Author: OpenDiscourse Contributors
Created: 2025-12-04
Last Modified: 2025-12-04
Version: 1.0.0

Description:
    Robust error handling system specifically for Congress CLI.
    Handles API errors, database errors, rate limiting, and data quality issues.

Dependencies:
    - logging: Error logging
    - datetime: Timestamp tracking
    - typing: Type hints

Classes:
    - CongressError: Base exception for Congress CLI
    - APIError: API-related errors
    - DatabaseError: Database-related errors
    - DataQualityError: Data validation errors
    - CongressErrorHandler: Centralized error handling

Usage:
    from scripts.ingestion.congress_error_handler import CongressErrorHandler

    handler = CongressErrorHandler()

    try:
        # Ingest data
        ...
    except Exception as e:
        handler.handle_error(e, context={"bill_id": "HR1"})

Changelog:
    2025-12-04: Initial creation

================================================================================
"""

import logging
import traceback
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum
from pathlib import Path


# ============================================================================
# Error Categories
# ============================================================================

class ErrorSeverity(str, Enum):
    """Error severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ErrorCategory(str, Enum):
    """Error categories for Congress CLI."""
    API_ERROR = "api_error"
    DATABASE_ERROR = "database_error"
    DATA_QUALITY = "data_quality"
    RATE_LIMIT = "rate_limit"
    AUTHENTICATION = "authentication"
    NETWORK = "network"
    VALIDATION = "validation"
    DUPLICATE = "duplicate"
    UNKNOWN = "unknown"


# ============================================================================
# Custom Exceptions
# ============================================================================

class CongressError(Exception):
    """Base exception for Congress CLI errors."""

    def __init__(self, message: str, category: ErrorCategory = ErrorCategory.UNKNOWN):
        self.message = message
        self.category = category
        self.timestamp = datetime.now()
        super().__init__(self.message)


class APIError(CongressError):
    """API-related errors."""

    def __init__(self, message: str, status_code: Optional[int] = None, endpoint: Optional[str] = None):
        super().__init__(message, ErrorCategory.API_ERROR)
        self.status_code = status_code
        self.endpoint = endpoint


class DatabaseError(CongressError):
    """Database-related errors."""

    def __init__(self, message: str, query: Optional[str] = None):
        super().__init__(message, ErrorCategory.DATABASE_ERROR)
        self.query = query


class DataQualityError(CongressError):
    """Data validation and quality errors."""

    def __init__(self, message: str, record_id: Optional[str] = None, field: Optional[str] = None):
        super().__init__(message, ErrorCategory.DATA_QUALITY)
        self.record_id = record_id
        self.field = field


class RateLimitError(CongressError):
    """Rate limit exceeded errors."""

    def __init__(self, message: str, retry_after: Optional[int] = None):
        super().__init__(message, ErrorCategory.RATE_LIMIT)
        self.retry_after = retry_after


class DuplicateRecordError(CongressError):
    """Duplicate record detected."""

    def __init__(self, message: str, record_id: str, fingerprint: Optional[str] = None):
        super().__init__(message, ErrorCategory.DUPLICATE)
        self.record_id = record_id
        self.fingerprint = fingerprint


# ============================================================================
# Error Handler
# ============================================================================

class CongressErrorHandler:
    """
    Centralized error handling for Congress CLI.

    Provides error logging, categorization, recovery strategies,
    and reporting capabilities.

    Attributes:
        logger: Logger instance
        error_log: List of errors encountered
        error_counts: Dictionary of error counts by category

    Methods:
        handle_error: Process and log an error
        get_error_summary: Get summary of errors
        clear_errors: Clear error log
        export_error_log: Export errors to file
    """

    def __init__(self, log_file: Optional[Path] = None):
        """
        Initialize error handler.

        Args:
            log_file: Optional file path for error logging
        """
        # Setup logging
        self.logger = logging.getLogger("CongressErrorHandler")

        # Configure file handler if provided
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.ERROR)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

        # Error tracking
        self.error_log: list[Dict[str, Any]] = []
        self.error_counts: Dict[ErrorCategory, int] = {
            cat: 0 for cat in ErrorCategory
        }

        self.logger.info("Congress error handler initialized")

    # ========================================================================
    # Error Handling
    # ========================================================================

    def handle_error(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        recoverable: bool = False
    ) -> Dict[str, Any]:
        """
        Handle an error with proper logging and categorization.

        Args:
            error: Exception that occurred
            context: Additional context (bill_id, congress, etc.)
            severity: Error severity level
            recoverable: Whether error is recoverable

        Returns:
            Dictionary with error details

        Example:
            >>> try:
            >>>     api_call()
            >>> except Exception as e:
            >>>     handler.handle_error(e, context={"bill_id": "HR1"})
        """
        # Determine error category
        category = self._categorize_error(error)

        # Create error record
        error_record = {
            "timestamp": datetime.now().isoformat(),
            "category": category.value,
            "severity": severity.value,
            "message": str(error),
            "type": type(error).__name__,
            "recoverable": recoverable,
            "context": context or {},
            "traceback": traceback.format_exc()
        }

        # Add category-specific details
        if isinstance(error, APIError):
            error_record["api_status_code"] = error.status_code
            error_record["api_endpoint"] = error.endpoint
        elif isinstance(error, DatabaseError):
            error_record["sql_query"] = error.query
        elif isinstance(error, DataQualityError):
            error_record["record_id"] = error.record_id
            error_record["field"] = error.field
        elif isinstance(error, RateLimitError):
            error_record["retry_after"] = error.retry_after
        elif isinstance(error, DuplicateRecordError):
            error_record["record_id"] = error.record_id
            error_record["fingerprint"] = error.fingerprint

        # Log error
        self._log_error(error_record)

        # Update tracking
        self.error_log.append(error_record)
        self.error_counts[category] += 1

        return error_record

    def _categorize_error(self, error: Exception) -> ErrorCategory:
        """
        Categorize an error.

        Args:
            error: Exception to categorize

        Returns:
            ErrorCategory
        """
        if isinstance(error, CongressError):
            return error.category

        # Categorize by error type
        error_type = type(error).__name__
        error_msg = str(error).lower()

        # API errors
        if "api" in error_msg or "request" in error_msg or "http" in error_msg:
            return ErrorCategory.API_ERROR

        # Database errors
        if "database" in error_msg or "sql" in error_msg or "psycopg2" in error_msg:
            return ErrorCategory.DATABASE_ERROR

        # Network errors
        if "connection" in error_msg or "timeout" in error_msg or "network" in error_msg:
            return ErrorCategory.NETWORK

        # Rate limit
        if "rate" in error_msg or "429" in error_msg:
            return ErrorCategory.RATE_LIMIT

        # Authentication
        if "auth" in error_msg or "401" in error_msg or "403" in error_msg:
            return ErrorCategory.AUTHENTICATION

        # Validation
        if "validation" in error_msg or "invalid" in error_msg:
            return ErrorCategory.VALIDATION

        return ErrorCategory.UNKNOWN

    def _log_error(self, error_record: Dict[str, Any]):
        """
        Log error to logger.

        Args:
            error_record: Error record to log
        """
        severity = error_record["severity"]
        message = (
            f"[{error_record['category']}] {error_record['message']} "
            f"(Context: {error_record['context']})"
        )

        if severity == ErrorSeverity.CRITICAL.value:
            self.logger.critical(message)
        elif severity == ErrorSeverity.ERROR.value:
            self.logger.error(message)
        elif severity == ErrorSeverity.WARNING.value:
            self.logger.warning(message)
        else:
            self.logger.info(message)

    # ========================================================================
    # Error Reporting
    # ========================================================================

    def get_error_summary(self) -> Dict[str, Any]:
        """
        Get summary of errors encountered.

        Returns:
            Dictionary with error statistics
        """
        total_errors = len(self.error_log)

        # Count by severity
        severity_counts = {}
        for record in self.error_log:
            sev = record["severity"]
            severity_counts[sev] = severity_counts.get(sev, 0) + 1

        # Recent errors (last 10)
        recent_errors = self.error_log[-10:] if self.error_log else []

        return {
            "total_errors": total_errors,
            "by_category": {cat.value: count for cat, count in self.error_counts.items()},
            "by_severity": severity_counts,
            "recent_errors": recent_errors
        }

    def print_error_summary(self):
        """Print formatted error summary."""
        summary = self.get_error_summary()

        print("\n" + "=" * 70)
        print("CONGRESS CLI ERROR SUMMARY")
        print("=" * 70)
        print(f"\nTotal Errors: {summary['total_errors']}")

        print("\nBy Category:")
        for cat, count in summary['by_category'].items():
            if count > 0:
                print(f"  {cat}: {count}")

        print("\nBy Severity:")
        for sev, count in summary['by_severity'].items():
            print(f"  {sev}: {count}")

        if summary['recent_errors']:
            print("\nRecent Errors (last 10):")
            for err in summary['recent_errors'][-5:]:  # Show last 5
                print(f"  [{err['category']}] {err['message'][:80]}")

        print("=" * 70 + "\n")

    def clear_errors(self):
        """Clear error log and reset counts."""
        self.error_log.clear()
        self.error_counts = {cat: 0 for cat in ErrorCategory}
        self.logger.info("Error log cleared")

    def export_error_log(self, filepath: Path):
        """
        Export error log to JSON file.

        Args:
            filepath: Path to export file
        """
        import json

        with open(filepath, 'w') as f:
            json.dump(self.error_log, f, indent=2)

        self.logger.info(f"Error log exported to {filepath}")


# ============================================================================
# Context Manager
# ============================================================================

class error_context:
    """
    Context manager for handling errors in a specific context.

    Usage:
        with error_context(handler, {"bill_id": "HR1"}) as ctx:
            # Code that might raise errors
            ...
    """

    def __init__(
        self,
        handler: CongressErrorHandler,
        context: Dict[str, Any],
        reraise: bool = False
    ):
        self.handler = handler
        self.context = context
        self.reraise = reraise

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_val:
            self.handler.handle_error(exc_val, context=self.context)
            return not self.reraise  # Suppress if not reraising
        return True


# ============================================================================
# Module Exports
# ============================================================================

__all__ = [
    'CongressError',
    'APIError',
    'DatabaseError',
    'DataQualityError',
    'RateLimitError',
    'DuplicateRecordError',
    'CongressErrorHandler',
    'ErrorCategory',
    'ErrorSeverity',
    'error_context',
]
