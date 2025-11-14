# Semantic Search Workflow

This document outlines how to ingest PDF documents and store their embeddings across multiple vector databases.

## Workflow Steps
1. **Parse PDF** using `pdfminer.six` to extract text.
2. **Generate embeddings** with `sentence-transformers/all-MiniLM-L6-v2`.
3. **Store embeddings** in:
   - **Chroma** via `VectorDatabase` (local persistence).
   - **Pinecone** index `pdf-docs`.
   - **Weaviate** class `PDFDoc` with custom schema.
4. **Translate text** (placeholder in `EmbeddingWorkflow.translate_document`), storing results in the `pdf_document_translations` table.
5. **Query** any of the vector stores for semantic search.

The `scripts/semantic_vector_workflow.py` script provides a minimal reference implementation.

