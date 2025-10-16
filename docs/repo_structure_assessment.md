# Repository Structure Assessment

## Purpose
This document inventories the current `opendiscourse` repository, explains the role of major directories and notable files, describes how components interact, and flags potential consolidation or cleanup opportunities as part of the repository merge effort.

## Top-Level Directory Overview

| Path | Purpose | Key Interactions | Importance | Cleanup Notes |
| --- | --- | --- | --- | --- |
| `api/` | FastAPI app entrypoint (`main.py`), route definitions, and Pydantic models for API exposure. | Depends on `opendiscourse/` core modules (`services`, `db`, `auth`). Consumed by deployment configs in `docker/` and infrastructure scripts. | **High** – public interface for backend services. | Ensure duplication with `server/` or `web/` APIs is minimized during merge. |
| `opendiscourse/` | Core Python package: data ingestion (`ingestion/`), LangChain integrations, RAG database utilities, service layer. | Used by `api/`, CLI scripts under `scripts/`, and ETL notebooks. | **Critical** – canonical business logic. | Contains legacy modules (e.g., `govdata_api.py`) that overlap with specialized scripts; review for redundancy. |
| `scripts/` | Operational scripts (ingestion, diagnostics, RAG helpers), deployment helpers, and automation entrypoints. | Calls into `opendiscourse/` package and shell tooling (`docker/`, `supabase/`). | **High** – orchestrates batch tasks and diagnostics. | Subfolders (`delegation/`, `rag/`, `reporting/`) should be normalized; some scripts duplicate functionality in `opendiscourse/ingestion`. |
| `docs/` | Project documentation, architecture notes, requirements, and task trackers. | Supports onboarding and planning; referenced by `README.md` and `CLEANUP.md`. | **Medium** – essential for knowledge transfer. | Several documents (e.g., `CLEANUP.md`, `README_CLEANUP.md`) overlap; consider consolidation. |
| `web/` & `webui/` | React/TypeScript frontend projects for dashboards and UI experiments. | Consume backend API endpoints, share config with `server/`. | **Medium** – product-facing UI. | Ensure only one frontend is kept after merging repos; `webui/` may be experimental. |
| `server/` | Alternative backend (likely Node/Express or GraphQL) for the web UI. | Interfaces with `web/`, database migrations, and Supabase. | **Medium** – evaluate overlap with Python API. |
| `rag/`, `search_engine/`, `vector_store/` | Specialized retrieval, semantic search, and vector storage implementations. | Used by ingestion scripts and API for RAG workflows. | **High** – core to semantic capabilities. | Audit for duplication across directories and align on a single vector store abstraction. |
| `nlp/`, `document_processing/`, `flow-framework/` | Experiments and frameworks for NLP pipelines, doc processing, and flow orchestration. | Interact with `scripts/nlp_processor.py` and `opendiscourse/document_loaders.py`. | **Medium** – useful but overlapping experiments. |
| `supabase/`, `terraform/`, `k8s/`, `docker/` | Infrastructure provisioning and deployment assets. | Coupled with CI/CD and devops workflows. | **High** – needed for production deployments. | Validate environment files are current; prune obsolete providers. |
| `examples/`, `templates/`, `monitoring/`, `diagnostic_reports/` | Reference material, template outputs, monitoring configs, historical reports. | Primarily documentation/supporting assets. | **Low-Medium** – retain if still referenced. |
| `_completed/`, `committee_*` docs, `member_*` docs | Legacy project tracking artifacts. | Inform planning but not part of runtime. | **Low** – archive if superseded by other tracking tools. |
| `opendiscourse-docs/` | Documentation submodule containing agent definitions and design guides. | Provides context for MAS architecture. | **Medium** – align with primary `docs/`. |

## Detailed Notes by Area

### Backend and Services
- **`api/` vs `server/`**: Both expose API layers. `api/` is Python/FastAPI, while `server/` hosts a Node-based API. Confirm if both are needed post-merge; consolidate endpoints where possible.
- **`opendiscourse/services/`**: Houses business logic (e.g., politician profiles, legislation scoring). Many scripts in `scripts/` import from here; consider converting scripts into reusable command modules inside the package to avoid drift.
- **`opendiscourse/ingestion/`**: Contains ETL pipelines, but there are parallel ingestion scripts in `scripts/data_ingestion/`. Merge them into a single ingestion framework.

### Data and Storage Layers
- **`opendiscourse/db/` and `vector_store/`**: Manage PostgreSQL connections and vector index configuration. The `rag_database.py` provides a bridge for retrieval pipelines. Ensure migrations (`server/prisma`, `supabase/`, or `drizzle.config.ts`) stay synchronized.
- **`supabase/` & `database` configs**: Provide Terraform, Supabase schema, and Docker Compose for infrastructure. Critical for reproducible deployments.

### Frontend Assets
- **`web/`**: Main React application with TypeScript, Vite, and Tailwind. Contains `src/` components for dashboards and analytics.
- **`webui/`**: Appears to be a separate Next.js or React experiment. Audit usage; if redundant, deprecate.
- **`monitoring/`**: Contains Grafana/Prometheus or Datadog dashboards; ensure these integrate with frontend health checks.

### NLP & AI
- **`nlp/`**: Contains notebooks and scripts for NLP experiments. Some functionalities (NER, embeddings) overlap with `opendiscourse/langchain_integrations`.
- **`rag/` and `search_engine/`**: Provide semantic retrieval pipelines, cross-encoder ranking, and evaluation scripts. These are critical to the legislative analysis use case.
- **`flow-framework/`**: Looks like a microservice orchestration or DAG builder; verify integration with `scripts/delegation`.

### Automation & Diagnostics
- **`scripts/diagnostic_runner.py`** and `diagnostic_tools/`: Evaluate data quality, ingestion status, and pipeline health. Keep for monitoring.
- **`monitoring/`**: Houses dashboards; ensure alignment with `AlertAgent` from doc.

### Legacy / Orphan Candidates
- `document_processing/` vs `documents` in `opendiscourse/`: Some features appear duplicated; audit and unify.
- `github_sync_*` and `copy-doc-repo.sh`: Possibly used for repo mirroring; if merging repositories, ensure they are still needed.
- `examples/` and `_completed/`: Likely archival – move to dedicated archive folder or remove after verification.

## Suggested Cleanup Priorities
1. **Backend Consolidation**: Decide on Python (`api/`) vs Node (`server/`) API. Unify service layers and remove redundant endpoints.
2. **Ingestion Scripts**: Merge `scripts/data_ingestion/*` with `opendiscourse/ingestion` modules. Create a shared configuration system.
3. **Frontend Rationalization**: Evaluate `web/` vs `webui/`. Keep the one actively maintained; decommission the other.
4. **Documentation Merge**: Combine `docs/`, `opendiscourse-docs/`, and various README variants into a single authoritative knowledge base.
5. **Archive Legacy Assets**: Move `_completed`, `committee_*`, `member_*`, and unused scripts into an `archive/` directory pending deletion.
6. **Dependency Audit**: Review `requirements*.txt`, `package-lock.json`, and `pnpm-lock.yaml` to remove unused packages and align with the chosen stack.

## Interactions Summary Diagram (Conceptual)
```
[Data Sources] -> [scripts/data_ingestion] -> [opendiscourse.ingestion] -> [PostgreSQL/Vector Stores/Neo4j]
                                           -> [langchain_integrations] -> [api]/[server]
                                           -> [reporting pipelines] -> [web dashboards]
```

## Next Steps
- Validate actual runtime dependencies to confirm which directories are actively used.
- Coordinate with other `opendiscourse` repositories to standardize module naming and directory layout before merging.
- Implement the research plan described in `docs/research_methodology_plan.md` to align NLP and analytics efforts.
