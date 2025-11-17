"""API configuration settings for all services"""

import os

# GovInfo API Configuration
GOVINFO_API_KEY = os.getenv("GOVINFO_API_KEY", "YOUR_API_KEY_HERE")
GOVINFO_BASE_URL = "https://api.govinfo.gov"
GOVINFO_HEADERS = {"X-Api-Key": GOVINFO_API_KEY, "Accept": "application/json"}

# Legacy aliases for backward compatibility
BASE_URL = GOVINFO_BASE_URL
HEADERS = GOVINFO_HEADERS
COLLECTIONS_URL = f"{GOVINFO_BASE_URL}/collections"

# Congress.gov API Configuration
CONGRESS_API_KEY = os.getenv("CONGRESS_API_KEY", "")
CONGRESS_BASE_URL = "https://api.congress.gov/v3"
CONGRESS_HEADERS = {"X-Api-Key": CONGRESS_API_KEY, "Accept": "application/json"}

# Bulk Data Configuration
BULK_DATA_CONFIG = {
    "rate_limit_delay": 0.5,  # seconds between requests
    "timeout": 30,
    "retry_attempts": 3,
    "data_dir": "data/bulk_ingestion"
}

# Ollama Configuration
OLLAMA_CONFIG = {
    "base_url": "http://localhost:11434",
    "default_model": "llama2",
    "timeout": 300,
    "max_retries": 3
}

# MCP Server Configuration
MCP_SERVER = "http://localhost:8080"
