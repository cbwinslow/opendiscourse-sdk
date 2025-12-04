#!/usr/bin/env python3
"""Debug script to check Congress.gov API response format"""

import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('CONGRESS_API_KEY')
if not api_key:
    print("No CONGRESS_API_KEY found")
    exit(1)

session = requests.Session()
session.headers.update({
    'X-API-Key': api_key,
    'Accept': 'application/json'
})

# Test the API
url = "https://api.congress.gov/v3/member/congress/118"
params = {'limit': 5, 'offset': 0}

try:
    response = session.get(url, params=params, timeout=30)
    response.raise_for_status()

    data = response.json()
    print("API Response Structure:")
    print(f"Keys: {list(data.keys())}")

    if 'members' in data:
        members = data['members']
        print(f"Members count: {len(members)}")
        if members:
            print(f"First member keys: {list(members[0].keys())}")
            print(f"First member type: {type(members[0])}")

    if 'pagination' in data:
        print(f"Pagination: {data['pagination']}")

    # Print full response for debugging
    print("\nFull response:")
    print(json.dumps(data, indent=2))

except Exception as e:
    print(f"Error: {e}")
