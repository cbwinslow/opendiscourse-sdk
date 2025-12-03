#!/usr/bin/env python3
"""Workflow for PDF ingestion and semantic search across Chroma, Pinecone, and Weaviate."""
import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, List

import pinecone
import weaviate
from pdfminer.high_level import extract_text
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

from opendiscourse.services.vector_store import VectorDatabase

load_dotenv()
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


@dataclass
class PDFDocument:
    """Simple representation of a PDF document."""

    doc_id: int
    title: str
    content: str
    metadata: Dict[str, Any]


@dataclass
class PDFTranslation:
    """Translated text of a PDF document."""

    doc_id: int
    language: str
    translated_text: str
    summary: str | None = None


class EmbeddingWorkflow:
    """Generate embeddings and store them in multiple vector DBs."""

    def __init__(self) -> None:
        self.model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        self.vector_db = VectorDatabase(collection_name="pdf_docs")
        pinecone.init(
            api_key=os.getenv("PINECONE_API_KEY"),
            environment=os.getenv("PINECONE_ENVIRONMENT"),
        )
        self.pinecone_index = pinecone.Index("pdf-docs")
        self.weaviate_client = weaviate.Client(
            url=os.getenv("WEAVIATE_URL", "http://localhost:8080")
        )
        self._ensure_weaviate_schema()

    def _ensure_weaviate_schema(self) -> None:
        schema = {
            "classes": [
                {
                    "class": "PDFDoc",
                    "vectorizer": "none",
                    "properties": [
                        {
                            "name": "doc_id",
                            "dataType": ["int"],
                            "description": "Document ID",
                        },
                        {
                            "name": "title",
                            "dataType": ["text"],
                            "description": "Document title",
                        },
                        {
                            "name": "content",
                            "dataType": ["text"],
                            "description": "Raw text",
                        },
                    ],
                }
            ]
        }
        existing = self.weaviate_client.schema.get()
        if not any(cls["class"] == "PDFDoc" for cls in existing.get("classes", [])):
            self.weaviate_client.schema.create(schema)

    def _embed(self, text: str) -> List[float]:
        return self.model.encode(text, convert_to_numpy=True).tolist()

    def add_pdf(self, pdf_path: str, doc_id: int, title: str) -> None:
        text = extract_text(pdf_path)
        metadata = {"source_file": os.path.basename(pdf_path)}
        document = PDFDocument(
            doc_id=doc_id, title=title, content=text, metadata=metadata
        )
        self.vector_db.add_document(doc_id, text, metadata)
        vector = self._embed(text)
        self.pinecone_index.upsert([(str(doc_id), vector, {"title": title})])
        self.weaviate_client.batch.add_data_object(
            {"doc_id": doc_id, "title": title, "content": text}, "PDFDoc", vector
        )

    def translate_document(
        self, document: PDFDocument, language: str = "en"
    ) -> PDFTranslation:
        # Placeholder translation step, replace with real model or API
        translated = document.content  # In practice call translation API
        return PDFTranslation(
            doc_id=document.doc_id, language=language, translated_text=translated
        )


if __name__ == "__main__":
    workflow = EmbeddingWorkflow()
    # Example usage: ingest sample.pdf with id 1
    if os.path.exists("sample.pdf"):
        workflow.add_pdf("sample.pdf", 1, "Sample PDF")
        logger.info("PDF ingested into all vector stores")
