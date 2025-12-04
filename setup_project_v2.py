#!/usr/bin/env python3
"""
GitHub Project v2 Setup for Ingestion Issues
Creates and configures Project v2 board for tracking ingestion fixes
"""

import os
import requests
import json

def create_project_v2(token, repo_owner="cbwinslow", repo_name="opendiscourse"):
    """Create GitHub Project v2 for ingestion issues"""

    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json"
    }

    # Create the project
    project_data = {
        "owner": repo_owner,
        "name": "Ingestion System Fixes",
        "body": "Tracking project for OpenDiscourse ingestion system fixes and improvements",
        "template": "basic"
    }

    url = f"https://api.github.com/orgs/{repo_owner}/projects"
    response = requests.post(url, headers=headers, json=project_data)

    if response.status_code == 201:
        project = response.json()
        print(f"✅ Created Project v2: {project['name']} (ID: {project['id']})")
        return project
    else:
        print(f"❌ Failed to create project: {response.status_code} - {response.text}")
        return None

def add_issues_to_project(token, project_id, issue_numbers):
    """Add issues to Project v2 board"""

    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json"
    }

    # GraphQL mutation to add items to project
    query = """
    mutation AddItemsToProject($projectId: ID!, $contentIds: [ID!]!) {
      addProjectV2ItemsById(input: {projectId: $projectId, contentIds: $contentIds}) {
        items {
          id
          content {
            ... on Issue {
              id
              title
              number
            }
          }
        }
      }
    }
    """

    # Convert issue numbers to node IDs (simplified approach)
    content_ids = [f"IID{issue}" for issue in issue_numbers]

    variables = {
        "projectId": project_id,
        "contentIds": content_ids
    }

    url = "https://api.github.com/graphql"
    response = requests.post(url, headers=headers, json={"query": query, "variables": variables})

    if response.status_code == 200:
        result = response.json()
        print(f"✅ Added {len(issue_numbers)} issues to project")
        return result
    else:
        print(f"❌ Failed to add issues: {response.status_code} - {response.text}")
        return None

def main():
    token = os.getenv('GITHUB_TOKEN')
    if not token:
        print("❌ GITHUB_TOKEN environment variable required")
        return

    print("🚀 Setting up GitHub Project v2 for Ingestion Issues")
    print("=" * 60)

    # Create project
    project = create_project_v2(token)
    if not project:
        return

    project_id = project['id']

    # Add issues to project
    issue_numbers = [174, 175, 176]  # The issues we just created
    result = add_issues_to_project(token, project_id, issue_numbers)

    print(f"\n📊 Project Setup Complete!")
    print(f"🔗 Project URL: https://github.com/orgs/cbwinslow/projects/{project_id}")
    print(f"📋 Issues Added: #{', #'.join(map(str, issue_numbers))}")

    print(f"\n🎯 Next Steps:")
    print(f"1. Visit the project board to organize issues")
    print(f"2. Create columns: Critical, High Priority, In Progress, Completed")
    print(f"3. Assign issues to appropriate columns")
    print(f"4. Start working on Issue #174 (Congress Bills) - most critical")

if __name__ == "__main__":
    main()
