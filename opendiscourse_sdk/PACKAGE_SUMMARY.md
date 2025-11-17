# OpenDiscourse SDK - Package Summary

## Overview

The OpenDiscourse SDK is a production-ready Python library for interacting with three major government legislative APIs:
- **Congress.gov API** - Federal legislative data
- **GovInfo.gov API** - Government publications
- **OpenStates API** - State-level legislative data

## Package Information

**Name:** `opendiscourse-sdk`
**Version:** 1.0.0
**License:** MIT
**Python:** >=3.8
**Status:** Production Ready / PyPI Ready

## Installation

### From PyPI (when published):
```bash
pip install opendiscourse-sdk
```

### From Source:
```bash
cd opendiscourse_sdk
pip install -e .
```

### With Development Dependencies:
```bash
pip install -e ".[dev]"
```

## Quick Start

```python
from opendiscourse_sdk import CongressClient, GovInfoClient, OpenStatesClient

# Congress.gov
congress = CongressClient(api_key="your_congress_key")
bills = congress.bills.list(congress=118, bill_type="hr", limit=10)

# GovInfo.gov
govinfo = GovInfoClient(api_key="your_govinfo_key")
packages = govinfo.packages.list("BILLS", start_date="2024-01-01")

# OpenStates
openstates = OpenStatesClient(api_key="your_openstates_key")
legislators = openstates.legislators.list(jurisdiction="ny")
```

## Architecture

### Design Principles
1. **Object-Oriented** - Clean class hierarchy with resource-based organization
2. **Strongly Typed** - Pydantic models for all data structures
3. **Error Handling** - Comprehensive exception hierarchy
4. **Well Documented** - Docstrings on every class and method
5. **PyPI Ready** - Modern packaging with pyproject.toml

### Package Structure
```
opendiscourse_sdk/
├── __init__.py              # Main package entry
├── base.py                  # Base client class
├── exceptions.py            # Exception classes
├── enums.py                 # Type-safe enumerations
├── models/                  # Pydantic data models
│   ├── common.py
│   ├── congress.py
│   ├── govinfo.py
│   └── openstates.py
├── congress/                # Congress.gov client
│   └── client.py
├── govinfo/                 # GovInfo.gov client
│   └── client.py
└── openstates/              # OpenStates client
    └── client.py
```

## Key Features

### Base Client
- ✅ Automatic retry with exponential backoff
- ✅ Rate limiting enforcement
- ✅ Session management with connection pooling
- ✅ Context manager support
- ✅ Configurable timeouts
- ✅ Comprehensive logging

### Exception Handling
```python
from opendiscourse_sdk.exceptions import (
    APIError,              # Base API error
    AuthenticationError,   # 401/403 errors
    RateLimitError,       # 429 with retry_after
    NotFoundError,        # 404 errors
    ValidationError,      # Pydantic validation errors
)
```

### Enumerations
- `BillType` - hr, s, hjres, sjres, hconres, sconres, hres, sres
- `Chamber` - house, senate, both
- `BillStatus` - introduced, referred, passed_house, etc.
- `GovInfoCollection` - BILLS, FR, CREC, CFR, USCODE, etc.
- `StateCode` - All 50 states + territories
- `Party`, `VoteResult`, `DocumentFormat`, and more

### Pydantic Models
All responses are validated against Pydantic models:
- `Bill`, `BillSummary` - Congressional bills
- `Member` - Members of Congress
- `Vote` - Congressional votes
- `Package` - GovInfo documents
- `Legislator` - State legislators
- `StateBill` - State bills

### Congress.gov Client
```python
client = CongressClient(api_key="your_key")

# Bills
bills = client.bills.list(congress=118, bill_type="hr", limit=20)
bill = client.bills.get(congress=118, bill_type="hr", number=1)
actions = client.bills.get_actions(118, "hr", 1)
cosponsors = client.bills.get_cosponsors(118, "hr", 1)

# Members
members = client.members.list(congress=118, chamber="house", state="CA")
member = client.members.get("P000197")

# Votes
votes = client.votes.list(congress=118, chamber="house")
vote = client.votes.get(congress=118, chamber="house", vote_number=1)
```

### GovInfo.gov Client
```python
client = GovInfoClient(api_key="your_key")

# Collections
collections = client.collections.list()
collection = client.collections.get("BILLS")

# Packages
packages = client.packages.list(
    collection="BILLS",
    start_date="2024-01-01",
    end_date="2024-01-31"
)
package = client.packages.get("BILLS-118hr1")
content = client.packages.get_content("BILLS-118hr1", "xml")
```

### OpenStates Client
```python
client = OpenStatesClient(api_key="your_key")

# Legislators
legislators = client.legislators.list(
    jurisdiction="ny",
    session="2023-2024"
)

# Bills
bills = client.bills.list(
    jurisdiction="ca",
    session="2023-2024"
)
```

## Advanced Usage

### Context Manager
```python
with CongressClient(api_key="your_key") as client:
    bills = client.bills.list(congress=118)
    # Session automatically closed
```

### Custom Configuration
```python
client = CongressClient(
    api_key="your_key",
    timeout=60,              # 60 second timeout
    rate_limit_delay=1.0,    # 1 second between requests
    max_retries=5            # Retry up to 5 times
)
```

### Error Handling
```python
try:
    bill = client.bills.get(118, "hr", 999999)
except NotFoundError:
    print("Bill not found")
except RateLimitError as e:
    print(f"Rate limited. Retry after {e.retry_after} seconds")
    time.sleep(e.retry_after)
except AuthenticationError:
    print("Invalid API key")
except APIError as e:
    print(f"API error: {e}")
```

### Pagination
```python
# Method 1: Manual pagination
page1 = client.bills.list(congress=118, limit=20, offset=0)
page2 = client.bills.list(congress=118, limit=20, offset=20)

# Method 2: Iterate through pages
offset = 0
limit = 20
while True:
    response = client.bills.list(congress=118, limit=limit, offset=offset)
    if not response.bills:
        break
    for bill in response.bills:
        process(bill)
    offset += limit
```

## Testing

### Run Validation
```bash
cd opendiscourse_sdk
python validate_sdk.py
```

### Run Unit Tests (requires pytest)
```bash
pip install pytest pytest-cov
pytest tests/ -v
```

### Run Examples
```bash
# Set API keys
export CONGRESS_API_KEY="your_key"
export GOVINFO_API_KEY="your_key"
export OPENSTATES_API_KEY="your_key"

# Run examples
python examples.py

# Or use the entry point
opendiscourse-sdk-examples
```

## Publishing to PyPI

### Build Distribution
```bash
cd opendiscourse_sdk
python -m build
```

### Upload to PyPI
```bash
python -m twine upload dist/*
```

### Test PyPI (recommended first)
```bash
python -m twine upload --repository testpypi dist/*
```

## API Keys

Get your API keys from:
- **Congress.gov:** https://api.congress.gov/sign-up/
- **GovInfo.gov:** https://www.govinfo.gov/developers/api
- **OpenStates:** https://openstates.org/api/

## Statistics

- **Total Files:** 20 Python files
- **Lines of Code:** 3,651
- **Test Coverage:** Basic unit tests included
- **Documentation:** Complete README with examples
- **Dependencies:** requests, pydantic, urllib3

## Dependencies

### Required
- `requests>=2.32.0` - HTTP client
- `pydantic>=2.0.0` - Data validation
- `urllib3>=1.26.0` - HTTP utilities

### Optional (Development)
- `pytest>=7.0.0` - Testing framework
- `pytest-cov>=4.0.0` - Coverage reporting
- `black>=23.0.0` - Code formatting
- `ruff>=0.1.0` - Linting
- `mypy>=1.0.0` - Type checking

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Ensure all tests pass
5. Submit a pull request

## Support

- **Documentation:** See README.md and inline docstrings
- **Examples:** See examples.py for complete working examples
- **Issues:** https://github.com/cbwinslow/opendiscourse/issues
- **Workflow Guides:** /docs/workflows/ for API-specific guides

## Related Projects

- **OpenDiscourse** - Full platform for analyzing political discourse
- **OpenDiscourse Documentation** - Comprehensive workflow guides

## License

MIT License - See LICENSE file for details

## Changelog

### Version 1.0.0 (2024-11-12)
- Initial release
- Full Congress.gov API support
- Full GovInfo.gov API support
- OpenStates API support (legislators, bills)
- Comprehensive error handling
- Pydantic models for all data structures
- PyPI-ready packaging
- Complete documentation

## Roadmap

Future enhancements:
- [ ] Async client support (aiohttp)
- [ ] CLI interface for quick queries
- [ ] Database integration layer
- [ ] Expanded API coverage (committees, amendments, etc.)
- [ ] GraphQL support for OpenStates
- [ ] Caching layer
- [ ] Bulk operations
- [ ] Export to various formats (CSV, JSON, XML)
- [ ] Sphinx documentation
- [ ] Integration tests with real APIs
- [ ] Performance benchmarks

## Authors

OpenDiscourse Team

## Acknowledgments

- Congress.gov API team
- GovInfo.gov API team
- OpenStates project
- Pydantic developers
- Python community
