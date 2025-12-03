"""
LangChain Integrations for OpenDiscourse

This package contains LangChain-based implementations and examples
adapted specifically for the OpenDiscourse project.

Modules:
- rag_service: Core RAG (Retrieval-Augmented Generation) service
- rag_api: FastAPI endpoints for RAG functionality
- document_loader_directory: Directory-based document loading utilities
- vectorstore_retriever: Vector store and retrieval utilities
"""

from .rag_service import (
    OpenDiscourseRAGService,
    RAGResult,
    DocumentMetadata,
    create_bill_metadata,
    create_committee_metadata,
)

try:
    from .rag_api import app as rag_api_app
except ImportError:
    # FastAPI might not be available in all environments
    rag_api_app = None

__all__ = [
    "OpenDiscourseRAGService",
    "RAGResult", 
    "DocumentMetadata",
    "create_bill_metadata",
    "create_committee_metadata",
    "rag_api_app",
]

