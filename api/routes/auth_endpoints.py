"""Authentication and authorization endpoints."""

import os
from datetime import datetime, timedelta
from typing import Optional

import psycopg2
import psycopg2.extras
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from opendiscourse.auth.models import (
    UserCreate, UserLogin, UserResponse, TokenResponse,
    APIKeyCreate, APIKeyResponse, PasswordChange, UserUpdate
)
from opendiscourse.auth.security import (
    hash_password, verify_password, validate_password_strength,
    create_access_token, verify_token, generate_api_key, verify_api_key,
    is_account_locked, calculate_lockout_time, PermissionChecker
)

router = APIRouter(prefix="/v1/auth", tags=["Authentication"])
security = HTTPBearer()

DB_URL = os.environ.get(
    "RAG_DB_URL", "postgresql://user:password@localhost:5432/opendiscourse"
)


def get_db_connection():
    """Get database connection."""
    return psycopg2.connect(DB_URL)


def get_user_by_username(username: str) -> Optional[dict]:
    """Get user by username from database."""
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        cur.execute("""
            SELECT id, username, email, password_hash, full_name, role, status, 
                   is_active, last_login, failed_login_attempts, locked_until,
                   metadata, created_at, updated_at
            FROM users WHERE username = %s
        """, (username,))
        
        user = cur.fetchone()
        cur.close()
        conn.close()
        
        return dict(user) if user else None
    except Exception as e:
        print(f"Database error: {e}")
        return None


def create_user_in_db(user_data: UserCreate) -> Optional[dict]:
    """Create a new user in the database."""
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Check if user already exists
        cur.execute("SELECT id FROM users WHERE username = %s OR email = %s", 
                   (user_data.username, user_data.email))
        if cur.fetchone():
            cur.close()
            conn.close()
            return None
        
        # Hash password
        password_hash = hash_password(user_data.password)
        
        # Insert user
        cur.execute("""
            INSERT INTO users (username, email, password_hash, full_name, role, status)
            VALUES (%s, %s, %s, %s, %s, 'active')
            RETURNING id, username, email, full_name, role, status, is_active, created_at
        """, (user_data.username, user_data.email, password_hash, 
              user_data.full_name, user_data.role.value))
        
        user = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        
        return dict(user) if user else None
    except Exception as e:
        print(f"Database error: {e}")
        return None


def update_login_attempt(username: str, success: bool):
    """Update login attempt information."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        if success:
            # Reset failed attempts and update last login
            cur.execute("""
                UPDATE users 
                SET failed_login_attempts = 0, locked_until = NULL, last_login = CURRENT_TIMESTAMP
                WHERE username = %s
            """, (username,))
        else:
            # Increment failed attempts and possibly lock account
            cur.execute("""
                UPDATE users 
                SET failed_login_attempts = failed_login_attempts + 1,
                    locked_until = CASE 
                        WHEN failed_login_attempts + 1 >= 5 
                        THEN CURRENT_TIMESTAMP + INTERVAL '15 minutes'
                        ELSE locked_until 
                    END
                WHERE username = %s
            """, (username,))
        
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Database error: {e}")


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Get current user from JWT token."""
    try:
        token = credentials.credentials
        payload = verify_token(token)
        username = payload.get("sub")
        
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user = get_user_by_username(username)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def require_role(required_role: str):
    """Dependency to require specific role."""
    async def role_checker(current_user: dict = Depends(get_current_user)):
        if current_user["role"] != required_role and current_user["role"] != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    return role_checker


@router.post("/register", response_model=UserResponse)
async def register_user(user_data: UserCreate):
    """Register a new user."""
    # Validate password strength
    if not validate_password_strength(user_data.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password does not meet security requirements"
        )
    
    # Create user
    user = create_user_in_db(user_data)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already exists"
        )
    
    return UserResponse(**user)


@router.post("/login", response_model=TokenResponse)
async def login_user(user_data: UserLogin):
    """Authenticate user and return access token."""
    user = get_user_by_username(user_data.username)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    # Check if account is locked
    if is_account_locked(user["failed_login_attempts"], user["locked_until"]):
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail="Account is temporarily locked due to failed login attempts"
        )
    
    # Verify password
    if not verify_password(user_data.password, user["password_hash"]):
        update_login_attempt(user_data.username, success=False)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    # Check if user is active
    if not user["is_active"] or user["status"] != "active":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is not active"
        )
    
    # Update successful login
    update_login_attempt(user_data.username, success=True)
    
    # Create access token
    access_token = create_access_token(
        data={"sub": user["username"], "role": user["role"]}
    )
    
    return TokenResponse(
        access_token=access_token,
        expires_in=1800,  # 30 minutes
        user=UserResponse(**user)
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current user information."""
    return UserResponse(**current_user)


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    update_data: UserUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update current user information."""
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Build update query dynamically
        updates = []
        values = []
        
        if update_data.full_name is not None:
            updates.append("full_name = %s")
            values.append(update_data.full_name)
        
        if update_data.email is not None:
            updates.append("email = %s")
            values.append(update_data.email)
        
        if not updates:
            return UserResponse(**current_user)
        
        values.append(current_user["id"])
        
        cur.execute(f"""
            UPDATE users 
            SET {', '.join(updates)}, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            RETURNING id, username, email, full_name, role, status, is_active, 
                     last_login, created_at, updated_at
        """, values)
        
        updated_user = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        
        return UserResponse(**updated_user)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user: {str(e)}"
        )


@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user: dict = Depends(get_current_user)
):
    """Change user password."""
    # Verify current password
    if not verify_password(password_data.current_password, current_user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Validate new password
    if not validate_password_strength(password_data.new_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password does not meet security requirements"
        )
    
    # Update password
    try:
        new_password_hash = hash_password(password_data.new_password)
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            UPDATE users 
            SET password_hash = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (new_password_hash, current_user["id"]))
        
        conn.commit()
        cur.close()
        conn.close()
        
        return {"message": "Password changed successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to change password: {str(e)}"
        )


@router.get("/users", response_model=list[UserResponse])
async def list_users(
    current_user: dict = Depends(require_role("admin")),
    limit: int = 50,
    offset: int = 0
):
    """List all users (admin only)."""
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        cur.execute("""
            SELECT id, username, email, full_name, role, status, is_active, 
                   last_login, created_at, updated_at
            FROM users 
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """, (limit, offset))
        
        users = cur.fetchall()
        cur.close()
        conn.close()
        
        return [UserResponse(**dict(user)) for user in users]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list users: {str(e)}"
        )


@router.post("/api-keys", response_model=dict)
async def create_api_key(
    key_data: APIKeyCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new API key."""
    try:
        api_key, key_hash = generate_api_key()
        prefix = api_key[:10]  # Store first 10 chars for identification
        
        expires_at = None
        if key_data.expires_days:
            expires_at = datetime.utcnow() + timedelta(days=key_data.expires_days)
        
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        cur.execute("""
            INSERT INTO api_keys (user_id, name, key_hash, prefix, expires_at, scopes)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id, name, prefix, expires_at, scopes, created_at
        """, (current_user["id"], key_data.name, key_hash, prefix, 
              expires_at, psycopg2.extras.Json(key_data.scopes)))
        
        api_key_record = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        
        return {
            "api_key": api_key,  # Only returned once!
            "key_info": APIKeyResponse(**api_key_record)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create API key: {str(e)}"
        )


@router.get("/permissions")
async def get_user_permissions(current_user: dict = Depends(get_current_user)):
    """Get current user's permissions."""
    permissions = PermissionChecker.get_user_permissions(current_user["role"])
    return {
        "user": current_user["username"],
        "role": current_user["role"],
        "permissions": permissions
    }
