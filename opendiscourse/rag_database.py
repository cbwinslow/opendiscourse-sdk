"""Simple RAG database wrapper built on top of the vector store."""

from __future__ import annotations

from .services.vector_store import VectorDatabase, vector_db


class RAGDatabase:
    """High level interface to store and retrieve documents for RAG."""

    def __init__(self, db: VectorDatabase | None = None) -> None:
        self.db = db or vector_db

    def add_document(
        self, document_id: int, content: str, metadata: dict[str, str]
    ) -> None:
        """Add a document to the underlying vector store."""
        self.db.add_document(
            document_id=document_id, content=content, metadata=metadata
        )
        self.db.persist()

    def search(self, query: str, k: int = 5) -> list[tuple[dict[str, str], float]]:
        """Retrieve documents relevant to a query."""
        return self.db.search(query=query, k=k)
