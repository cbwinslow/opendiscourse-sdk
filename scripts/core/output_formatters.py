"""
================================================================================
File: output_formatters.py
Author: OpenDiscourse Contributors
Created: 2025-12-04
Last Modified: 2025-12-04
Version: 2.0.0

Description:
    Flexible output formatters for exporting data in multiple formats.
    Supports JSON, JSONL, CSV, Parquet, SQLite with configurable
    destinations (stdout, file, database) and compression.

Dependencies:
    - json: JSON serialization
    - csv: CSV writing
    - pandas: DataFrame operations (optional for Parquet)
    - pyarrow: Parquet support (optional)
    - gzip: Compression
    - typing: Type hints

Classes:
    - OutputFormat: Enum for available formats
    - OutputDestination: Enum for output locations
    - Formatter: Base formatter class
    - JSONFormatter: JSON output
    - JSONLFormatter: Line-delimited JSON
    - CSVFormatter: CSV output
    - ParquetFormatter: Parquet output
    - SQLiteFormatter: SQLite database export

Usage:
    from scripts.core.output_formatters import FormatterFactory, OutputFormat

    # Create CSV formatter
    formatter = FormatterFactory.create(
        format=OutputFormat.CSV,
        destination="data/bills.csv",
        compress=True
    )

    # Write data
    formatter.write(bills_data)

Changelog:
    2025-12-04: Initial creation

Notes:
    - Pandas/PyArrow are optional for Parquet support
    - Automatic compression based on file extension or flag
    - Streaming support for large datasets
================================================================================
"""

import json
import csv
import gzip
import logging
import sqlite3
from enum import Enum
from pathlib import Path
from typing import List, Dict, Any, Optional, Union, TextIO
from abc import ABC, abstractmethod

# Optional imports
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

try:
    import pyarrow as pa
    import pyarrow.parquet as pq
    PYARROW_AVAILABLE = True
except ImportError:
    PYARROW_AVAILABLE = False


# ============================================================================
# Enums
# ============================================================================

class OutputFormat(str, Enum):
    """
    Supported output formats.

    Values:
        JSON: Standard JSON array
        JSONL: Line-delimited JSON (one object per line)
        CSV: Comma-separated values
        PARQUET: Apache Parquet columnar format
        SQLITE: SQLite database file
    """
    JSON = "json"
    JSONL = "jsonl"
    CSV = "csv"
    PARQUET = "parquet"
    SQLITE = "sqlite"


class CompressionType(str, Enum):
    """
    Compression types.

    Values:
        NONE: No compression
        GZIP: Gzip compression
        BROTLI: Brotli compression (if available)
    """
    NONE = "none"
    GZIP = "gzip"
    BROTLI = "brotli"


# ============================================================================
# Base Formatter
# ============================================================================

class Formatter(ABC):
    """
    Abstract base class for formatters.

    Defines interface for writing data in various formats.
    """

    def __init__(
        self,
        destination: Union[str, Path, TextIO] = None,
        compress: bool = False,
        **options
    ):
        """
        Initialize formatter.

        Args:
            destination: Output destination (file path or stream)
            compress: Enable gzip compression
            **options: Format-specific options
        """
        self.destination = destination
        self.compress = compress
        self.options = options
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def write(self, data: List[Dict[str, Any]]):
        """Write data in the specified format."""
        pass

    @abstractmethod
    def write_batch(self, data: List[Dict[str, Any]]):
        """Write data in batches for streaming."""
        pass


# ============================================================================
# JSON Formatter
# ============================================================================

class JSONFormatter(Formatter):
    """
    JSON array formatter.

    Outputs data as a JSON array. Good for small-medium datasets.
    """

    def write(self, data: List[Dict[str, Any]]):
        """
        Write data as JSON array.

        Args:
            data: List of dictionaries to write
        """
        json_data = json.dumps(
            data,
            indent=self.options.get('indent', 2),
            ensure_ascii=self.options.get('ensure_ascii', False),
            default=str  # Handle non-serializable types
        )

        self._write_content(json_data)

    def write_batch(self, data: List[Dict[str, Any]]):
        """JSON doesn't support batching, writes all at once."""
        self.write(data)

    def _write_content(self, content: str):
        """Write content to destination."""
        if isinstance(self.destination, (str, Path)):
            # File path
            path = Path(self.destination)
            path.parent.mkdir(parents=True, exist_ok=True)

            if self.compress:
                with gzip.open(str(path) + '.gz', 'wt', encoding='utf-8') as f:
                    f.write(content)
            else:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(content)

            self.logger.info(f"Written to {path}")
        else:
            # Stream (stdout or file object)
            self.destination.write(content)


# ============================================================================
# JSONL Formatter
# ============================================================================

class JSONLFormatter(Formatter):
    """
    JSON Lines formatter (one JSON object per line).

    Better for large datasets and streaming. Each line is valid JSON.
    """

    def write(self, data: List[Dict[str, Any]]):
        """
        Write data as JSONL.

        Args:
            data: List of dictionaries to write
        """
        lines = [json.dumps(record, default=str) for record in data]
        content = '\n'.join(lines)

        self._write_content(content)

    def write_batch(self, data: List[Dict[str, Any]]):
        """Write batch (appending)."""
        lines = [json.dumps(record, default=str) for record in data]
        content = '\n'.join(lines) + '\n'

        if isinstance(self.destination, (str, Path)):
            path = Path(self.destination)
            mode = 'at' if path.exists() else 'wt'

            if self.compress:
                with gzip.open(str(path) + '.gz', mode, encoding='utf-8') as f:
                    f.write(content)
            else:
                with open(path, mode, encoding='utf-8') as f:
                    f.write(content)
        else:
            self.destination.write(content)

    def _write_content(self, content: str):
        """Write content to destination."""
        if isinstance(self.destination, (str, Path)):
            path = Path(self.destination)
            path.parent.mkdir(parents=True, exist_ok=True)

            if self.compress:
                with gzip.open(str(path) + '.gz', 'wt', encoding='utf-8') as f:
                    f.write(content)
            else:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(content)

            self.logger.info(f"Written to {path}")
        else:
            self.destination.write(content)


# ============================================================================
# CSV Formatter
# ============================================================================

class CSVFormatter(Formatter):
    """
    CSV formatter.

    Outputs data as comma-separated values. Good for tabular data.
    """

    def write(self, data: List[Dict[str, Any]]):
        """
        Write data as CSV.

        Args:
            data: List of dictionaries to write
        """
        if not data:
            self.logger.warning("No data to write")
            return

        # Get all unique keys from all records
        fieldnames = list(data[0].keys())
        for record in data[1:]:
            for key in record.keys():
                if key not in fieldnames:
                    fieldnames.append(key)

        # Write CSV
        if isinstance(self.destination, (str, Path)):
            path = Path(self.destination)
            path.parent.mkdir(parents=True, exist_ok=True)

            open_func = gzip.open if self.compress else open
            file_path = str(path) + '.gz' if self.compress else str(path)
            mode = 'wt' if self.compress else 'w'

            with open_func(file_path, mode, encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)

            self.logger.info(f"Written {len(data)} rows to {path}")
        else:
            # Stream
            writer = csv.DictWriter(self.destination, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)

    def write_batch(self, data: List[Dict[str, Any]]):
        """Write batch (appending without header)."""
        if not data:
            return

        fieldnames = list(data[0].keys())

        if isinstance(self.destination, (str, Path)):
            path = Path(self.destination)
            exists = path.exists()

            open_func = gzip.open if self.compress else open
            file_path = str(path) + '.gz' if self.compress else str(path)
            mode = 'at' if exists else 'wt'

            with open_func(file_path, mode, encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                if not exists:
                    writer.writeheader()
                writer.writerows(data)
        else:
            writer = csv.DictWriter(self.destination, fieldnames=fieldnames)
            writer.writerows(data)


# ============================================================================
# Parquet Formatter
# ============================================================================

class ParquetFormatter(Formatter):
    """
    Parquet formatter (requires pandas and pyarrow).

    Outputs data in Apache Parquet columnar format. Excellent for
    large datasets and analytics.
    """

    def __init__(self, *args, **kwargs):
        """Initialize Parquet formatter."""
        if not PANDAS_AVAILABLE or not PYARROW_AVAILABLE:
            raise ImportError("pandas and pyarrow required for Parquet support")

        super().__init__(*args, **kwargs)

    def write(self, data: List[Dict[str, Any]]):
        """
        Write data as Parquet file.

        Args:
            data: List of dictionaries to write
        """
        if not data:
            self.logger.warning("No data to write")
            return

        # Convert to DataFrame
        df = pd.DataFrame(data)

        # Write to Parquet
        if isinstance(self.destination, (str, Path)):
            path = Path(self.destination)
            path.parent.mkdir(parents=True, exist_ok=True)

            # Parquet has built-in compression
            compression = self.options.get('compression', 'snappy')

            df.to_parquet(
                path,
                engine='pyarrow',
                compression=compression,
                index=False
            )

            self.logger.info(f"Written {len(df)} rows to {path}")
        else:
            # Write to stream not directly supported
            raise ValueError("Parquet formatter requires file path destination")

    def write_batch(self, data: List[Dict[str, Any]]):
        """Write batch (append mode)."""
        if not data:
            return

        df = pd.DataFrame(data)
        path = Path(self.destination)

        # Check if file exists
        if path.exists():
            # Append to existing Parquet file
            existing_df = pd.read_parquet(path)
            combined_df = pd.concat([existing_df, df], ignore_index=True)
            combined_df.to_parquet(path, engine='pyarrow', index=False)
        else:
            # Create new file
            self.write(data)


# ============================================================================
# SQLite Formatter
# ============================================================================

class SQLiteFormatter(Formatter):
    """
    SQLite database formatter.

    Exports data to SQLite database. Useful for local data storage
    and SQL querying.
    """

    def __init__(self, destination: Union[str, Path], table_name: str = "data", **options):
        """
        Initialize SQLite formatter.

        Args:
            destination: SQLite database file path
            table_name: Table name to create
            **options: Additional options
        """
        super().__init__(destination, **options)
        self.table_name = table_name

    def write(self, data: List[Dict[str, Any]]):
        """
        Write data to SQLite database.

        Args:
            data: List of dictionaries to write
        """
        if not data:
            self.logger.warning("No data to write")
            return

        # Create database connection
        path = Path(self.destination)
        path.parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(str(path))

        try:
            # Use pandas if available for easier insertion
            if PANDAS_AVAILABLE:
                df = pd.DataFrame(data)
                df.to_sql(
                    self.table_name,
                    conn,
                    if_exists=self.options.get('if_exists', 'replace'),
                    index=False
                )
            else:
                # Manual insertion
                cursor = conn.cursor()

                # Create table from first record
                columns = list(data[0].keys())
                placeholders = ','.join(['?' for _ in columns])

                create_table = f"""
                    CREATE TABLE IF NOT EXISTS {self.table_name} (
                        {','.join(f'{col} TEXT' for col in columns)}
                    )
                """
                cursor.execute(create_table)

                # Insert data
                insert_sql = f"INSERT INTO {self.table_name} VALUES ({placeholders})"
                for record in data:
                    values = [record.get(col) for col in columns]
                    cursor.execute(insert_sql, values)

                conn.commit()

            self.logger.info(f"Written {len(data)} rows to {path}:{self.table_name}")

        finally:
            conn.close()

    def write_batch(self, data: List[Dict[str, Any]]):
        """Write batch (append mode)."""
        if not data:
            return

        conn = sqlite3.connect(str(self.destination))

        try:
            if PANDAS_AVAILABLE:
                df = pd.DataFrame(data)
                df.to_sql(self.table_name, conn, if_exists='append', index=False)
            else:
                # Manual batch insert
                cursor = conn.cursor()
                columns = list(data[0].keys())
                placeholders = ','.join(['?' for _ in columns])
                insert_sql = f"INSERT INTO {self.table_name} VALUES ({placeholders})"

                for record in data:
                    values = [record.get(col) for col in columns]
                    cursor.execute(insert_sql, values)

                conn.commit()

        finally:
            conn.close()


# ============================================================================
# Formatter Factory
# ============================================================================

class FormatterFactory:
    """
    Factory for creating formatters.
    """

    @staticmethod
    def create(
        format: OutputFormat,
        destination: Union[str, Path, TextIO],
        **options
    ) -> Formatter:
        """
        Create formatter for specified format.

        Args:
            format: Output format
            destination: Output destination
            **options: Format-specific options

        Returns:
            Formatter instance

        Example:
            >>> formatter = FormatterFactory.create(
            >>>     format=OutputFormat.CSV,
            >>>     destination="data/bills.csv",
            >>>     compress=True
            >>> )
        """
        if format == OutputFormat.JSON:
            return JSONFormatter(destination, **options)
        elif format == OutputFormat.JSONL:
            return JSONLFormatter(destination, **options)
        elif format == OutputFormat.CSV:
            return CSVFormatter(destination, **options)
        elif format == OutputFormat.PARQUET:
            return ParquetFormatter(destination, **options)
        elif format == OutputFormat.SQLITE:
            return SQLiteFormatter(destination, **options)
        else:
            raise ValueError(f"Unsupported format: {format}")


# ============================================================================
# Module Exports
# ============================================================================

__all__ = [
    'OutputFormat',
    'Formatter',
    'JSONFormatter',
    'JSONLFormatter',
    'CSVFormatter',
    'ParquetFormatter',
    'SQLiteFormatter',
    'FormatterFactory',
]
