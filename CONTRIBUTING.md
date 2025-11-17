# Contributing to OpenDiscourse

Thank you for your interest in contributing to OpenDiscourse! This document provides guidelines and best practices for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Coding Standards](#coding-standards)
- [Contribution Workflow](#contribution-workflow)
- [Pull Request Process](#pull-request-process)
- [Issue Guidelines](#issue-guidelines)
- [Testing Guidelines](#testing-guidelines)
- [Documentation](#documentation)
- [Community](#community)

## Code of Conduct

We are committed to providing a welcoming and inclusive environment. Please be respectful and constructive in all interactions.

### Expected Behavior

- Use welcoming and inclusive language
- Be respectful of differing viewpoints and experiences
- Gracefully accept constructive criticism
- Focus on what is best for the community
- Show empathy towards other community members

### Unacceptable Behavior

- Trolling, insulting/derogatory comments, and personal attacks
- Public or private harassment
- Publishing others' private information without explicit permission
- Other conduct which could reasonably be considered inappropriate

## Getting Started

### Prerequisites

- **Python**: 3.11+ (3.13+ recommended)
- **Node.js**: 18+ (22+ recommended)
- **PostgreSQL**: 14+ with pgvector extension
- **pnpm**: 8.0+ (package manager)
- **Docker**: Latest version (optional, for containerized development)
- **Git**: Latest version

### First Time Setup

1. **Fork the repository** on GitHub
2. **Clone your fork**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/opendiscourse.git
   cd opendiscourse
   ```

3. **Add upstream remote**:
   ```bash
   git remote add upstream https://github.com/cbwinslow/opendiscourse.git
   ```

4. **Set up Python environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements-dev.txt
   ```

5. **Set up Node.js environment**:
   ```bash
   pnpm install
   ```

6. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

7. **Initialize database**:
   ```bash
   python scripts/setup/init_db.py
   ```

8. **Install pre-commit hooks**:
   ```bash
   pre-commit install
   ```

## Development Setup

### Running the Application

#### Development Mode

**Backend (FastAPI)**:
```bash
# From project root
python -m uvicorn api.main:app --reload --port 8000
```

**Frontend (Next.js)**:
```bash
# From project root
pnpm dev:web
```

#### Docker Development
```bash
docker-compose up -d
```

### Running Tests

**Python Tests**:
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=opendiscourse --cov-report=html

# Run specific test file
pytest tests/unit/test_specific.py

# Run tests matching a pattern
pytest -k "test_search"
```

**JavaScript/TypeScript Tests**:
```bash
# Run all tests
pnpm test

# Run tests in watch mode
pnpm test:watch

# Run tests with coverage
pnpm test:coverage
```

## Coding Standards

We maintain high coding standards to ensure code quality, maintainability, and consistency across the project. See [CODING_STANDARDS.md](CODING_STANDARDS.md) for comprehensive guidelines.

### Quick Reference

#### Python Style

- **Follow PEP 8** style guide
- **Use type hints** for all function parameters and return values
- **Line length**: Maximum 88 characters (Black formatter default)
- **Formatter**: Use `black` for code formatting
- **Linter**: Use `ruff` for linting
- **Imports**: Sort with `isort` (managed by Black)
- **Docstrings**: Use Google-style docstrings

**Example**:
```python
from typing import Optional

def process_document(
    document_id: str,
    user_id: Optional[str] = None,
    validate: bool = True
) -> dict[str, any]:
    """Process a document and return its metadata.

    Args:
        document_id: Unique identifier for the document
        user_id: Optional user identifier for tracking
        validate: Whether to validate document structure

    Returns:
        Dictionary containing document metadata and processing status

    Raises:
        DocumentNotFoundError: If document_id doesn't exist
        ValidationError: If validation fails
    """
    pass
```

#### TypeScript/JavaScript Style

- **Follow Airbnb style guide** with adjustments
- **Use TypeScript** for all new code
- **Formatter**: Use `prettier`
- **Linter**: Use `eslint` with TypeScript support
- **React**: Use functional components with hooks
- **Naming**: 
  - Components: PascalCase
  - Functions/variables: camelCase
  - Constants: UPPER_SNAKE_CASE
  - Files: kebab-case

**Example**:
```typescript
interface DocumentProps {
  id: string;
  title: string;
  onUpdate?: (id: string) => void;
}

export const DocumentCard: React.FC<DocumentProps> = ({ 
  id, 
  title, 
  onUpdate 
}) => {
  const [isLoading, setIsLoading] = useState(false);

  const handleUpdate = async () => {
    setIsLoading(true);
    try {
      await updateDocument(id);
      onUpdate?.(id);
    } catch (error) {
      console.error('Failed to update document:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="document-card">
      <h3>{title}</h3>
      <button onClick={handleUpdate} disabled={isLoading}>
        Update
      </button>
    </div>
  );
};
```

### Code Quality Tools

Before submitting code, ensure it passes all quality checks:

**Python**:
```bash
# Format code
black opendiscourse/ tests/

# Lint code
ruff check opendiscourse/ tests/

# Type check
mypy opendiscourse/

# Run all checks
./scripts/quality-check.sh
```

**TypeScript/JavaScript**:
```bash
# Format code
pnpm format

# Lint code
pnpm lint

# Type check
pnpm type-check
```

## Contribution Workflow

### Branch Naming Convention

Use descriptive branch names following this pattern:
- `feature/description` - New features
- `fix/description` - Bug fixes
- `docs/description` - Documentation updates
- `refactor/description` - Code refactoring
- `test/description` - Test additions/updates
- `chore/description` - Maintenance tasks

**Examples**:
- `feature/add-semantic-search`
- `fix/document-upload-error`
- `docs/update-api-guide`

### Commit Message Convention

Follow [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `test`: Adding or updating tests
- `chore`: Maintenance tasks
- `ci`: CI/CD changes

**Examples**:
```
feat(search): add semantic search capability

Implement vector-based semantic search using pgvector.
Includes indexing pipeline and query processing.

Closes #123
```

```
fix(api): handle timeout errors in document processing

Add retry logic and proper error handling for timeout scenarios.

Fixes #456
```

### Making Changes

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following the coding standards

3. **Write/update tests** for your changes

4. **Run tests and linters**:
   ```bash
   pytest
   pnpm test
   ./scripts/quality-check.sh
   ```

5. **Commit your changes**:
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```

6. **Keep your branch updated**:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

7. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

## Pull Request Process

### Before Submitting

- [ ] All tests pass locally
- [ ] Code is formatted and linted
- [ ] Type checking passes
- [ ] Documentation is updated
- [ ] CHANGELOG.md is updated (if applicable)
- [ ] Commit messages follow conventional commits
- [ ] Branch is up to date with main

### PR Title

Use the same format as commit messages:
```
feat(scope): brief description
```

### PR Description

Use the provided PR template and include:

1. **Description**: Clear explanation of changes
2. **Type of Change**: Select appropriate type(s)
3. **Related Issues**: Link to related issues
4. **Changes Made**: Detailed list of changes
5. **Testing**: How changes were tested
6. **Documentation**: Documentation updates made
7. **Screenshots**: If applicable (UI changes)

### Review Process

1. **Automated Checks**: Must pass CI/CD pipeline
2. **Code Review**: Requires at least one approval from maintainers
3. **Testing**: Reviewer will test functionality
4. **Documentation**: Verify documentation is complete and accurate

### After PR Approval

- PRs will be merged using **squash and merge** strategy
- Delete your feature branch after merge
- Update your local main branch:
  ```bash
  git checkout main
  git pull upstream main
  ```

## Issue Guidelines

### Before Creating an Issue

1. **Search existing issues** to avoid duplicates
2. **Check documentation** - your question might be answered
3. **Gather information** - logs, error messages, reproduction steps

### Issue Types

We use issue templates for:
- **Bug Reports**: Report bugs and errors
- **Feature Requests**: Suggest new features
- **Performance Issues**: Report performance problems
- **Security Vulnerabilities**: Report security issues (privately)
- **Documentation**: Documentation improvements

### Writing Good Issues

**Bug Reports** should include:
- Clear, descriptive title
- Steps to reproduce
- Expected behavior
- Actual behavior
- Environment details
- Error messages/logs
- Screenshots (if applicable)

**Feature Requests** should include:
- Clear, descriptive title
- Problem statement
- Proposed solution
- Alternative solutions considered
- Use cases
- Priority/impact assessment

### Issue Labels

Issues are automatically labeled and triaged. Common labels:
- `bug` - Something isn't working
- `enhancement` - New feature or request
- `documentation` - Documentation updates
- `good first issue` - Good for newcomers
- `help wanted` - Extra attention needed
- `priority: high/medium/low` - Priority level
- `type: frontend/backend/infrastructure` - Component type

## Testing Guidelines

### Test Coverage

- Maintain **minimum 80% code coverage**
- All new features must include tests
- Bug fixes must include regression tests
- Test both happy paths and error cases

### Test Structure

**Python Tests** (pytest):
```python
import pytest
from opendiscourse.services import DocumentService

class TestDocumentService:
    """Test suite for DocumentService."""

    @pytest.fixture
    def service(self):
        """Create a DocumentService instance for testing."""
        return DocumentService()

    def test_process_document_success(self, service):
        """Test successful document processing."""
        result = service.process_document("test.pdf")
        assert result.status == "success"
        assert result.document_id is not None

    def test_process_document_invalid_format(self, service):
        """Test error handling for invalid document format."""
        with pytest.raises(ValidationError):
            service.process_document("invalid.xyz")
```

**TypeScript/JavaScript Tests** (Jest/Vitest):
```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import { DocumentCard } from './DocumentCard';

describe('DocumentCard', () => {
  it('renders document title', () => {
    render(<DocumentCard id="1" title="Test Document" />);
    expect(screen.getByText('Test Document')).toBeInTheDocument();
  });

  it('calls onUpdate when button is clicked', async () => {
    const onUpdate = jest.fn();
    render(
      <DocumentCard id="1" title="Test" onUpdate={onUpdate} />
    );
    
    fireEvent.click(screen.getByText('Update'));
    await waitFor(() => expect(onUpdate).toHaveBeenCalledWith('1'));
  });
});
```

### Integration Tests

- Test interactions between multiple components
- Use test database for database operations
- Clean up resources after tests
- Use fixtures for test data

### Performance Tests

- Benchmark critical operations
- Test with realistic data volumes
- Monitor memory usage
- Test concurrent operations

## Documentation

### Code Documentation

- **Python**: Use Google-style docstrings
- **TypeScript**: Use JSDoc comments
- Document public APIs comprehensively
- Include usage examples for complex functions
- Keep documentation up-to-date with code changes

### Project Documentation

Update relevant documentation when making changes:
- **README.md**: High-level project overview
- **API Documentation**: API endpoint changes
- **Developer Guides**: New development workflows
- **Architecture Docs**: Architectural changes
- **CHANGELOG.md**: All user-facing changes

### Documentation Style

- Use clear, concise language
- Include code examples
- Use diagrams where helpful (Mermaid)
- Keep examples up-to-date
- Proofread for grammar and spelling

## Community

### Getting Help

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: Questions and community discussion
- **Documentation**: Check `/docs` directory
- **Examples**: See `/examples` directory

### Communication Channels

- **GitHub Issues**: Technical discussions
- **Pull Requests**: Code review discussions
- **GitHub Discussions**: General questions and ideas

### Recognition

Contributors are recognized in:
- CHANGELOG.md for significant contributions
- GitHub contributors page
- Release notes

## Additional Resources

- [Coding Standards](CODING_STANDARDS.md) - Comprehensive coding guidelines
- [Architecture Overview](docs/PROJECT_STRUCTURE.md) - System architecture
- [API Documentation](docs/api/) - API reference
- [Development Guide](docs/DEVELOPER_GUIDE.md) - Detailed development guide
- [Project Plan](docs/PROJECT_PLAN.md) - Roadmap and planning

## Questions?

If you have questions not covered in this guide:
1. Check the [documentation](docs/)
2. Search [existing issues](https://github.com/cbwinslow/opendiscourse/issues)
3. Start a [discussion](https://github.com/cbwinslow/opendiscourse/discussions)
4. Ask in your pull request

Thank you for contributing to OpenDiscourse! 🎉
