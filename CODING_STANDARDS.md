# OpenDiscourse Coding Standards

This document defines the coding standards and best practices for the OpenDiscourse project. All contributors should follow these guidelines to maintain code quality, consistency, and maintainability.

## Table of Contents

- [General Principles](#general-principles)
- [Python Standards](#python-standards)
- [TypeScript/JavaScript Standards](#typescriptjavascript-standards)
- [SQL and Database Standards](#sql-and-database-standards)
- [API Design Standards](#api-design-standards)
- [Security Standards](#security-standards)
- [Performance Standards](#performance-standards)
- [Testing Standards](#testing-standards)
- [Documentation Standards](#documentation-standards)
- [Git Standards](#git-standards)

## General Principles

### Code Quality Principles

1. **Readability First**: Code is read more often than it's written
2. **SOLID Principles**: Follow Single Responsibility, Open/Closed, Liskov Substitution, Interface Segregation, and Dependency Inversion
3. **DRY (Don't Repeat Yourself)**: Eliminate code duplication
4. **KISS (Keep It Simple, Stupid)**: Prefer simple solutions over complex ones
5. **YAGNI (You Aren't Gonna Need It)**: Don't implement features until they're needed
6. **Explicit is Better Than Implicit**: Make intentions clear
7. **Fail Fast**: Detect and report errors early
8. **Defensive Programming**: Validate inputs and handle errors gracefully

### File Organization

- **File Size**: Keep files under 500 lines
- **Module Cohesion**: Each module should have a single, well-defined purpose
- **Directory Structure**: Follow project structure conventions
- **Naming**: Use descriptive, meaningful names

### Dependency Management

- Pin dependency versions in production
- Use lock files (pnpm-lock.yaml, requirements.txt)
- Audit dependencies regularly for security vulnerabilities
- Minimize external dependencies
- Document why each dependency is needed

## Python Standards

### Style Guide

Follow **PEP 8** with these specifications:

#### Line Length
- **Maximum 88 characters** (Black formatter default)
- For longer lines, use parentheses for implicit line continuation

#### Indentation
- **4 spaces** per indentation level
- Never use tabs

#### Naming Conventions
```python
# Modules and packages: lowercase with underscores
# my_module.py, my_package/

# Classes: PascalCase
class DocumentProcessor:
    pass

# Functions and methods: snake_case
def process_document():
    pass

# Variables: snake_case
user_count = 0

# Constants: UPPER_SNAKE_CASE
MAX_UPLOAD_SIZE = 10485760

# Private members: prefix with single underscore
def _internal_helper():
    pass

# Protected members (inheritance): prefix with single underscore
class Base:
    def _protected_method(self):
        pass
```

### Type Hints

**Always use type hints** for function signatures and class attributes:

```python
from typing import Optional, Union, Any
from collections.abc import Sequence, Mapping

# Function with type hints
def fetch_documents(
    user_id: str,
    limit: int = 10,
    offset: int = 0,
    filters: Optional[dict[str, Any]] = None
) -> list[Document]:
    """Fetch documents for a user."""
    pass

# Class with type hints
class DocumentService:
    """Service for document operations."""
    
    def __init__(self, db: Database) -> None:
        self.db: Database = db
        self._cache: dict[str, Document] = {}
    
    def get(self, doc_id: str) -> Optional[Document]:
        """Get a document by ID."""
        pass

# Use modern type hint syntax (Python 3.10+)
def process_items(items: list[str]) -> dict[str, int]:
    """Process a list of items."""
    pass

# Use Union with | operator (Python 3.10+)
def get_value(key: str) -> str | int | None:
    """Get a value that could be string, int, or None."""
    pass
```

### Docstrings

Use **Google-style docstrings** for all public modules, classes, and functions:

```python
def calculate_similarity(
    text1: str,
    text2: str,
    method: str = "cosine"
) -> float:
    """Calculate similarity between two texts.

    This function computes the similarity score between two text strings
    using various similarity metrics.

    Args:
        text1: The first text string to compare
        text2: The second text string to compare
        method: Similarity metric to use. Options: 'cosine', 'jaccard', 'levenshtein'.
            Defaults to 'cosine'.

    Returns:
        A float between 0.0 and 1.0 representing the similarity score,
        where 1.0 indicates identical texts.

    Raises:
        ValueError: If method is not one of the supported metrics
        TypeError: If text1 or text2 are not strings

    Examples:
        >>> calculate_similarity("hello world", "hello world")
        1.0
        >>> calculate_similarity("hello", "world", method="jaccard")
        0.0

    Note:
        The 'cosine' method is recommended for longer texts, while 'jaccard'
        works better for short phrases or token-based comparison.
    """
    pass
```

### Error Handling

```python
# Define custom exceptions
class DocumentError(Exception):
    """Base exception for document-related errors."""
    pass

class DocumentNotFoundError(DocumentError):
    """Raised when a document cannot be found."""
    
    def __init__(self, document_id: str) -> None:
        self.document_id = document_id
        super().__init__(f"Document not found: {document_id}")

class ValidationError(DocumentError):
    """Raised when document validation fails."""
    pass

# Use specific exception handling
def process_document(doc_id: str) -> Document:
    """Process a document."""
    try:
        document = fetch_document(doc_id)
        validate_document(document)
        return transform_document(document)
    except DocumentNotFoundError:
        logger.error(f"Document not found: {doc_id}")
        raise
    except ValidationError as e:
        logger.error(f"Validation failed for {doc_id}: {e}")
        raise
    except Exception as e:
        logger.exception(f"Unexpected error processing document {doc_id}")
        raise DocumentError(f"Failed to process document: {e}") from e
```

### Imports

```python
# Standard library imports first
import os
import sys
from collections import defaultdict
from typing import Optional

# Third-party imports second
import numpy as np
import pandas as pd
from fastapi import FastAPI, Depends
from sqlalchemy import select

# Local imports last
from opendiscourse.core import config
from opendiscourse.db.models import Document
from opendiscourse.services.search import SearchService

# Avoid wildcard imports
# BAD: from module import *
# GOOD: from module import specific_function
```

### Code Structure

```python
# Module-level constants
DEFAULT_TIMEOUT = 30
MAX_RETRIES = 3

# Module-level type aliases
DocumentID = str
Metadata = dict[str, Any]

# Helper functions (private)
def _validate_input(data: str) -> bool:
    """Validate input data."""
    return len(data) > 0

# Main classes
class DocumentProcessor:
    """Process and validate documents."""
    
    # Class attributes
    supported_formats: list[str] = [".pdf", ".docx", ".txt"]
    
    def __init__(self, config: Config) -> None:
        """Initialize processor with configuration."""
        self.config = config
        self._cache: dict[str, Document] = {}
    
    # Public methods
    def process(self, document: Document) -> ProcessedDocument:
        """Process a document."""
        if not self._is_valid(document):
            raise ValidationError("Invalid document")
        return self._transform(document)
    
    # Private methods
    def _is_valid(self, document: Document) -> bool:
        """Validate document format."""
        return document.format in self.supported_formats
    
    def _transform(self, document: Document) -> ProcessedDocument:
        """Transform document to processed format."""
        pass

# Module initialization code (if needed)
if __name__ == "__main__":
    # Module test code
    pass
```

### Async/Await

```python
import asyncio
from typing import Coroutine

# Use async for I/O-bound operations
async def fetch_document(doc_id: str) -> Document:
    """Fetch document asynchronously."""
    async with aiohttp.ClientSession() as session:
        async with session.get(f"/api/documents/{doc_id}") as response:
            return await response.json()

# Use asyncio.gather for concurrent operations
async def fetch_multiple_documents(doc_ids: list[str]) -> list[Document]:
    """Fetch multiple documents concurrently."""
    tasks = [fetch_document(doc_id) for doc_id in doc_ids]
    return await asyncio.gather(*tasks)

# Handle exceptions in async code
async def safe_fetch_document(doc_id: str) -> Optional[Document]:
    """Fetch document with error handling."""
    try:
        return await fetch_document(doc_id)
    except Exception as e:
        logger.error(f"Failed to fetch document {doc_id}: {e}")
        return None
```

### Context Managers

```python
from contextlib import contextmanager
from typing import Generator

# Use context managers for resource management
@contextmanager
def database_connection(connection_string: str) -> Generator[Connection, None, None]:
    """Context manager for database connections."""
    conn = create_connection(connection_string)
    try:
        yield conn
    finally:
        conn.close()

# Usage
with database_connection("postgresql://...") as conn:
    result = conn.execute("SELECT * FROM documents")
```

## TypeScript/JavaScript Standards

### Style Guide

Follow **Airbnb JavaScript Style Guide** with TypeScript extensions.

#### Naming Conventions

```typescript
// Interfaces and Types: PascalCase
interface DocumentMetadata {
  id: string;
  title: string;
}

type DocumentStatus = 'pending' | 'processed' | 'failed';

// Classes: PascalCase
class DocumentProcessor {
  private cache: Map<string, Document>;
  
  constructor() {
    this.cache = new Map();
  }
}

// Functions and variables: camelCase
const processDocument = (doc: Document): ProcessedDocument => {
  return transform(doc);
};

const userCount = 0;

// Constants: UPPER_SNAKE_CASE
const MAX_UPLOAD_SIZE = 10485760;
const API_BASE_URL = 'https://api.example.com';

// Files: kebab-case
// document-processor.ts
// user-service.ts

// React Components: PascalCase
// DocumentCard.tsx
// UserProfile.tsx
```

### TypeScript Best Practices

```typescript
// Always use strict mode
// tsconfig.json: "strict": true

// Define explicit return types
function calculateTotal(items: Item[]): number {
  return items.reduce((sum, item) => sum + item.price, 0);
}

// Use interfaces for object shapes
interface Document {
  id: string;
  title: string;
  content: string;
  createdAt: Date;
}

// Use type guards
function isDocument(obj: unknown): obj is Document {
  return (
    typeof obj === 'object' &&
    obj !== null &&
    'id' in obj &&
    'title' in obj
  );
}

// Use enums for fixed sets of values
enum DocumentStatus {
  Pending = 'PENDING',
  Processing = 'PROCESSING',
  Completed = 'COMPLETED',
  Failed = 'FAILED'
}

// Use union types for alternatives
type Result<T> = 
  | { success: true; data: T }
  | { success: false; error: string };

// Use generics for reusable code
function findById<T extends { id: string }>(
  items: T[],
  id: string
): T | undefined {
  return items.find(item => item.id === id);
}

// Avoid 'any' - use 'unknown' instead
function processData(data: unknown): ProcessedData {
  if (!isValidData(data)) {
    throw new Error('Invalid data');
  }
  return transform(data);
}
```

### React Best Practices

```typescript
// Use functional components
import { useState, useEffect, useMemo, useCallback } from 'react';

interface DocumentCardProps {
  document: Document;
  onUpdate?: (id: string) => void;
  className?: string;
}

export const DocumentCard: React.FC<DocumentCardProps> = ({
  document,
  onUpdate,
  className = ''
}) => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Memoize expensive calculations
  const formattedDate = useMemo(
    () => formatDate(document.createdAt),
    [document.createdAt]
  );

  // Memoize callbacks to prevent unnecessary re-renders
  const handleUpdate = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      await updateDocument(document.id);
      onUpdate?.(document.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Update failed');
    } finally {
      setIsLoading(false);
    }
  }, [document.id, onUpdate]);

  // Cleanup effects
  useEffect(() => {
    const subscription = subscribeToUpdates(document.id, handleUpdate);
    return () => subscription.unsubscribe();
  }, [document.id, handleUpdate]);

  if (error) {
    return <ErrorMessage message={error} />;
  }

  return (
    <div className={`document-card ${className}`}>
      <h3>{document.title}</h3>
      <p>{formattedDate}</p>
      <button 
        onClick={handleUpdate} 
        disabled={isLoading}
        aria-busy={isLoading}
      >
        {isLoading ? 'Updating...' : 'Update'}
      </button>
    </div>
  );
};
```

### Async/Promises

```typescript
// Use async/await instead of promise chains
async function fetchDocuments(userId: string): Promise<Document[]> {
  try {
    const response = await fetch(`/api/users/${userId}/documents`);
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    return data.documents;
  } catch (error) {
    console.error('Failed to fetch documents:', error);
    throw error;
  }
}

// Handle multiple async operations
async function fetchUserData(userId: string): Promise<UserData> {
  const [user, documents, settings] = await Promise.all([
    fetchUser(userId),
    fetchDocuments(userId),
    fetchSettings(userId)
  ]);
  
  return { user, documents, settings };
}

// Use Promise.allSettled for error resilience
async function fetchAllData(ids: string[]): Promise<Result[]> {
  const results = await Promise.allSettled(
    ids.map(id => fetchData(id))
  );
  
  return results.map((result, index) => {
    if (result.status === 'fulfilled') {
      return { success: true, data: result.value };
    } else {
      return { success: false, error: result.reason };
    }
  });
}
```

### Error Handling

```typescript
// Custom error classes
class APIError extends Error {
  constructor(
    message: string,
    public statusCode: number,
    public code: string
  ) {
    super(message);
    this.name = 'APIError';
  }
}

class ValidationError extends Error {
  constructor(
    message: string,
    public field: string
  ) {
    super(message);
    this.name = 'ValidationError';
  }
}

// Type-safe error handling
type ErrorHandler = (error: unknown) => void;

function handleError(error: unknown): void {
  if (error instanceof APIError) {
    console.error(`API Error (${error.statusCode}): ${error.message}`);
  } else if (error instanceof ValidationError) {
    console.error(`Validation Error in ${error.field}: ${error.message}`);
  } else if (error instanceof Error) {
    console.error(`Error: ${error.message}`);
  } else {
    console.error('Unknown error:', error);
  }
}
```

## SQL and Database Standards

### Query Formatting

```sql
-- Use uppercase for SQL keywords
-- Use meaningful table and column aliases
-- One clause per line for complex queries

SELECT 
    d.id,
    d.title,
    d.content,
    u.username AS author,
    COUNT(c.id) AS comment_count
FROM documents d
INNER JOIN users u ON d.user_id = u.id
LEFT JOIN comments c ON d.id = c.document_id
WHERE d.status = 'published'
    AND d.created_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY d.id, d.title, d.content, u.username
HAVING COUNT(c.id) > 0
ORDER BY d.created_at DESC
LIMIT 100;
```

### Migrations

```python
# Alembic migration example
"""Add document_status column

Revision ID: abc123
Revises: xyz789
Create Date: 2025-01-15 10:30:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = 'abc123'
down_revision = 'xyz789'
branch_labels = None
depends_on = None

def upgrade():
    """Add document_status column with default value."""
    op.add_column(
        'documents',
        sa.Column(
            'status',
            sa.String(20),
            nullable=False,
            server_default='pending'
        )
    )
    
    # Create index for frequently queried column
    op.create_index(
        'ix_documents_status',
        'documents',
        ['status']
    )

def downgrade():
    """Remove document_status column and index."""
    op.drop_index('ix_documents_status', table_name='documents')
    op.drop_column('documents', 'status')
```

### ORM Best Practices

```python
from sqlalchemy import select, func
from sqlalchemy.orm import joinedload

# Use explicit queries instead of lazy loading
async def get_document_with_author(doc_id: str) -> Optional[Document]:
    """Get document with author loaded."""
    query = (
        select(Document)
        .options(joinedload(Document.author))
        .where(Document.id == doc_id)
    )
    result = await session.execute(query)
    return result.scalar_one_or_none()

# Use bulk operations for better performance
async def create_documents(documents: list[Document]) -> None:
    """Create multiple documents efficiently."""
    session.add_all(documents)
    await session.commit()

# Use proper transaction handling
async def transfer_document(doc_id: str, new_owner_id: str) -> None:
    """Transfer document ownership atomically."""
    async with session.begin():
        doc = await session.get(Document, doc_id)
        if not doc:
            raise DocumentNotFoundError(doc_id)
        
        doc.owner_id = new_owner_id
        doc.transferred_at = datetime.utcnow()
        
        audit_log = AuditLog(
            action='transfer',
            document_id=doc_id,
            new_owner_id=new_owner_id
        )
        session.add(audit_log)
```

## API Design Standards

### RESTful API Conventions

```
# Resource naming (plural nouns)
GET    /api/v1/documents          # List documents
POST   /api/v1/documents          # Create document
GET    /api/v1/documents/{id}     # Get specific document
PUT    /api/v1/documents/{id}     # Update document (full)
PATCH  /api/v1/documents/{id}     # Update document (partial)
DELETE /api/v1/documents/{id}     # Delete document

# Nested resources
GET    /api/v1/documents/{id}/comments
POST   /api/v1/documents/{id}/comments

# Actions (use verbs for non-CRUD operations)
POST   /api/v1/documents/{id}/publish
POST   /api/v1/documents/{id}/archive
POST   /api/v1/search
```

### Request/Response Format

```python
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

# Request models
class CreateDocumentRequest(BaseModel):
    """Request model for creating a document."""
    
    title: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1)
    tags: list[str] = Field(default_factory=list, max_length=10)
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Sample Document",
                "content": "This is the document content",
                "tags": ["sample", "test"]
            }
        }

# Response models
class DocumentResponse(BaseModel):
    """Response model for document data."""
    
    id: str
    title: str
    content: str
    author: str
    created_at: datetime
    updated_at: datetime
    tags: list[str]
    
    class Config:
        from_attributes = True

# List responses with pagination
class PaginatedDocumentsResponse(BaseModel):
    """Paginated list of documents."""
    
    items: list[DocumentResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

# Error responses
class ErrorResponse(BaseModel):
    """Standard error response."""
    
    error: str
    message: str
    details: Optional[dict] = None
```

### Status Codes

```python
from fastapi import status

# Success responses
200 OK                  # Successful GET, PUT, PATCH
201 Created             # Successful POST
204 No Content          # Successful DELETE

# Client error responses
400 Bad Request         # Invalid request data
401 Unauthorized        # Missing/invalid authentication
403 Forbidden           # Insufficient permissions
404 Not Found           # Resource doesn't exist
409 Conflict            # Resource conflict (e.g., duplicate)
422 Unprocessable Entity # Validation error

# Server error responses
500 Internal Server Error # Server error
503 Service Unavailable   # Service temporarily unavailable
```

## Security Standards

### Input Validation

```python
from pydantic import BaseModel, validator, Field
import re

class UserInput(BaseModel):
    """Validated user input."""
    
    email: str = Field(..., regex=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    username: str = Field(..., min_length=3, max_length=30)
    
    @validator('username')
    def validate_username(cls, v):
        """Validate username format."""
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Username can only contain letters, numbers, hyphens, and underscores')
        return v
```

### Authentication & Authorization

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """Get the current authenticated user."""
    token = credentials.credentials
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = await get_user(user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user

def require_permission(permission: str):
    """Decorator to require specific permission."""
    async def permission_checker(user: User = Depends(get_current_user)):
        if not user.has_permission(permission):
            raise HTTPException(
                status_code=403,
                detail=f"Permission required: {permission}"
            )
        return user
    return permission_checker
```

### Secrets Management

```python
# NEVER commit secrets to code
# BAD:
API_KEY = "sk-1234567890abcdef"

# GOOD: Use environment variables
import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings."""
    
    api_key: str
    database_url: str
    secret_key: str
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
```

### SQL Injection Prevention

```python
# NEVER use string formatting for queries
# BAD:
query = f"SELECT * FROM users WHERE id = {user_id}"

# GOOD: Use parameterized queries
from sqlalchemy import text

query = text("SELECT * FROM users WHERE id = :user_id")
result = await session.execute(query, {"user_id": user_id})
```

## Performance Standards

### Database Optimization

```python
# Use indexes for frequently queried columns
from sqlalchemy import Index

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False)
    status = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False)
    
    __table_args__ = (
        Index('ix_documents_user_status', 'user_id', 'status'),
        Index('ix_documents_created', 'created_at'),
    )

# Use appropriate query pagination
async def list_documents(
    page: int = 1,
    page_size: int = 20
) -> PaginatedResponse:
    """List documents with pagination."""
    offset = (page - 1) * page_size
    
    query = select(Document).offset(offset).limit(page_size)
    result = await session.execute(query)
    documents = result.scalars().all()
    
    # Get total count (consider caching for large tables)
    count_query = select(func.count()).select_from(Document)
    total = await session.scalar(count_query)
    
    return PaginatedResponse(
        items=documents,
        total=total,
        page=page,
        page_size=page_size
    )
```

### Caching

```python
from functools import lru_cache
from typing import Optional
import redis

# In-memory caching for pure functions
@lru_cache(maxsize=1000)
def calculate_score(value: int) -> float:
    """Calculate score (cached)."""
    return complex_calculation(value)

# Redis caching for distributed systems
class CacheService:
    """Service for caching operations."""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.default_ttl = 3600  # 1 hour
    
    async def get(self, key: str) -> Optional[str]:
        """Get value from cache."""
        return await self.redis.get(key)
    
    async def set(
        self,
        key: str,
        value: str,
        ttl: Optional[int] = None
    ) -> None:
        """Set value in cache with TTL."""
        await self.redis.setex(
            key,
            ttl or self.default_ttl,
            value
        )
    
    async def get_or_compute(
        self,
        key: str,
        compute_fn: Callable[[], Awaitable[str]],
        ttl: Optional[int] = None
    ) -> str:
        """Get from cache or compute and cache."""
        cached = await self.get(key)
        if cached is not None:
            return cached
        
        value = await compute_fn()
        await self.set(key, value, ttl)
        return value
```

## Testing Standards

### Test Organization

```
tests/
├── unit/              # Unit tests
│   ├── services/
│   ├── models/
│   └── utils/
├── integration/       # Integration tests
│   ├── api/
│   └── db/
├── e2e/              # End-to-end tests
├── fixtures/         # Test fixtures
│   ├── data/
│   └── mocks/
└── conftest.py       # Pytest configuration
```

### Test Naming

```python
# Pattern: test_<function>_<scenario>_<expected_result>

def test_process_document_valid_pdf_returns_success():
    """Test that processing a valid PDF returns success."""
    pass

def test_process_document_invalid_format_raises_error():
    """Test that invalid format raises ValidationError."""
    pass

def test_fetch_document_not_found_returns_none():
    """Test that fetching non-existent document returns None."""
    pass
```

### Test Structure (AAA Pattern)

```python
def test_create_document():
    """Test document creation."""
    # Arrange: Set up test data and dependencies
    service = DocumentService(db=mock_db)
    document_data = {
        "title": "Test Document",
        "content": "Test content"
    }
    
    # Act: Execute the function being tested
    result = service.create_document(document_data)
    
    # Assert: Verify the expected outcome
    assert result.title == "Test Document"
    assert result.content == "Test content"
    assert result.id is not None
```

## Documentation Standards

### Code Comments

```python
# Use comments sparingly - prefer self-documenting code
# BAD: Redundant comment
user_count = 0  # Initialize user count to zero

# GOOD: Explains non-obvious logic
# Use binary search since the list is sorted by timestamp
index = bisect.bisect_left(timestamps, target_time)

# GOOD: Explains why, not what
# Skip validation for admin users to improve performance
if not user.is_admin:
    validate_input(data)
```

### README Files

Every directory should have a README if it contains non-obvious code:

```markdown
# Service Directory

## Overview
This directory contains business logic services.

## Structure
- `document.py` - Document processing service
- `search.py` - Search and indexing service
- `user.py` - User management service

## Usage
```python
from opendiscourse.services import DocumentService

service = DocumentService(db)
result = service.process_document(document)
```

## Dependencies
- PostgreSQL with pgvector extension
- Redis for caching
```

## Git Standards

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting
- `refactor`: Code restructuring
- `perf`: Performance improvement
- `test`: Adding tests
- `chore`: Maintenance

**Examples**:
```
feat(search): add semantic search capability

Implement vector-based semantic search using pgvector.
Includes indexing pipeline and query processing.

Closes #123
```

```
fix(api): handle timeout errors in document processing

Add retry logic with exponential backoff for timeout scenarios.
Improves reliability for large document processing.

Fixes #456
```

### Branch Strategy

- `main` - Production-ready code
- `develop` - Integration branch
- `feature/*` - New features
- `fix/*` - Bug fixes
- `hotfix/*` - Critical production fixes

### Pull Request Guidelines

1. Keep PRs small and focused
2. Include tests for new functionality
3. Update documentation
4. Ensure CI passes
5. Request review from relevant team members
6. Squash commits before merging

---

## Enforcement

These standards are enforced through:

1. **Pre-commit hooks** - Automated formatting and linting
2. **CI/CD pipeline** - Automated testing and quality checks
3. **Code reviews** - Manual review of all changes
4. **Static analysis** - Type checking and security scanning

## Questions?

If you have questions about these standards:
1. Check the [Contributing Guide](CONTRIBUTING.md)
2. Review existing code for examples
3. Ask in the pull request or discussion

**Last Updated**: 2025-11-17
