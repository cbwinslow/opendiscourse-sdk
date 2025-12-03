import logging
import sys
from typing import Any

import requests
import yaml
from integration_constants import (
    RETRYABLE_CODES,
    SUCCESS_CODES,
    VERIFICATION_ENDPOINTS,
    WEBHOOK_TEST_PAYLOADS,
)

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def load_config() -> dict[str, Any]:
    """Load configuration from YAML file."""
    try:
        with open("integration_config.yaml") as f:
            return yaml.safe_load(f)
    except Exception as e:
        logging.error(f"Failed to load configuration: {e!s}")
        raise


def verify_jira_connection(config: dict[str, Any]) -> bool:
    """Verify Jira connection."""
    try:
        headers = {
            "Authorization": f'Basic {config["jira"]["api_token"]}',
            "Content-Type": "application/json",
        }

        response = requests.get(
            f"{config['jira']['base_url']}{VERIFICATION_ENDPOINTS['JIRA']}",
            headers=headers,
            timeout=REQUEST_TIMEOUT,
        )

        if response.status_code in SUCCESS_CODES:
            logging.info("Jira connection verified successfully")
            return True
        elif response.status_code in RETRYABLE_CODES:
            logging.warning(f"Temporary failure verifying Jira: {response.status_code}")
            return False
        else:
            logging.error(
                f"Failed to verify Jira: {response.status_code} - {response.text}"
            )
            return False
    except Exception as e:
        logging.error(f"Error verifying Jira: {e!s}")
        return False


def verify_github_connection(config: dict[str, Any]) -> bool:
    """Verify GitHub connection."""
    try:
        headers = {
            "Authorization": f'token {config["github"]["token"]}',
            "Accept": "application/vnd.github.v3+json",
        }

        response = requests.get(
            f"https://api.github.com{VERIFICATION_ENDPOINTS['GITHUB']}",
            headers=headers,
            timeout=REQUEST_TIMEOUT,
        )

        if response.status_code in SUCCESS_CODES:
            logging.info("GitHub connection verified successfully")
            return True
        elif response.status_code in RETRYABLE_CODES:
            logging.warning(
                f"Temporary failure verifying GitHub: {response.status_code}"
            )
            return False
        else:
            logging.error(
                f"Failed to verify GitHub: {response.status_code} - {response.text}"
            )
            return False
    except Exception as e:
        logging.error(f"Error verifying GitHub: {e!s}")
        return False


def verify_bitbucket_connection(config: dict[str, Any]) -> bool:
    """Verify Bitbucket connection."""
    try:
        headers = {
            "Authorization": f'Basic {config["bitbucket"]["app_password"]}',
            "Content-Type": "application/json",
        }

        response = requests.get(
            f"{config['bitbucket']['base_url']}{VERIFICATION_ENDPOINTS['BITBUCKET']}",
            headers=headers,
            timeout=REQUEST_TIMEOUT,
        )

        if response.status_code in SUCCESS_CODES:
            logging.info("Bitbucket connection verified successfully")
            return True
        elif response.status_code in RETRYABLE_CODES:
            logging.warning(
                f"Temporary failure verifying Bitbucket: {response.status_code}"
            )
            return False
        else:
            logging.error(
                f"Failed to verify Bitbucket: {response.status_code} - {response.text}"
            )
            return False
    except Exception as e:
        logging.error(f"Error verifying Bitbucket: {e!s}")
        return False


def test_webhooks(config: dict[str, Any]) -> bool:
    """Test all configured webhooks."""
    try:
        # Test Jira webhook
        jira_response = requests.post(
            config["webhooks"]["jira_webhook_url"],
            json=WEBHOOK_TEST_PAYLOADS["JIRA"],
            timeout=REQUEST_TIMEOUT,
        )

        if jira_response.status_code not in SUCCESS_CODES:
            logging.error(f"Jira webhook test failed: {jira_response.status_code}")
            return False

        # Test Bitbucket webhook
        bitbucket_response = requests.post(
            config["webhooks"]["bitbucket_webhook_url"].format(
                workspace=config["bitbucket"]["workspace"], repo_slug="opendiscourse"
            ),
            json=WEBHOOK_TEST_PAYLOADS["BITBUCKET"],
            timeout=REQUEST_TIMEOUT,
        )

        if bitbucket_response.status_code not in SUCCESS_CODES:
            logging.error(
                f"Bitbucket webhook test failed: {bitbucket_response.status_code}"
            )
            return False

        logging.info("All webhooks tested successfully")
        return True
    except Exception as e:
        logging.error(f"Error testing webhooks: {e!s}")
        return False


def verify_repository_links(config: dict[str, Any]) -> bool:
    """Verify repository links between GitHub and Bitbucket."""
    try:
        headers = {
            "Authorization": f'Basic {config["bitbucket"]["app_password"]}',
            "Content-Type": "application/json",
        }

        response = requests.get(
            f"{config['bitbucket']['base_url']}/repositories/{config['bitbucket']['workspace']}/opendiscourse/links",
            headers=headers,
            timeout=REQUEST_TIMEOUT,
        )

        if response.status_code in SUCCESS_CODES and response.json():
            logging.info("Repository links verified successfully")
            return True
        elif response.status_code in RETRYABLE_CODES:
            logging.warning(
                f"Temporary failure verifying repository links: {response.status_code}"
            )
            return False
        else:
            logging.error(
                f"Failed to verify repository links: {response.status_code} - {response.text}"
            )
            return False
    except Exception as e:
        logging.error(f"Error verifying repository links: {e!s}")
        return False


def main():
    config = load_config()

    logging.info("Starting integration verification...")

    # Verify connections
    jira_ok = verify_jira_connection(config)
    github_ok = verify_github_connection(config)
    bitbucket_ok = verify_bitbucket_connection(config)

    # Verify webhooks
    webhooks_ok = test_webhooks(config)

    # Verify repository links
    links_ok = verify_repository_links(config)

    # Check overall status
    all_ok = all([jira_ok, github_ok, bitbucket_ok, webhooks_ok, links_ok])

    if all_ok:
        logging.info("All integration components verified successfully!")
    else:
        logging.error("One or more integration components failed verification")

    return all_ok


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
