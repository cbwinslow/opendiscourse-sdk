"""Base model class for all database models."""

from datetime import datetime
from typing import Any

from sqlalchemy import Column, DateTime, Integer
from sqlalchemy.ext.declarative import as_declarative, declared_attr
from sqlalchemy.orm import Session


@as_declarative()
class Base:
    """Base class for all database models.

    Provides common columns and methods for all models.
    """

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    @declared_attr
    def __tablename__(cls) -> str:
        """Generate table name from class name."""
        return cls.__name__.lower()

    def save(self, db: Session) -> None:
        """Save the model instance to the database."""
        db.add(self)
        db.commit()
        db.refresh(self)

    def delete(self, db: Session) -> None:
        """Delete the model instance from the database."""
        db.delete(self)
        db.commit()

    def update(self, db: Session, **kwargs: Any) -> None:
        """Update the model instance with the given attributes."""
        for key, value in kwargs.items():
            setattr(self, key, value)
        self.save(db)

    @classmethod
    def get_by_id(cls, db: Session, id: int) -> "Base":
        """Get a model instance by ID."""
        return db.query(cls).filter(cls.id == id).first()

    @classmethod
    def get_all(cls, db: Session, skip: int = 0, limit: int = 100) -> list["Base"]:
        """Get all model instances."""
        return db.query(cls).offset(skip).limit(limit).all()

    def to_dict(self) -> dict[str, Any]:
        """Convert the model instance to a dictionary."""
        return {
            column.name: getattr(self, column.name) for column in self.__table__.columns
        }
