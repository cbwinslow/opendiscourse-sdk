"""Templates for ingesting data from the GovInfo APIs and bulk data."""

from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import Optional

import requests

from .document_ingestion import DocumentMetadata, _save_document
from vector_store.weaviate_manager import WeaviateManager

logger = logging.getLogger(__name__)


def ingest_govinfo_api(package_id: str) -> Optional[int]:
    """Fetch a package from the GovInfo API and ingest it."""

    weaviate_manager = WeaviateManager() # Instantiate WeaviateManager

    api_key = os.getenv("GOVINFO_API_KEY")
    if not api_key:
        logger.error("GOVINFO_API_KEY not configured")
        return None

    base_url = "https://api.govinfo.gov/v1/package"
    url = f"{base_url}/{package_id}?api_key={api_key}"
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    text_link = data.get("textLink")
    if not text_link:
        logger.error("No textLink in package %s", package_id)
        return None

    text_resp = requests.get(text_link, timeout=30)
    text_resp.raise_for_status()

    metadata: DocumentMetadata = {
        "title": data.get("title", "GovInfo Document"),
        "source_url": text_link,
        "source_id": package_id,
        "source_type": "govinfo_api",
        "source_date": data.get("dateIssued", ""),
        "source_collection": data.get("collectionCode", ""),
        "created_at": datetime.utcnow(),
        "document_type": data.get("documentType"),
    }

    # Prepare data for Weaviate Document class
    weaviate_document_data = {
        "doc_id": package_id, # Using package_id as doc_id
        "title": metadata["title"],
        "content": text_resp.text,
        "url": metadata["source_url"],
        "publicationDate": metadata["source_date"], # Assuming source_date is in a format Weaviate accepts (ISO 8601)
        "documentType": metadata["document_type"],
        "source": metadata["source_collection"], # Using source_collection as source
        "metadata": metadata # Storing the full metadata as a nested object
    }

    weaviate_manager.add_document(weaviate_document_data)
    return _save_document(text_resp.text, metadata) # Keep existing document saving if needed


def ingest_govinfo_bulkdata(
    collection: str, year: int, file_name: str
) -> Optional[int]:
    """Download a bulk data file from GovInfo and ingest it."""

    weaviate_manager = WeaviateManager() # Instantiate WeaviateManager

    url = f"https://www.govinfo.gov/bulkdata/{collection}/{year}/{file_name}"
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()

    metadata: DocumentMetadata = {
        "title": file_name,
        "source_url": url,
        "source_id": file_name,
        "source_type": "govinfo_bulkdata",
        "source_date": str(year),
        "source_collection": collection,
        "created_at": datetime.utcnow(),
        "document_type": None,
    }
    # Prepare data for Weaviate Document class
    weaviate_document_data = {
        "doc_id": file_name, # Using file_name as doc_id
        "title": metadata["title"],
        "content": resp.text,
        "url": metadata["source_url"],
        "publicationDate": metadata["source_date"], # Assuming source_date is in a format Weaviate accepts (ISO 8601)
        "documentType": metadata["document_type"],
        "source": metadata["source_collection"], # Using source_collection as source
        "metadata": metadata # Storing the full metadata as a nested object
    }

    weaviate_manager.add_document(weaviate_document_data)
    return _save_document(resp.text, metadata) # Keep existing document saving if needed
