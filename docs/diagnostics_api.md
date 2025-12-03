# Diagnostics API

## Endpoints

### GET `/diagnostics/linux`
- Runs the LinuxDiagnosticCollector and returns a structured system diagnostics report (hardware, network, errors, etc).
- Example response:
```json
{
  "hardware": { ... },
  "network": [ ... ],
  "collection_errors": []
}
```

### POST `/ingest/diagnostics`
- Accepts a diagnostics report (JSON) and optional metadata (host, tags, notes), stores it in the `diagnostics_reports` table.
- Request body:
```json
{
  "report": { ... },
  "host": "hostname.example.com",
  "tags": ["prod", "linux"],
  "notes": "Routine health check"
}
```
- Example response:
```json
{
  "report_id": 1,
  "status": "ingested into DB"
}
```

## Database Schema

Table: `diagnostics_reports`
- `id SERIAL PRIMARY KEY`
- `report JSONB NOT NULL` (full diagnostics report)
- `collected_at TIMESTAMP DEFAULT now()`
- `host TEXT`
- `tags TEXT[]`
- `notes TEXT`

## Usage
- Use the GET endpoint to collect diagnostics from a running Linux system.
- Use the POST endpoint to ingest diagnostics data into the RAG database for later search, analytics, or reporting.
