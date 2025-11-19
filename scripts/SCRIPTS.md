# Open Discourse Script Directory Structure

This document describes the structure and purpose of each script directory after consolidation.

## 1. Data Ingestion & Population (`scripts/data_ingestion/`)
- `populate_database.py`: Populate the database with initial or bulk data.
- `scrape_documents.py`: Scrape documents from external sources.
- `save_articles.py`: Save articles to the database or storage.

## 2. RAG & NLP Pipeline (`scripts/rag/`)
- `rag_data_management.py`: Manage RAG data flows.
- `rag_lightweight.py`: Lightweight RAG operations.
- `rag_nlp_operations.py`: NLP operations for RAG.
- `rag_orchestrator.py`: Orchestrate RAG pipeline steps.
- `rag_query_reporting.py`: Query and report on RAG data.
- `semantic_vector_workflow.py`: Semantic vector workflow utilities.
- `vector_analysis.py`: Analyze vector data.
- `embedding_analysis.py`: Analyze embeddings.

## 3. Database & Setup (`scripts/setup/`)
- `check_imports.py`: Check Python imports for consistency.
- `setup_integrations.py`: Set up integrations with external services.
- `init_db.py`: Initialize the database.
- `update_imports.py`: Update import statements in codebase.

## 4. Reporting (`scripts/reporting/`)
- `report_builder.py`: Build and generate reports.

## 5. Testing (`scripts/tests/`)
- `test_rag_scripts.py`: Test RAG scripts and pipeline.
- `test_integration.js`: Integration tests for scripts.

## 6. Runner (`scripts/`)
- `run.py`: Main entry point for running scripts.
- `deploy_infrastructure.sh`: Deploy OpenDiscourse infrastructure using Terraform with safety checks.

## Legacy Scripts
- All original scripts are preserved in `scripts/legacy/` for reference.
