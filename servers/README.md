# OpenDiscourse MCP Servers

This directory contains Model Context Protocol (MCP) servers for the OpenDiscourse data sources: Congress, OpenStates, and GovInfo.

## Prerequisites

- Python 3.10+
- `uv` or `pip`

## Installation

You can install the dependencies for each server using `pip`:

```bash
pip install -e servers/congress
pip install -e servers/openstates
pip install -e servers/govinfo
```

## Running the Servers

Each server can be run directly using the `mcp` CLI or by running the python module.

### Congress MCP Server

```bash
# Using python module
python servers/congress/src/congress_mcp/server.py
```

### OpenStates MCP Server

```bash
# Using python module
python servers/openstates/src/openstates_mcp/server.py
```

### GovInfo MCP Server

```bash
# Using python module
python servers/govinfo/src/govinfo_mcp/server.py
```

## Tools Available

### Congress
- `ingest_bills(congress, batch_size)`
- `ingest_votes(congress, year)`
- `get_ingestion_status(congress)`

### OpenStates
- `ingest_bills(jurisdiction)`
- `ingest_votes(jurisdiction, year)`
- `get_jurisdiction_status(jurisdiction)`

### GovInfo
- `ingest_bills(congress, batch_size)`
- `ingest_votes(collection, year)`
