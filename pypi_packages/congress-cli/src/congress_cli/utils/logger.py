"""
Logging utilities for Congress CLI.
"""

import logging
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime
from rich.logging import RichHandler
from rich.console import Console


def setup_logging(verbose: bool = False, log_file: Optional[str] = None):
    """Setup logging configuration."""

    # Determine log level
    log_level = logging.DEBUG if verbose else logging.INFO

    # Create console
    console = Console(stderr=True)

    # Setup rich handler for console
    rich_handler = RichHandler(
        console=console,
        show_time=True,
        show_path=verbose,
        markup=True,
        rich_tracebacks=True
    )
    rich_handler.setLevel(log_level)

    # Setup formatters
    console_formatter = logging.Formatter(
        fmt="%(message)s",
        datefmt="[%X]"
    )
    rich_handler.setFormatter(console_formatter)

    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Clear existing handlers
    root_logger.handlers.clear()

    # Add console handler
    root_logger.addHandler(rich_handler)

    # Add file handler if specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(log_level)

        file_formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(file_formatter)

        root_logger.addHandler(file_handler)

    # Set specific logger levels
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("psycopg2").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get logger instance."""
    return logging.getLogger(name)


class IngestionLogger:
    """Specialized logger for ingestion operations."""

    def __init__(self, data_source: str, data_type: str):
        self.data_source = data_source
        self.data_type = data_type
        self.logger = get_logger(f"ingestion.{data_source}.{data_type}")
        self.start_time = datetime.now()
        self.processed_count = 0
        self.error_count = 0

    def info(self, message: str, **kwargs):
        """Log info message with context."""
        self.logger.info(f"[{self.data_source}:{self.data_type}] {message}", **kwargs)

    def warning(self, message: str, **kwargs):
        """Log warning message with context."""
        self.logger.warning(f"[{self.data_source}:{self.data_type}] {message}", **kwargs)

    def error(self, message: str, **kwargs):
        """Log error message with context."""
        self.error_count += 1
        self.logger.error(f"[{self.data_source}:{self.data_type}] {message}", **kwargs)

    def debug(self, message: str, **kwargs):
        """Log debug message with context."""
        self.logger.debug(f"[{self.data_source}:{self.data_type}] {message}", **kwargs)

    def progress(self, processed: int, total: int, rate: float = 0.0):
        """Log progress information."""
        self.processed_count = processed
        percentage = (processed / total * 100) if total > 0 else 0

        eta_str = ""
        if rate > 0:
            remaining = total - processed
            eta_seconds = remaining / rate
            eta_str = f" ETA: {eta_seconds:.0f}s"

        self.info(f"Progress: {processed:,}/{total:,} ({percentage:.1f}%) Rate: {rate:.1f}/s{eta_str}")

    def summary(self):
        """Log ingestion summary."""
        duration = (datetime.now() - self.start_time).total_seconds()
        rate = self.processed_count / duration if duration > 0 else 0

        self.info(
            f"Ingestion completed - Processed: {self.processed_count:,}, "
            f"Errors: {self.error_count}, Duration: {duration:.1f}s, "
            f"Rate: {rate:.1f}/s"
        )


def create_log_file_name(data_source: str, data_type: str) -> str:
    """Create log file name with timestamp."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{data_source}_{data_type}_{timestamp}.log"
