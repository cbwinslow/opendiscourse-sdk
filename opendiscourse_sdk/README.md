# OpenDiscourse SDK

A comprehensive Python library for interacting with government legislative APIs.

## Features

- **Congress.gov API** - Access federal legislative data (bills, members, votes)
- **GovInfo.gov API** - Access government publications and documents
- **OpenStates API** - Access state-level legislative data for all 50 states
- **Strongly Typed** - Full Pydantic models with validation
- **Error Handling** - Comprehensive exception hierarchy
- **Rate Limiting** - Built-in rate limiting and retry logic
- **Well Documented** - Detailed docstrings and examples

## Installation

```bash
pip install opendiscourse-sdk
```

## Quick Start

### Congress.gov API

```python
from opendiscourse_sdk import CongressClient

# Initialize client
client = CongressClient(api_key="your_congress_api_key")

# List recent House bills
bills = client.bills.list(congress=118, bill_type="hr", limit=10)
for bill in bills.bills:
    print(f"H.R. {bill.number}: {bill.title}")

# Get a specific bill
bill = client.bills.get(congress=118, bill_type="hr", number=1)
print(f"Introduced: {bill.introduced_date}")
print(f"Sponsors: {len(bill.sponsors)}")

# List members
members = client.members.list(congress=118, chamber="house", state="CA")
for member in members.members:
    print(f"{member.name} ({member.party}-{member.state})")
```

### GovInfo.gov API

```python
from opendiscourse_sdk import GovInfoClient

# Initialize client
client = GovInfoClient(api_key="your_govinfo_api_key")

# List available collections
collections = client.collections.list()
for collection in collections.collections:
    print(f"{collection.collection_code}: {collection.collection_name}")

# Get packages from a collection
packages = client.packages.list(
    collection="BILLS",
    start_date="2024-01-01",
    end_date="2024-01-31"
)

# Get a specific package
package = client.packages.get("BILLS-118hr1")
print(f"Title: {package.title}")
print(f"Issued: {package.date_issued}")

# Get package content
content = client.packages.get_content("BILLS-118hr1", content_type="xml")
```

### OpenStates API

```python
from opendiscourse_sdk import OpenStatesClient

# Initialize client
client = OpenStatesClient(api_key="your_openstates_api_key")

# Get legislators from a state
legislators = client.legislators.list(jurisdiction="ny")
for leg in legislators.results:
    print(f"{leg.name} ({leg.party})")

# Get bills from a state
bills = client.bills.list(
    jurisdiction="ca",
    session="2023-2024"
)
```

## Authentication

All three APIs require API keys. You can provide them in several ways:

### 1. Direct Parameter

```python
client = CongressClient(api_key="your_key")
```

### 2. Environment Variables

```bash
export CONGRESS_API_KEY="your_key"
export GOVINFO_API_KEY="your_key"
export OPENSTATES_API_KEY="your_key"
```

```python
# Keys will be automatically loaded from environment
client = CongressClient()
```

### 3. .env File

Create a `.env` file in your project root:

```env
CONGRESS_API_KEY=your_congress_key
GOVINFO_API_KEY=your_govinfo_key
OPENSTATES_API_KEY=your_openstates_key
```

## Error Handling

The SDK provides comprehensive error handling:

```python
from opendiscourse_sdk import CongressClient
from opendiscourse_sdk.exceptions import (
    AuthenticationError,
    RateLimitError,
    NotFoundError,
    APIError
)

client = CongressClient(api_key="your_key")

try:
    bill = client.bills.get(congress=118, bill_type="hr", number=99999)
except NotFoundError:
    print("Bill not found")
except RateLimitError as e:
    print(f"Rate limit exceeded. Retry after {e.retry_after} seconds")
except AuthenticationError:
    print("Invalid API key")
except APIError as e:
    print(f"API error: {e}")
```

## Context Manager

Use clients as context managers for automatic resource cleanup:

```python
with CongressClient(api_key="your_key") as client:
    bills = client.bills.list(congress=118, limit=10)
    # Session is automatically closed when exiting the context
```

## Advanced Features

### Custom Timeout and Retry

```python
client = CongressClient(
    api_key="your_key",
    timeout=60,  # 60 second timeout
    rate_limit_delay=1.0,  # 1 second between requests
    max_retries=5  # Retry up to 5 times
)
```

### Pagination

```python
# Get first page
bills_page1 = client.bills.list(congress=118, limit=20, offset=0)

# Get second page
bills_page2 = client.bills.list(congress=118, limit=20, offset=20)
```

## API Reference

### Congress.gov Client

- `client.bills.list()` - List bills
- `client.bills.get()` - Get specific bill
- `client.bills.get_actions()` - Get bill actions
- `client.bills.get_cosponsors()` - Get bill cosponsors
- `client.members.list()` - List members
- `client.members.get()` - Get specific member
- `client.votes.list()` - List votes
- `client.votes.get()` - Get specific vote

### GovInfo.gov Client

- `client.collections.list()` - List all collections
- `client.collections.get()` - Get specific collection
- `client.packages.list()` - List packages from a collection
- `client.packages.get()` - Get specific package
- `client.packages.get_content()` - Get package content

### OpenStates Client

- `client.legislators.list()` - List state legislators
- `client.bills.list()` - List state bills

## Getting API Keys

- **Congress.gov**: https://api.congress.gov/sign-up/
- **GovInfo.gov**: https://www.govinfo.gov/developers/api
- **OpenStates**: https://openstates.org/api/

## Requirements

- Python 3.8+
- pydantic>=2.0.0
- requests>=2.32.0

## License

MIT License

## Contributing

Contributions are welcome! Please see the main OpenDiscourse repository for guidelines.

## Support

For issues or questions:
- GitHub Issues: https://github.com/cbwinslow/opendiscourse/issues
- Documentation: https://github.com/cbwinslow/opendiscourse/tree/main/docs/workflows

## Related Projects

- [OpenDiscourse](https://github.com/cbwinslow/opendiscourse) - Full platform for analyzing political discourse
- [OpenDiscourse Documentation](https://github.com/cbwinslow/opendiscourse/tree/main/docs/workflows) - Comprehensive workflow guides
