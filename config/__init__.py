"""Configuration modules for OpenDiscourse."""

from .govinfo_config import (
    CollectionType,
    DocumentStatus,
    ErrorType,
    COLLECTION_TYPES,
    SCHEMA_VERSIONS,
    REQUIRED_FIELDS,
    PROCESSING_CONFIG,
    XML_NAMESPACES,
    METADATA_XPATHS,
    DATABASE_TABLES,
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