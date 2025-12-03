"""Configuration file for GovInfo document processing.

This module contains all configuration constants that were previously
hardcoded in the govinfo_document_processor.py file.
"""

from typing import Dict, List

# Collection Types Configuration
class CollectionType:
    """Supported document collection types."""
    BILLS = "BILLS"
    CFR = "CFR"
    FEDERAL_REGISTER = "FR"
    COMMITTEE_HEARINGS = "CHRG"
    CONGRESSIONAL_RECORD = "CREC"
    HOUSE_DOCUMENTS = "HDOC"
    SENATE_DOCUMENTS = "SDOC"


# Collection metadata mapping
COLLECTION_TYPES: Dict[str, str] = {
    CollectionType.BILLS: "Bills",
    CollectionType.CFR: "Code of Federal Regulations",
    CollectionType.FEDERAL_REGISTER: "Federal Register",
    CollectionType.COMMITTEE_HEARINGS: "Committee Hearings",
    CollectionType.CONGRESSIONAL_RECORD: "Congressional Record",
    CollectionType.HOUSE_DOCUMENTS: "House Documents",
    CollectionType.SENATE_DOCUMENTS: "Senate Documents",
}

# Schema versions for validation
SCHEMA_VERSIONS: Dict[str, str] = {
    CollectionType.BILLS: "uslm-2.1.0.xsd",
    CollectionType.CFR: "uslm-2.1.0.xsd",
    CollectionType.FEDERAL_REGISTER: "uslm-2.1.0.xsd",
    CollectionType.COMMITTEE_HEARINGS: "uslm-2.1.0.xsd",
    CollectionType.CONGRESSIONAL_RECORD: "uslm-2.1.0.xsd",
    CollectionType.HOUSE_DOCUMENTS: "uslm-2.1.0.xsd",
    CollectionType.SENATE_DOCUMENTS: "uslm-2.1.0.xsd",
}

# Required fields for each collection type
REQUIRED_FIELDS: Dict[str, List[str]] = {
    CollectionType.BILLS: ["title", "version", "document_id", "congress"],
    CollectionType.CFR: ["title", "version", "document_id", "title_number"],
    CollectionType.FEDERAL_REGISTER: ["title", "version", "document_id", "publication_date"],
    CollectionType.COMMITTEE_HEARINGS: ["title", "version", "document_id", "committee"],
    CollectionType.CONGRESSIONAL_RECORD: ["title", "version", "document_id", "session_date"],
    CollectionType.HOUSE_DOCUMENTS: ["title", "version", "document_id", "congress"],
    CollectionType.SENATE_DOCUMENTS: ["title", "version", "document_id", "congress"],
}

# Document processing statuses
class DocumentStatus:
    """Document processing statuses."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"
    VALIDATING = "validating"
    VALID = "valid"
    INVALID = "invalid"
    SKIPPED = "skipped"


# Error types for document processing
class ErrorType:
    """Error types for document processing."""
    SCHEMA_VALIDATION = "schema_validation"
    METADATA_VALIDATION = "metadata_validation"
    VERSION_CONFLICT = "version_conflict"
    PROCESSING_ERROR = "processing_error"
    NETWORK_ERROR = "network_error"
    DATABASE_ERROR = "database_error"
    PARSE_ERROR = "parse_error"


# Processing configuration
PROCESSING_CONFIG = {
    "max_retries": 3,
    "retry_delay": 1.0,  # seconds
    "batch_size": 100,
    "timeout": 30,  # seconds
    "schema_validation_enabled": True,
    "metadata_validation_enabled": True,
    "version_tracking_enabled": True,
}

# XML namespace mappings for different document types
XML_NAMESPACES: Dict[str, Dict[str, str]] = {
    CollectionType.BILLS: {
        "uslm": "http://xml.house.gov/schemas/uslm/1.0",
        "dc": "http://purl.org/dc/elements/1.1/",
    },
    CollectionType.CFR: {
        "uslm": "http://xml.house.gov/schemas/uslm/1.0",
        "dc": "http://purl.org/dc/elements/1.1/",
    },
    CollectionType.FEDERAL_REGISTER: {
        "fr": "http://www.govinfo.gov/metadata/fedregister/",
        "dc": "http://purl.org/dc/elements/1.1/",
    },
}

# XPath expressions for extracting metadata from different document types
METADATA_XPATHS: Dict[str, Dict[str, str]] = {
    CollectionType.BILLS: {
        "title": ".//uslm:title/text()",
        "congress": ".//uslm:congress/text()",
        "session": ".//uslm:session/text()",
        "bill_type": ".//uslm:billType/text()",
        "bill_number": ".//uslm:billNumber/text()",
    },
    CollectionType.CFR: {
        "title": ".//uslm:title/text()",
        "title_number": ".//uslm:titleNumber/text()",
        "chapter": ".//uslm:chapter/text()",
        "part": ".//uslm:part/text()",
    },
    CollectionType.FEDERAL_REGISTER: {
        "title": ".//fr:title/text()",
        "agency": ".//fr:agency/text()",
        "document_number": ".//fr:documentNumber/text()",
        "publication_date": ".//fr:publicationDate/text()",
    },
}

# Database table configurations
DATABASE_TABLES = {
    "documents": {
        "primary_key": "id",
        "indexes": [
            "collection_type",
            "document_id", 
            "status",
            "processed_at",
            ("collection_type", "document_id"),  # Composite index
        ]
    },
    "document_versions": {
        "primary_key": "id",
        "indexes": [
            "document_id",
            "version",
            "created_at",
        ]
    }
}