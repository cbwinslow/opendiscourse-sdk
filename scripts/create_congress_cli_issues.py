#!/usr/bin/env python3
"""
Create GitHub issues for Congress CLI ingestion bugs.
"""
import requests
import json
import os

# Load GitHub token from environment variables for security
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "YOUR_GITHUB_TOKEN_HERE")  # Set this in your environment
REPO_OWNER = "cbwinslow"
REPO_NAME = "opendiscourse-sdk"

headers = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28"
}

issues_data = [
    {
        "title": "Fix Congress CLI Votes Ingestion Endpoint",
        "body": """## Problem
The Congress.gov API does not support the `/roll-call-vote/{congress}/{chamber}/{session}` endpoint that was originally used for votes ingestion. This causes 404 errors when attempting to ingest votes.

## Current Status
- ✅ Code updated to use `/house-vote` endpoint
- ⚠️ Needs real-run verification
- ⚠️ Senate votes not available via list endpoint

## Details
- **File:** `scripts/ingestion/congress_cli.py`
- **Function:** `ingest_votes()`
- **API Endpoint:** Currently uses `/house-vote` which only provides House votes
- **Error:** Senate votes return 404 when attempting `/senate-vote`

## Solution
1. Verify `/house-vote` ingestion works correctly
2. Document Senate vote limitation
3. Consider using GovInfo API as alternative for Senate votes

## Related
- Component: Congress CLI
- Priority: High
- Type: Bug""",
        "labels": ["bug", "congress-cli", "ingestion", "priority: high"]
    },
    {
        "title": "Verify Committee Members Ingestion After Parent Data Fix",
        "body": """## Problem
The `ingest-committee-members` command requires the `congress.committees` table to be populated first. Previously failed silently with 0 records when table was empty.

## Current Status
- ✅ Parent data (`congress.committees`) now populated (806 committees)
- ⚠️ Needs verification that committee members ingestion works

## Details
- **File:** `scripts/ingestion/congress_cli.py`
- **Function:** `ingest_committee_members()`
- **Dependency:** Requires `congress.committees` to be populated first

## Verification Steps
```bash
source .venv/bin/activate && source ~/.env
python3 scripts/ingestion/congress_cli.py ingest-committee-members 118
```

## Expected Result
Should ingest committee members for all 806 committees in Congress 118.

## Related
- Component: Congress CLI
- Priority: Medium
- Type: Verification""",
        "labels": ["verification", "congress-cli", "ingestion", "priority: medium", "dependencies"]
    },
    {
        "title": "Review and Update Transform Functions for API Compatibility",
        "body": """## Problem
Transform functions in `congress_cli.py` may not correctly map API response fields to database schema. This can cause insertion failures or data quality issues.

## Functions Needing Review
1. `transform_vote()` - Verify positions JSONB structure matches API
2. `transform_committee_member()` - Verify field mappings
3. `transform_bill_*()` functions - Verify natural key to UUID lookups work correctly

## Details
- **File:** `scripts/ingestion/congress_cli.py`
- **Impact:** Data quality, insertion failures

## Solution
1. Test each transform function with actual API responses
2. Update `mapping_test.py` with real API data samples
3. Add validation/logging to catch mapping errors

## Related Issues
- Depends on real API testing
- May affect: votes, committee members, bill details

## Related
- Component: Congress CLI
- Priority: Medium
- Type: Enhancement""",
        "labels": ["enhancement", "congress-cli", "data-quality", "priority: medium"]
    },
    {
        "title": "Document Bill Details Ingestion Dependencies",
        "body": """## Problem
All bill detail ingestion functions (`ingest-bill-actions`, `ingest-bill-cosponsors`, `ingest-bill-subjects`, `ingest-bill-titles`, `ingest-related-bills`) depend on the `congress.bills` table being populated first. They use subqueries to lookup `bill_id` UUIDs from natural keys.

## Current Behavior
- Silently fails or returns 0 records if bills table is empty
- No clear error message to user about missing dependency

## Details
- **File:** `scripts/ingestion/congress_cli.py`
- **Function:** `ingest_bill_details()`
- **Dependency:** Requires `congress.bills` populated first

## Solution
1. Add dependency documentation to README/CLI help
2. Add validation check at start of function
3. Provide clear error/warning if bills table empty
4. Consider adding `--check-dependencies` flag

## Recommended Ingestion Order
```bash
# Required parent data first
python3 scripts/ingestion/congress_cli.py ingest-bills 118

# Then child data
python3 scripts/ingestion/congress_cli.py ingest-bill-actions 118
python3 scripts/ingestion/congress_cli.py ingest-bill-cosponsors 118
# etc.
```

## Related
- Component: Congress CLI
- Priority: Low
- Type: Documentation""",
        "labels": ["documentation", "congress-cli", "ingestion", "priority: low", "dependencies"]
    }
]

def create_issue(issue_data):
    """Create a GitHub issue."""
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/issues"
    response = requests.post(url, headers=headers, json=issue_data)
    if response.status_code == 201:
        issue = response.json()
        print(f"✅ Created issue #{issue['number']}: {issue['title']}")
        return issue
    else:
        print(f"❌ Failed to create issue: {issue_data['title']}")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
        return None

def main():
    print(f"Creating {len(issues_data)} GitHub issues...\n")
    created_issues = []

    for issue_data in issues_data:
        issue = create_issue(issue_data)
        if issue:
            created_issues.append(issue)

    print(f"\n✅ Successfully created {len(created_issues)}/{len(issues_data)} issues")

    # Save issue numbers for reference
    with open("created_issues.json", "w") as f:
        json.dump([{"number": i["number"], "title": i["title"], "url": i["html_url"]} for i in created_issues], f, indent=2)
    print(f"📝 Issue details saved to created_issues.json")

if __name__ == "__main__":
    main()
