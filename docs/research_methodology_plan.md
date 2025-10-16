# Research Methodology & AI Integration Plan

This plan outlines the research workflow for building a political legislation analysis and politician/government assessment platform using embeddings, NLP/NLG, knowledge graphs, and automated data collection.

## 1. Research Objectives
1. **Legislation Understanding**: Extract topics, policy areas, stakeholders, and impacts from bill texts.
2. **Politician Profiling**: Quantify ideology, bias, consistency, and KPI trends from voting records and public statements.
3. **Cross-Source Validation**: Compare social media, press releases, and news coverage against voting behavior to flag inconsistencies.
4. **Alerting & Reporting**: Provide automated, explainable summaries and dashboards for analysts.

## 2. Data Acquisition Strategy
- **Primary Legislative Sources**:
  - `congress.gov`: Bill summaries, voting records, amendment history.
  - `govinfo.gov`: Official documents (PDF, XML) for legislation and hearings.
  - `openstates.org`: State-level bills, roll calls, committee data.
  - `openlegislation` project: (NY State or other jurisdictions) for additional regional coverage.
- **Secondary Sources**:
  - Social media APIs (X/Twitter, Facebook, Instagram, Threads) via official APIs or third-party connectors.
  - News APIs (GDELT, NewsAPI) and RSS feeds.
  - Public financial disclosures and lobbying data.
- **Acquisition Tools**:
  - `crawl4ai` with OpenRouter-hosted LLMs for adaptive scraping, summarization, and metadata extraction.
  - `n8n` automations (see templates) to schedule crawls, deduplicate inputs, and trigger downstream pipelines.
  - `Flowise` for orchestrating AI agent prompts and evaluation loops.

## 3. Data Processing Pipeline
1. **Ingestion Layer**: `scripts/data_ingestion/crawl4ai_openrouter.py` orchestrates crawlers; `source_ingestion_tasks.py` schedules per-source jobs.
2. **Normalization**:
   - Parse bill metadata (title, sponsors, committees, status) and voting roll calls.
   - Normalize person entities using canonical IDs (e.g., bioguide, OpenStates IDs).
   - Convert PDFs to text (Tika, pdfminer) and clean social media text.
3. **Enrichment**:
   - Named entity recognition (spaCy, transformer-based NER) with bias detection tags.
   - Relation extraction to link politicians to votes, bills, and statements.
   - Topic modeling (BERTopic, Top2Vec) and stance classification (fine-tuned BERT/Sentence Transformers).
4. **Storage**:
   - **PostgreSQL**: canonical relational data (bills, votes, people, KPI metrics).
   - **MongoDB/Cassandra**: semi-structured documents, raw crawls, social media posts.
   - **Neo4j**: knowledge graph linking entities, events, claims, and evidence.
   - **Vector Stores**: pgvector or Milvus for embeddings powering semantic search.
5. **Quality Assurance**: Use Langfuse for tracing model outputs, and `diagnostic_tools/` for ingestion QA.

## 4. Embeddings & NLP Methodology
- **Embeddings Models**:
  - Sentence Transformers (e.g., `all-mpnet-base-v2`, `politics-specific` fine-tunes) for semantic similarity.
  - Domain-adapted embeddings via continual learning on legislative corpora.
- **spaCy Pipelines**: Custom NER, dependency parsing, and text categorization with domain-specific labels (policy areas, sentiment).
- **Transformer Models**:
  - BERT/RoBERTa for stance detection, bias classification, misinformation scoring.
  - Long-context models (Longformer, Claude Sonnet via OpenRouter) for lengthy bills.
- **Bias & Misinformation Detection**:
  - Train classifiers using labelled datasets (Media Bias/Fact Check, Poynter IFCN) and reinforcement through fact-check pipelines.
  - Use cross-checking agent (FactChecker) to compare claims with knowledge graph evidence.
- **NLG for Reporting**:
  - Template-guided generation with guardrails via Guardrails.ai or structured prompts.
  - Human-in-the-loop review with Langfuse feedback capture.

## 5. Knowledge Graph Construction
- **Graph Schema**:
  - Nodes: `Person`, `Bill`, `Vote`, `Organization`, `PolicyArea`, `Statement`, `Event`.
  - Relationships: `SPONSORED`, `VOTED_FOR/AGAINST`, `MENTIONS`, `FUNDED_BY`, `ALIGNS_WITH`, `CONTRADICTS`.
  - Properties: timestamps, sources, confidence scores, sentiment/bias metrics.
- **Population Strategy**:
  - Use ingestion pipeline to upsert nodes/edges via Neo4j Python driver.
  - Maintain provenance (source URL, crawl ID) for each relationship.
  - Run periodic deduplication and community detection to surface coalitions.
- **Analytics**:
  - Graph algorithms (PageRank, betweenness, community detection) to derive influence metrics.
  - Connect to reporting dashboards (Superset, Metabase) for visualization.

## 6. KPI & Consistency Tracking
- Define KPIs: attendance, party loyalty, ideological scores, sponsor success rate, alignment between statements and votes.
- Use time-series analysis (Prophet, ARIMA) to track trends.
- Flag anomalies with z-score thresholds and change-point detection.

## 7. Agent & Automation Layer
- **LangChain Agents**: Manage retrieval + reasoning tasks, integrate with OpenRouter models for summarization.
- **Langfuse**: Capture traces, monitor prompt drift, collect human feedback.
- **Flowise**: Build visual agent workflows; integrate with `scripts/data_ingestion` for triggers.
- **n8n Templates**: Automate source-specific ingestion, dedupe, and notifications (see `templates/n8n/`).

## 8. Evaluation Plan
- **Data Quality Metrics**: coverage of votes vs official records, entity resolution accuracy, graph completeness.
- **Model Metrics**: F1 for stance/bias classifiers, BLEU/ROUGE for summaries, retrieval precision@k.
- **Human Review**: periodic audits by policy analysts, tracked in Langfuse.
- **A/B Testing**: compare different embeddings models and prompts using offline evaluation sets.

## 9. Roadmap
1. Stand up ingestion infrastructure (databases, message queues).
2. Implement `crawl4ai` pipelines for federal sources.
3. Build Neo4j schema migrations and ingestion jobs.
4. Develop KPI computation jobs and reporting dashboards.
5. Roll out bias/misinformation detection models and integrate with alerting.
6. Iterate on automation templates and agent orchestration.

## 10. Open Questions
- Preferred canonical database (PostgreSQL vs existing managed service)?
- Which social media APIs are approved for production use?
- Are there licensing constraints for external datasets (GDELT, LegiScan)?
- Confirm retention policies and compliance requirements (GDPR, CCPA).
