# Code Review Notes and Recommendations

**Review Date**: 2025-11-17  
**Project**: OpenDiscourse  
**Purpose**: Comprehensive codebase analysis and improvement recommendations

## Overview

This document provides detailed notes from the codebase review, specific recommendations for improvements, and examples of best practices to follow. It serves as a companion to [CODEBASE_REVIEW.md](CODEBASE_REVIEW.md) with actionable code examples.

## Table of Contents

- [Critical Fixes Required](#critical-fixes-required)
- [Code Quality Improvements](#code-quality-improvements)
- [Security Enhancements](#security-enhancements)
- [Performance Optimizations](#performance-optimizations)
- [Testing Recommendations](#testing-recommendations)
- [Documentation Guidelines](#documentation-guidelines)
- [Best Practice Examples](#best-practice-examples)

## Critical Fixes Required

### 1. Fix Bare Except Clauses

**File**: `opendiscourse/services/scraping/govinfo_document_processor.py`

**Current Code** (❌ Bad):
```python
try:
    process_document()
except:  # BAD: Catches ALL exceptions including KeyboardInterrupt, SystemExit
    pass
```

**Recommended Fix** (✅ Good):
```python
from typing import Optional
import logging

logger = logging.getLogger(__name__)

def process_document(doc_id: str) -> Optional[ProcessedDocument]:
    """Process a document with proper error handling.
    
    Args:
        doc_id: Document identifier
        
    Returns:
        Processed document or None if processing fails
        
    Raises:
        DocumentNotFoundError: If document doesn't exist
        ValidationError: If document validation fails
    """
    try:
        document = fetch_document(doc_id)
        validate_document(document)
        return transform_document(document)
    except DocumentNotFoundError:
        logger.error(f"Document not found: {doc_id}")
        raise  # Re-raise to let caller handle
    except ValidationError as e:
        logger.error(f"Document validation failed for {doc_id}: {e}")
        return None  # Return None for validation failures
    except Exception as e:
        # Catch unexpected errors but be specific
        logger.exception(f"Unexpected error processing {doc_id}")
        raise DocumentProcessingError(f"Failed to process document: {e}") from e
```

**Why This Matters**:
- Bare `except:` catches system signals (Ctrl+C, system exit)
- Makes debugging extremely difficult
- Can hide serious bugs
- Violates PEP 8 guidelines

### 2. Implement API Rate Limiting

**Files**: All API endpoints in `api/` directory

**Current State**: No rate limiting visible

**Recommended Implementation**:

```python
# requirements-dev.txt
slowapi>=0.1.9

# api/main.py or api/middleware/rate_limit.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import FastAPI, Request

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# In FastAPI app initialization
app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Apply to endpoints
from slowapi import Limiter

@app.post("/api/v1/documents/")
@limiter.limit("10/minute")  # 10 requests per minute per IP
async def create_document(
    request: Request,
    document: DocumentCreate,
    user: User = Depends(get_current_user)
):
    """Create a new document with rate limiting."""
    return await document_service.create(document)

@app.get("/api/v1/search")
@limiter.limit("30/minute")  # More generous for read operations
async def search(request: Request, query: str):
    """Search with rate limiting."""
    return await search_service.search(query)
```

**Configuration by User Type**:
```python
from functools import wraps

def rate_limit_by_user(public_limit: str, authenticated_limit: str):
    """Apply different rate limits based on authentication."""
    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            user = await get_current_user_optional(request)
            if user:
                # Authenticated users get higher limits
                limit = limiter.limit(authenticated_limit)
            else:
                # Public users get lower limits
                limit = limiter.limit(public_limit)
            return await limit(func)(request, *args, **kwargs)
        return wrapper
    return decorator

@app.post("/api/v1/rag/query")
@rate_limit_by_user(public_limit="5/minute", authenticated_limit="30/minute")
async def rag_query(request: Request, query: str):
    """RAG query with tiered rate limiting."""
    return await rag_service.query(query)
```

### 3. Add Security Headers

**File**: `api/main.py`

**Current State**: Need to verify security headers

**Recommended Implementation**:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware

app = FastAPI()

# Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    
    # Prevent clickjacking
    response.headers["X-Frame-Options"] = "DENY"
    
    # Prevent MIME type sniffing
    response.headers["X-Content-Type-Options"] = "nosniff"
    
    # Enable XSS protection
    response.headers["X-XSS-Protection"] = "1; mode=block"
    
    # HSTS (force HTTPS)
    response.headers["Strict-Transport-Security"] = (
        "max-age=31536000; includeSubDomains"
    )
    
    # Content Security Policy
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "font-src 'self' data:; "
        "connect-src 'self' https://api.opendiscourse.com"
    )
    
    # Referrer policy
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    # Permissions policy
    response.headers["Permissions-Policy"] = (
        "geolocation=(), microphone=(), camera=()"
    )
    
    return response

# HTTPS redirect in production
if settings.ENVIRONMENT == "production":
    app.add_middleware(HTTPSRedirectMiddleware)

# Trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS
)

# CORS with strict settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,  # Don't use ["*"] in production!
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
    max_age=3600,
)
```

## Code Quality Improvements

### 1. Add Missing Type Hints

**Files**: Various `__init__.py` and utility modules

**Bad Example** (❌):
```python
def process_items(items):
    results = []
    for item in items:
        results.append(transform(item))
    return results
```

**Good Example** (✅):
```python
from typing import TypeVar, Callable
from collections.abc import Sequence

T = TypeVar('T')
U = TypeVar('U')

def process_items(
    items: Sequence[T],
    transform: Callable[[T], U]
) -> list[U]:
    """Process items with a transformation function.
    
    Args:
        items: Sequence of items to process
        transform: Function to transform each item
        
    Returns:
        List of transformed items
        
    Examples:
        >>> process_items([1, 2, 3], lambda x: x * 2)
        [2, 4, 6]
    """
    return [transform(item) for item in items]
```

### 2. Improve ID Generation in React Components

**File**: `web/src/components/DocumentUpload.tsx`

**Current Code** (❌ Bad):
```typescript
const newFiles: UploadedFile[] = acceptedFiles.map(file => ({
  id: Math.random().toString(36).substr(2, 9),  // Can have collisions!
  name: file.name,
  size: file.size,
  // ...
}));
```

**Recommended Fix** (✅ Good):
```typescript
// Option 1: Use native crypto.randomUUID() (Node 16.7.0+, browsers with crypto)
const newFiles: UploadedFile[] = acceptedFiles.map(file => ({
  id: crypto.randomUUID(),  // Cryptographically secure, no collisions
  name: file.name,
  size: file.size,
  // ...
}));

// Option 2: Use uuid library for older environments
import { v4 as uuidv4 } from 'uuid';

const newFiles: UploadedFile[] = acceptedFiles.map(file => ({
  id: uuidv4(),
  name: file.name,
  size: file.size,
  // ...
}));
```

### 3. Standardize Error Handling in React

**Current Pattern** (❌ Inconsistent):
```typescript
try {
  await uploadFile(file);
} catch (error) {
  console.error('Upload failed:', error);  // Just logging
}
```

**Recommended Pattern** (✅ Good):
```typescript
import { useState } from 'react';

interface ErrorState {
  message: string;
  code?: string;
  details?: unknown;
}

export function useFileUpload() {
  const [error, setError] = useState<ErrorState | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const uploadFile = async (file: File): Promise<void> => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/v1/documents/', {
        method: 'POST',
        body: createFormData(file),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || 'Upload failed');
      }

      const data = await response.json();
      return data;
    } catch (err) {
      const errorState: ErrorState = {
        message: err instanceof Error ? err.message : 'Unknown error',
        code: err instanceof Error ? (err as any).code : undefined,
        details: err,
      };
      
      setError(errorState);
      
      // Also report to error tracking service
      reportError(errorState);
      
      throw err;  // Re-throw for caller to handle
    } finally {
      setIsLoading(false);
    }
  };

  return { uploadFile, error, isLoading };
}
```

## Security Enhancements

### 1. Input Validation Best Practices

**File**: API request models

**Good Example** (✅):
```python
from pydantic import BaseModel, Field, validator, root_validator
from typing import Optional
import re

class DocumentCreate(BaseModel):
    """Request model for document creation with comprehensive validation."""
    
    title: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Document title"
    )
    
    content: str = Field(
        ...,
        min_length=1,
        max_length=1_000_000,  # 1MB limit
        description="Document content"
    )
    
    tags: list[str] = Field(
        default_factory=list,
        max_length=10,
        description="Document tags"
    )
    
    @validator('title')
    def validate_title(cls, v: str) -> str:
        """Validate title format."""
        # Remove control characters
        v = ''.join(char for char in v if ord(char) >= 32)
        
        if not v.strip():
            raise ValueError('Title cannot be empty or whitespace only')
        
        # Check for suspicious patterns
        if re.search(r'<script|javascript:|onerror=', v, re.IGNORECASE):
            raise ValueError('Title contains suspicious content')
        
        return v.strip()
    
    @validator('tags', each_item=True)
    def validate_tag(cls, v: str) -> str:
        """Validate each tag."""
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError(
                f'Tag "{v}" contains invalid characters. '
                'Only alphanumeric, hyphens, and underscores allowed'
            )
        
        if len(v) > 50:
            raise ValueError(f'Tag "{v}" exceeds maximum length of 50')
        
        return v.lower()  # Normalize to lowercase
    
    @root_validator
    def validate_content_format(cls, values):
        """Cross-field validation."""
        title = values.get('title', '')
        content = values.get('content', '')
        
        # Ensure content is not just the title repeated
        if content.strip() == title.strip():
            raise ValueError('Content cannot be identical to title')
        
        return values
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Climate Change Policy Analysis",
                "content": "Detailed analysis of climate change policies...",
                "tags": ["climate", "policy", "analysis"]
            }
        }
```

### 2. SQL Injection Prevention

**Always use ORM or parameterized queries**:

```python
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

# ❌ BAD: String formatting (SQL injection vulnerability!)
async def get_user_bad(username: str, session: AsyncSession):
    query = f"SELECT * FROM users WHERE username = '{username}'"
    result = await session.execute(text(query))
    return result.fetchone()

# ✅ GOOD: ORM (safe)
async def get_user_orm(username: str, session: AsyncSession):
    query = select(User).where(User.username == username)
    result = await session.execute(query)
    return result.scalar_one_or_none()

# ✅ GOOD: Parameterized query (safe)
async def get_user_parameterized(username: str, session: AsyncSession):
    query = text("SELECT * FROM users WHERE username = :username")
    result = await session.execute(query, {"username": username})
    return result.fetchone()
```

### 3. File Upload Security

```python
from pathlib import Path
import mimetypes
import magic  # python-magic library

ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.txt', '.md'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

async def validate_upload(file: UploadFile) -> None:
    """Validate uploaded file for security.
    
    Args:
        file: Uploaded file
        
    Raises:
        ValidationError: If file fails validation
    """
    # Check file size
    file_size = 0
    while chunk := await file.read(8192):
        file_size += len(chunk)
        if file_size > MAX_FILE_SIZE:
            raise ValidationError(
                f"File size exceeds maximum of {MAX_FILE_SIZE} bytes"
            )
    
    await file.seek(0)  # Reset file pointer
    
    # Validate extension
    file_path = Path(file.filename)
    if file_path.suffix.lower() not in ALLOWED_EXTENSIONS:
        raise ValidationError(
            f"File type {file_path.suffix} not allowed. "
            f"Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Validate MIME type (prevent extension spoofing)
    content = await file.read(2048)
    await file.seek(0)
    
    mime = magic.from_buffer(content, mime=True)
    
    expected_mimes = {
        '.pdf': 'application/pdf',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        '.txt': 'text/plain',
        '.md': 'text/plain',
    }
    
    expected = expected_mimes.get(file_path.suffix.lower())
    if expected and mime != expected:
        raise ValidationError(
            f"File content does not match extension. "
            f"Expected {expected}, got {mime}"
        )
    
    # Sanitize filename
    safe_filename = "".join(
        c for c in file.filename if c.isalnum() or c in ('_', '-', '.')
    )
    
    if safe_filename != file.filename:
        logger.warning(
            f"Filename sanitized: {file.filename} -> {safe_filename}"
        )
```

## Performance Optimizations

### 1. Implement Caching

```python
from functools import lru_cache
from typing import Optional
import redis.asyncio as redis
import json
from datetime import timedelta

# In-memory caching for pure functions
@lru_cache(maxsize=1000)
def calculate_similarity(text1: str, text2: str) -> float:
    """Calculate similarity (cached in memory)."""
    # Expensive computation
    return compute_similarity(text1, text2)

# Redis caching for distributed systems
class CacheService:
    """Caching service using Redis."""
    
    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url)
    
    async def get_cached(
        self,
        key: str,
        compute_fn: Callable[[], Awaitable[dict]],
        ttl: timedelta = timedelta(hours=1)
    ) -> dict:
        """Get value from cache or compute and cache it.
        
        Args:
            key: Cache key
            compute_fn: Function to compute value if not cached
            ttl: Time to live for cached value
            
        Returns:
            Cached or computed value
        """
        # Try to get from cache
        cached = await self.redis.get(key)
        if cached:
            logger.debug(f"Cache hit: {key}")
            return json.loads(cached)
        
        # Compute value
        logger.debug(f"Cache miss: {key}")
        value = await compute_fn()
        
        # Store in cache
        await self.redis.setex(
            key,
            int(ttl.total_seconds()),
            json.dumps(value)
        )
        
        return value
    
    async def invalidate(self, pattern: str) -> int:
        """Invalidate cache keys matching pattern.
        
        Args:
            pattern: Redis key pattern (e.g., "user:*")
            
        Returns:
            Number of keys deleted
        """
        keys = []
        async for key in self.redis.scan_iter(match=pattern):
            keys.append(key)
        
        if keys:
            return await self.redis.delete(*keys)
        return 0

# Usage in API endpoint
from fastapi import Depends

async def get_cache_service() -> CacheService:
    """Dependency for cache service."""
    return CacheService(settings.REDIS_URL)

@app.get("/api/v1/documents/{doc_id}")
async def get_document(
    doc_id: str,
    cache: CacheService = Depends(get_cache_service)
):
    """Get document with caching."""
    return await cache.get_cached(
        key=f"document:{doc_id}",
        compute_fn=lambda: fetch_document_from_db(doc_id),
        ttl=timedelta(minutes=15)
    )
```

### 2. Database Query Optimization

```python
from sqlalchemy import select
from sqlalchemy.orm import joinedload, selectinload

# ❌ BAD: N+1 query problem
async def get_documents_bad(session: AsyncSession) -> list[Document]:
    """Inefficient query causing N+1 problem."""
    query = select(Document)
    result = await session.execute(query)
    documents = result.scalars().all()
    
    # This causes N additional queries!
    for doc in documents:
        _ = doc.author  # Triggers lazy load for each document
    
    return documents

# ✅ GOOD: Eager loading with joinedload
async def get_documents_good(session: AsyncSession) -> list[Document]:
    """Efficient query with eager loading."""
    query = (
        select(Document)
        .options(
            joinedload(Document.author),  # Single JOIN
            selectinload(Document.tags)   # Separate query for one-to-many
        )
        .order_by(Document.created_at.desc())
    )
    
    result = await session.execute(query)
    return result.unique().scalars().all()

# ✅ GOOD: Pagination for large result sets
from pydantic import BaseModel

class PaginationParams(BaseModel):
    """Pagination parameters."""
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)

async def list_documents_paginated(
    pagination: PaginationParams,
    session: AsyncSession
) -> dict:
    """List documents with pagination."""
    offset = (pagination.page - 1) * pagination.page_size
    
    # Get total count (consider caching for large tables)
    count_query = select(func.count()).select_from(Document)
    total = await session.scalar(count_query)
    
    # Get paginated results
    query = (
        select(Document)
        .options(joinedload(Document.author))
        .offset(offset)
        .limit(pagination.page_size)
        .order_by(Document.created_at.desc())
    )
    
    result = await session.execute(query)
    documents = result.unique().scalars().all()
    
    return {
        "items": documents,
        "total": total,
        "page": pagination.page,
        "page_size": pagination.page_size,
        "total_pages": (total + pagination.page_size - 1) // pagination.page_size
    }
```

## Testing Recommendations

### 1. Comprehensive Test Structure

```python
# tests/unit/services/test_document_service.py
import pytest
from unittest.mock import Mock, AsyncMock, patch
from opendiscourse.services.document import DocumentService
from opendiscourse.db.models import Document

class TestDocumentService:
    """Test suite for DocumentService."""
    
    @pytest.fixture
    def mock_session(self):
        """Create a mock database session."""
        session = AsyncMock()
        return session
    
    @pytest.fixture
    def service(self, mock_session):
        """Create DocumentService instance."""
        return DocumentService(session=mock_session)
    
    @pytest.mark.asyncio
    async def test_create_document_success(self, service, mock_session):
        """Test successful document creation."""
        # Arrange
        document_data = {
            "title": "Test Document",
            "content": "Test content"
        }
        
        expected_doc = Document(id="123", **document_data)
        mock_session.add = Mock()
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()
        
        # Act
        result = await service.create_document(document_data)
        
        # Assert
        assert result.title == document_data["title"]
        assert result.content == document_data["content"]
        mock_session.add.assert_called_once()
        mock_session.commit.assert_awaited_once()
    
    @pytest.mark.asyncio
    async def test_create_document_validation_error(self, service):
        """Test document creation with invalid data."""
        # Arrange
        invalid_data = {
            "title": "",  # Invalid: empty title
            "content": "Test content"
        }
        
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            await service.create_document(invalid_data)
        
        assert "title" in str(exc_info.value).lower()
    
    @pytest.mark.parametrize("title,expected_valid", [
        ("Valid Title", True),
        ("", False),
        ("A" * 256, False),  # Too long
        ("Valid-Title_123", True),
        ("<script>alert('xss')</script>", False),
    ])
    def test_validate_title(self, service, title, expected_valid):
        """Test title validation with various inputs."""
        if expected_valid:
            assert service.validate_title(title) == title
        else:
            with pytest.raises(ValidationError):
                service.validate_title(title)
```

### 2. Integration Tests

```python
# tests/integration/test_document_api.py
import pytest
from httpx import AsyncClient
from fastapi import status

@pytest.mark.integration
class TestDocumentAPI:
    """Integration tests for document API."""
    
    @pytest.fixture
    async def client(self, app):
        """Create test client."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            yield client
    
    @pytest.fixture
    async def auth_headers(self, test_user):
        """Get authentication headers."""
        token = create_test_token(test_user)
        return {"Authorization": f"Bearer {token}"}
    
    @pytest.mark.asyncio
    async def test_create_document_authenticated(
        self,
        client,
        auth_headers
    ):
        """Test document creation with authentication."""
        # Arrange
        document_data = {
            "title": "Integration Test Document",
            "content": "Test content for integration"
        }
        
        # Act
        response = await client.post(
            "/api/v1/documents/",
            json=document_data,
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["title"] == document_data["title"]
        assert "id" in data
        assert "created_at" in data
    
    @pytest.mark.asyncio
    async def test_create_document_unauthenticated(self, client):
        """Test that unauthenticated requests are rejected."""
        # Act
        response = await client.post(
            "/api/v1/documents/",
            json={"title": "Test", "content": "Test"}
        )
        
        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    @pytest.mark.asyncio
    async def test_list_documents_pagination(
        self,
        client,
        auth_headers,
        test_documents  # Fixture that creates test data
    ):
        """Test document listing with pagination."""
        # Act
        response = await client.get(
            "/api/v1/documents/?page=1&page_size=10",
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert len(data["items"]) <= 10
```

### 3. React Component Tests

```typescript
// web/src/components/__tests__/DocumentCard.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { DocumentCard } from '../DocumentCard';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
};

describe('DocumentCard', () => {
  const mockDocument = {
    id: '123',
    title: 'Test Document',
    content: 'Test content',
    createdAt: '2025-01-01T00:00:00Z',
  };

  it('renders document information', () => {
    render(<DocumentCard document={mockDocument} />, {
      wrapper: createWrapper(),
    });

    expect(screen.getByText('Test Document')).toBeInTheDocument();
    expect(screen.getByText(/test content/i)).toBeInTheDocument();
  });

  it('handles update click', async () => {
    const onUpdate = jest.fn();
    
    render(
      <DocumentCard document={mockDocument} onUpdate={onUpdate} />,
      { wrapper: createWrapper() }
    );

    const updateButton = screen.getByRole('button', { name: /update/i });
    fireEvent.click(updateButton);

    await waitFor(() => {
      expect(onUpdate).toHaveBeenCalledWith('123');
    });
  });

  it('shows loading state during update', async () => {
    render(<DocumentCard document={mockDocument} />, {
      wrapper: createWrapper(),
    });

    const updateButton = screen.getByRole('button', { name: /update/i });
    fireEvent.click(updateButton);

    expect(screen.getByText(/updating/i)).toBeInTheDocument();
    expect(updateButton).toBeDisabled();
  });

  it('displays error message on update failure', async () => {
    // Mock API to fail
    global.fetch = jest.fn(() =>
      Promise.reject(new Error('Update failed'))
    );

    render(<DocumentCard document={mockDocument} />, {
      wrapper: createWrapper(),
    });

    const updateButton = screen.getByRole('button', { name: /update/i });
    fireEvent.click(updateButton);

    await waitFor(() => {
      expect(screen.getByText(/update failed/i)).toBeInTheDocument();
    });
  });
});
```

## Documentation Guidelines

### 1. Module Documentation Template

```python
"""Module for document processing operations.

This module provides services for processing, validating, and transforming
documents in various formats. It supports PDF, DOCX, TXT, and Markdown files.

Key Features:
    - Document validation and sanitization
    - Format conversion and normalization
    - Metadata extraction
    - Content analysis and indexing

Examples:
    Basic document processing:
    
    >>> from opendiscourse.services import DocumentService
    >>> service = DocumentService()
    >>> result = await service.process_document("document.pdf")
    >>> print(result.status)
    'completed'

    Batch processing:
    
    >>> documents = ["doc1.pdf", "doc2.docx"]
    >>> results = await service.process_batch(documents)
    >>> print(f"Processed {len(results)} documents")

Dependencies:
    - PyPDF2: PDF processing
    - python-docx: DOCX processing
    - BeautifulSoup4: HTML cleaning

See Also:
    - opendiscourse.db.models: Database models for documents
    - opendiscourse.services.search: Search and indexing services

Note:
    This module requires PostgreSQL with pgvector extension for vector
    operations. Ensure the extension is installed before use.

Todo:
    * Add support for ODT format (Issue #123)
    * Improve error handling for corrupted files (Issue #456)
    * Add progress tracking for large batches (Issue #789)
"""

from typing import Optional, Sequence
import logging

logger = logging.getLogger(__name__)

# Module constants
SUPPORTED_FORMATS = [".pdf", ".docx", ".txt", ".md"]
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# Rest of module code...
```

### 2. API Documentation Template

```python
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])

@router.post(
    "/",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new document",
    description="""
    Create a new document in the system.
    
    This endpoint accepts document metadata and content, validates the input,
    and stores it in the database. The document will be indexed for search.
    
    **Authentication**: Required  
    **Rate Limit**: 10 requests per minute
    
    **Permissions**:
    - Authenticated users can create documents
    - Documents are owned by the creating user
    
    **Validation**:
    - Title: 1-255 characters
    - Content: 1-1,000,000 characters
    - Tags: Maximum 10 tags, each 1-50 characters
    """,
    responses={
        201: {
            "description": "Document created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "title": "Climate Policy Analysis",
                        "content": "Detailed analysis...",
                        "author": "user@example.com",
                        "created_at": "2025-01-15T10:30:00Z",
                        "tags": ["climate", "policy"]
                    }
                }
            }
        },
        400: {
            "description": "Invalid input data",
            "content": {
                "application/json": {
                    "example": {
                        "error": "ValidationError",
                        "message": "Title cannot be empty",
                        "details": {"field": "title"}
                    }
                }
            }
        },
        401: {"description": "Authentication required"},
        429: {"description": "Rate limit exceeded"}
    }
)
async def create_document(
    document: DocumentCreate,
    user: User = Depends(get_current_user),
    service: DocumentService = Depends(get_document_service)
) -> DocumentResponse:
    """Create a new document.
    
    Args:
        document: Document creation data
        user: Current authenticated user
        service: Document service instance
        
    Returns:
        Created document with generated ID
        
    Raises:
        HTTPException: 400 if validation fails
        HTTPException: 401 if not authenticated
        HTTPException: 429 if rate limit exceeded
    """
    try:
        created = await service.create_document(document, user_id=user.id)
        return created
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "ValidationError", "message": str(e)}
        )
```

## Best Practice Examples

### 1. Configuration Management

```python
# config/settings.py
from pydantic_settings import BaseSettings
from typing import Optional
from functools import lru_cache

class Settings(BaseSettings):
    """Application settings."""
    
    # App
    APP_NAME: str = "OpenDiscourse"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    
    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_WORKERS: int = 4
    
    # Database
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Security
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALLOWED_HOSTS: list[str] = ["localhost", "127.0.0.1"]
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]
    
    # External APIs
    GOVINFO_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    
    # Feature Flags
    FEATURE_RAG_ENABLED: bool = True
    FEATURE_VECTOR_SEARCH: bool = True
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

# Usage
settings = get_settings()
```

### 2. Logging Configuration

```python
# config/logging.py
import logging
import sys
from typing import Optional

def setup_logging(
    level: str = "INFO",
    json_format: bool = False
) -> None:
    """Configure application logging.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_format: Whether to use JSON format for logs
    """
    log_level = getattr(logging, level.upper())
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Set specific log levels for noisy libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    
    # Configure application logger
    logger = logging.getLogger("opendiscourse")
    logger.setLevel(log_level)
    
    logger.info(
        f"Logging configured: level={level}, json_format={json_format}"
    )
```

### 3. Dependency Injection Pattern

```python
# api/dependencies.py
from typing import AsyncGenerator
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from opendiscourse.db.session import get_db_session
from opendiscourse.services import DocumentService, SearchService

async def get_document_service(
    session: AsyncSession = Depends(get_db_session)
) -> DocumentService:
    """Get document service instance.
    
    Args:
        session: Database session
        
    Returns:
        Document service instance
    """
    return DocumentService(session=session)

async def get_search_service(
    session: AsyncSession = Depends(get_db_session)
) -> SearchService:
    """Get search service instance.
    
    Args:
        session: Database session
        
    Returns:
        Search service instance
    """
    return SearchService(session=session)

# Usage in endpoint
@app.get("/api/v1/documents/{doc_id}")
async def get_document(
    doc_id: str,
    service: DocumentService = Depends(get_document_service)
):
    """Get document by ID."""
    document = await service.get_by_id(doc_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {doc_id} not found"
        )
    return document
```

## Summary

This document provides actionable code examples and recommendations based on the codebase review. Key takeaways:

1. **Fix critical issues immediately**: Bare except clauses, rate limiting, security headers
2. **Improve code quality**: Type hints, error handling, documentation
3. **Enhance security**: Input validation, file upload security, SQL injection prevention
4. **Optimize performance**: Caching, query optimization, pagination
5. **Increase test coverage**: Aim for 80%+ with comprehensive test suites
6. **Standardize documentation**: Use consistent patterns across the codebase

For questions or clarifications, refer to:
- [CODING_STANDARDS.md](CODING_STANDARDS.md) - Coding standards and guidelines
- [CONTRIBUTING.md](CONTRIBUTING.md) - Contributing guidelines
- [CODEBASE_REVIEW.md](CODEBASE_REVIEW.md) - Comprehensive review findings

---

**Last Updated**: 2025-11-17  
**Next Review**: After implementing critical fixes
