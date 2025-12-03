"""Authentication models for OpenDiscourse."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, EmailStr
from sqlalchemy import Boolean, DateTime, Integer, String, text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class UserRole(str, Enum):
    """User roles in the system."""
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"
    ANALYST = "analyst"
    REVIEWER = "reviewer"


class UserStatus(str, Enum):
    """User account status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"


class AuthBase(DeclarativeBase):
    """Base class for authentication models."""
    pass


class User(AuthBase):
    """User model for authentication."""
    
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        SQLEnum(UserRole, name="user_role_enum"),
        nullable=False,
        default=UserRole.USER
    )
    status: Mapped[UserStatus] = mapped_column(
        SQLEnum(UserStatus, name="user_status_enum"),
        nullable=False,
        default=UserStatus.PENDING
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0)
    locked_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    metadata_: Mapped[dict] = mapped_column(
        "metadata",
        JSONB,
        nullable=True,
        server_default=text("{}"),
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
        return f"<User(id={self.id}, username='{self.username}', role={self.role})>"


class APIKey(AuthBase):
    """API key model for programmatic access."""
    
    __tablename__ = "api_keys"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    key_hash: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    prefix: Mapped[str] = mapped_column(String(10), nullable=False)  # First few chars for identification
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_used: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    scopes: Mapped[list] = mapped_column(JSONB, nullable=True, default=list)
    metadata_: Mapped[dict] = mapped_column(
        "metadata",
        JSONB,
        nullable=True,
        server_default=text("{}"),
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


# Pydantic models for API
class UserCreate(BaseModel):
    """Model for creating a new user."""
    username: str
    email: EmailStr
    password: str
    full_name: str
    role: UserRole = UserRole.USER


class UserLogin(BaseModel):
    """Model for user login."""
    username: str
    password: str


class UserResponse(BaseModel):
    """Model for user response."""
    id: int
    username: str
    email: str
    full_name: str
    role: UserRole
    status: UserStatus
    is_active: bool
    last_login: Optional[datetime]
    created_at: datetime


class TokenResponse(BaseModel):
    """Model for token response."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class APIKeyCreate(BaseModel):
    """Model for creating API key."""
    name: str
    expires_days: Optional[int] = None
    scopes: list[str] = []


class APIKeyResponse(BaseModel):
    """Model for API key response."""
    id: int
    name: str
    prefix: str
    is_active: bool
    expires_at: Optional[datetime]
    scopes: list[str]
    created_at: datetime
    last_used: Optional[datetime]


class PasswordChange(BaseModel):
    """Model for password change."""
    current_password: str
    new_password: str


class PasswordReset(BaseModel):
    """Model for password reset."""
    email: EmailStr


class UserUpdate(BaseModel):
    """Model for updating user."""
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[UserRole] = None
    status: Optional[UserStatus] = None
    is_active: Optional[bool] = None
