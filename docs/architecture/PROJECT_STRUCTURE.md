# Project Structure & File Documentation

This document provides an overview of the files and folders in the `opendiscourse` project, describing their purpose and how they fit into the overall architecture. This will help onboard new contributors, clarify the project layout, and ensure maintainability.

**Last Updated:** After merging v1.0.1 branch with database components, data pipeline workflow, and RAG/govdata integrations.

---

## Root Directory

| File/Folder         | Purpose/Function                                                                                   |
|--------------------|----------------------------------------------------------------------------------------------------|
| `.editorconfig`    | Editor configuration for consistent coding style across different editors                           |
| `.env.example`     | Template for environment variables (API keys, DB URLs, etc.) - moved to config/                   |
| `.gitignore`       | Specifies files/folders to exclude from git version control (e.g., node_modules, secrets, builds)   |
| `.windsurfrules`   | WindSurf IDE specific rules and configurations                                                      |
| `mypy.ini`         | MyPy type checker configuration for Python                                                         |
| `pyproject.toml`   | Python project configuration (dependencies, build system, tools)                                   |
| `setup.cfg`        | Python setup configuration for testing and development tools                                       |

---

## Attached Assets

| File/Folder                        | Purpose/Function                                                                                   |
|------------------------------------|----------------------------------------------------------------------------------------------------|
| `attached_assets/`                 | Project documentation, knowledge base, and project management docs                                 |
| ├─ `document_storage.txt`          | Knowledge base for legislative analysis app                                                        |
| ├─ `govlinks.md`                   | List of government data source links                                                               |
| ├─ `project_summary.md`            | Technical and methodological summary of the platform                                               |
| └─ `project_tasks.md`              | Project task plan and checklist                                                                    |

---

## Client (Frontend)

| File/Folder                        | Purpose/Function                                                                                   |
|------------------------------------|----------------------------------------------------------------------------------------------------|
| `client/`                          | Frontend React app                                                                                 |
| ├─ `index.html`                    | HTML entry point for the React app                                                                 |
| └─ `src/`                          | React source code                                                                                  |
|    ├─ `App.tsx`                    | Main React app component                                                                           |
|    ├─ `main.tsx`                   | React app entry point (mounts App)                                                                 |
|    ├─ `index.css`                  | Global CSS (Tailwind, custom styles)                                                               |
|    ├─ `pages/`                     | Page-level React components (e.g., documents, government-document-crawler, document-detail, etc.)  |
|    └─ `components/`                | Shared UI components (cards, tabs, buttons, etc.)                                                  |
| └─ `OllamaAgentDemo.tsx`               | UI page for submitting prompts to Ollama and viewing results.                                    |
| `client/src/pages/OllamaBatchLogViewer.tsx`             | UI page for viewing Ollama batch logs and documentation.                                         |
| `client/src/pages/OllamaBatchAdmin.tsx`                 | UI page for administering batch prompts and viewing/editing batch logs.                          |
| `client/src/pages/McpBatchLogViewer.tsx`                | UI page for viewing MCP batch logs and results.                                               |

---

## Server (Backend)

| File/Folder                        | Purpose/Function                                                                                   |
|------------------------------------|----------------------------------------------------------------------------------------------------|
| `server/`                          | Backend Express app and services                                                                   |
| ├─ `api.ts`                        | Express API router, defines REST endpoints                                                         |
| ├─ `db.ts`                         | Database connection and Drizzle ORM setup                                                          |
| ├─ `index.ts`                      | Main server entry point, sets up Express, routes, and services                                     |
| ├─ `routes.ts`                     | Registers all API routes and WebSocket handlers                                                    |
| ├─ `vite.ts`                       | Vite integration for dev server and static serving                                                 |
| ├─ `utils.ts`                      | Utility functions (responses, hashing, text cleaning, etc.)                                        |
| ├─ `storage.ts`                    | Storage abstraction and implementation for DB
| ├─ `controllers/`                  | Express controllers for handling business logic (e.g., agent, media)                              |
| ├─ `routes/`                       | Modular route handlers for different API endpoints                                                 |
| ├─ `scripts/`                      | Batch or utility scripts (e.g., batchRAGProcessor, importers)                                      |
| ├─ `services/`                     | Core business logic and integration with external APIs (e.g., govInfo, document analysis)          |
| ├─ `workers/`                      | Background workers (e.g., ragWorker)                                                               |
| ├─ `routes/ollamaAgent.ts`                  | API routes for submitting workloads to Ollama, checking status, and webhook callback.              |
| └─ `services/ollamaAgentService.ts`         | Service for managing Ollama workloads, results, and webhook notifications.                        |
| ├─ `scripts/testOllamaApiCall.ts`                | Script to test the Ollama agent API by submitting a prompt and polling for the result.           |
| `server/mcpServer.ts`                              | Minimal MCP server exposing endpoints to submit and query Ollama agent workflows.                 |
| `server/scripts/scheduleOllamaBatch.ts`                | Script to schedule and execute a batch of prompts with Ollama, log results, and document runs.    |
| `ollama_batch_prompts.json`                            | List of prompts to be executed in a batch by the Ollama agent.                                   |
| `ollama_batch_log.json`                                | Persistent log of all batch runs and their results.                                              |
| `docs/ollama_batch_runs.md`                            | Markdown log of all batch runs, prompts, and results for documentation and traceability.          |

---

## Server Scripts
## Server Scripts

| File/Folder                                 | Purpose/Function                                                                                   |
|---------------------------------------------|----------------------------------------------------------------------------------------------------|
| `server/scripts/dbMigrate.ts`               | Runs database migrations using Drizzle ORM.                                        |
| `server/scripts/dbSeed.ts`                  | Scaffold for seeding the database with initial data.                                               |
| `server/scripts/dbHealthCheck.ts`           | Checks database connectivity and prints status.                                                    |
| `server/scripts/nimApiHealthCheck.ts`       | Checks NVIDIA NIM API key and connectivity.                                                        |
| `server/scripts/updateNimModelConfig.ts`    | Scaffold for updating NIM model config in `k8s/configmap.yaml`.                                    |
| `server/scripts/dbBackup.sh`                | Backs up the PostgreSQL database from the Kubernetes pod.                                          |
| `server/scripts/dbRestore.sh`               | Restores the PostgreSQL database to the Kubernetes pod from a backup.                              |
| `server/scripts/delegateToCodex.ts`         | Delegates coding tasks to OpenAI Codex/ChatGPT via API and saves the result.                      |
| `server/scripts/delegateToOllama.ts`        | Delegates coding tasks to Ollama (local LLM) via REST API and saves the result.                  |
| `server/scripts/ollamaApiHealthCheck.ts`    | Verifies Ollama API health, model availability, and connection status.                            |
| `server/scripts/ollamaModelConfig.ts`       | Manages Ollama model configurations and settings.                                                 |
| `server/scripts/healthCheck.ts`             | Comprehensive health check script for all system components.                                      |
| `server/scripts/monitorAgent.ts`            | Monitors agent health, resource usage, and performance metrics.                                    |
| `server/scripts/agentOrchestrator.ts`       | Orchestrates multi-agent workflows and task delegation.                                           |
| `server/scripts/agentMetrics.ts`            | Collects and reports agent performance and reliability metrics.                                    |
| `server/scripts/vectorStoreManager.ts`      | Manages vector store configuration, updates, and maintenance.                                      |
| `server/scripts/ragMonitor.ts`              | Monitors RAG performance, latency, and result quality.                                            |
---

## Shared

| File/Folder                        | Purpose/Function                                                                                   |
|------------------------------------|----------------------------------------------------------------------------------------------------|
| `shared/`                          | Shared TypeScript code (types, schema) between client and server                                   |
| └─ `schema.ts`                     | Database schema definitions and types for Drizzle ORM                                              |

---

## Docs

| File/Folder                        | Purpose/Function                                                                                   |
|------------------------------------|----------------------------------------------------------------------------------------------------|
| `docs/`                            | Project documentation                                                                              |
| └─ `government_api/`               | Docs for government API integration                                                                |
|    ├─ `govinfo_api_reference.md`   | Reference for GovInfo API                                                                          |
|    └─ `technical_implementation.md`| Technical implementation plan for GovInfo API integration                                          |
| `docs/mcp_api_reference.md`                         | API reference for the MCP server endpoints for Ollama workflow integration.                       |

---

## Deploy

| File/Folder                        | Purpose/Function                                                                                   |
|------------------------------------|----------------------------------------------------------------------------------------------------|
| `deploy/`                          | Deployment scripts and configs                                                                     |
| └─ `deploy.sh`                     | Bash script for Kubernetes/Ceph deployment, scaling, and health checks                            |

---

## Kubernetes (Optional/Prod)

| File/Folder                        | Purpose/Function                                                                                   |
|------------------------------------|----------------------------------------------------------------------------------------------------|
| `k8s/`                             | Kubernetes manifests for production deployment                                                     |
| ├─ `configmap.yaml`                | ConfigMap for environment variables                                                                |
| ├─ `deployment.yaml`               | Main app deployment manifest                                                                       |
| ├─ `namespace.yaml`                | Namespace definition                                                                               |
| ├─ `postgres.yaml`                 | Postgres DB deployment and PVC                                                                     |
| ├─ `rag-workers.yaml`              | RAG worker deployment                                                                              |
| └─ `secrets.yaml`                  | Kubernetes secrets for sensitive config                                                            |

---

## CI/CD

| File/Folder                        | Purpose/Function                                                                                   |
|------------------------------------|----------------------------------------------------------------------------------------------------|
| `.github/workflows/`               | GitHub Actions workflows for CI/CD, linting, testing, and integrations                             |
| ├─ `ci.yml`                        | Main CI workflow: lint, test, and integration triggers                                             |
| └─ `issue-sync.yml`                | Workflow for syncing issues/tickets across platforms                                               |

---

## Documentation

| File/Folder                        | Purpose/Function                                                                                   |
|------------------------------------|----------------------------------------------------------------------------------------------------|
| `DEVELOPMENT.md`                   | Development workflow, microgoal process, and best practices documentation.                         |
| `AGENT.md`                         | AI agent orchestration, setup, and delegation documentation.                                       |
| `SRS.md`                           | Software Requirements Specification with microgoals and measurable criteria.                       |
| `project_tasks.md`                 | Project task board and microgoal tracking.                                                         |

---

## Summary

- All files/folders above are needed for a full-stack, production-ready, and maintainable project.
- Docs and attached assets provide essential knowledge, onboarding, and project management.
- Kubernetes and deploy scripts are optional for local dev but required for scalable production.
- CI/CD workflows automate code quality and integration with external platforms.

---

*For more details on any file or folder, see the inline comments or ask for a deep dive on a specific area.*
