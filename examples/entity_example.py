#!/usr/bin/env python3
"""
Example script demonstrating how to use the Entity model.

This script demonstrates how to:
1. Initialize the database
2. Create new entities
3. Query entities
4. Update entities
5. Delete entities
"""

import sys
from pathlib import Path
from typing import Any, Optional

from sqlalchemy.orm import Session

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import after modifying path
from database import SessionLocal, init_db  # noqa: E402
from models.entity import Entity, EntityType  # noqa: E402


def create_entity(session: Session, data: dict[str, Any]) -> Entity:
    """Create a new entity from the given data.

    Args:
        session: Database session
        data: Dictionary containing entity data with required 'name' and 'entity_type' keys

    Returns:
        Entity: The created entity

    Raises:
        ValueError: If required fields are missing or invalid
    """
    try:
        # Extract and validate required fields
        if not data.get("name"):
            msg = "Name cannot be empty"
            raise ValueError(msg)
        name = str(data["name"])

        if not data.get("entity_type"):
            msg = "Entity type cannot be empty"
            raise ValueError(msg)
        entity_type = EntityType(str(data["entity_type"]))

        # Handle optional fields
        description = (
            str(data["description"])
            if "description" in data and data["description"] is not None
            else None
        )
        metadata_ = data.get("metadata")

        # Create and return the entity
        entity = Entity(
            name=name,
            entity_type=entity_type,
            description=description,
            metadata_=metadata_,
        )
        session.add(entity)
        session.commit()
        return entity

    except KeyError as e:
        session.rollback()
        msg = f"Missing required field: {e}"
        raise ValueError(msg) from e
    except Exception as e:
        session.rollback()
        msg = f"Failed to create entity: {e}"
        raise ValueError(msg) from e


def get_entity(session: Session, entity_id: int) -> Optional[Entity]:
    """Get an entity by ID.

    Args:
        session: Database session
        entity_id: ID of the entity to retrieve

    Returns:
        Optional[Entity]: The requested entity, or None if not found
    """
    return session.get(Entity, entity_id)


def get_entity_by_name(session: Session, name: str) -> Optional[Entity]:
    """Get an entity by name.

    Args:
        session: Database session
        name: Name of the entity to retrieve

    Returns:
        Optional[Entity]: The requested entity, or None if not found
    """
    return session.query(Entity).filter(Entity.name == name).first()


def list_entities(
    session: Session,
    entity_type: Optional[EntityType] = None,
    limit: int = 100,
    offset: int = 0,
) -> list[Entity]:
    """List entities with optional filtering.

    Args:
        session: Database session
        entity_type: Optional EntityType to filter by
        limit: Maximum number of entities to return
        offset: Number of entities to skip

    Returns:
        List[Entity]: List of matching entities
    """
    query = session.query(Entity)
    if entity_type is not None:
        query = query.filter(Entity.entity_type == entity_type)
    return query.offset(offset).limit(limit).all()


def update_entity(
    session: Session, entity_id: int, data: dict[str, Any]
) -> Optional[Entity]:
    """Update an entity with the given data.

    Args:
        session: Database session
        entity_id: ID of the entity to update
        data: Dictionary containing fields to update

    Returns:
        Optional[Entity]: The updated entity, or None if not found

    Raises:
        ValueError: If the update data is invalid
    """
    entity = get_entity(session, entity_id)
    if not entity:
        return None

    try:
        # Update name if provided
        if "name" in data:
            if not data["name"]:
                msg = "Name cannot be empty"
                raise ValueError(msg)
            entity.name = str(data["name"])

        # Update entity_type if provided
        if "entity_type" in data:
            if not data["entity_type"]:
                msg = "Entity type cannot be empty"
                raise ValueError(msg)
            entity.entity_type = EntityType(str(data["entity_type"]))

        # Update description if provided
        if "description" in data:
            entity.description = (
                str(data["description"]) if data["description"] is not None else None
            )

        # Update metadata if provided
        if "metadata" in data and data["metadata"] is not None:
            if not isinstance(data["metadata"], dict):
                msg = "Metadata must be a dictionary"
                raise ValueError(msg)
            entity.metadata_ = data["metadata"]

        session.commit()
        return entity

    except Exception as e:
        session.rollback()
        msg = f"Failed to update entity: {e}"
        raise ValueError(msg) from e


def delete_entity(session: Session, entity_id: int) -> bool:
    """Delete an entity by ID.

    Args:
        session: Database session
        entity_id: ID of the entity to delete

    Returns:
        bool: True if the entity was deleted, False if not found
    """
    entity = get_entity(session, entity_id)
    if not entity:
        return False

    try:
        session.delete(entity)
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        msg = f"Failed to delete entity: {e}"
        raise RuntimeError(msg) from e


def print_entity(entity: Entity) -> None:
    """Print entity details in a formatted way.

    Args:
        entity: The entity to print
    """
    if not entity:
        print("No entity found")
        return

    try:
        # Safely access entity attributes
        getattr(entity, "id", "N/A")
        getattr(entity, "name", "Unnamed")
        getattr(entity, "entity_type", None)
        getattr(entity, "description", None)
        getattr(entity, "metadata_", None)
        getattr(entity, "created_at", "N/A")
        getattr(entity, "updated_at", "N/A")

        # Format the output using direct attribute access since we know the types
        print("\n" + "=" * 50)
        print(f"ID: {entity.id}")
        print(f"Name: {entity.name}")
        print(f"Type: {entity.entity_type.value}")
        if entity.description:
            print(f"Description: {entity.description}")
        if entity.metadata_:
            print("Metadata:")
            for key, value in entity.metadata_.items():
                print(f"  {key}: {value}")
        print(f"Created: {entity.created_at}")
        print(f"Updated: {entity.updated_at}")
        print("=" * 50 + "\n")

    except Exception as e:
        print(f"Error printing entity: {e}")


def main() -> None:
    """Example usage of the Entity model."""
    try:
        # Initialize the database
        print("Initializing database...")
        init_db()

        # Create a new session
        db = SessionLocal()

        try:
            # Create some example entities
            print("\nCreating example entities...")

            # Example 1: Organization
            org_data = {
                "name": "Open Source Initiative",
                "entity_type": EntityType.ORGANIZATION.value,
                "description": "Non-profit organization promoting open source software",
                "metadata": {"founded": 1998, "website": "https://opensource.org"},
            }
            org = create_entity(db, org_data)
            print("Created organization:")
            print_entity(org)

            # Example 2: Person
            person_data = {
                "name": "Linus Torvalds",
                "entity_type": EntityType.PERSON.value,
                "description": "Creator of Linux and Git",
                "metadata": {
                    "nationality": "Finnish-American",
                    "known_for": ["Linux kernel", "Git"],
                },
            }
            person = create_entity(db, person_data)
            print("Created person:")
            print_entity(person)

            # Example 3: Location
            location_data = {
                "name": "Silicon Valley",
                "entity_type": EntityType.LOCATION.value,
                "description": "Region in California known for tech companies",
                "metadata": {
                    "region": "Northern California",
                    "notable_companies": ["Apple", "Google", "Facebook", "Tesla"],
                },
            }
            location = create_entity(db, location_data)
            print("Created location:")
            print_entity(location)

            # List all entities
            print("\nListing all entities:")
            all_entities = list_entities(db)
            for i, entity in enumerate(all_entities, 1):
                print(f"{i}. {entity.name} ({entity.entity_type.value})")

            # Get an entity by ID
            print("\nGetting entity by ID:")
            entity = get_entity(db, person.id)
            if entity:
                print_entity(entity)
            else:
                print("Entity not found")

            # Update an entity
            print("Updating entity...")
            updated = update_entity(
                db,
                entity.id,
                {
                    "description": "Creator of Linux kernel and Git version control system"
                },
            )
            print("Updated entity:")
            print_entity(updated)

            # Search for entities
            print("Searching for organizations:")
            orgs = list_entities(db, entity_type=EntityType.ORGANIZATION)
            for org in orgs:
                print(f"- {org.name}")

            # Clean up (delete test data)
            print("\nCleaning up test data...")
            for entity in all_entities:
                if not delete_entity(db, entity.id):
                    print(f"Warning: Failed to delete entity {entity.id}")

            print("\nExample completed successfully!")

        finally:
            # Close the session
            db.close()

    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)
        raise


if __name__ == "__main__":
    try:
        main()
        print("\nExample completed successfully!")
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)
