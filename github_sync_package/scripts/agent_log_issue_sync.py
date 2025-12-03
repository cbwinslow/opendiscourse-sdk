#!/usr/bin/env python3
import json, os
from github import Github

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO = "cbwinslow/opendiscourse"
g = Github(GITHUB_TOKEN)
repo = g.get_repo(REPO)

def parse_log_and_create_issue(log_path):
    with open(log_path) as f:
        entries = json.load(f)
    for entry in entries:
        title = f"[Agent Error] {entry['agent']} - {entry['error']}"
        body = (
            f"**Agent**: {entry['agent']}
"
            f"**Error**: {entry['error']}
"
            f"**Time**: {entry['timestamp']}"
        )
        repo.create_issue(title=title, body=body, labels=["agent-logs"])

# Example usage
# parse_log_and_create_issue("logs/agent-failures.json")
