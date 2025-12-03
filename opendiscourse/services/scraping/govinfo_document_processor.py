"""Document processor for GovInfo documents.

This module provides functionality to process, validate, and store documents
from the GovInfo API, including bills, regulations, and other government documents.
"""

# Standard library imports
import hashlib
import json
import logging
import os
from typing import Any, Dict, List, Optional, TypedDict, Union
from xml.etree import ElementTree as ET

# Third-party imports
import psycopg2
import requests
import xmlschema
from dotenv import load_dotenv
from psycopg2.extensions import connection as PgConnection

# Local imports
from ...config.govinfo_config import (
    CollectionType,
    DocumentStatus,
    ErrorType,
    COLLECTION_TYPES,
    SCHEMA_VERSIONS,
    REQUIRED_FIELDS,
    PROCESSING_CONFIG,
    XML_NAMESPACES,
    METADATA_XPATHS,
)

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Type aliases
JsonDict = Dict[str, Any]
ValidationResult = Dict[str, Union[bool, List[str], str]]


def get_db_connection() -> PgConnection:
    """Get a database connection.

    Returns:
        A connection to the PostgreSQL database.

    Raises:
        psycopg2.OperationalError: If the connection to the database fails.
    """
    try:
        return psycopg2.connect(
            dbname=os.getenv("DB_NAME", "opendiscourse"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", ""),
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432"),
        )
    except psycopg2.Error as e:
        logger.error("Failed to connect to database: %s", str(e))
        raise


def validate_schema(content: str, collection: str) -> ValidationResult:
    """Validate XML content against USLM schema.

    Args:
        content: The XML content to validate.
        collection: The collection type (e.g., 'BILLS', 'CFR').

    Returns:
        A dictionary containing:
        - is_valid: Boolean indicating if validation passed
        - errors: List of error messages
        - schema_version: Version of the schema used for validation
    """
    try:
        schema_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "docs",
            "ref",
            "uslm",
            SCHEMA_VERSIONS.get(collection, "uslm-2.1.0.xsd"),
        )

        if not os.path.exists(schema_path):
            error_msg = f"Schema file not found: {schema_path}"
            logger.error(error_msg)
            return {
                "is_valid": False,
                "errors": [error_msg],
                "schema_version": "unknown",
            }

        schema = xmlschema.XMLSchema(schema_path)
        schema.validate(content)

        return {
            "is_valid": True,
            "errors": [],
            "schema_version": SCHEMA_VERSIONS.get(collection, "unknown"),
        }

    except xmlschema.XMLSchemaException as e:
        logger.error("Schema validation error: %s", str(e))
        return {
            "is_valid": False,
            "errors": [f"Schema validation failed: {str(e)}"],
            "schema_version": SCHEMA_VERSIONS.get(collection, "unknown"),
        }
    except Exception as e:  # pylint: disable=broad-except
        logger.exception("Unexpected error during schema validation")
        return {
            "is_valid": False,
            "errors": [f"Unexpected error during validation: {str(e)}"],
            "schema_version": SCHEMA_VERSIONS.get(collection, "unknown"),
        }


def validate_metadata(metadata: JsonDict, collection: str) -> ValidationResult:
    """Validate document metadata against required fields for the collection.

    Args:
        metadata: Dictionary containing document metadata.
        collection: The collection type (e.g., 'BILLS', 'CFR').

    Returns:
        A dictionary containing:
        - is_valid: Boolean indicating if all required fields are present
        - errors: List of error messages for missing fields
    """
    errors: List[str] = []

    # Get required fields from configuration
    required_fields = REQUIRED_FIELDS.get(collection, ["title", "version", "document_id"])

    # Check for missing required fields
    for field in required_fields:
        if not metadata.get(field):
            errors.append(f"Missing required field: {field}")

    # Check for empty values in required fields
    for field, value in metadata.items():
        if field in required_fields and not value:
            errors.append(f"Empty value for required field: {field}")

    return {
        "is_valid": len(errors) == 0,
        "errors": errors,
        "schema_version": "n/a",  # For consistency with validate_schema return type
    }


def calculate_content_hash(content: str) -> str:
    """Calculate a SHA-256 hash of the content for version tracking.

    Args:
        content: The content to hash.

    Returns:
        A hexadecimal string representing the SHA-256 hash of the content.
    """
    try:
        return hashlib.sha256(content.encode("utf-8")).hexdigest()
    except Exception as e:  # pylint: disable=broad-except
        logger.error("Failed to calculate content hash: %s", str(e))
        raise ValueError("Failed to calculate content hash") from e


def find_previous_version(
    doc_id: str, collection: str, conn: PgConnection
) -> Optional[Dict[str, Any]]:
    """Find the most recent previous version of a document in the database.

    Args:
        doc_id: The document identifier.
        collection: The collection type (e.g., 'BILLS', 'CFR').
        conn: An active database connection.

    Returns:
        A dictionary containing the previous version's id, content, and version,
        or None if no previous version exists.

    Raises:
        psycopg2.DatabaseError: If there's an error executing the database query.
    """
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT id, content, version
            FROM documents
            WHERE collection_type = %s
            AND document_id = %s
            AND status = %s
            ORDER BY processed_at DESC
            LIMIT 1
            """,
            (collection, doc_id, DocumentStatus.COMPLETED),
        )

        if result := cursor.fetchone():
            return {
                "id": result[0],
                "content": result[1],
                "version": result[2],
            }
        return None
    except psycopg2.Error as e:
        logger.error("Database error finding previous version: %s", str(e))
        raise
    finally:
        cursor.close()


class ProcessedDocument(TypedDict):
    """Type definition for a processed document."""

    doc_id: str
    content: str
    metadata: JsonDict
    schema_validation: ValidationResult
    metadata_validation: ValidationResult
    content_hash: str
    previous_version: Optional[Dict[str, Any]]
    status: str
    collection: str


def process_uslm(
    doc_id: str, content: str, collection: str, conn: Optional[PgConnection] = None
) -> Optional[ProcessedDocument]:
    """Process a USLM document with all validation and version tracking.

    Args:
        doc_id: The document identifier.
        content: The XML content of the document.
        collection: The collection type (e.g., 'BILLS', 'CFR').
        conn: Optional database connection. If not provided, a new one will be created.

    Returns:
        A dictionary containing the processed document data or None if processing fails.

    Raises:
        ValueError: If the document content is empty or invalid.
        ET.ParseError: If the XML content is malformed.
    """
    if not content.strip():
        raise ValueError("Document content cannot be empty")

    close_conn = False
    if conn is None:
        conn = get_db_connection()
        close_conn = True

    try:
        # Parse XML content
        try:
            root = ET.fromstring(content)
        except ET.ParseError as e:
            logger.error(
                "Failed to parse XML content for document %s: %s", doc_id, str(e)
            )
            raise

        # Extract metadata with proper error handling
        metadata: JsonDict = {
            "type": "uslm",
            "collection": collection,
            "title": getattr(root.find(".//title"), "text", ""),
            "date": getattr(root.find(".//date"), "text", ""),
            "version": getattr(root.find(".//version"), "text", ""),
            "document_id": getattr(root.find(".//documentId"), "text", doc_id),
        }

        # Validate schema
        schema_validation = validate_schema(content, collection)
        if not schema_validation["is_valid"]:
            logger.error(
                "Schema validation failed for %s: %s",
                doc_id,
                "; ".join(schema_validation["errors"]),
            )
            return None

        # Validate metadata
        metadata_validation = validate_metadata(metadata, collection)
        if not metadata_validation["is_valid"]:
            logger.error(
                "Metadata validation failed for %s: %s",
                doc_id,
                "; ".join(metadata_validation["errors"]),
            )
            return None

        # Extract main content
        text = "".join(
            ET.tostring(section, encoding="unicode", method="xml")
            for section in root.findall(".//section")
        )

        # Calculate content hash for version tracking
        content_hash = calculate_content_hash(text)

        # Check for previous version
        previous_version = find_previous_version(doc_id, collection, conn)

        # Prepare result
        result: ProcessedDocument = {
            "doc_id": doc_id,
            "content": text,
            "metadata": metadata,
            "schema_validation": schema_validation,
            "metadata_validation": metadata_validation,
            "content_hash": content_hash,
            "previous_version": previous_version,
            "status": DocumentStatus.PENDING,
            "collection": collection,
        }

        # Check for changes if previous version exists
        if previous_version:
            previous_content_hash = calculate_content_hash(previous_version["content"])
            if content_hash == previous_content_hash:
                logger.info("Document %s has not changed, skipping update", doc_id)
                result["status"] = DocumentStatus.COMPLETED
            else:
                logger.info("Document %s has changed, update required", doc_id)

        return result

    except Exception as e:  # pylint: disable=broad-except
        logger.exception("Error processing document %s: %s", doc_id, str(e))
        return None
    finally:
        if close_conn and conn is not None:
            try:
                conn.close()
            except Exception:  # pylint: disable=broad-except
                logger.warning("Failed to close database connection")


def process_bill(doc_id, content):
    """Process a bill document."""
    return process_uslm(doc_id, content, "BILLS")


def process_cfr(doc_id, content):
    """Process a CFR document."""
    try:
        # Parse XML content
        root = ET.fromstring(content)

        # Extract metadata
        metadata = {
            "type": "cfr",
            "title": root.find(".//title").text,
            "part": root.find(".//part").text,
            "section": root.find(".//section").text,
            "effective_date": root.find(".//effectiveDate").text,
            "updated_date": root.find(".//updatedDate").text,
        }

        # Extract main content
        text = ET.tostring(root.find(".//text"), encoding="unicode")

        return {"content": text, "metadata": metadata}
    except Exception as e:
        logging.error(f"Error processing CFR {doc_id}: {e!s}")
        return None


def process_federal_register(doc_id, content):
    """Process a Federal Register document."""
    try:
        # Parse XML content
        root = ET.fromstring(content)

        # Extract metadata
        metadata = {
            "type": "federal_register",
            "document_number": root.find(".//documentNumber").text,
            "title": root.find(".//title").text,
            "agency": root.find(".//agency").text,
            "published_date": root.find(".//publishedDate").text,
            "document_type": root.find(".//documentType").text,
        }

        # Extract main content
        text = ET.tostring(root.find(".//text"), encoding="unicode")

        return {"content": text, "metadata": metadata}
    except Exception as e:
        logging.error(f"Error processing Federal Register {doc_id}: {e!s}")
        return None


def save_document(
    doc_id: str,
    content: str,
    metadata: dict[str, Any],
    schema_validation: dict[str, Any],
    metadata_validation: dict[str, Any],
    status: str,
    collection: str,
) -> None:
    """Save document to PostgreSQL database with all validation and version tracking."""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Insert document
        cursor.execute(
            """
            INSERT INTO documents (
                document_id,
                title,
                content,
                metadata,
                schema_version,
                schema_validation_result,
                metadata_validation_result,
                collection_type,
                collection_metadata,
                status,
                processed_at,
                is_valid,
                validation_errors,
                version,
                previous_version_id,
                next_version_id
            ) VALUES (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                CURRENT_TIMESTAMP,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s
            ) RETURNING id
        """,
            (
                doc_id,
                metadata.get("title", ""),
                content,
                metadata,
                schema_validation.get("schema_version", ""),
                json.dumps(schema_validation),
                json.dumps(metadata_validation),
                collection,
                json.dumps(
                    {
                        "collection_type": COLLECTION_TYPES.get(collection, "unknown"),
                        "collection_code": collection,
                    }
                ),
                status,
                schema_validation["is_valid"] and metadata_validation["is_valid"],
                json.dumps(
                    schema_validation.get("errors", [])
                    + metadata_validation.get("errors", [])
                ),
                metadata.get("version", ""),
                metadata.get("previous_version_id", None),
                None,  # Next version ID will be set when a new version is created
            ),
        )

        new_doc_id = cursor.fetchone()[0]
        conn.commit()

        # If this is a new version, update previous version's next_version_id
        if metadata.get("previous_version_id"):
            cursor.execute(
                """
                UPDATE documents
                SET next_version_id = %s
                WHERE id = %s
            """,
                (new_doc_id, metadata["previous_version_id"]),
            )
            conn.commit()

        logging.info(f"Saved document with ID: {new_doc_id}")

    except Exception as e:
        conn.rollback()
        logging.error(f"Error saving document: {e!s}")
    finally:
        cursor.close()
        conn.close()


def process_document(doc_id: str, collection: str, content: str) -> None:
    """Process a document with full validation and error handling."""
    try:
        # Update document status to processing
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO documents (document_id, collection_type, status)
            VALUES (%s, %s, %s)
            ON CONFLICT (document_id, collection_type)
            DO UPDATE SET status = %s
        """,
            (doc_id, collection, DocumentStatus.PROCESSING, DocumentStatus.PROCESSING),
        )
        conn.commit()

        # Process using USLM schema
        result = process_uslm(doc_id, content, collection)

        if result:
            # Save document with validation results
            save_document(
                doc_id,
                result["content"],
                result["metadata"],
                result["schema_validation"],
                result["metadata_validation"],
                DocumentStatus.COMPLETED,
                collection,
            )
        else:
            # Update status to error if processing failed
            cursor.execute(
                """
                UPDATE documents
                SET status = %s,
                    error_message = %s,
                    processed_at = CURRENT_TIMESTAMP
                WHERE document_id = %s
                AND collection_type = %s
            """,
                (DocumentStatus.ERROR, "Processing failed", doc_id, collection),
            )
            conn.commit()

    except Exception as e:
        logging.error(f"Error processing document {doc_id}: {e!s}")
        try:
            # Update status to error if there was a database error
            cursor.execute(
                """
                UPDATE documents
                SET status = %s,
                    error_message = %s,
                    processed_at = CURRENT_TIMESTAMP
                WHERE document_id = %s
                AND collection_type = %s
            """,
                (DocumentStatus.ERROR, str(e), doc_id, collection),
            )
            conn.commit()
        except:
            pass  # Best effort to update status
    finally:
        if "cursor" in locals():
            cursor.close()
        if "conn" in locals():
            conn.close()


def fetch_and_process_collection(collection):
    """Fetch and process documents from a specific collection."""
    base_url = "https://api.govinfo.gov"
    api_key = os.getenv("GOVINFO_API_KEY")

    # Get documents for collection
    documents_url = f"{base_url}/packages?collectionCode={collection}&api_key={api_key}"
    response = requests.get(documents_url)
    response.raise_for_status()
    documents = response.json()

    # Process each document
    for doc in documents["packages"]:
        try:
            # Get document content
            content_url = f"{base_url}/packages/{doc['packageId']}/content-detail.xml?api_key={api_key}"
            content_response = requests.get(content_url)

            if content_response.status_code == 200:
                process_document(doc["packageId"], collection, content_response.text)
            else:
                logging.warning(f"No content available for {doc['packageId']}")

        except Exception as e:
            logging.error(f"Error processing document {doc['packageId']}: {e!s}")


def main():
    """Main function to process all document collections."""
    logging.info("Starting document processing...")

    # List of collections to process
    collections = ["BILLS", "CFR", "FR"]

    for collection in collections:
        logging.info(f"Processing collection: {collection}")
        fetch_and_process_collection(collection)

    logging.info("Document processing completed")


if __name__ == "__main__":
    main()
