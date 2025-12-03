"""SQLAlchemy models for the OpenDiscourse application.

This module defines the database models using SQLAlchemy ORM.
"""

from __future__ import annotations

from enum import Enum as PyEnum
from typing import TYPE_CHECKING, Any, TypeVar, final
from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Float, Integer, String, text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID as SQLAlchemyUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from typing_extensions import Self, override

if TYPE_CHECKING:
    from datetime import datetime

    from sqlalchemy.orm import Mapper as MapperType

# Type aliases
JSONType = dict[str, Any]  # Type alias for JSON/dict data


class EntityType(str, PyEnum):
    """Types of entities in the system.

    This enum represents the different types of entities that can be stored in the system.
    Each entity type has a string representation that matches its name.
    """

    PERSON = "PERSON"  # Individual person
    ORGANIZATION = "ORGANIZATION"  # Generic organization
    GOVERNMENT_BODY = "GOVERNMENT_BODY"  # Any government body
    LEGISLATIVE_BODY = (
        "LEGISLATIVE_BODY"  # Legislative body (e.g., Congress, Parliament)
    )
    JUDICIAL_BODY = "JUDICIAL_BODY"  # Judicial body (e.g., Supreme Court)
    EXECUTIVE_BODY = "EXECUTIVE_BODY"  # Executive body (e.g., White House)
    COMMITTEE = "COMMITTEE"  # Committee within an organization
    SUBCOMMITTEE = "SUBCOMMITTEE"  # Subcommittee within a committee
    POLITICAL_PARTY = "POLITICAL_PARTY"  # Political party
    ELECTION = "ELECTION"  # Election event
    TERM = "TERM"  # Term of office

    def __str__(self) -> str:
        """Return the string representation of the enum value."""
        return self.value


# Type variable for entity classes (covariant for better type checking)
T = TypeVar("T", bound="Entity", covariant=True)


@final
class EntityBase(DeclarativeBase):
    """Base class for all entity types in the system."""

    # Type hints for SQLAlchemy internals
    if TYPE_CHECKING:
        __mapper__: MapperType[Self]
        __tablename__: str = ""

    # SQLAlchemy model configuration
    __mapper_args__: dict[str, Any] = {}

    # Mark as abstract to prevent SQLAlchemy from creating a table for this class
    __abstract__: bool = True


class Entity(EntityBase):
    """Concrete entity class representing any entity in the system.

    Attributes:
        id: Unique identifier for the entity
        name: Name of the entity
        entity_type: Type of the entity (from EntityType enum)
        description: Optional description of the entity
        metadata_: Additional metadata as a JSON object
        created_at: Timestamp when the entity was created
        updated_at: Timestamp when the entity was last updated
    """

    __tablename__ = "entities"

    # Entity attributes with type hints and column definitions
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    entity_type: Mapped[EntityType] = mapped_column(
        SQLEnum(EntityType, name="entity_type_enum"),
        nullable=False,
        index=True,
        doc="Type of the entity (person, organization, etc.)",
    )
    description: Mapped[str | None] = mapped_column(
        String(2000), nullable=True, doc="Brief description of the entity"
    )
    metadata_: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata",  # Actual column name in the database
        JSONB,
        nullable=True,
        server_default=text("{}"),
        doc="Additional metadata in JSON format",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        doc="Timestamp when the entity was created",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=text("CURRENT_TIMESTAMP"),
        doc="Timestamp when the entity was last updated",
    )

    def __init__(
        self,
        name: str,
        entity_type: EntityType,
        description: str | None = None,
        metadata_: dict[str, Any] | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize a new Entity instance.

        Args:
            name: Name of the entity
            entity_type: Type of the entity
            description: Optional description
            metadata_: Optional metadata dictionary
            created_at: Optional creation timestamp
            updated_at: Optional last update timestamp
            **kwargs: Additional keyword arguments
        """
        super().__init__()
        self.name = name
        self.entity_type = entity_type
        self.description = description
        self.metadata_ = metadata_ or {}

        # Set timestamps if provided, otherwise they'll be set by the database
        if created_at is not None:
            self.created_at = created_at
        if updated_at is not None:
            self.updated_at = updated_at

        # Handle any additional attributes
        for key, value in kwargs.items():
            setattr(self, key, value)

    @override
    def __repr__(self) -> str:
        """Return a string representation of the entity."""
        return f"<Entity(id={self.id}, name='{self.name}', type={self.entity_type})>"

    def to_dict(self, exclude: set[str] | None = None) -> dict[str, Any]:
        """Convert the entity to a dictionary.

        Args:
            exclude: Optional set of field names to exclude from the result

        Returns:
            Dictionary representation of the entity
        """
        exclude_set = exclude or set()
        result = {
            "id": self.id,
            "name": self.name,
            "entity_type": self.entity_type.value,
            "description": self.description,
            "metadata": self.metadata_,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

        # Remove excluded fields
        for field in exclude_set:
            result.pop(field, None)

        return result

    @classmethod
    def from_dict(cls: type[T], data: dict[str, Any]) -> T:
        """Create an Entity instance from a dictionary.

        Args:
            data: Dictionary containing entity data

        Returns:
            New Entity instance

        Raises:
            ValueError: If required fields are missing or invalid
        """
        required_fields = {"name", "entity_type"}
        missing_fields = required_fields - set(data.keys())
        if missing_fields:
            msg = f"Missing required fields: {', '.join(missing_fields)}"
            raise ValueError(msg)

        try:
            entity_type = EntityType(data["entity_type"])
        except ValueError as e:
            msg = f"Invalid entity type: {data['entity_type']}"
            raise ValueError(msg) from e

        # Create the entity with the provided data
        entity = cls(
            name=str(data["name"]),
            entity_type=entity_type,
            description=str(data["description"]) if data.get("description") else None,
            metadata_=dict(data.get("metadata", {})) if data.get("metadata") else {},
        )

        # Handle timestamps if provided
        if "created_at" in data and data["created_at"] is not None:
            try:
                entity.created_at = data["created_at"]
            except (TypeError, ValueError) as e:
                msg = f"Invalid created_at: {data['created_at']}"
                raise ValueError(msg) from e

        if "updated_at" in data and data["updated_at"] is not None:
            try:
                entity.updated_at = data["updated_at"]
            except (TypeError, ValueError) as e:
                msg = f"Invalid updated_at: {data['updated_at']}"
                raise ValueError(msg) from e

        return entity


class TaskStatus(str, PyEnum):
    """Status values for tasks."""
    TODO = "todo"
    IN_PROGRESS = "in-progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

    def __str__(self) -> str:
        return self.value


class TaskPriority(str, PyEnum):
    """Priority levels for tasks."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

    def __str__(self) -> str:
        return self.value


class Task(EntityBase):
    """Task model for tracking work items and assignments."""

    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(SQLAlchemyUUID(as_uuid=False), primary_key=True)
    title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[TaskStatus] = mapped_column(
        SQLEnum(TaskStatus, name="task_status_enum"),
        nullable=False,
        default=TaskStatus.TODO,
        index=True
    )
    priority: Mapped[TaskPriority] = mapped_column(
        SQLEnum(TaskPriority, name="task_priority_enum"),
        nullable=False,
        default=TaskPriority.MEDIUM,
        index=True
    )
    assignee: Mapped[str | None] = mapped_column(String(255), nullable=True)
    due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    metadata_: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata",
        JSONB,
        nullable=True,
        server_default=text("{}"),
    )
    entity_ids: Mapped[list[str] | None] = mapped_column(
        ARRAY(SQLAlchemyUUID(as_uuid=False)), nullable=True
    )
    document_ids: Mapped[list[str] | None] = mapped_column(
        ARRAY(SQLAlchemyUUID(as_uuid=False)), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=text("CURRENT_TIMESTAMP"),
    )

    def __repr__(self) -> str:
        return f"<Task(id={self.id}, title='{self.title}', status={self.status})>"


class Inference(EntityBase):
    """Inference model for storing AI-generated insights and conclusions."""

    __tablename__ = "inferences"

    id: Mapped[str] = mapped_column(SQLAlchemyUUID(as_uuid=False), primary_key=True)
    type: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    content: Mapped[str] = mapped_column(String, nullable=False)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    source_document_id: Mapped[str | None] = mapped_column(
        SQLAlchemyUUID(as_uuid=False), nullable=True
    )
    source_task_id: Mapped[str | None] = mapped_column(
        SQLAlchemyUUID(as_uuid=False), nullable=True
    )
    metadata_: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata",
        JSONB,
        nullable=True,
        server_default=text("{}"),
    )
    entity_ids: Mapped[list[str] | None] = mapped_column(
        ARRAY(SQLAlchemyUUID(as_uuid=False)), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=text("CURRENT_TIMESTAMP"),
    )

    def __repr__(self) -> str:
        return f"<Inference(id={self.id}, type='{self.type}', confidence={self.confidence})>"
