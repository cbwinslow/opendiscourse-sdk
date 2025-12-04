import json, urllib.request

TOKEN = "YOUR_LINEAR_API_TOKEN_HERE"  # Replace with your actual Linear API token
endpoint = "https://api.linear.app/graphql"
query = {"query": "query { viewer { id name } }"}
req = urllib.request.Request(
    endpoint,
    data=json.dumps(query).encode(),
    headers={"Authorization": "Bearer " + TOKEN, "Content-Type": "application/json"},
)
try:
    with urllib.request.urlopen(req) as resp:
        print(resp.read().decode())
except urllib.error.HTTPError as e:
    print("HTTPError:", e.code, e.read().decode())
except Exception as e:
    print("Error:", e)
