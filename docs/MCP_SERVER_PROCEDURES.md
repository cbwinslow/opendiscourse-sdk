# MCP Server Procedures

This document outlines the procedures for using, maintaining, and extending the OpenDiscourse MCP servers.

## 1. Overview

The MCP servers provide a standardized interface for AI agents to interact with the OpenDiscourse data ingestion pipeline. They are located in the `servers/` directory:

- `servers/congress`: Congress.gov data
- `servers/openstates`: OpenStates.org data
- `servers/govinfo`: GovInfo.gov data

## 2. Installation & Setup

### Prerequisites
- Python 3.10+
- `uv` or `pip`
- Valid API keys in `.env` file

### Installation
Run the following commands to install the servers in editable mode:

```bash
pip install -e servers/congress
pip install -e servers/openstates
pip install -e servers/govinfo
```

## 3. Usage Procedures

### Starting a Server
To start a server, use the `mcp` CLI or run the python module directly:

```bash
# Congress
python servers/congress/src/congress_mcp/server.py

# OpenStates
python servers/openstates/src/openstates_mcp/server.py

# GovInfo
python servers/govinfo/src/govinfo_mcp/server.py
```

### Ingesting Data
AI agents can use the exposed tools to trigger ingestion.

**Example: Ingesting Congress Bills**
1.  Call `ingest_bills(congress=118)`
2.  The server validates API keys.
3.  The server runs the `CongressBillsIngestor`.
4.  Logs are written to `logs/mcp_congress.log`.
5.  Status is returned to the agent.

## 4. Maintenance & Troubleshooting

### Logging
All server activities are logged to the `logs/` directory.
- `logs/mcp_congress.log`
- `logs/mcp_openstates.log`
- `logs/mcp_govinfo.log`

Check these logs for errors or detailed progress information.

### Common Issues
- **API Key Errors**: Ensure `CONGRESS_API_KEY`, `OPENSTATES_API_KEY`, and `GOVINFO_API_KEY` are set in `.env`.
- **Database Errors**: Ensure PostgreSQL is running and the `opendiscourse` database exists.

## 5. Extension Procedures

To add new tools to a server:

1.  Identify the existing ingestion script in `scripts/`.
2.  Import the script in the server file (e.g., `servers/congress/src/congress_mcp/server.py`).
3.  Define a new tool using the `@mcp.tool()` decorator.
4.  Wrap the script execution in a try-except block.
5.  Return a user-friendly string describing the result.

**Example:**
```python
@mcp.tool()
def ingest_new_data_type(param: str) -> str:
    try:
        # Call existing script logic
        result = existing_script.run(param)
        return f"Success: {result}"
    except Exception as e:
        return f"Error: {e}"
```
