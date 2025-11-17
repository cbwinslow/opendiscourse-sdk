"""Configuration for committee data access."""

import os

API_KEY = os.getenv("GOVINFO_API_KEY", "YOUR_API_KEY_HERE")
BASE_URL = "https://api.govinfo.gov"
HEADERS = {"X-Api-Key": API_KEY, "Accept": "application/json"}
COMMITTEE_BROWSE_URL = f"{BASE_URL}/browse/committee"
COMMITTEE_DETAILS_URL = f"{BASE_URL}/committees"
COMMITTEE_DOCUMENTS_URL = f"{BASE_URL}/committee/documents"
COMMITTEE_DATA_DIR = "committee_data"
os.makedirs(COMMITTEE_DATA_DIR, exist_ok=True)
