import requests
import os
import json
import sys

api_key = os.environ.get('OPENSTATES_API_KEY')
if not api_key:
    print("Error: OPENSTATES_API_KEY not set")
    sys.exit(1)

headers = {'X-API-KEY': api_key}
base_url = 'https://v3.openstates.org'

def get(url, params=None):
    try:
        resp = requests.get(url, params=params, headers=headers)
        print(f"GET {url} {params} -> {resp.status_code}")
        if resp.status_code == 200:
            return resp.json()
        else:
            print(f"Error: {resp.text}")
            return None
    except Exception as e:
        print(f"Exception: {e}")
        return None

# 1. Find Jurisdiction ID for CA
print("\n--- Finding Jurisdiction ID for CA ---")
jurisdictions = get(f'{base_url}/jurisdictions', {'classification': 'state'})
ca_id = None
if jurisdictions:
    for j in jurisdictions.get('results', []):
        if j['name'] == 'California':
            ca_id = j['id']
            break
print(f"California ID: {ca_id}")

if not ca_id:
    sys.exit(1)

# 2. Fetch Jurisdiction Details (check for sessions and organizations with include)
print(f"\n--- Fetching Jurisdiction Details for {ca_id} with include ---")
# Try passing list for multiple values if requests supports it, or just one for now to be safe.
# Let's try getting organizations first.
j_details = get(f'{base_url}/jurisdictions/{ca_id}', {'include': 'organizations'})
if j_details:
    if 'organizations' in j_details:
        print(f"Found {len(j_details['organizations'])} organizations")
        # Check for districts in organizations (posts)
        for org in j_details['organizations']:
            if org['classification'] in ['lower', 'upper', 'legislature']:
                print(f"Org {org['name']} ({org['classification']}) has posts: {'posts' in org}")
                if 'posts' in org:
                     print(f"Sample Post: {org['posts'][0]}")
    else:
        print("No 'organizations' key found even with include")

# Check sessions separately
j_sessions = get(f'{base_url}/jurisdictions/{ca_id}', {'include': 'legislative_sessions'})
if j_sessions and 'legislative_sessions' in j_sessions:
    print(f"Found {len(j_sessions['legislative_sessions'])} legislative sessions")

# 6. Probe Bills with 'ca' and page param (to reproduce 400)
print(f"\n--- Probing Bills for 'ca' with page=1 ---")
bills_ca = get(f'{base_url}/bills', {'jurisdiction': 'ca', 'page': 1, 'per_page': 50})
if bills_ca:
    print("Success with page=1")
else:
    print("Failed with page=1")
