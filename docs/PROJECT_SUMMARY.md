**Project Summary & Description**

The OpenDiscourse platform is a comprehensive, AI-powered media intelligence and discourse analysis system. It is designed to systematically extract, analyze, fact-check, and provide context for information sourced from social media, government records, news articles, and public forums. The platform’s core mission is promoting transparency, enhancing accountability, and supporting informed public discourse.

Structured around a robust, multi-layered architecture, the platform employs ingestion pipelines, retrieval-augmented generation (RAG) agents, intelligent document indexing, vector databases, entity tracking, and a coordinated multi-agent orchestration framework. Leveraging advanced large language models (LLMs) such as Ollama, Codex, and Agent-Zero, along with vectorization tools like pgvector and Weaviate, it ensures efficient data processing and insightful analysis. Background workers operate continuously, managing real-time tasks and ensuring traceability through a microgoal-based task management system.

**Process Flow**

1. **Data Ingestion**: Gathers documents, tweets, posts, and transcripts from APIs (e.g., govinfo.gov, congress.gov, Twitter) and web crawlers (Scrapy, Amass, Playwright), alongside PDF processing with OCR and metadata extraction.
2. **Document Processing**: Ingested data undergoes parsing, cleaning, classification, chunking, and embedding using sophisticated models. Results are stored and indexed for quick retrieval.
3. **Entity Extraction and Attribution**: Utilizes Named Entity Recognition (NER) and dependency parsing to identify key figures, institutions, dates, legislation, and other significant entities, linking them to detailed internal profiles.
4. **Microgoal Management**: Each analytical task is decomposed into microgoals via a Directed Acyclic Graph (DAG) system, assigning them efficiently to specialized AI agents.
5. **Advanced Retrieval and Analysis**: Agents retrieve context from vector databases, generating detailed responses, summaries, or insights, all with comprehensive citation tracking.
6. **Interactive UI and User Feedback**: A React-based interface enables user interaction for queries, fact-checking, exploration of debate summaries, and participation in verification through gamified activities.
7. **Data Storage and Monitoring**: Maintains comprehensive logs and records for all processes, ensuring auditability and accountability in microgoal registries and agent logs.

**Feature Overview**

* **Ingestion Pipelines**: Manages structured and unstructured data from various sources, including OCR and metadata extraction.
* **Entity Profiling**: Tracks key individuals and institutions, documenting stances, interactions, and evolving narratives.
* **RAG Engine**: Facilitates real-time, context-aware querying and content summarization.
* **Fact-Checking**: Verifies social media claims and provides transparent credibility scoring.
* **Voice Transcription**: Processes real-time audio chats for analysis.
* **Gamified User Verification**: Encourages community involvement in content verification.
* **Debate Analysis**: Provides automated summaries and identifies discourse clusters.
* **Opinion Visualization**: Graphically represents ideological diversity within discussions.
* **Graph-based Analysis**: Develops interconnected knowledge graphs for in-depth contextual insights.

---

**Software Requirements Specification (SRS)**

**Project:** OpenDiscourse Media Intelligence Platform

**Functional Requirements**

* Multi-agent orchestration utilizing Codex, Ollama, and Agent-Zero
* DAG-based microgoal planning and execution
* Continuous document analysis through background workers
* Integration of robust search engines (PostgreSQL, Weaviate)
* PDF processing including OCR and metadata management
* Comprehensive entity recognition and relationship mapping
* Real-time fact-checking and claim verification
* Voice transcription for live discussions
* Interactive and gamified user interfaces
* Advanced visualizations for discourse analysis

**Non-Functional Requirements**

* Complete and transparent logging
* Robust security for data storage and API access
* Continuous integration and deployment (CI/CD) via GitHub Actions
* Scalable deployment using Kubernetes and Docker
* Modular architecture for ease of maintenance and extension

**Traceability**
All defined microgoals and tasks are fully documented and traceable within the project management systems.

---

**Next Steps**

* Finalize integration with government document APIs (govinfo.gov and congress.gov).
* Implement advanced PDF OCR and sanitization processes.
* Deploy and optimize the entity extraction and profiling systems.
* Enhance the retrieval and embedding systems with advanced chunking and HyDE methods.
* Fully operationalize the DAG-based task orchestration system with clear agent responsibilities.
* Implement comprehensive real-time social media monitoring and verification.
* Develop the interactive and gamified components of the UI.
* Set up robust CI/CD pipelines and complete Kubernetes-based deployment processes.
* Expand and refine project documentation, including detailed system diagrams and ERDs.
