#!/usr/bin/env python3
"""REST-based GitHub issue creator (no external deps).
Reads github_issues_payload.json and POSTs issues to the repo via GitHub REST API.
Requires GITHUB_TOKEN env var with repo permissions.
"""

import json
import os
import sys
from urllib import request, error

REPO = "cbwinslow/opendiscourse"
API_BASE = "https://api.github.com"
PAYLOAD_FILE = "github_issues_payload.json"
OUTPUT_FILE = "github_issues_created.json"


def post_issue(token, repo, payload):
    url = f"{API_BASE}/repos/{repo}/issues"
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
            "User-Agent": "opendiscourse-script",
        },
    )
    with request.urlopen(req) as resp:
        body = resp.read()
        return json.loads(body.decode("utf-8"))


def main():
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("ERROR: GITHUB_TOKEN environment variable not set.")
        sys.exit(2)

    try:
        with open(PAYLOAD_FILE, "r") as f:
            payloads = json.load(f)
    except FileNotFoundError:
        print(f"ERROR: Payload file not found: {PAYLOAD_FILE}")
        sys.exit(3)
    except json.JSONDecodeError as e:
        print(f"ERROR: Failed to parse payload: {e}")
        sys.exit(4)

    created = []
    failures = []

    for item in payloads:
        try:
            issue = post_issue(token, REPO, item)
            created.append(
                {
                    "number": issue.get("number"),
                    "title": issue.get("title"),
                    "url": issue.get("html_url"),
                    "labels": [l.get("name") for l in issue.get("labels", [])],
                }
            )
            print(f"Created #{issue.get('number')} - {issue.get('title')}")
        except error.HTTPError as e:
            code = e.code
            body = e.read().decode()
            failures.append(
                {"title": item.get("title"), "code": code, "response": body}
            )
            print(f"ERROR [{code}] creating: {item.get('title')[:60]}...: {body}")
        except Exception as e:
            failures.append({"title": item.get("title"), "error": str(e)})
            print(f"ERROR creating: {item.get('title')[:60]}...: {e}")

    results = {
        "timestamp": __import__("datetime").datetime.utcnow().isoformat() + "Z",
        "repository": REPO,
        "total_payloads": len(payloads),
        "created_issues": created,
        "failed_issues": len(payloads) - len(created),
        "failures": failures,
    }

    with open(OUTPUT_FILE, "w") as f:
        json.dump(results, f, indent=2)

    print(
        f"\nSummary: {len(created)} created, {len(payloads) - len(created)} failed. Output: {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()
