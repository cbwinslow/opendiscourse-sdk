"""Security utilities for authentication."""

import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional

import bcrypt
import jwt
from fastapi import HTTPException, status


class SecurityConfig:
    """Security configuration."""
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    PASSWORD_MIN_LENGTH: int = 8
    MAX_FAILED_ATTEMPTS: int = 5
    LOCKOUT_DURATION_MINUTES: int = 15


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))


def validate_password_strength(password: str) -> bool:
    """Validate password meets minimum requirements."""
    if len(password) < SecurityConfig.PASSWORD_MIN_LENGTH:
        return False
    
    # Check for at least one uppercase, lowercase, digit, and special character
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(c in "!@#$%^&*(),.?\":{}|<>" for c in password)
    
    return has_upper and has_lower and has_digit and has_special


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=SecurityConfig.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SecurityConfig.SECRET_KEY, algorithm=SecurityConfig.ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """Create a JWT refresh token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=SecurityConfig.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SecurityConfig.SECRET_KEY, algorithm=SecurityConfig.ALGORITHM)
    return encoded_jwt


def verify_token(token: str, expected_type: str = "access") -> dict:
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(token, SecurityConfig.SECRET_KEY, algorithms=[SecurityConfig.ALGORITHM])
        token_type = payload.get("type")
        if token_type != expected_type:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token type. Expected {expected_type}, got {token_type}",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def generate_api_key() -> tuple[str, str]:
    """Generate an API key and its hash."""
    # Generate random API key
    api_key = f"od_{secrets.token_urlsafe(32)}"
    
    # Create hash for storage
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    
    return api_key, key_hash


def verify_api_key(api_key: str, stored_hash: str) -> bool:
    """Verify an API key against its stored hash."""
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    return key_hash == stored_hash


def is_account_locked(failed_attempts: int, locked_until: Optional[datetime]) -> bool:
    """Check if an account is locked due to failed login attempts."""
    if failed_attempts >= SecurityConfig.MAX_FAILED_ATTEMPTS:
        if locked_until and locked_until > datetime.utcnow():
            return True
    return False


def calculate_lockout_time() -> datetime:
    """Calculate when an account should be unlocked."""
    return datetime.utcnow() + timedelta(minutes=SecurityConfig.LOCKOUT_DURATION_MINUTES)


class PermissionChecker:
    """Check user permissions for various operations."""
    
    # Define permission mappings
    ROLE_PERMISSIONS = {
        "admin": [
            "read_all", "write_all", "delete_all", 
            "manage_users", "manage_system", "view_admin"
        ],
        "analyst": [
            "read_documents", "write_documents", "search_documents",
            "create_tasks", "read_tasks", "update_tasks"
        ],
        "user": [
            "read_documents", "search_documents", "create_tasks", "read_tasks"
        ],
        "reviewer": [
            "read_documents", "search_documents", "read_tasks", "update_tasks"
        ],
        "guest": [
            "read_documents", "search_documents"
        ]
    }
    
    @classmethod
    def has_permission(cls, user_role: str, required_permission: str) -> bool:
        """Check if a user role has a specific permission."""
        permissions = cls.ROLE_PERMISSIONS.get(user_role, [])
        return required_permission in permissions
    
    @classmethod
    def check_permission(cls, user_role: str, required_permission: str) -> None:
        """Check permission and raise exception if not authorized."""
        if not cls.has_permission(user_role, required_permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {required_permission}"
            )
    
    @classmethod
    def get_user_permissions(cls, user_role: str) -> list[str]:
        """Get all permissions for a user role."""
        return cls.ROLE_PERMISSIONS.get(user_role, [])


def require_permissions(*permissions: str):
    """Decorator to require specific permissions."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # This would be used with dependency injection in FastAPI
            # For now, it's a placeholder for the decorator pattern
            return func(*args, **kwargs)
        return wrapper
    return decorator
