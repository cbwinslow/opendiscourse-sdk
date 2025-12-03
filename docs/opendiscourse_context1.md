# Government Document Ingestion Workflow Report

## Purpose

This report describes the end-to-end workflow for ingesting legal and legislative documents from govinfo.gov and congress.gov into a local database system, including SQL and vector databases. It covers data extraction, normalization, entity linking, legal NLP analysis, and reporting.

---

## Overview of Workflow

### 1. **Source Data Acquisition**

* **Sources:**

  * [govinfo.gov Bulk Data](https://www.govinfo.gov/bulkdata): Prepackaged dumps by document type and date.
  * [govinfo.gov API](https://www.govinfo.gov/developers/api): Real-time, document-by-document REST access.
  * [congress.gov Bulk Data & API](https://github.com/LibraryOfCongress/api.congress.gov): Bulk download and API for bills, summaries, roll calls, etc.
* **Automation:**

  * Use scheduled jobs (cron, Airflow, or server-side scheduler) to poll for new documents or data updates.
  * Download and cache all document files and metadata. Support multiple formats (XML, JSON, TXT, PDF). Maintain a local manifest of ingested document IDs and last-ingested timestamp to avoid duplication.

### 2. **Metadata Parsing & Normalization**

* **Parsing:**

  * Extract fields: document ID, title, publication date, document type (bill, hearing, law), sponsors, cosponsors, committees, agency, status, links (PDF, XML, HTML), keywords.
* **Normalization:**

  * Standardize dates, names, and type values. Map government source fields to internal schema for compatibility (e.g., always store `bill_type` and `congress_number` for bills).
  * Validate all mandatory fields; handle missing/irregular data with logging and optional fallbacks.

### 3. **Document Storage**

* **SQL Table Design:**

  * Store metadata and fulltext in a `documents` table with unique document ID, source, timestamps, and all parsed fields.
  * Use upsert logic (insert or update if exists) to avoid duplicates.
* **Raw Document Archive:**

  * Optionally store original XML/JSON/PDFs in object storage or blob field for full traceability.

### 4. **Text Preprocessing**

* **Extraction:**

  * Extract plain text from XML or PDF using text extraction tools (e.g., PDFMiner, xml.etree, Tika).
* **Cleaning:**

  * Remove headers, footers, page numbers, watermarks, and special characters. Normalize whitespace and line breaks.
* **Chunking Preparation:**

  * Detect section headers ("Sec. 1", "Findings", etc.) and paragraph boundaries. Flag chunk starts and ends for downstream processing.

### 5. **Embedding & Vector Database Storage**

* **Embedding:**

  * Use embedding models (OpenAI, NVIDIA NIM, Legal-BERT, or BGE via Ollama/Verba) to convert document or chunked text into high-dimensional vectors.
* **Vector DB Storage:**

  * Store vectors in a vector DB (pgvector, Weaviate, Pinecone), linking each vector to its document ID and section/chunk ID.
  * Support for similarity search, nearest neighbor queries, and RAG workflows.

### 6. **Entity Extraction & Ingestion**

* **Named Entity Recognition (NER):**

  * Apply legal-domain NER models (LexNLP, Legal-BERT, spaCy) to extract people, organizations, places, referenced bills, agencies, dates, codes, etc.
* **Entity Table Ingestion:**

  * Insert new entities into `entities` table with unique IDs, names, type (person/org/law/bill), and attributes. Use fuzzy matching or lookups to avoid duplicates.
  * Enrich entities with additional API queries (e.g., get member details from congress.gov) if available.
* **Linkage:**

  * Create foreign key or many-to-many links between document and entities, with join tables for multi-entity references.

### 7. **Relationship & Citation Extraction**

* **Relationships:**

  * Extract structured relations (e.g., "Senator X sponsors Bill Y", "Committee Z reports on Topic Q"). Store as tuples (doc\_id, entity\_id, relation\_type, context).
* **Citations:**

  * Parse references to other bills, US Code sections, previous acts, court cases. Store in a citation table for cross-document navigation and analysis.

### 8. **Section/Clause Chunking**

* **Chunking Strategy:**

  * Split documents into semantically meaningful sections, clauses, or atomic provisions. Use section headers, enumerated items, or LLM-assisted chunking.
* **Chunk Indexing:**

  * Store chunks with positional info (start, end, section name/number) for fine-grained retrieval and RAG.

### 9. **Summarization & Classification**

* **Summarization:**

  * Generate concise summaries for entire documents and each major section using LLMs or dedicated summarization models.
* **Classification:**

  * Assign document type (e.g., "appropriation bill", "resolution", "committee report") and topic labels (e.g., "health", "defense", "civil rights") using rule-based or ML classifiers.

### 10. **Fact/Event Extraction**

* **Fact Mining:**

  * Use LLMs or regex to extract real-world actions, mandates, appropriations, deadlines, and effective dates from text.
* **Event Table:**

  * Store structured event or fact records with links to their originating clause/section for compliance, reporting, and analytics.

### 11. **Logging, Validation & Reporting**

* **Processing Logs:**

  * Record all actions, warnings, and errors to a persistent log file and/or logging table in SQL.
* **Validation:**

  * Run unit/integration tests for ingestion, NER, entity linking, and chunking.
  * Periodically review data quality and completeness.
* **Reporting:**

  * Produce analytics reports: total docs ingested, entities extracted, relationship/citation coverage, data quality metrics, and error rates. Use dashboards for monitoring pipeline health.

---

## Microgoals Breakdown (Action Items)

| Step | Microgoal                                                  | Criteria/Definition                                            |
| ---- | ---------------------------------------------------------- | -------------------------------------------------------------- |
| 1    | Implement ingestion scripts for govinfo.gov & congress.gov | New docs are downloaded and stored; incremental sync supported |
| 2    | Parse and normalize document metadata                      | Metadata ready for SQL insertion                               |
| 3    | Store document in `documents` SQL table                    | Unique ID, timestamps, no duplicates                           |
| 4    | Extract & clean plain text                                 | Usable text extracted, headers/footers removed                 |
| 5    | Generate & store text embeddings                           | Embeddings stored and linked in vector DB                      |
| 6    | Run NER & ingest entities                                  | Entities extracted and inserted/enriched in `entities` table   |
| 7    | Extract relationships & citations                          | Relationship/citation tables populated                         |
| 8    | Chunk text into sections/clauses                           | Indexed, searchable chunks stored                              |
| 9    | Summarize & classify documents                             | Summaries/classifications available in SQL                     |
| 10   | Extract facts/events                                       | Structured event/fact table populated                          |
| 11   | Logging, status, and validation                            | Process logs and data validation in place                      |

---

## Example Ingestion Flow (Pseudocode)

1. **Schedule ingestion**: `fetch_govinfo_docs.py` runs daily or as needed.
2. **For each new or updated document:**

   * Fetch document metadata and files via API or bulk data.
   * Parse and normalize metadata. Validate all required fields.
   * Insert or update document record in `documents` SQL table.
   * Extract, clean, and preprocess plain text.
   * Split text into sections/clauses; index for search.
   * Generate embeddings for text/chunks and store in vector DB.
   * Run NER for entities (people, orgs, bills, laws); insert or enrich in `entities` table.
   * Extract and insert relationships (e.g., sponsorships) and citations (references).
   * Summarize document and sections; classify document type and topic.
   * Extract facts/events (mandates, appropriations, deadlines).
   * Log all steps, errors, and outcomes. Update monitoring dashboards/status tables.

---

## Visual Diagram (Workflow)

**1. API/Bulkdata Fetch** → **2. Metadata Parse** → **3. SQL Insert** → **4. Text Clean/Extract** → **5. Embeddings/Vector DB** → **6. NER & Entities** → **7. Relationships/Citations** → **8. Chunking** → **9. Summarize/Classify** → **10. Fact Extraction** → **11. Logging/Report**

---

## References & Tools

* govinfo.gov/api & bulkdata docs
* congress.gov API & bulkdata
* Legal NLP models: LexNLP, Legal-BERT, CaseLaw-BERT, spaCy legal models, RAG pipelines (Verba, Weaviate, HyDE)
* PDF/XML extractors: pdfminer, tika, xml.etree, PyMuPDF
* Embedding: OpenAI, NVIDIA NIM, Ollama, Weaviate, BGE, Legal-BERT
* Scheduling: cron, Airflow, Celery
* Monitoring: Grafana, custom SQL dashboards

---

This report may be used for onboarding, delegation to AI agents, and as a blueprint for automation or code generation.
