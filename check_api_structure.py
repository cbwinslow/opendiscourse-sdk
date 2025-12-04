#!/usr/bin/env python3
"""Check official API structure"""

import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('CONGRESS_API_KEY')
session = requests.Session()
session.headers.update({
    'X-API-Key': api_key,
    'Accept': 'application/json'
})

# Get a sample member
url = "https://api.congress.gov/v3/member/congress/118"
params = {'limit': 1, 'offset': 0}

response = session.get(url, params=params, timeout=30)
data = response.json()

# Show the structure
member = data['members'][0]
print("API Member Structure:")
print(json.dumps(member, indent=2))

# Show terms structure
if 'terms' in member:
    print("\nTerms Structure:")
    print(json.dumps(member['terms'], indent=2))