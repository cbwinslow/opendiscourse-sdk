# Congress.gov Relational Data Model

The schema described below synthesizes official Congress.gov documentation, publicly available data
samples, and structural cues from the website. It is designed to accommodate every major collection
published by the API while remaining normalized and query-friendly.

> **Note:** Congress.gov evolves continuously. Treat this model as a strong baseline and monitor the
> API changelog for new fields or entities that may require schema extensions.

## Core Reference Tables

| Table | Purpose |
| --- | --- |
| `congress.sessions` | One row per numbered Congress (e.g., 118th), including start/end dates and calendar year range. |
| `congress.chambers` | Enumerates the House, Senate, and Joint designations used by multiple resources. |
| `congress.parties` | Catalogues political parties for member affiliation history. |
| `congress.states` | ISO-like references for U.S. states and territories, re-used across members and committees. |

## People and Organizations

- **Members**: Stored in `congress.members` with biographical metadata. Temporal service information
  lives in `congress.member_terms`, enabling many-to-one relationships across Congress sessions,
  chambers, and parties.
- **Committees**: Captured by `congress.committees` with optional `parent_committee_id` for
  subcommittees. Committee membership (including leadership roles) is managed via
  `congress.committee_members`.

## Legislative Instruments

| Entity | Tables | Highlights |
| --- | --- | --- |
| Bills & Resolutions | `congress.bills`, `congress.bill_titles`, `congress.bill_actions`, `congress.bill_text_versions`, `congress.bill_summaries`, `congress.bill_subjects`, `congress.bill_cosponsors`, `congress.related_bills` | Covers metadata, multi-lingual titles, action history, full-text versions, CRS summaries, topical subjects, and co-sponsorship data. |
| Amendments | `congress.amendments`, `congress.amendment_actions`, `congress.amendment_sponsors` | Mirrors the bill structure for amendment records. |
| Nominations | `congress.nominations`, `congress.nomination_actions`, `congress.nomination_candidates` | Tracks presidential nominations and Senate action. |
| Treaties | `congress.treaties`, `congress.treaty_actions`, `congress.treaty_topics` | Stores treaty documents and consideration steps. |
| Congressional Records | `congress.congressional_record_sections`, `congress.congressional_record_pages` | Enables ingestion of daily Congressional Record text and metadata. |
| Committee Materials | `congress.committee_reports`, `congress.hearings`, `congress.hearing_witnesses` | Supports published reports, hearing schedules, and witness rosters. |

## Legislative Activity

- **Actions and Votes**: All legislative actions are normalized in `congress.bill_actions` and related
  tables. Roll call votes from both chambers live in `congress.roll_calls` with individual positions in
  `congress.roll_call_votes`.
- **Calendars**: Floor calendars and schedule entries are modeled in `congress.floor_calendars` and
  `congress.floor_calendar_entries`.

## Supporting Structures

- **Documents & Media**: `congress.documents` stores references to PDFs, XML, and other artifacts,
  linking them back to primary entities through join tables.
- **Search Indexing**: The schema includes `tsvector` columns (e.g., `search_document`) in several
  tables to enable PostgreSQL full-text search acceleration.
- **Audit Columns**: Every table carries `created_at`, `updated_at`, and immutable natural keys from
  the API, making the ingestion process idempotent.

## Entity Relationship Diagram (Textual)

```
members 1---* member_terms *---1 chambers
members 1---* bill_sponsors *---1 bills
bills   1---* bill_actions
bills   1---* bill_text_versions
bills   *---* subjects (via bill_subjects)
bills   *---* committees (via bill_committees)
bills   *---* roll_calls *---* members (via roll_call_votes)
amendments *---1 bills (via parent_bill_id)
```

## API Alignment

- **Pagination**: All API collections use cursor-based pagination. The ingestion pipeline stores the
  `next` token in `congress.ingest_checkpoints` for resumability.
- **Change Tracking**: Congress.gov publishes `lastModifiedDate` fields. These populate
  `updated_at` columns and support incremental refreshes with `--changed-since` CLI filters.
- **Identifiers**: Primary keys follow the API's composite keys (e.g., bill type + number + congress)
  to avoid synthetic IDs where unnecessary.

## Future Extensions

1. **Historical Data Normalization**: Some early Congresses have incomplete metadata. Consider
   augmenting the schema with archival datasets when available.
2. **Event Streams**: If near-real-time updates are required, add Kafka topics fed by the ingestion
   script and consumers that apply change sets to the database.
3. **Analytic Warehousing**: Mirror the normalized schema into star schemas in your analytics layer
   for simplified reporting (e.g., `fact_votes`, `dim_member`).

