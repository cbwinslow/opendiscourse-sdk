# Integration Constants

# Retry settings
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 5
BACKOFF_FACTOR = 2.0

# Timeout settings
REQUEST_TIMEOUT = 30  # seconds

# HTTP status codes
SUCCESS_CODES = [200, 201, 202, 204]
RETRYABLE_CODES = [429, 500, 502, 503, 504]

# Webhook test payloads
JIRA_WEBHOOK_PAYLOAD = {
    "webhookEvent": "jira:issue_created",
    "issue": {
        "key": "OPD-1",
        "fields": {
            "summary": "Test Issue",
            "description": "This is a test issue",
            "status": {"name": "To Do"},
        },
    },
}

BITBUCKET_WEBHOOK_PAYLOAD = {
    "push": {
        "changes": [
            {
                "new": {
                    "name": "main",
                    "target": {"hash": "1234567890", "message": "Test commit"},
                }
            }
        ]
    }
}

# Error types
ERROR_TYPES = {
    "CONNECTION": "Connection error occurred",
    "AUTH": "Authentication failed",
    "CONFIG": "Configuration error",
    "API": "API error",
    "UNKNOWN": "Unknown error",
}

# Verification endpoints
VERIFICATION_ENDPOINTS = {
    "JIRA": "/rest/api/2/myself",
    "GITHUB": "/user",
    "BITBUCKET": "/user",
}

# Webhook verification payloads
WEBHOOK_TEST_PAYLOADS = {
    "JIRA": {"event": "github.push", "repository": "opendiscourse"},
    "BITBUCKET": {"event": "repo:push", "repository": "opendiscourse"},
}

# Status codes
SUCCESS_CODES = range(200, 300)
RETRYABLE_CODES = {
    429,  # Too Many Requests
    500,  # Internal Server Error
    502,  # Bad Gateway
    503,  # Service Unavailable
    504,  # Gateway Timeout
}
