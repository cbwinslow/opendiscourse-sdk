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

# Test organizations endpoint
print("\n--- Testing /organizations endpoint ---")
# Try with full ID
orgs = get(f'{base_url}/organizations', {'jurisdiction': ca_id})
if orgs:
    print(f"Found {len(orgs.get('results', []))} orgs via /organizations with full ID")

# Try with state code
orgs_ca = get(f'{base_url}/organizations', {'jurisdiction': 'ca'})
if orgs_ca:
     print(f"Found {len(orgs_ca.get('results', []))} orgs via /organizations with 'ca'")
