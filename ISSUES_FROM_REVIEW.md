# GitHub Issues to Create from Codebase Review

This document lists issues identified during the codebase review that should be created in GitHub Issues. Each issue includes a title, description, labels, and priority.

**Review Date**: 2025-11-17  
**Source**: [CODEBASE_REVIEW.md](CODEBASE_REVIEW.md)

## How to Create These Issues

You can create these issues manually in GitHub, or use the GitHub CLI:

```bash
# Install GitHub CLI if needed
# brew install gh  # macOS
# choco install gh  # Windows

# Login to GitHub
gh auth login

# Create issues from this file (adjust as needed)
gh issue create --title "Issue Title" --body "Issue description" --label "label1,label2"
```

---

## Critical Priority Issues

### Issue 1: Fix Bare Except Clause in govinfo_document_processor.py

**Title**: Fix bare except clause causing potential bugs

**Labels**: `bug`, `priority: critical`, `type: backend`, `good first issue`

**Description**:
```markdown
## Problem
The file `opendiscourse/services/scraping/govinfo_document_processor.py` contains a bare `except:` clause that catches all exceptions including system signals like `KeyboardInterrupt` and `SystemExit`.

## Location
File: `opendiscourse/services/scraping/govinfo_document_processor.py`

## Why This is Critical
- Makes debugging extremely difficult
- Can hide serious bugs
- Catches system signals that should propagate
- Violates PEP 8 coding standards

## Recommended Fix
Replace with specific exception handling:

```python
# Instead of:
try:
    process_document()
except:  # BAD
    pass

# Use:
try:
    process_document()
except (ValueError, TypeError, IOError) as e:
    logger.error(f"Document processing failed: {e}")
    raise
except Exception as e:
    logger.exception(f"Unexpected error: {e}")
    raise DocumentProcessingError(f"Failed to process: {e}") from e
```

## Acceptance Criteria
- [ ] Remove bare `except:` clause
- [ ] Add specific exception types
- [ ] Add proper logging
- [ ] Add test cases for error scenarios
- [ ] Verify no other bare except clauses exist in codebase

## References
- [CODEBASE_REVIEW.md](../CODEBASE_REVIEW.md#issue-1-bare-except-clause)
- [CODING_STANDARDS.md](../CODING_STANDARDS.md#error-handling)
- [PEP 8 - Programming Recommendations](https://peps.python.org/pep-0008/#programming-recommendations)
```

---

### Issue 2: Implement API Rate Limiting

**Title**: Implement rate limiting for API endpoints

**Labels**: `enhancement`, `priority: critical`, `type: backend`, `security`

**Description**:
```markdown
## Problem
API endpoints currently have no rate limiting, making them vulnerable to:
- Denial of Service (DoS) attacks
- Resource exhaustion
- Abuse and scraping
- Excessive costs

## Scope
All API endpoints in `api/` directory need rate limiting.

## Recommended Implementation

### 1. Install slowapi
```bash
pip install slowapi
```

### 2. Configure Rate Limiter
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
```

### 3. Apply to Endpoints
```python
@app.post("/api/v1/documents/")
@limiter.limit("10/minute")
async def create_document(request: Request, ...):
    ...
```

## Suggested Rate Limits
- **Public endpoints**: 10-30 requests/minute
- **Authenticated users**: 60-100 requests/minute
- **Search/RAG endpoints**: 5-20 requests/minute (expensive operations)
- **Admin endpoints**: 200 requests/minute

## Acceptance Criteria
- [ ] slowapi installed and configured
- [ ] Rate limits applied to all API endpoints
- [ ] Different limits for authenticated vs unauthenticated users
- [ ] Rate limit headers included in responses
- [ ] Custom rate limit exceeded error response
- [ ] Documentation updated with rate limits
- [ ] Tests added for rate limiting behavior

## References
- [CODE_REVIEW_NOTES.md](../CODE_REVIEW_NOTES.md#2-implement-api-rate-limiting)
- [slowapi documentation](https://slowapi.readthedocs.io/)
```

---

### Issue 3: Add Security Headers to API Responses

**Title**: Add security headers to all API responses

**Labels**: `enhancement`, `priority: critical`, `type: backend`, `security`

**Description**:
```markdown
## Problem
API responses lack important security headers that protect against common web vulnerabilities.

## Missing Headers
- `X-Frame-Options` - Prevents clickjacking
- `X-Content-Type-Options` - Prevents MIME sniffing
- `X-XSS-Protection` - XSS protection
- `Strict-Transport-Security` - Forces HTTPS
- `Content-Security-Policy` - Controls resource loading
- `Referrer-Policy` - Controls referrer information
- `Permissions-Policy` - Controls browser features

## Recommended Implementation

Add middleware to `api/main.py`:

```python
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    
    return response
```

## Acceptance Criteria
- [ ] Security headers middleware implemented
- [ ] All headers properly configured for application needs
- [ ] HTTPS redirect enabled in production
- [ ] Headers tested with security scanning tools
- [ ] Documentation updated
- [ ] CSP policy tailored to application (not too restrictive)

## References
- [CODE_REVIEW_NOTES.md](../CODE_REVIEW_NOTES.md#3-add-security-headers)
- [OWASP Secure Headers Project](https://owasp.org/www-project-secure-headers/)
- [Mozilla Observatory](https://observatory.mozilla.org/)
```

---

### Issue 4: Increase Test Coverage to 80%

**Title**: Increase test coverage from ~45% to minimum 80%

**Labels**: `enhancement`, `priority: critical`, `type: testing`

**Description**:
```markdown
## Problem
Current test coverage is estimated at 40-50%, well below the recommended 80% minimum. This increases the risk of bugs and makes refactoring risky.

## Current State
- 17 Python test files
- Jest configuration for frontend
- No coverage reporting configured
- Many modules lack tests entirely

## Goal
Achieve minimum 80% test coverage across:
- Backend Python code (opendiscourse/, api/)
- Frontend TypeScript code (web/src/)

## Implementation Plan

### Phase 1: Set Up Coverage Reporting
- [ ] Configure pytest-cov for Python
- [ ] Configure Jest coverage for TypeScript
- [ ] Add coverage reporting to CI/CD
- [ ] Set up coverage badge in README

### Phase 2: Add Missing Tests (Priority Order)
1. [ ] Services layer (document, search, scraping)
2. [ ] API endpoints (integration tests)
3. [ ] Database models and queries
4. [ ] Utility functions
5. [ ] React components
6. [ ] Frontend hooks and utilities

### Phase 3: Enforce Coverage
- [ ] Add coverage gate to CI/CD (fail if below 80%)
- [ ] Add pre-commit hook for coverage check
- [ ] Document testing requirements in CONTRIBUTING.md

## Suggested Tools
- Python: `pytest`, `pytest-cov`, `pytest-asyncio`
- TypeScript: `jest`, `@testing-library/react`, `@testing-library/user-event`
- Coverage: `codecov` or `coveralls`

## Acceptance Criteria
- [ ] Coverage reporting configured
- [ ] Test coverage ≥80% for backend
- [ ] Test coverage ≥80% for frontend
- [ ] CI/CD fails if coverage drops below 80%
- [ ] Coverage badge added to README
- [ ] Testing guide added to documentation

## References
- [CODEBASE_REVIEW.md](../CODEBASE_REVIEW.md#testing-analysis)
- [CODE_REVIEW_NOTES.md](../CODE_REVIEW_NOTES.md#testing-recommendations)
- [CODING_STANDARDS.md](../CODING_STANDARDS.md#testing-standards)
```

---

## High Priority Issues

### Issue 5: Implement Caching Layer with Redis

**Title**: Add Redis caching layer for performance optimization

**Labels**: `enhancement`, `priority: high`, `type: backend`, `performance`

**Description**:
```markdown
## Problem
No caching implementation is visible in the codebase. Caching would significantly improve:
- API response times
- Database load
- Search performance
- User experience

## Scope
Implement caching for:
1. Frequently accessed documents
2. Search results
3. API responses
4. User sessions
5. Computed results (embeddings, similarity scores)

## Recommended Implementation

### 1. Add Redis Dependency
```toml
# pyproject.toml
dependencies = [
    "redis[hiredis]>=5.0.0",
]
```

### 2. Implement Cache Service
See [CODE_REVIEW_NOTES.md](../CODE_REVIEW_NOTES.md#1-implement-caching) for full implementation example.

### 3. Apply Caching Strategy
- **Cache Duration**:
  - Documents: 15 minutes
  - Search results: 5 minutes
  - User data: 30 minutes
  - Static content: 1 hour
- **Cache Invalidation**: On updates/deletes
- **Cache Keys**: Consistent naming convention

## Acceptance Criteria
- [ ] Redis integration implemented
- [ ] CacheService with get/set/invalidate methods
- [ ] Caching applied to high-traffic endpoints
- [ ] Cache hit/miss metrics logged
- [ ] Cache invalidation on data updates
- [ ] Redis configuration in environment variables
- [ ] Documentation updated
- [ ] Performance benchmarks showing improvement

## References
- [CODE_REVIEW_NOTES.md](../CODE_REVIEW_NOTES.md#1-implement-caching)
- [CODEBASE_REVIEW.md](../CODEBASE_REVIEW.md#caching)
```

---

### Issue 6: Optimize Database Queries and Add Indexes

**Title**: Review and optimize database queries for performance

**Labels**: `enhancement`, `priority: high`, `type: backend`, `performance`, `database`

**Description**:
```markdown
## Problem
Need to review database queries for:
- N+1 query problems
- Missing indexes
- Inefficient joins
- Large result sets without pagination

## Tasks

### 1. Review Queries for N+1 Problems
- [ ] Audit all SQLAlchemy queries
- [ ] Add `joinedload`/`selectinload` where needed
- [ ] Test with realistic data volumes

### 2. Add Missing Indexes
- [ ] Review slow query log
- [ ] Identify frequently queried columns
- [ ] Add composite indexes for common query patterns
- [ ] Document indexing strategy

### 3. Implement Query Optimization
- [ ] Use select_in_loading for one-to-many relationships
- [ ] Implement query result caching
- [ ] Add database query logging in development
- [ ] Set up query performance monitoring

### 4. Ensure Pagination
- [ ] Verify all list endpoints use pagination
- [ ] Implement cursor-based pagination for large datasets
- [ ] Document pagination parameters

## Example Issues to Fix
```python
# N+1 Problem Example
query = select(Document)  # Missing eager loading
documents = await session.execute(query)
for doc in documents:
    author = doc.author  # N+1! Triggers separate query for each doc
```

## Acceptance Criteria
- [ ] All queries reviewed and optimized
- [ ] No N+1 query problems remain
- [ ] Appropriate indexes added
- [ ] Query performance benchmarks recorded
- [ ] Slow query monitoring configured
- [ ] Documentation updated with query patterns

## References
- [CODE_REVIEW_NOTES.md](../CODE_REVIEW_NOTES.md#2-database-query-optimization)
- [SQLAlchemy Performance Documentation](https://docs.sqlalchemy.org/en/20/orm/queryguide/performance.html)
```

---

### Issue 7: Complete Missing Documentation

**Title**: Complete documentation for undocumented modules

**Labels**: `documentation`, `priority: high`, `good first issue`

**Description**:
```markdown
## Problem
Several modules lack documentation:
- Some `__init__.py` files have no docstrings
- Utility modules missing function documentation
- Inconsistent docstring quality across modules

## Requirements
All documentation should follow [CODING_STANDARDS.md](../CODING_STANDARDS.md#documentation-standards):
- Google-style docstrings
- Type information in docstrings
- Usage examples for complex functions
- Module-level docstrings with overview

## Modules Needing Documentation

### High Priority
- [ ] `opendiscourse/utils/*.py` - Utility modules
- [ ] `opendiscourse/services/*.py` - Service modules
- [ ] Various `__init__.py` files

### Medium Priority
- [ ] API endpoint documentation
- [ ] Database model field descriptions
- [ ] Configuration module documentation

### Low Priority
- [ ] Test file documentation
- [ ] Script documentation

## Documentation Template
See [CODE_REVIEW_NOTES.md](../CODE_REVIEW_NOTES.md#1-module-documentation-template) for templates.

## Acceptance Criteria
- [ ] All public modules have docstrings
- [ ] All public functions have docstrings
- [ ] Docstrings follow Google style
- [ ] Complex functions have usage examples
- [ ] API documentation auto-generated and accurate

## References
- [CODING_STANDARDS.md](../CODING_STANDARDS.md#documentation-standards)
- [CODE_REVIEW_NOTES.md](../CODE_REVIEW_NOTES.md#documentation-guidelines)
- [Google Python Style Guide - Docstrings](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings)
```

---

### Issue 8: Standardize Error Handling Across Codebase

**Title**: Implement consistent error handling patterns

**Labels**: `enhancement`, `priority: high`, `type: backend`, `type: frontend`

**Description**:
```markdown
## Problem
Error handling patterns are inconsistent across the codebase:
- Different error response formats
- Inconsistent exception types
- Missing error logging
- No centralized error handling

## Goals
1. Standardize error response format
2. Create custom exception hierarchy
3. Implement centralized error handlers
4. Add comprehensive error logging

## Implementation Plan

### Backend (Python/FastAPI)

1. **Create Exception Hierarchy**
```python
class OpenDiscourseError(Exception):
    """Base exception for OpenDiscourse."""
    pass

class ValidationError(OpenDiscourseError):
    """Validation error."""
    pass

class NotFoundError(OpenDiscourseError):
    """Resource not found."""
    pass

class AuthenticationError(OpenDiscourseError):
    """Authentication failed."""
    pass
```

2. **Standard Error Response Format**
```python
class ErrorResponse(BaseModel):
    error: str
    message: str
    details: Optional[dict] = None
    timestamp: datetime
```

3. **Global Exception Handlers**
```python
@app.exception_handler(ValidationError)
async def validation_error_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content=ErrorResponse(
            error="ValidationError",
            message=str(exc),
            timestamp=datetime.utcnow()
        ).dict()
    )
```

### Frontend (TypeScript/React)

1. **Error State Type**
```typescript
interface ErrorState {
  message: string;
  code?: string;
  details?: unknown;
}
```

2. **Error Boundaries**
3. **Centralized Error Reporting**

## Acceptance Criteria
- [ ] Custom exception hierarchy created
- [ ] Standard error response format defined
- [ ] Global exception handlers implemented
- [ ] Error logging configured
- [ ] Frontend error boundaries added
- [ ] Error handling documentation updated
- [ ] Tests added for error scenarios

## References
- [CODE_REVIEW_NOTES.md](../CODE_REVIEW_NOTES.md#error-handling)
- [FastAPI Error Handling](https://fastapi.tiangolo.com/tutorial/handling-errors/)
```

---

## Medium Priority Issues

### Issue 9: Fix Weak ID Generation in DocumentUpload Component

**Title**: Replace Math.random() with cryptographically secure UUID

**Labels**: `bug`, `priority: medium`, `type: frontend`, `security`

**Description**:
```markdown
## Problem
File: `web/src/components/DocumentUpload.tsx`

The component uses `Math.random().toString(36).substr(2, 9)` for generating file IDs, which:
- Is not cryptographically secure
- Can produce collisions
- Generates variable-length IDs

## Current Code
```typescript
id: Math.random().toString(36).substr(2, 9),
```

## Recommended Fix
```typescript
// Use native crypto.randomUUID()
id: crypto.randomUUID(),

// Or use uuid library for older environments
import { v4 as uuidv4 } from 'uuid';
id: uuidv4(),
```

## Acceptance Criteria
- [ ] Replace Math.random() with crypto.randomUUID() or uuid library
- [ ] Update TypeScript types if needed
- [ ] Test in supported browsers
- [ ] Add polyfill if targeting older browsers
- [ ] Search codebase for other uses of Math.random() for IDs

## References
- [CODEBASE_REVIEW.md](../CODEBASE_REVIEW.md#issue-2-weak-id-generation)
- [CODE_REVIEW_NOTES.md](../CODE_REVIEW_NOTES.md#2-improve-id-generation-in-react-components)
```

---

### Issue 10: Add Missing Type Hints to Utility Modules

**Title**: Add comprehensive type hints to remaining modules

**Labels**: `enhancement`, `priority: medium`, `type: backend`, `good first issue`

**Description**:
```markdown
## Problem
Some utility modules and `__init__.py` files lack complete type hints, reducing:
- Code clarity
- IDE support
- Type safety
- Documentation quality

## Files Needing Type Hints
- Various `__init__.py` files
- Some utility modules in `opendiscourse/utils/`
- Helper functions across the codebase

## Requirements
- All function parameters must have type hints
- All return values must have type hints
- Use modern Python 3.10+ syntax (`list[str]`, `dict[str, int]`, `X | Y`)
- Complex types should use type aliases or TypedDict

## Example
```python
# Before (no type hints)
def process_items(items, transform_fn):
    return [transform_fn(item) for item in items]

# After (with type hints)
from typing import TypeVar, Callable
from collections.abc import Sequence

T = TypeVar('T')
U = TypeVar('U')

def process_items(
    items: Sequence[T],
    transform_fn: Callable[[T], U]
) -> list[U]:
    """Process items with a transformation function."""
    return [transform_fn(item) for item in items]
```

## Acceptance Criteria
- [ ] All public functions have type hints
- [ ] Type hints follow modern Python syntax
- [ ] mypy passes with no errors
- [ ] IDE autocomplete works correctly

## References
- [CODING_STANDARDS.md](../CODING_STANDARDS.md#type-hints)
- [Python Type Hints Documentation](https://docs.python.org/3/library/typing.html)
```

---

### Issue 11: Implement Comprehensive API Pagination

**Title**: Ensure all list endpoints implement pagination

**Labels**: `enhancement`, `priority: medium`, `type: backend`, `api`

**Description**:
```markdown
## Problem
Need to verify and standardize pagination across all list endpoints to:
- Prevent performance issues with large datasets
- Improve user experience
- Reduce memory usage
- Enable efficient data browsing

## Tasks
1. **Audit All List Endpoints**
   - [ ] Identify all endpoints returning lists
   - [ ] Check if pagination is implemented
   - [ ] Document current pagination patterns

2. **Implement Standard Pagination**
   - [ ] Create reusable pagination models
   - [ ] Implement consistent pagination parameters
   - [ ] Add pagination metadata to responses

3. **Consider Cursor-Based Pagination**
   - [ ] For large datasets (>10k records)
   - [ ] For real-time data
   - [ ] For better performance

## Standard Pagination Format
```python
class PaginationParams(BaseModel):
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)

class PaginatedResponse(BaseModel):
    items: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int
```

## Acceptance Criteria
- [ ] All list endpoints paginated
- [ ] Consistent pagination parameters
- [ ] Pagination metadata in responses
- [ ] Documentation updated
- [ ] Tests for pagination
- [ ] Performance tested with large datasets

## References
- [CODE_REVIEW_NOTES.md](../CODE_REVIEW_NOTES.md#2-database-query-optimization)
- [CODEBASE_REVIEW.md](../CODEBASE_REVIEW.md#pagination)
```

---

## Low Priority Issues

### Issue 12: Standardize Import Organization

**Title**: Ensure consistent import organization with isort

**Labels**: `chore`, `priority: low`, `type: backend`

**Description**:
```markdown
## Problem
Import statements are generally well-organized but have some inconsistencies.

## Solution
Configure and enforce `isort` for automatic import sorting.

## Configuration
```toml
# pyproject.toml
[tool.isort]
profile = "black"
known_first_party = ["opendiscourse"]
line_length = 88
```

## Implementation
1. [ ] Add isort to requirements-dev.txt
2. [ ] Configure isort in pyproject.toml
3. [ ] Add to pre-commit hooks
4. [ ] Run on entire codebase
5. [ ] Add to CI/CD checks

## Acceptance Criteria
- [ ] isort configured
- [ ] Pre-commit hook added
- [ ] CI/CD checks imports
- [ ] All imports reorganized

## References
- [CODING_STANDARDS.md](../CODING_STANDARDS.md#imports)
```

---

### Issue 13: Create Shared Loading State Components

**Title**: Standardize loading states across React components

**Labels**: `enhancement`, `priority: low`, `type: frontend`, `ui/ux`

**Description**:
```markdown
## Problem
Loading states are inconsistent across components, affecting:
- User experience
- Code reusability
- Maintenance

## Solution
Create shared loading components and hooks:

1. **LoadingSpinner Component**
2. **LoadingState Hook**
3. **Skeleton Loaders**
4. **Loading Boundaries**

## Implementation
```typescript
// hooks/useLoadingState.ts
export function useLoadingState() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  
  const withLoading = async <T,>(fn: () => Promise<T>): Promise<T> => {
    setIsLoading(true);
    setError(null);
    try {
      return await fn();
    } catch (err) {
      setError(err as Error);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };
  
  return { isLoading, error, withLoading };
}
```

## Acceptance Criteria
- [ ] Shared loading components created
- [ ] Loading hook implemented
- [ ] Applied to existing components
- [ ] Consistent loading UX
- [ ] Documentation updated

## References
- [CODEBASE_REVIEW.md](../CODEBASE_REVIEW.md#loading-states)
```

---

## Summary

**Total Issues**: 13
- **Critical**: 4 issues
- **High**: 4 issues  
- **Medium**: 3 issues
- **Low**: 2 issues

## Priority Order for Implementation

1. Fix bare except clause (#1)
2. Implement rate limiting (#2)
3. Add security headers (#3)
4. Increase test coverage (#4)
5. Implement caching (#5)
6. Optimize database queries (#6)
7. Complete documentation (#7)
8. Standardize error handling (#8)
9. Fix ID generation (#9)
10. Add type hints (#10)
11. Implement pagination (#11)
12. Organize imports (#12)
13. Standardize loading states (#13)

## Creating Issues in Bulk

To create these issues, you can:

1. **Manually**: Copy each issue section and create in GitHub UI
2. **GitHub CLI**: Use the `gh issue create` command
3. **GitHub API**: Script the creation using GitHub's REST API
4. **Project Management**: Import into project board for tracking

---

**Generated**: 2025-11-17  
**Review Source**: [CODEBASE_REVIEW.md](CODEBASE_REVIEW.md)
