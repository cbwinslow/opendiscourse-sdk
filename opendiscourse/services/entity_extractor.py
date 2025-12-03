from __future__ import annotations

import json
import logging
import os
import re
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Generator, Optional

import psycopg2
from dotenv import load_dotenv

try:
    import torch
except ImportError:
    torch = None

# Get logger for this module
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()



# Define entity patterns
ENTITY_PATTERNS = {
    "GOVERNMENT_BODY": [
        r"\b(111th|112th|113th|114th|115th|116th|117th|118th) Congress\b",
        r"\bHouse of Representatives\b",
        r"\bSenate\b",
        r"\bSupreme Court\b",
        r"\bExecutive Branch\b",
        r"\bLegislative Branch\b",
        r"\bJudicial Branch\b",
    ],
    "LEGISLATIVE_BODY": [
        r"\bHouse Committee\b",
        r"\bSenate Committee\b",
        r"\bJoint Committee\b",
    ],
    "PERSON": [
        r"\b(Senator|Representative|Congressman|Congresswoman)\s+[A-Z][a-z]+\s+[A-Z][a-z]+\b",
        r"\bPresident\s+[A-Z][a-z]+\b",
        r"\bVice President\s+[A-Z][a-z]+\b",
    ],
}

# Map transformer entity types to our entity types
ENTITY_TYPE_MAP = {
    "PER": "PERSON",
    "ORG": "ORGANIZATION",
    "MISC": "ORGANIZATION",
    "LOC": "ORGANIZATION",
}


@dataclass
class Entity:
    text: str
    label: str
    start: int
    end: int

    def __post_init__(self) -> None:
        if not self.text or not isinstance(self.text, str):
            msg = "Entity text must be a non-empty string"
            raise ValueError(msg)
        if not self.label or not isinstance(self.label, str):
            msg = "Entity label must be a non-empty string"
            raise ValueError(msg)


@contextmanager
def get_db_connection() -> Generator[psycopg2.extensions.connection, None, None]:
    """Context manager for database connections.

    Yields:
        A PostgreSQL database connection

    Raises:
        psycopg2.OperationalError: If connection fails
    """
    connection = None
    try:
        # Use environment variables for database configuration
        connection = psycopg2.connect(
            dbname=os.getenv("DB_NAME", "opendiscourse"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "postgres"),
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432"),
        )
        yield connection

    except psycopg2.Error as e:
        logger.error("Database connection error: %s", str(e))
        if connection:
            connection.rollback()
        raise
    except Exception as e:
        logger.error("Unexpected error with database connection: %s", str(e))
        if connection:
            connection.rollback()
        raise
    finally:
        if connection:
            try:
                connection.close()
            except Exception as e:
                logger.warning("Error closing database connection: %s", str(e))


def extract_entities(text: str, document_id: int) -> list[dict[str, Any]]:
    """Extract entities from text using transformers and custom patterns."""
    try:
        # Get the lazy-loaded NER pipeline
        ner_pipeline = get_ner_pipeline()

        # Process with transformers
        pipeline = get_ner_pipeline()
        if pipeline is None:
            logging.warning("NER pipeline not available, using pattern-based extraction only")
            entities = []
        else:
            entities = pipeline(text)

        # Extract relevant information from transformer output
        tokens = [entity["word"] for entity in entities]
        predicted_labels = [entity["entity"] for entity in entities]
        scores = [entity["score"] for entity in entities]

        transformer_entities: list[dict[str, Any]] = []
        current_entity: Entity | None = None
        current_entity_text = ""

        for token, label in zip(tokens, predicted_labels):
            if label != "O":  # O means no entity
                if current_entity is None:
                    current_entity = Entity(
                        text=token,
                        label=label,
                        start=0,  # Will be updated later
                        end=0,  # Will be updated later
                    )
                    current_entity_text = token
                elif label == current_entity.label:
                    current_entity_text += " " + token
                else:
                    _process_entity_text(
                        current_entity_text,
                        current_entity.label,
                        text,
                        scores,
                        transformer_entities,
                    )
                    current_entity = Entity(
                        text=token,
                        label=label,
                        start=0,  # Will be updated later
                        end=0,  # Will be updated later
                    )
                    current_entity_text = token

        if current_entity is not None:
            _process_entity_text(
                current_entity_text,
                current_entity.label,
                text,
                scores,
                transformer_entities,
            )

        return _process_entity_list(transformer_entities, document_id, text)

    except Exception as e:
        error_msg = f"Error extracting entities: {e!s}"
        logger.error(error_msg, exc_info=True)
        raise RuntimeError(error_msg) from e


def _process_entity_text(
    entity_text: str,
    label: str,
    text: str,
    scores: list[float],
    entities_list: list[dict[str, Any]],
) -> None:
    """Process a single entity's text and add it to the entities list."""
    clean_text = entity_text.replace("##", "").strip()
    start_pos = text.find(clean_text)
    if start_pos >= 0:  # Only add if found
        # Use first score from the list as fallback
        score = scores[0] if scores else 0.5
        entities_list.append(
            {
                "entity": clean_text,
                "start": start_pos,
                "end": start_pos + len(clean_text),
                "score": float(score),
                "label": label,
            }
        )


def _process_entity_list(
    entities: list[dict[str, Any]], document_id: int, text: str
) -> list[dict[str, Any]]:
    """Process the list of extracted entities."""
    result: list[dict[str, Any]] = []
    seen_entities: set[str] = set()

    for ent in entities:
        entity_text = ent["entity"]
        if entity_text in ENTITY_TYPE_MAP and entity_text not in seen_entities:
            seen_entities.add(entity_text)
            result.append(
                {
                    "text": entity_text,
                    "type": ENTITY_TYPE_MAP[entity_text],
                    "start": ent["start"],
                    "end": ent["end"],
                    "confidence": ent["score"],
                }
            )

            # Check if this is a new entity
            _process_vector_db_entity(entity_text, ent, document_id)

    return result


def _process_vector_db_entity(
    entity_text: str, entity: dict[str, Any], document_id: int
) -> None:
    """Process an entity for vector database operations."""
    try:
        # Search for similar entities in the vector database
        search_results = vector_db.search(query=entity_text, k=3) if vector_db else []

        # If no similar entities found, add this as new
        if not search_results:
            # Create embedding for new entity
            embedding = vector_db.embeddings.embed_query(entity_text)
            _ = vector_db.vector_store.add_texts(
                texts=[entity_text],
                metadatas=[
                    {
                        "entity_type": ENTITY_TYPE_MAP.get(entity.get("label", "")),
                        "source_document": document_id,
                        "confidence": entity.get("score", 0.0),
                    }
                ],
                embeddings=[embedding],
            )
            vector_db.persist()
    except Exception as e:
        logging.error(
            "Error in vector database operation for entity %s: %s", entity_text, str(e)
        )


def deduplicate_entities(entities: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Deduplicate entities based on text and type."""
    seen = set()
    unique_entities = []

    for entity in entities:
        key = (entity["text"].lower(), entity["type"])
        if key not in seen:
            seen.add(key)
            unique_entities.append(entity)

    return unique_entities


def infer_relationships(
    entities: list[dict[str, Any]], text: str
) -> list[dict[str, Any]]:
    """Infer relationships between entities based on context."""
    relationships = []

    # Create entity text mapping
    entity_map = {e["text"].lower(): e for e in entities}

    # Look for membership relationships
    membership_patterns = [
        r"\b(\w+)\s+of\s+(\w+)\b",
        r"\b(\w+)\s+in\s+(\w+)\b",
        r"\b(\w+)\s+with\s+(\w+)\b",
    ]

    for pattern in membership_patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            member = match.group(1)
            group = match.group(2)

            if member.lower() in entity_map and group.lower() in entity_map:
                relationships.append(
                    {
                        "entity_id": entity_map[member.lower()]["id"],
                        "related_entity_id": entity_map[group.lower()]["id"],
                        "relationship_type": "MEMBER_OF",
                        "confidence": 0.7,
                    }
                )

    return relationships


def extract_declarations(
    entities: list[dict[str, Any]], text: str
) -> list[dict[str, Any]]:
    """Extract declarations from text."""
    declarations = []

    # Look for declarative patterns
    declaration_patterns = [
        r"\bshall\b",
        r"\bmust\b",
        r"\bwill\b",
        r"\brequired\b",
        r"\bprohibited\b",
        r"\bmandated\b",
    ]

    for entity in entities:
        # Look for declarations near entity mentions
        for pattern in declaration_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                # Get context around declaration
                start = max(0, match.start() - 200)
                end = min(len(text), match.end() + 200)
                context = text[start:end]

                declarations.append(
                    {
                        "entity_text": entity["text"],
                        "declaration_text": context,
                        "declaration_type": "ACTIONABLE",
                        "confidence": 0.7,
                    }
                )

    return declarations


class DatabaseHelper:
    """Helper class for database operations with error handling and commits."""

    @staticmethod
    def execute_query_with_result(query: str, params: tuple, operation_name: str) -> Optional[Any]:
        """Execute a query that returns a result with proper error handling.

        Args:
            query: SQL query to execute
            params: Parameters for the query
            operation_name: Name of the operation for logging

        Returns:
            Query result or None if failed
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, params)
                    result = cursor.fetchone()
                    conn.commit()
                    logger.debug("Successfully completed %s", operation_name)
                    return result
        except Exception as e:
            logger.error("Error in %s: %s", operation_name, str(e), exc_info=True)
            return None

    @staticmethod
    def execute_query_no_result(query: str, params: tuple, operation_name: str) -> bool:
        """Execute a query that doesn't return a result with proper error handling.

        Args:
            query: SQL query to execute
            params: Parameters for the query
            operation_name: Name of the operation for logging

        Returns:
            True if successful, False otherwise
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, params)
                    conn.commit()
                    logger.debug("Successfully completed %s", operation_name)
                    return True
        except Exception as e:
            logger.error("Error in %s: %s", operation_name, str(e), exc_info=True)
            return False


def save_entity(entity: dict[str, Any]) -> Optional[int]:
    """Save entity to database.

    Args:
        entity: Dictionary containing entity information with keys:
               - text: The entity text
               - type: The entity type
               - confidence: Optional confidence score

    Returns:
        int: The database ID of the saved entity, or None if failed

    Raises:
        ValueError: If entity data is invalid
    """
    if not entity.get("text") or not entity.get("type"):
        raise ValueError("Entity must have 'text' and 'type' fields")

    query = """
        INSERT INTO entities (text, type, metadata, created_at, updated_at)
        VALUES (%s, %s, %s, NOW(), NOW())
        ON CONFLICT (text, type) DO UPDATE
        SET updated_at = NOW()
        RETURNING id
    """

    params = (
        entity["text"],
        entity["type"],
        json.dumps({"confidence": entity.get("confidence", 0.0)}),
    )

    result = DatabaseHelper.execute_query_with_result(query, params, "save entity")
    return result[0] if result else None


def save_entity_relationship(relationship: dict[str, Any]) -> bool:
    """Save entity relationship to database.

    Args:
        relationship: Dictionary containing relationship information

    Returns:
        True if successful, False otherwise
    """
    query = """
        INSERT INTO entity_relationships (entity_id, related_entity_id, relationship_type, confidence, created_at)
        VALUES (%s, %s, %s, %s, %s)
    """

    params = (
        relationship["entity_id"],
        relationship["related_entity_id"],
        relationship["relationship_type"],
        relationship.get("confidence", 0.5),
        datetime.now(),
    )

    return DatabaseHelper.execute_query_no_result(query, params, "save entity relationship")


def save_entity_mention(
    mention: dict[str, Any], document_id: int, entity_id: int
) -> bool:
    """Save entity mention to database.

    Args:
        mention: Dictionary containing mention information
        document_id: ID of the document containing the mention
        entity_id: ID of the entity being mentioned

    Returns:
        True if successful, False otherwise
    """
    query = """
        INSERT INTO entity_mentions (text, type, confidence, document_id, entity_id, created_at)
        VALUES (%s, %s, %s, %s, %s, %s)
    """

    params = (
        mention["text"],
        mention["type"],
        mention["confidence"],
        document_id,
        entity_id,
        datetime.now(),
    )

    return DatabaseHelper.execute_query_no_result(query, params, "save entity mention")
def save_declaration(declaration: dict[str, Any], document_id: int) -> bool:
    """Save declaration to database.

    Args:
        declaration: Dictionary containing declaration information
        document_id: ID of the document containing the declaration

    Returns:
        True if successful, False otherwise
    """
    query = """
        INSERT INTO declarations (document_id, entity_id, declaration_text, declaration_type, confidence, created_at)
        VALUES (%s, %s, %s, %s, %s, %s)
    """

    params = (
        document_id,
        declaration["entity_id"],
        declaration["declaration_text"],
        declaration["declaration_type"],
        declaration["confidence"],
        datetime.now(),
    )

    return DatabaseHelper.execute_query_no_result(query, params, "save declaration")


def process_document(document_id: int, content: str, metadata: dict[str, str]) -> None:
    """Process a document for entity extraction.

    Args:
        document_id: ID of the document to process
        content: Text content of the document
        metadata: Metadata associated with the document
    """
    try:
        logger.info("Starting entity extraction for document %d", document_id)

        # Extract entities with continuous discovery
        entities = extract_entities(content, document_id)
        logger.debug("Extracted %d entities from document %d", len(entities), document_id)

        # Deduplicate entities
        entities = deduplicate_entities(entities)
        logger.debug("After deduplication: %d entities for document %d", len(entities), document_id)

        # Infer relationships
        relationships = infer_relationships(entities, content)
        logger.debug("Inferred %d relationships for document %d", len(relationships), document_id)

        # Extract declarations
        declarations = extract_declarations(entities, content)
        logger.debug("Extracted %d declarations for document %d", len(declarations), document_id)

        # Save to vector database using lazy-loaded instance
        vector_db = get_vector_db()
        vector_db.add_document(document_id, content, metadata)
        logger.debug("Added document %d to vector database", document_id)

        # Save entities and relationships
        saved_entity_count = 0
        for entity in entities:
            entity_id = save_entity(entity)
            if entity_id:
                save_entity_mention(entity, document_id, entity_id)
                saved_entity_count += 1
            else:
                logger.warning("Failed to save entity: %s", entity.get("text", "unknown"))

        saved_relationship_count = 0
        for relationship in relationships:
            if save_entity_relationship(relationship):
                saved_relationship_count += 1

        saved_declaration_count = 0
        for declaration in declarations:
            if save_declaration(declaration, document_id):
                saved_declaration_count += 1

        logger.info(
            "Completed processing document %d: %d entities, %d relationships, %d declarations saved",
            document_id, saved_entity_count, saved_relationship_count, saved_declaration_count
        )

    except Exception as e:
        logger.error("Error processing document %d: %s", document_id, str(e), exc_info=True)
        raise


def main():
    """Main function to process documents."""
    logger.info("Starting entity extraction...")

    # Get unprocessed documents
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id, content, title
                    FROM documents
                    WHERE content IS NOT NULL
                    AND LENGTH(content) > 0
                    ORDER BY id
                    """
                )
                documents = cursor.fetchall()

                logger.info("Found %d documents to process", len(documents))

                for doc_id, content, title in documents:
                    try:
                        logger.info("Processing document %d: %s", doc_id, title or "Untitled")
                        metadata = {"title": title or "Untitled"}
                        process_document(doc_id, content, metadata)
                    except Exception as e:
                        logger.error("Failed to process document %d: %s", doc_id, str(e))
                        continue

        logger.info("Entity extraction completed")

    except Exception as e:
        logger.error("Error in main entity extraction process: %s", str(e), exc_info=True)
        raise


if __name__ == "__main__":
    main()
