"""
Congress CLI - Bulk data ingestion tool for Congress.gov

A comprehensive CLI tool for ingesting bulk data from Congress.gov with:
- SQL database bootstrap
- Incremental ingestion with offset tracking
- Real-time monitoring and progress tracking
- Sophisticated error handling and retry logic
- Pydantic models for data validation
"""

__version__ = "1.0.0"
__author__ = "OpenDiscourse Team"
__email__ = "team@opendiscourse.org"

from .cli import cli
from .database.migrations import DatabaseBootstrap
from .ingestion.incremental import IncrementalIngestor
from .models.api_models import APIResponse, CongressBill, CongressMember

__all__ = [
    "cli",
    "CongressMember",
    "CongressBill",
    "APIResponse",
    "DatabaseBootstrap",
    "IncrementalIngestor",
]
