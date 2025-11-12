# Code Improvement Recommendations (Consolidated)

This document consolidates all recommendations from previous project history and dated files.

## General Recommendations

- Implement unit tests for new ingestion functions using temporary files and mocks
- Add pdfminer.six and markdown parsing libraries to requirements for full functionality
- Replace unavailable `bloomberg-api` dependency with a maintained alternative or mock implementation to allow `npm install` to succeed.
- Implement real LangChain integration inside `src/api/rag.js` for document retrieval and embedding.
- Add database migrations and Sequelize models to replace raw SQL queries.
- Expand front-end pages with authentication and better UX.
- Consolidate API configuration into a single module with typed classes.
- Add tests that mock HTTP responses for ingestion scripts.
- Consider isolating test dependencies in a virtual environment to avoid pyenv conflicts with system python.
- Consider implementing a backend endpoint to ingest selected documents into the vector database.
- Add authentication UI for saving EXA API key in localStorage.
- Consider verifying if the `MediaInsightTracker` directory exists in another location or branch. If present, merge its contents into the repository root for easier maintenance.
- Implement real translation support using a dedicated model and store results in `pdf_document_translations`.
- Add automated tests for `scripts/semantic_vector_workflow.py` to verify vector store writes.
- Consider orchestrating the ingestion workflow via a task queue for large batches of PDFs.
- Ensure tasks T-01 through T-12 are prioritized and scheduled for implementation.
- Consider setting up CI to automatically enforce creation of DIFF and RECOMMENDATIONS files on each commit.
- Consider adding continuous integration tests to catch outdated scripts earlier.
- Provide a `scripts/` directory for maintainable operational tasks.
- Remove remaining deployment scripts or consolidate them into a single automation tool if still required.
- Keep example code in `examples/` and maintain minimal docs in the root `README.md`.
- Maintain documentation files in version control even during large cleanups to avoid accidental loss.
- Consider grouping operational scripts under a dedicated `scripts/` directory for clarity.
- Consolidate documentation for all shell scripts in a single `scripts/README.md`.
- Consider replacing custom session auth with Passport.js strategies for OAuth providers.
- Add automated tests for the new tracking API to ensure logs are stored as expected.
- Expand the workspace interface to load historical answers from the server rather than local storage.
- Remove duplicate `get_db` function in `opendiscourse/db/database.py` to avoid confusion.
- Add unit tests for the vector store to validate `add_document` and `search` functionality.

## Python Files

### `opendiscourse-api.py`
1. Load database configuration from environment variables instead of hardcoding credentials.
2. Add error handling for database operations and input validation for request data.
3. Separate models and routes into modules to keep the file concise and improve testability.

### `govinfo_scraper.py`
1. Parameterize database credentials and API keys using environment variables.
2. Break long functions into smaller units (e.g., separate metadata fetching and saving) to reduce complexity.
3. Implement retry logic for HTTP requests with exponential backoff to handle transient network failures.

### `scrape_documents.py`
1. Consolidate repeated request logic into reusable functions and ensure timeouts are set for all network calls.
2. Replace manual SQL operations with an ORM or prepared statements to prevent SQL injection.
3. Add unit tests for database interactions and error cases.

### `search_documents.py`
1. Validate environment variables before initializing external services like Pinecone and OpenAI.
2. Handle exceptions from the embedding service and Pinecone separately for clearer debugging.
3. Provide command‐line interface parameters for query input to facilitate automation.

### `populate_database.py`
1. Wrap database connections in context managers and use parameterized queries to improve security.
2. Add command‐line options to select specific stages (scrape vs. process) for easier reuse.
3. Log progress with document IDs to make troubleshooting simpler.

### `govinfo_document_processor.py`
1. Move large dictionaries such as `COLLECTION_TYPES` and `SCHEMA_VERSIONS` into a configuration file.
2. Refactor repetitive code for XML parsing and validation into helper functions.
3. Add type hints and docstrings for all functions to improve clarity and IDE support.

### `entity_extractor.py`
1. Lazy‐load heavy models (`AutoModelForTokenClassification`) to reduce startup time when not needed.
2. Store embeddings in a dedicated service class rather than directly in the vector database from within extraction logic.
3. Replace duplicated code for database insertions with a single helper that handles errors and commits.

### `retry_decorator.py`
1. Document typical usage examples in the module docstring for easier adoption.
2. Allow logging level to be configurable instead of always using `warning`.
3. Provide jitter in the backoff calculation to avoid thundering herd problems when many retries occur.

### `vector_database.py`
1. Defer model loading until the first operation to save resources if the database is unused.
2. Externalize configuration of the storage directory and embedding model name via environment variables.
3. Add graceful shutdown logic to flush or close resources when the application exits.

### `integration_setup.py`
1. Abstract Jira, GitHub, and Bitbucket operations into separate helper modules for clearer separation of concerns.
2. Replace inline configuration validation with pydantic or dataclasses for stronger typing.
3. Improve logging by including request identifiers or correlation IDs for troubleshooting distributed workflows.

### `verify_integration.py`
1. Consolidate repetitive HTTP request code into a helper that manages headers and retries.
2. Parameterize endpoints and secrets via environment variables to avoid accidental exposure in source control.
3. Use structured logging (e.g., `logging.getLogger(__name__)`) to allow different log levels per module.

### `integration_constants.py`
1. Remove duplicate constant names (e.g., `SUCCESS_CODES` defined twice) to prevent confusion.
2. Group related constants into dataclasses or simple namespaces to clarify their usage.
3. Document expected units for timeouts and backoff factors in comments or docstrings.

### `test_entity_extractor.py`
1. Replace hardcoded project path modifications with relative imports or a test helper module.
2. Use a testing framework assertion library instead of plain `print` statements for results.
3. Mock database interactions to allow running tests without a live PostgreSQL instance.

### Documentation Scripts in `docs/`
- **`news_api.py`, `news_api_functions.py`, `save_articles.py`**
  1. Store API keys in environment variables rather than directly in the source.
  2. Use consistent logging instead of `print` for better diagnostics.
  3. Add argument parsing to allow running example functions from the command line.

## Node.js Files (under `src/`)

### `src/index.js`
1. Handle database connection errors gracefully and exit if initialization fails.
2. Move route registrations into a dedicated function to simplify server setup.
3. Add rate limiting middleware to protect the API from abuse.

### `src/api/*` and `src/services/*`
1. Validate all incoming data using a consistent schema validation library and return detailed error messages.
2. Extract repeated axios request logic into a common helper to handle timeouts and retries.
3. Write unit tests for service methods to verify behavior without relying on external APIs.

### `src/jobs/govinfoMonitor.js` and other job files
1. Schedule jobs using a library like `node-cron` and store schedules in configuration files.
2. Add error handling and logging around each job step to aid monitoring in production.
3. Provide graceful shutdown hooks to stop scheduled tasks when the application exits.

## Shell Scripts
1. Add `set -euo pipefail` to each script to catch errors early and avoid partial execution.
2. Quote variables and paths to prevent word splitting and globbing issues.
3. Provide usage instructions or help flags so users understand the required environment and arguments.

## SQL Files
- Ensure all SQL scripts include `IF NOT EXISTS` guards and use transactional execution to avoid partial updates during setup.

These recommendations aim to enhance maintainability, security, and usability across the project.
