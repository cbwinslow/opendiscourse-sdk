import os
from typing import Any

import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def setup_jira_webhook(config: dict[str, Any]) -> None:
    """Set up Jira webhook."""
    jira_config = config["jira"]

    headers = {
        "Content-Type": "application/json",
        "Authorization": f'Basic {os.environ.get("JIRA_AUTH_TOKEN")}',
    }

    webhook_data = {
        "name": "OpenDiscourse Integration",
        "url": jira_config["webhook_url"],
        "events": ["jira:issue_created", "jira:issue_updated", "jira:issue_deleted"],
        "filters": {"issue-related-events-section": True},
    }

    try:
        response = requests.post(
            jira_config["webhooks"]["jira"], headers=headers, json=webhook_data
        )
        response.raise_for_status()
        print("Jira webhook setup successful!")
    except Exception as e:
        print(f"Error setting up Jira webhook: {e!s}")


def setup_github_webhook(config: dict[str, Any]) -> None:
    """Set up GitHub webhook."""
    github_config = config["github"]

    headers = {
        "Authorization": f'token {github_config["token"]}',
        "Accept": "application/vnd.github.v3+json",
    }

    webhook_data = {
        "name": "web",
        "active": True,
        "events": ["push", "pull_request", "issues", "issue_comment"],
        "config": {
            "url": config["webhooks"]["github"],
            "content_type": "json",
            "insecure_ssl": "0",
        },
    }

    try:
        response = requests.post(
            f'https://api.github.com/repos/{github_config["repository"]}/hooks',
            headers=headers,
            json=webhook_data,
        )
        response.raise_for_status()
        print("GitHub webhook setup successful!")
    except Exception as e:
        print(f"Error setting up GitHub webhook: {e!s}")


def main():
    """Main function to set up all integrations."""
    # Load configuration
    with open("integration_config.yaml") as f:
        config = yaml.safe_load(f)

    # Set up Jira webhook
    setup_jira_webhook(config)

    # Set up GitHub webhook
    setup_github_webhook(config)


if __name__ == "__main__":
    main()
