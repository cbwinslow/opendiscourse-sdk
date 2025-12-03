"""Scraping-related services for OpenDiscourse.

This package contains modules for scraping and processing data from various sources.
"""

from __future__ import annotations

# Import the classes to make them available when importing from the package
from .govinfo_scraper import GOVInfoScraper

# Define what gets imported with 'from opendiscourse.services.scraping import *'
__all__ = [
    "GOVInfoScraper",
]
