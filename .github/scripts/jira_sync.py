import os
import re

import requests

JIRA_URL = os.environ.get("JIRA_BASE_URL")
JIRA_USER = os.environ.get("JIRA_USER_EMAIL")
JIRA_TOKEN = os.environ.get("JIRA_API_TOKEN")
PROJECT_KEY = "OD"  # Change to your Jira project key

TASKS_FILE = "TASKS.md"

ISSUE_TYPE = "Task"

headers = {
    "Content-Type": "application/json"
}
auth = (JIRA_USER, JIRA_TOKEN)

def parse_tasks():
    tasks = []
    with open(TASKS_FILE, "r") as f:
        for line in f:
            m = re.match(r"\| ([^|]+)\| ([^|]+)\| ([^|]+)\| ([^|]+)\|", line)
            if m:
                summary = m.group(1).strip()
                description = m.group(2).strip()
                status = m.group(3).strip()
                if status.upper() == "TODO":
                    tasks.append((summary, description))
    return tasks

def create_issue(summary, description):
    url = f"{JIRA_URL}/rest/api/3/issue"
    data = {
        "fields": {
            "project": {"key": PROJECT_KEY},
            "summary": summary,
            "description": description,
            "issuetype": {"name": ISSUE_TYPE},
        }
    }
    r = requests.post(url, json=data, headers=headers, auth=auth)
    if r.status_code == 201:
        print(f"Created Jira issue: {summary}")
    else:
        print(f"Failed to create issue: {summary} ({r.status_code}) {r.text}")

def main():
    tasks = parse_tasks()
    for summary, description in tasks:
        create_issue(summary, description)

if __name__ == "__main__":
    main()
