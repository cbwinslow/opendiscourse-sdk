# AI Agents Usage Guide
## OpenDiscourse CLI Tools Development

This document provides guidelines for AI agents (Gemini, Claude, GPT) when working on the OpenDiscourse CLI tools project.

---

## 1. Project Overview

### 1.1 Architecture
```
opendiscourse/
├── scripts/
│   ├── ingestion/          # CLI tools
│   │   ├── congress_cli.py
│   │   ├── openstates_cli.py
│   │   └── govinfo_cli.py
│   └── utils/              # Shared utilities
│       └── resource_manager.py
├── docs/                   # Documentation
├── migrations/             # Database schemas
└── tests/                  # Test suites
```

### 1.2 Technology Stack
- **Language**: Python 3.9+
- **CLI Framework**: argparse (migrating to Click/Typer)
- **Database**: PostgreSQL 12+
- **API Clients**: requests
- **Testing**: pytest
- **Packaging**: setuptools, pyproject.toml

---

## 2. Agent Capabilities

### 2.1 Code Generation
**When to use agents:**
- Boilerplate CLI commands
- Transform functions
- Database queries
- Test cases
- Documentation

**Best practices:**
- Follow existing patterns
- Type hints required
- Docstrings in Google style
- Error handling mandatory

### 2.2 Code Review
**What agents should check:**
- Type safety
- Error handling
- Rate limiting compliance
- Database transaction safety
- API pagination handling

### 2.3 Documentation
**Agent responsibilities:**
- Keep SRS.md updated
- Update features.md for new features
- Maintain changelog
- Generate API documentation

---

## 3. Development Workflow

### 3.1 Feature Development

```mermaid
graph LR
    A[Feature Request] --> B[Update SRS]
    B --> C[Design in features.md]
    C --> D[Create Implementation Plan]
    D --> E[Generate Code]
    E --> F[Write Tests]
    F --> G[Update Docs]
    G --> H[Create PR]
```

### 3.2 Agent Prompts

**For new features:**
```
I need to add {feature} to {cli_tool}.

Requirements:
- {requirement_1}
- {requirement_2}

Please:
1. Update docs/features.md
2. Create implementation in scripts/ingestion/{cli}.py
3. Add tests in tests/test_{cli}.py
4. Update docs/cli_documentation.md
```

**For bug fixes:**
```
There's a bug in {function} where {description}.

Context: {additional_context}

Please:
1. Identify root cause
2. Propose fix
3. Add regression test
4. Update changelog
```

---

## 4. Code Standards

### 4.1 Python Style
- **Formatter**: Black (line length 100)
- **Linter**: Ruff
- **Type Checker**: mypy (strict mode)
- **Import Order**: isort

### 4.2 Naming Conventions
```python
# Classes: PascalCase
class CongressCLI:
    pass

# Functions: snake_case
def ingest_bills():
    pass

# Constants: UPPER_SNAKE_CASE
MAX_RETRIES = 3

# Private: _leading_underscore
def _internal_helper():
    pass
```

### 4.3 Type Hints
```python
from typing import Optional, Dict, List

def transform_bill(
    bill_data: Dict[str, Any],
    congress: int
) -> tuple[str, str, int]:
    """Transform bill data."""
    pass
```

---

## 5. Testing Strategy

### 5.1 Test Types
1. **Unit Tests**: Individual functions
2. **Integration Tests**: Database interactions
3. **CLI Tests**: Command execution
4. **API Mock Tests**: External API calls

### 5.2 Test Structure
```python
def test_transform_bill_success():
    """Test successful bill transformation."""
    # Arrange
    bill_data = {"number": 1234, ...}

    # Act
    result = transform_bill(bill_data, 118)

    # Assert
    assert result[2] == 1234
```

### 5.3 Fixtures
```python
@pytest.fixture
def mock_api_response():
    """Mock Congress API response."""
    return {
        "bills": [
            {"number": 1234, "title": "Test Bill"}
        ]
    }
```

---

## 6. Database Interactions

### 6.1 Query Patterns
```python
# Good: Parameterized queries
cursor.execute(
    "SELECT * FROM congress.bills WHERE congress_number = %s",
    (congress,)
)

# Bad: String concatenation
cursor.execute(
    f"SELECT * FROM congress.bills WHERE congress_number = {congress}"
)
```

### 6.2 Transactions
```python
try:
    cursor.execute(query, values)
    conn.commit()
except Exception as e:
    conn.rollback()
    logger.error(f"Transaction failed: {e}")
    raise
```

---

## 7. API Client Patterns

### 7.1 Rate Limiting
```python
from rate_limiter import rate_limiter

def get(self, endpoint: str) -> Optional[Dict]:
    rate_limiter.wait("congress.gov")
    response = self.session.get(url)
    # ...
```

### 7.2 Retry Logic
```python
max_retries = 3
base_delay = 2.0

for attempt in range(max_retries + 1):
    try:
        response = requests.get(url)
        if response.status_code == 429:
            delay = base_delay * (2 ** attempt)
            time.sleep(delay)
            continue
        response.raise_for_status()
        return response.json()
    except RequestException:
        # Handle error
```

---

## 8. Documentation Standards

### 8.1 Docstring Format
```python
def ingest_bills(congress: int, bill_type: str = "hr") -> int:
    """Ingest bills for a specific congress.

    Args:
        congress: Congress number (e.g., 118)
        bill_type: Type of bill (hr, s, etc.)

    Returns:
        Number of bills ingested

    Raises:
        ValueError: If congress number is invalid
        DatabaseError: If database operation fails

    Example:
        >>> count = ingest_bills(118, "hr")
        >>> print(f"Ingested {count} bills")
    """
```

### 8.2 README Structure
- Installation
- Quick Start
- Configuration
- Usage Examples
- API Reference
- Contributing
- License

---

## 9. Common Tasks

### 9.1 Adding a New CLI Command
```python
# 1. Add subparser
cmd_parser = subparsers.add_parser(
    'new-command',
    help='Description'
)
cmd_parser.add_argument('--param', help='Parameter')

# 2. Add handler
elif args.command == 'new-command':
    cli.new_command(args.param)

# 3. Implement method
def new_command(self, param: str):
    """Command implementation."""
    pass

# 4. Add test
def test_new_command():
    """Test new command."""
    pass
```

### 9.2 Adding Export Format
```python
# 1. Add format option
parser.add_argument(
    '--format',
    choices=['json', 'csv', 'parquet', 'new-format']
)

# 2. Implement exporter
def export_new_format(data: List[Dict], output: Path):
    """Export to new format."""
    pass

# 3. Update docs
```

---

## 10. Agent-Specific Notes

### 10.1 Gemini Best Practices
- Use for: Large-scale refactoring, documentation generation
- Strength: Understanding complex codebases
- Limitation: May over-engineer solutions

### 10.2 Claude Best Practices
- Use for: Precise code generation, debugging
- Strength: Following specific instructions
- Limitation: Verbose in explanations

### 10.3 GPT Best Practices
- Use for: Quick prototypes, API integration
- Strength: Creative problem solving
- Limitation: May hallucinate API methods

---

## 11. Quality Checklist

Before submitting code, agents should verify:

- [ ] Type hints on all functions
- [ ] Docstrings with examples
- [ ] Error handling implemented
- [ ] Tests written and passing
- [ ] Rate limiting respected
- [ ] Database transactions safe
- [ ] Configuration externalized
- [ ] Logging added
- [ ] Documentation updated
- [ ] Changelog entry added

---

## 12. Resources

### 12.1 Official Documentation
- [Congress.gov API](https://api.congress.gov/v3)
- [OpenStates API](https://docs.openstates.org/api-v3/)
- [GovInfo API](https://api.govinfo.gov/)

### 12.2 Internal Documentation
- `docs/SRS.md` - Requirements
- `docs/features.md` - Feature specs
- `docs/cli_documentation.md` - User guide
- `migrations/` - Database schema

### 12.3 Development Tools
- `pytest` - Testing
- `mypy` - Type checking
- `ruff` - Linting
- `black` - Formatting
