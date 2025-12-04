# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Modern Python packaging via `pyproject.toml`
- Professional README with usage examples
- Comprehensive planning documentation (SRS, features, implementation plan)
- Development guides for AI agents (Gemini, Claude)
- Development journal for tracking progress

## [2.0.0] - In Development

### Added
- **Congress CLI Enhancements**
  - Committee reports ingestion (`ingest-committee-reports`)
  - Committee prints ingestion (`ingest-committee-prints`)
  - Hearings ingestion (`ingest-hearings`)
  - Congressional Record ingestion (`ingest-congressional-record`)
  - Nominations ingestion (`ingest-nominations`)
  - Treaties ingestion (`ingest-treaties`)
  - House communications ingestion (`ingest-house-communications`)
  - Senate communications ingestion (`ingest-senate-communications`)

- **OpenStates CLI Enhancements**
  - `--years-back` parameter for historical bill data
  - Resource manager integration for API keys

- **GovInfo CLI Enhancements**
  - `ingest-collection` bulk command for simplified usage
  - Resource manager integration

- **Infrastructure**
  - 20-year bulk ingestion script (`run_20_year_ingestion.py`)
  - Resource manager for centralized configuration (`scripts/utils/resource_manager.py`)
  - Rate limiting with exponential backoff across all CLIs
  - Extended database schema (`migrations/015_congress_extended_schema.sql`)

### Changed
- All CLIs now use resource manager for API keys
- Improved error handling and retry logic
- Enhanced logging and progress indicators

### Documentation
- `docs/SRS.md` - Software Requirements Specification
- `docs/features.md` - Detailed feature specifications
- `docs/agents.md` - AI agent development guide
- `docs/gemini.md` - Gemini-specific usage patterns
- `docs/claude.md` - Claude-specific best practices
- `docs/journal.md` - Development journal
- `docs/cli_documentation.md` - Comprehensive CLI documentation

## [1.0.0] - 2024-12-03

### Added
- Initial CLI tools for Congress, OpenStates, and GovInfo
- Basic data ingestion capabilities
- PostgreSQL database integration
- Rate limiting and retry mechanisms
- Dry-run mode for testing
- Status commands for all CLIs

### Features
- Congress.gov data ingestion (bills, members, votes, committees)
- OpenStates data ingestion (bills, people, jurisdictions)
- GovInfo data ingestion (collections, packages, granules)

---

## Version History

- **2.0.0** (In Development) - Production-ready package with enhanced features
- **1.0.0** (2024-12-03) - Initial release with basic ingestion capabilities

---

## Migration Guides

### Migrating from 1.x to 2.x

**API Keys:**
- Now loaded automatically via resource manager
- Store in `.env` file (same format as before)
- No code changes required

**Database:**
- Run new migration: `psql opendiscourse < migrations/015_congress_extended_schema.sql`
- Existing data preserved and compatible

**CLI Usage:**
- All existing commands remain backwards compatible
- New features available via additional flags/commands
