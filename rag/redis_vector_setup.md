# Memorystore for Redis Vector Search & LangChain Integration

## Overview
- Use Google Cloud Memorystore for Redis 7.2+ as a vector store for ultra-low latency RAG, semantic search, and LLM memory.
- Integrates natively with LangChain for Python.

## Key Features
- Native vector data types in Redis 7.2+ (FLAT and HNSW search)
- LangChain integration for vector store, document loader, and chat memory
- Ultra-fast, in-memory vector search for RAG and LLM applications

## Setup Steps
1. **Provision Memorystore for Redis 7.2+**
   - Create an instance in Google Cloud Console
   - Enable vector search features
2. **Connect from Python (LangChain)**
   - Install integration: `pip install langchain-google-memorystore-redis`
   - See [LangChain Memorystore integration docs](https://github.com/googleapis/langchain-google-memorystore-redis-python)
3. **Load Data**
   - Use LangChain Document Loader to load documents
   - Use Vertex AI or other embedding service to generate embeddings
   - Store embeddings and metadata in Memorystore via LangChain Vector Store
4. **RAG Workflow**
   - On user query, generate embedding
   - Use LangChain to search vectors in Memorystore
   - Retrieve top N docs, feed to LLM for grounded answer

## Example Code
See the [official quickstart notebook](https://github.com/googleapis/langchain-google-memorystore-redis-python/blob/main/samples/langchain_quick_start.ipynb) for a full example.

## References
- [Google Cloud Blog: Memorystore for Redis vector search and LangChain](https://cloud.google.com/blog/products/databases/memorystore-for-redis-vector-search-and-langchain-integration)
- [LangChain Memorystore Integration](https://github.com/googleapis/langchain-google-memorystore-redis-python)
