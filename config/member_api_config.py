"""Configuration for Congress member API."""

import os

API_KEY = os.getenv("CONGRESS_API_KEY", "YOUR_API_KEY_HERE")
BASE_URL = "https://api.congress.gov/v3"
HEADERS = {"X-Api-Key": API_KEY, "Accept": "application/json"}
MEMBER_LIST_URL = f"{BASE_URL}/member"
MEMBER_DETAILS_URL = f"{BASE_URL}/member/{{member_id}}"
MEMBER_VOTES_URL = f"{BASE_URL}/member/{{member_id}}/votes"
MEMBER_DATA_DIR = "member_data"
os.makedirs(MEMBER_DATA_DIR, exist_ok=True)
