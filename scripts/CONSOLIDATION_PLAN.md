# Script Consolidation Plan for Open Discourse

## Status: ✅ Completed (as of July 12, 2025)

## Goals
- Retain all unique logic and effort from existing scripts
- Reduce duplication by grouping scripts by function
- Make maintenance and onboarding easier

## Proposed Structure

### 1. Data Ingestion & Population
- **Directory:** `scripts/data_ingestion/`
- **Consolidate:**
  - `populate_database.py`
  - `scrape_documents.py`
  - `save_articles.py`
  - Any related helpers

### 2. RAG & NLP Pipeline
- **Directory:** `scripts/rag/`
- **Consolidate:**
  - `rag_data_management.py`
  - `rag_lightweight.py`
  - `rag_nlp_operations.py`
  - `rag_orchestrator.py`
  - `rag_query_reporting.py`
  - `semantic_vector_workflow.py`
  - `vector_analysis.py`
  - `embedding_analysis.py`

### 3. Database & Setup
- **Directory:** `scripts/setup/`
- **Consolidate:**
  - `check_imports.py`
  - `setup_integrations.py`
  - `init_db.py`
  - `update_imports.py` (from `database/`)

### 4. Reporting
- **Directory:** `scripts/reporting/`
- **Consolidate:**
  - `report_builder.py`

### 5. Testing
- **Directory:** `scripts/tests/`
- **Consolidate:**
  - `test_rag_scripts.py`
  - `test_integration.js`

### 6. Runner
- **Directory:** `scripts/`
- **Keep:**
  - `run.py` (as main entry point)

## Notes
- All original scripts should be preserved in a `scripts/legacy/` folder after consolidation for reference.
- Update or create a `SCRIPTS.md` to document the new structure and usage.
- Refactor code to use modules/functions where poss
