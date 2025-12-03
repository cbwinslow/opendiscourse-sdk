# Linear Import Guide

This guide outlines how to import core items into Linear via the MCP server or API.

## Payload Shapes
- Pulses: { type: 'pulse', name, description, status, due_date, owner_id, related_issues }
- Customers: { type: 'customer', name, contact_email, account_type, notes }
- Members: { type: 'member', name, role, email, joined_at, status }

## Example Import Payload
{
  "pulses": [ { ... } ],
  "customers": [ { ... } ],
  "members": [ { ... } ]
}

## Import Endpoints (example)
- MCP server endpoint: POST /linear/import
- Expected payload: { pulses: [...], customers: [...], members: [...] }

## Authentication
- Use a Linear API token associated with the target workspace.
- Include as Authorization: Bearer <token> in headers.

## Next Steps
1) Provide Linear workspace/project IDs and an API token.
2) Run import against the MCP server or Linear API using the payload above.
3) Verify created items and link related GitHub issues when applicable.
