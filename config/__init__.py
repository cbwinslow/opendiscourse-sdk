"""Configuration modules for OpenDiscourse."""

from .govinfo_config import (
    COLLECTION_TYPES,
    DATABASE_TABLES,
    METADATA_XPATHS,
    PROCESSING_CONFIG,
    REQUIRED_FIELDS,
    SCHEMA_VERSIONS,
    XML_NAMESPACES,
    CollectionType,
    DocumentStatus,
    ErrorType,
)

__all__ = [
    "CollectionType",
    "DocumentStatus", 
    "ErrorType",
    "COLLECTION_TYPES",
    "SCHEMA_VERSIONS",
    "REQUIRED_FIELDS",
    "PROCESSING_CONFIG",
    "XML_NAMESPACES",
    "METADATA_XPATHS",
    "DATABASE_TABLES",
]