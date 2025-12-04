# OpenDiscourse CLI Tools

Professional CLI tools for ingesting and querying US legislative data from Congress.gov, OpenStates, and GovInfo APIs.

[![PyPI version](https://badge.fury.io/py/opendiscourse.svg)](https://badge.fury.io/py/opendiscourse)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

- 🏛️ **Congress.gov** - Comprehensive bill, member, and voting data
- 🗳️ **OpenStates** - State legislature data for all 50 states + territories
- 📰 **GovInfo** - Federal Register, Congressional Record, and more
- 📊 **Multi-format Export** - JSON, CSV, Parquet, SQLite
- 🔍 **Advanced Filtering** - Complex queries with multiple criteria
- 🔄 **Incremental Sync** - Efficient updates with checkpoints
- ⚡ **High Performance** - Parallel processing, rate limiting, retry logic

## Quick Start

### Installation

```bash
# From PyPI (coming soon)
pip install opendiscourse

# From source (current)
git clone https://github.com/cbwinslow/opendiscourse.git
cd opendiscourse
pip install -e .
```

### Configuration

```bash
# Create .env file from template
cp .env.example .env

# Edit .env and add your API keys
nano .env
```

### Database Setup

```bash
# Interactive database bootstrap
opendiscourse bootstrap

# Or use the dedicated command
opendiscourse-bootstrap
```

### Basic Usage

```bash
# Unified CLI (NEW!)
opendiscourse congress bills 118
opendiscourse states bills ca --years-back 5
opendiscourse govinfo collections

# Legacy individual commands (still supported)
opendiscourse-congress ingest-bills 118
opendiscourse-states ingest-bills ca --years-back 5
opendiscourse-govinfo ingest-collection BILLS

# Verify system setup
opendiscourse verify
```

## Configuration

Create a `.env` file:

```bash
# API Keys
CONGRESS_API_KEY=your_key_here
OPENSTATES_API_KEY=your_key_here
GOVINFO_API_KEY=your_key_here

# Database (PostgreSQL)
DB_HOST=/var/run/postgresql
DB_NAME=opendiscourse
DB_USER=your_username
```

## Advanced Features

### Filtering

```bash
# Filter bills by sponsor, party, state
opendiscourseongress bills \
  --congress 118 \
  --sponsor "Smith" \
  --party "D,R" \
  --cosponsors-min 50
```

### Export Formats

```bash
# Export to CSV
opendiscourse-congress bills --congress 118 --format csv --output bills.csv

# Export to Parquet (columnar)
opendiscourse-congress bills --congress 118 --format parquet --output bills.parquet

# Export to SQLite (portable database)
opendiscourse-congress bills --congress 118 --format sqlite --output bills.db
```

### Incremental Sync

```bash
# Initial sync
opendiscourse-congress sync bills --congress 118

# Later: only fetch new/updated (uses checkpoint from last run)
opendiscourse-congress sync bills --congress 118

# Continuous monitoring (daemon mode)
opendiscourse-congress sync bills --congress 118 --watch --interval 3600
```

## CLI Tools

### Congress CLI (`opendiscourse-congress`)

- **Bills** - All bill types (HR, S, HJRES, etc.)
- **Members** - Representatives and Senators
- **Committees** - Committee rosters and activities
- **Votes** - Roll call votes
- **Hearings** - Committee hearings
- **Reports** - Committee reports
- **Nominations** - Presidential nominations
- **Treaties** - International treaties

### OpenStates CLI (`opendiscourse-states`)

- **Bills** - State legislation
- **People** - State legislators
- **Committees** - State committees
- **Vote Events** - State votes
- **Events** - Legislative events
- **Jurisdictions** - State metadata

### GovInfo CLI (`opendiscourse-govinfo`)

- **Collections** - Available document collections
- **Packages** - Document packages
- **Granules** - Individual documents
- **Congressional Record**
- **Federal Register**

## Documentation

- [Full Documentation](https://opendiscourse.readthedocs.io) (coming soon)
- [API Reference](docs/cli_documentation.md)
- [Feature Specifications](docs/features.md)
- [Development Guide](docs/agents.md)

## Development

### Setup

```bash
# Clone repository
git clone https://github.com/cbwinslow/opendiscourse.git
cd opendiscourse

# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Lint code
ruff check .
black --check .
mypy .
```

### Project Structure

```
opendiscourse/
├── scripts/
│   ├── ingestion/          # CLI tools
│   │   ├── congress_cli.py
│   │   ├── openstates_cli.py
│   │   └── govinfo_cli.py
│   └── utils/              # Shared utilities
├── migrations/             # Database schemas
├── docs/                   # Documentation
├── tests/                  # Test suites
└── pyproject.toml          # Package configuration
```

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgments

- [Congress.gov API](https://api.congress.gov/)
- [OpenStates API](https://docs.openstates.org/api-v3/)
- [GovInfo API](https://api.govinfo.gov/)

## Support

- [Issue Tracker](https://github.com/cbwinslow/opendiscourse/issues)
- [Discussions](https://github.com/cbwinslow/opendiscourse/discussions)

---

**Status**: Active development (v2.0.0 release planned for Q1 2025)
