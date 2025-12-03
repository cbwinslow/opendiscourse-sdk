# Media Intelligence Platform – Comprehensive Context Report

*Prepared for internal LLM consumption – v0.1 (2025‑07‑08)*

---

## 1  Executive Summary

This report consolidates **all key reference material** for the News Media Benchmark / OpenDiscourse initiative into a single, structured document that large‑language‑models (LLMs) can load as long‑term context. It captures the project’s mission, architecture, agent design, data pipelines, technical stack, compliance posture, and current task status. Use it as a *single source of truth* when prompting autonomous agents or fine‑tuning context windows.

---

## 2  Vision & Core Mission

* Create a **real‑time, AI‑augmented news‑intelligence platform** that monitors mainstream media, social media, and government documents.
* Provide **transparent bias, accuracy, and consistency ratings** for outlets, journalists, politicians, and influencers.
* Equip the public with *searchable datasets, dashboards, and automated fact‑checks* to foster accountability and informed decision‑making.

---

## 3  High‑Level System Overview

```
User / Admin            ⬅───►  Web UI  (React / Next.js / Tailwind)
                               |
MAS Orchestrator  ──►  CrewAI / LangChain (Python, FastAPI gateway)
                               |
           ┌───────────┬───────────┬───────────┐
           │           │           │           │
    Research‑Agent  Content‑Gen  SEO‑Agent  Fact‑Check … (n)
           │           │           │           │
           └──────────▶ Knowledge / Memory Layer ◀──────────┘
                               |
   • Vector DB (Weaviate/Pinecone) – embeddings & RAG
   • Relational DB (PostgreSQL + pgvector) – articles, tasks, logs
                               |
 External Tools ➜  OpenRouter (LLMs, web‑search, PDF OCR)
                   Ghost CMS API (publishing)
                   Zapier / n8n (peripheral automations)
```

*The AI Overseer* governs quality control, conflict resolution, cost optimisation, and final publish decisions.

---

## 4  Multi‑Agent Roles & Synergies

| Agent                   | Core Responsibilities                              | Key Tools                                 |
| ----------------------- | -------------------------------------------------- | ----------------------------------------- |
| **Topic ID**            | Surface trending topics from RSS, X, Google Trends | OpenRouter\:online, NewsAPI               |
| **Research**            | Gather & synthesise sources; load PDFs; embed docs | OpenRouter PDF engines, Vector DB         |
| **Content Generation**  | Draft article in Markdown under pseudonym          | LLM (GPT‑4o/Claude‑3), Persona DB         |
| **SEO**                 | Keyword analysis, meta tags, schema JSON‑LD        | textstat, OpenRouter, Ghost custom fields |
| **Fact‑Check**          | Verify claims, assign confidence score             | Web search plugin, structured notes       |
| **Ethics & Compliance** | Bias & disclosure scanning                         | LLM prompts, rule‑set                     |
| **Publishing**          | Push final HTML to CMS, update XML sitemap         | Ghost Admin API                           |
| **AI Overseer**         | Gatekeeper & orchestrator                          | LangChain judge LLM + deterministic rules |

---

## 5  Data Pipelines

### 5.1  Media & Social Streams

* Transcribe TV/radio via Whisper; scrape RSS/headlines; ingest X posts.
* Sentiment & stance clustering using embeddings ➜ Vector DB.

### 5.2  Government Documents

* Crawler stack (Scrapy + Playwright) aimed at `.gov`/govinfo APIs; advanced discovery via CT logs & ASN mapping.
* PDF/OCR → text → metadata extractor (spaCy, LexNLP) → pgvector.

### 5.3  OpenDiscourse Forum

* Debezium CDC stream → Weaviate; RAG endpoints provide contextual replies and debate summaries.

---

## 6  Technical Stack Snapshot

* **Backend :** Python 3.12 · FastAPI · LangChain / CrewAI
* **Frontend :** React + Vite + Tailwind (+ shadcn/ui)
* **LLM Gateway :** OpenRouter (GPT‑4o, Claude‑3, Gemini 1.5, Mixtral‑8x7b, etc.)
* **Databases :** PostgreSQL + pgvector · Weaviate (Docker) for embeddings
* **Infra :** Kubernetes (EKS/GKE) · Ceph + S3 for storage · Redis/Celery for task queues
* **CI/CD :** GitHub Actions · Docker‑build · Helm charts
* **Observability :** ELK or Prometheus + Grafana · Langfuse/OpenTelemetry for LLM traces

---

## 7  Software Requirements & Microgoals

### 7.1  Functional Requirements (excerpt)

1  Multi‑Agent orchestration with Ollama, Agent‑Zero, Codex.
2  Microgoal tracking in `project_tasks.md`.
3  Automation scripts for DB migration, health checks, backups.
4  Comprehensive docs in `PROJECT_STRUCTURE.md`, `DEVELOPMENT.md`, `AGENT.md`.

### 7.2  Current Microgoal Board (status)

*❑ Integrate Ollama local agent – TODO*
*☑ Codex delegation workflow – DONE*
*❑ Finalize committee/member DB schemas – In progress*

---

## 8  Deployment & Ops Highlights

* **Reference script:** `deploy/deploy.sh` spins up full Kubernetes stack with NVIDIA NIM RAG workers for heavy embeddings workload.
* **Scaling:** HPA auto‑scales web pods (3‑10) and RAG worker pods (5‑20) based on CPU.
* **Secrets management:** Kubernetes Secrets + Vault integration; API keys never in repo.
* **Backup:** `dbBackup.sh` + Ceph snapshots; restore automation included.

---

## 9  Ethics, Legal & Compliance

* AI disclosures comply with CA SB‑942 and Utah AI Policy Act.
* Content carries provenance metadata & confidence scores; inline citations link to source snippets.
* Fact‑checking agent + Overseer enforce zero‑tolerance for misinformation and hate speech.
* Copyright stance: platform claims compilation & editorial arrangement; purely AI‑generated segments acknowledged per US Copyright Office guidance.

---

## 10  Future Roadmap

| Phase         | Goal                                             | ETA     |
| ------------- | ------------------------------------------------ | ------- |
| **Boot**      | Compose stack (Weaviate + Verba)                 | 2 days  |
| **RAG MVP**   | `/ask` endpoint in OpenDiscourse                 | 1 week  |
| **Graph‑RAG** | NodeRAG over bills & votes                       | 2 weeks |
| **UX Polish** | Debate summariser + badges                       | 2 weeks |
| **Stretch**   | Opinion Divergence Radar, edge‑cached embeddings | Q4 2025 |

---

## 11  Appendices

* **A  Document Map:** SRS, Project Structure, AI News Framework PDF, Deployment Guide, Committee/Member TODOs.
* **B  Prompt Templates:** (*omitted here to save context window; see `prompts/` folder*)
* **C  API Reference Endpoints:** Ghost Admin v5, MCP Server, Ollama agent.

---

*End of consolidated context report.*
