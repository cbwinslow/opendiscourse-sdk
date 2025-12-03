import logging
from typing import Any

import requests
import yaml
from atlassian import Bitbucket, Jira
from github import Github
from integration_constants import BACKOFF_FACTOR, MAX_RETRIES, RETRY_DELAY_SECONDS
from retry_decorator import retry

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


@retry(max_retries=MAX_RETRIES, delay=RETRY_DELAY_SECONDS, backoff=BACKOFF_FACTOR)
def setup_jira_webhook(config: dict[str, Any]) -> None:
    """Set up Jira webhook for GitHub integration."""
    try:
        jira_config = config.get("jira", {})

        def validate_jira_config(jira_config: dict[str, Any]) -> None:
            """Validate Jira configuration."""
            required_fields = ["base_url", "username", "api_token", "webhook_url"]
            missing_fields = [
                field for field in required_fields if field not in jira_config
            ]

            if missing_fields:
                logging.error(
                    f"Missing required Jira configuration fields: {', '.join(missing_fields)}"
                )
                msg = f"Missing required Jira configuration fields: {', '.join(missing_fields)}"
                raise Exception(msg)

            # Check for placeholder values
            placeholder_values = []
            if jira_config["username"] == "your-jira-email":
                placeholder_values.append("username")
            if jira_config["api_token"] == "your-jira-api-token":
                placeholder_values.append("api_token")

            if placeholder_values:
                logging.error(
                    f"Please replace placeholder values in Jira configuration: {', '.join(placeholder_values)}"
                )
                msg = f"Please replace placeholder values in Jira configuration: {', '.join(placeholder_values)}"
                raise Exception(msg)

        validate_jira_config(jira_config)

        # Initialize Jira client with detailed error handling
        try:
            jira = Jira(
                url=jira_config["base_url"],
                username=jira_config["username"],
                password=jira_config["api_token"],
                cloud=True,  # Explicitly set cloud=True for Jira Cloud
            )

            # Test basic authentication
            try:
                auth_response = jira.get(
                    "rest/api/2/myself", headers={"Accept": "application/json"}
                )
                if auth_response.status_code == 200:
                    logging.info("Successfully authenticated with Jira")
                else:
                    logging.error(
                        f"Authentication failed. Status code: {auth_response.status_code}"
                    )
                    logging.error(f"Response content: {auth_response.text}")
                    msg = f"Authentication failed with status code {auth_response.status_code}"
                    raise Exception(msg)
            except Exception as auth_error:
                logging.error(f"Failed to authenticate with Jira: {auth_error!s}")
                raise
        except Exception as init_error:
            logging.error(f"Failed to initialize Jira client: {init_error!s}")
            raise

        # Test connection to Jira
        try:
            # Try a simple GET request to test connection
            response = jira.get("rest/api/2/myself")
            if response.status_code == 200:
                logging.info("Successfully connected to Jira")
                return

            # Log detailed error information
            logging.error(
                f"Failed to connect to Jira. Status code: {response.status_code}"
            )
            try:
                error_details = response.json()
                logging.error(f"Error details: {error_details}")
            except ValueError:
                logging.error(f"Response text: {response.text}")

            msg = f"Failed to connect to Jira. Status code: {response.status_code}"
            raise Exception(msg)
        except requests.exceptions.HTTPError as e:
            logging.error(f"HTTP error occurred: {e!s}")
            logging.error(
                f"Response status: {e.response.status_code if e.response else 'No response'}"
            )
            try:
                logging.error(
                    f"Response content: {e.response.content.decode() if e.response else 'No response content'}"
                )
            except Exception:
                logging.error("Could not decode response content")
            raise
        except Exception as e:
            logging.error(f"Unexpected error connecting to Jira: {e!s}")
            raise

        # Get existing webhooks using REST API
        try:
            response = jira.get("rest/webhooks/1.0/webhook")
            response.raise_for_status()
            existing_webhooks = response.json()
            webhook_name = "GitHub Integration Webhook"

            # Check if webhook already exists
            existing_webhook = next(
                (w for w in existing_webhooks if w.get("name") == webhook_name), None
            )

            if existing_webhook:
                logging.info(f"Webhook '{webhook_name}' already exists")
                return

            # Create new webhook
            webhook_data = {
                "name": webhook_name,
                "url": webhook_url,
                "description": "Webhook for GitHub integration",
                "events": [
                    "jira:issue_created",
                    "jira:issue_updated",
                    "jira:issue_deleted",
                ],
                "filters": {
                    "issueCreated": True,
                    "issueUpdated": True,
                    "issueDeleted": True,
                },
                "authentication": {"type": "none"},
            }

            try:
                # Create webhook using REST API
                response = jira.post("rest/webhooks/1.0/webhook", json=webhook_data)
                if response.status_code == 201:
                    logging.info("Successfully created Jira webhook")
                    return
                elif response.status_code == 409:
                    logging.info("Webhook already exists with this URL")
                    return

                # For other status codes, log more details
                logging.error(
                    f"Failed to create Jira webhook. Status code: {response.status_code}"
                )
                try:
                    error_details = response.json()
                    logging.error(f"Error details: {error_details}")
                except ValueError:
                    logging.error(f"Response text: {response.text}")
                msg = f"Failed to create Jira webhook. Status code: {response.status_code}"
                raise Exception(msg)
            except requests.exceptions.HTTPError as e:
                logging.error(f"HTTP error occurred: {e!s}")
                logging.error(
                    f"Response status: {e.response.status_code if e.response else 'No response'}"
                )
                try:
                    logging.error(
                        f"Response content: {e.response.content.decode() if e.response else 'No response content'}"
                    )
                except Exception:
                    logging.error("Could not decode response content")
                raise
            except Exception as e:
                logging.error(f"Unexpected error: {e!s}")
                raise
        except requests.exceptions.HTTPError as e:
            logging.error(f"Failed to create Jira webhook. Error: {e!s}")
            logging.error(
                f"Response text: {e.response.text if e.response else 'No response text'}"
            )
            raise
        except Exception as e:
            logging.error(f"Failed to create Jira webhook. Error: {e!s}")
            raise
    except Exception as e:
        logging.error(f"Error setting up Jira webhook: {e!s}")
        raise


@retry(max_retries=MAX_RETRIES, delay=RETRY_DELAY_SECONDS, backoff=BACKOFF_FACTOR)
def setup_bitbucket_webhook(config: dict[str, Any]) -> None:
    """Set up Bitbucket webhook for GitHub repository."""
    try:
        bitbucket_config = config["bitbucket"]
        bitbucket = Bitbucket(
            url=bitbucket_config["base_url"],
            username=bitbucket_config["username"],
            password=bitbucket_config["app_password"],
        )

        # Create webhook
        webhook_url = config["webhooks"]["bitbucket"]
        webhook_data = {
            "description": "GitHub Webhook",
            "url": webhook_url,
            "active": True,
            "events": ["repo:push", "repo:fork"],
        }

        # Get repository
        workspace = bitbucket_config["workspace"]
        repo_slug = config["github"]["repository"].split("/")[-1]

        # Create webhook
        response = bitbucket.create_webhook(
            workspace=workspace, repo_slug=repo_slug, webhook_data=webhook_data
        )

        if response.status_code == 201:
            logging.info(f"Successfully created Bitbucket webhook at {webhook_url}")
        else:
            logging.error(
                f"Failed to create Bitbucket webhook. Status code: {response.status_code}"
            )
            msg = f"Failed to create Bitbucket webhook. Status code: {response.status_code}"
            raise Exception(msg)
    except Exception as e:
        logging.error(f"Error setting up Bitbucket webhook: {e!s}")
        raise


@retry(max_retries=MAX_RETRIES, delay=RETRY_DELAY_SECONDS, backoff=BACKOFF_FACTOR)
def setup_github_webhooks(config: dict[str, Any]) -> None:
    """Set up GitHub webhooks for Jira and Bitbucket."""
    try:
        g = Github(config["github"]["token"])
        repo = g.get_repo(config["github"]["repository"])

        # Set up Jira webhook
        repo.create_hook(
            name="web",
            config={
                "url": config["webhooks"]["jira_webhook_url"],
                "content_type": "json",
            },
            events=["push"],
            active=True,
        )
        logging.info("Successfully set up GitHub webhook for Jira")

        # Set up Bitbucket webhook
        repo.create_hook(
            name="web",
            config={
                "url": config["webhooks"]["bitbucket_webhook_url"].format(
                    workspace=config["bitbucket"]["workspace"],
                    repo_slug="opendiscourse",
                ),
                "content_type": "json",
            },
            events=["push"],
            active=True,
        )
        logging.info("Successfully set up GitHub webhook for Bitbucket")
    except requests.exceptions.RequestException as e:
        logging.error(f"Request error setting up GitHub webhooks: {e!s}")
        raise
    except Exception as e:
        logging.error(f"Unexpected error setting up GitHub webhooks: {e!s}")
        raise


@retry(max_retries=MAX_RETRIES, delay=RETRY_DELAY_SECONDS, backoff=BACKOFF_FACTOR)
def setup_repository_links(config: dict[str, Any]) -> None:
    """Set up repository links between GitHub and Bitbucket."""
    try:
        bitbucket_config = config["bitbucket"]
        bitbucket = Bitbucket(
            url=bitbucket_config["base_url"],
            username=bitbucket_config["username"],
            password=bitbucket_config["app_password"],
        )

        # Get repository
        workspace = bitbucket_config["workspace"]
        repo_slug = config["github"]["repository"].split("/")[-1]

        # Create repository link
        link_data = {
            "name": "GitHub Link",
            "url": f'https://github.com/{config["github"]["repository"]}',
            "type": "github",
        }

        # Create link
        response = bitbucket.create_link(
            workspace=workspace, repo_slug=repo_slug, link_data=link_data
        )

        if response.status_code == 201:
            logging.info("Successfully created repository link to GitHub")
        else:
            logging.error(
                f"Failed to create repository link. Status code: {response.status_code}"
            )
            msg = (
                f"Failed to create repository link. Status code: {response.status_code}"
            )
            raise Exception(msg)
    except Exception as e:
        logging.error(f"Error setting up repository links: {e!s}")
        raise


def main():
    config = load_config()

    try:
        logging.info("Starting integration setup...")

        # Setup webhooks
        setup_jira_webhook(config)
        setup_bitbucket_webhook(config)
        setup_github_webhooks(config)

        # Setup repository links
        setup_repository_links(config)

        # Verify the setup
        from verify_integration import main as verify_main

        if not verify_main():
            logging.error("Verification failed after setup")
            msg = "Integration verification failed"
            raise Exception(msg)

        logging.info("Integration setup completed successfully!")

    except Exception as e:
        logging.error(f"Integration setup failed: {e!s}")
        raise


if __name__ == "__main__":
    main()
