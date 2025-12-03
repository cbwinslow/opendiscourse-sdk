"""Entity utilities module for OpenDiscourse.

This module provides utility functions for entity extraction, deduplication,
and relationship inference.
"""

from typing import Any, List, Dict
from .services.entity_extractor import (
    deduplicate_entities,
    infer_relationships,
    extract_declarations,
    extract_entities,
)


class EntityExtractor:
    """Entity extractor utility class."""

    def __init__(self):
        """Initialize the entity extractor."""
        pass

    def deduplicate_entities(
        self, entities: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Deduplicate entities based on text and type."""
        return deduplicate_entities(entities)

    def infer_relationships(
        self, entities: List[Dict[str, Any]], text: str
    ) -> List[Dict[str, Any]]:
        """Infer relationships between entities based on context."""
        return infer_relationships(entities, text)

    def extract_declarations(
        self, entities: List[Dict[str, Any]], text: str
    ) -> List[Dict[str, Any]]:
        """Extract declarations from text."""
        return extract_declarations(entities, text)

    def extract_entities(self, text: str, document_id: int = 0) -> List[Dict[str, Any]]:
        """Extract entities from text."""
        return extract_entities(text, document_id)
