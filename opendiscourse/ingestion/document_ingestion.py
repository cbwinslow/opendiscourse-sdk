"""Utility functions for ingesting various document types into the database."""

from __future__ import annotations

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

import requests
from bs4 import BeautifulSoup

from vector_store.weaviate_manager import WeaviateManager
from typing_extensions import TypedDict

try:  # Optional dependencies
    from pdfminer.high_level import extract_text as extract_pdf_text
except Exception:  # pragma: no cover - optional dependency may be missing
    extract_pdf_text = None

try:
    import whisper
except Exception:  # pragma: no cover
    whisper = None


class DocumentMetadata(TypedDict, total=False):
    """Metadata used when saving documents."""

    title: str
    source_url: str
    source_id: str
    source_type: str
    source_date: str
    source_collection: str
    created_at: datetime
    document_type: Optional[str]
    type: Optional[str]


def _get_db_connection():
    """Create a database connection using environment variables."""
    import psycopg2

    return psycopg2.connect(
        dbname=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        host=os.getenv("POSTGRES_HOST"),
        port=os.getenv("POSTGRES_PORT"),
    )


def _save_document(content: str, metadata: DocumentMetadata) -> Optional[int]:
    """Save document content and metadata to the database."""
    weaviate_manager = WeaviateManager()

    try:
        conn = _get_db_connection()
    except Exception as exc:  # pragma: no cover - database may be unavailable
        logging.error("Database connection failed: %s", exc)
        return None

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO documents (
                    title,
                    content,
                    source_url,
                    source_id,
                    source_type,
                    source_date,
                    source_collection,
                    created_at,
                    document_type
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    metadata.get("title", "Untitled"),
                    content,
                    metadata.get("source_url", ""),
                    metadata.get("source_id", ""),
                    metadata.get("source_type", ""),
                    metadata.get("source_date", ""),
                    metadata.get("source_collection", ""),
                    metadata.get("created_at", datetime.utcnow()),
                    metadata.get("document_type"),
                ),
            )
            doc_id = cur.fetchone()[0]
            conn.commit()

            # --- Placeholder for Entity and Declaration Extraction ---
            # Future work: Add NLP logic here to extract entities and declarations
            extracted_entities = []  # Placeholder list
            extracted_declarations = [] # Placeholder list
            # --- End Placeholder ---

            # --- Ingest into Weaviate ---
            # Add extracted entities to Weaviate
            for entity_data in extracted_entities:
                 weaviate_manager.add_entity(entity_data)
            # Add extracted declarations to Weaviate
            for declaration_data in extracted_declarations:
                 weaviate_manager.add_declaration(declaration_data)
    except Exception as exc:  # pragma: no cover - db errors
        conn.rollback()
        logging.error("Failed to save document: %s", exc)
        return None
    finally:
        conn.close()

    return int(doc_id)

def ingest_text(text: str, metadata: DocumentMetadata) -> Optional[int]:
    """Ingest a plain text document."""

    return _save_document(text, metadata)


def ingest_markdown(path: str | Path, metadata: DocumentMetadata) -> Optional[int]:
    """Ingest a Markdown file as plain text."""

    content = Path(path).read_text(encoding="utf-8")
    return _save_document(content, metadata)


def ingest_pdf(path: str | Path, metadata: DocumentMetadata) -> Optional[int]:
    """Ingest a PDF file using pdfminer if available."""

    if extract_pdf_text is None:  # pragma: no cover - dependency missing
        logging.error("pdfminer.six is not installed")
        return None

    content = extract_pdf_text(str(path))
    return _save_document(content, metadata)


def ingest_website(url: str, metadata: DocumentMetadata) -> Optional[int]:
    """Download a webpage and ingest the text content."""

    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    text = soup.get_text(separator="\n")
    return _save_document(text, metadata)


def ingest_http_code(url: str, metadata: DocumentMetadata) -> Optional[int]:
    """Ingest code from an HTTP endpoint."""

    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return _save_document(resp.text, metadata)


def ingest_video(path: str | Path, metadata: DocumentMetadata) -> Optional[int]:
    """Transcribe and ingest a video file using Whisper if available."""

    if whisper is None:  # pragma: no cover - dependency missing
        logging.error("whisper is not installed")
        return None

    model = whisper.load_model("base")
    result = model.transcribe(str(path))
    return _save_document(result.get("text", ""), metadata)
