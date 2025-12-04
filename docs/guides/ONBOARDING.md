# OpenDiscourse Developer Onboarding Guide

Welcome to the OpenDiscourse project! This guide will help you get up and running as a contributor to our enterprise government document analysis platform.

## 🚀 Quick Start

### Prerequisites
- **Python 3.11+** (for backend development)
- **Node.js 18+** (for frontend development)
- **PostgreSQL 14+** with pgvector extension
- **Git** (for version control)
- **Docker** (optional, for containerized development)

### 1. Clone the Repository
```bash
git clone https://github.com/cbwinslow/opendiscourse.git
cd opendiscourse
```

### 2. Development Setup
Follow the detailed [Development Setup Guide](guides/DEVELOPMENT_SETUP.md) for complete environment configuration.

### 3. Quick Verification
```bash
# Backend dependencies
pip install -r requirements-dev.txt

# Frontend dependencies
pnpm install

# Run tests (if available)
pytest -q

# Start development servers
pnpm dev  # Frontend
python -m opendiscourse  # Backend
```

### 4. Development Workflow
1. **Create a feature branch** for your work
2. **Track tasks** in relevant documentation
3. **Follow coding standards** and testing requirements
4. **Submit Pull Requests** with clear descriptions

## 📚 Key Resources

- [Project Documentation](README.md) - Complete documentation overview
- [API Reference](api/API_REFERENCE.md) - REST API documentation
- [Development Setup](guides/DEVELOPMENT_SETUP.md) - Detailed environment setup
- [Project Structure](PROJECT_STRUCTURE.md) - Codebase organization

## 🤝 Getting Help

- **GitHub Issues**: Report bugs and request features
- **Discussions**: Ask questions and share ideas
- **Documentation**: Comprehensive guides in `/docs`

Happy coding!

Welcome to the OpenDiscourse project! This guide will help you get up and running as a contributor to our enterprise government document analysis platform.

## 🚀 Quick Start

### Prerequisites
- **Python 3.11+** (for backend development)
- **Node.js 18+** (for frontend development)
- **PostgreSQL 14+** with pgvector extension
- **Git** (for version control)
- **Docker** (optional, for containerized development)

### 1. Clone the Repository
```bash
git clone https://github.com/cbwinslow/opendiscourse.git
cd opendiscourse
```

### 2. Set Up Your Development Environment

#### Backend Setup (Python)
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration
```

#### Frontend Setup (Node.js)
```bash
cd web/
npm install
npm run dev  # Start development server
```

#### Database Setup
```bash
# Install PostgreSQL with pgvector
# Ubuntu/Debian:
sudo apt-get install postgresql postgresql-contrib
sudo apt-get install postgresql-14-pgvector

# Create database
sudo -u postgres createdb opendiscourse
sudo -u postgres psql -c "CREATE USER opendiscourse WITH PASSWORD 'your_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE opendiscourse TO opendiscourse;"

# Run migrations
python scripts/data_ingestion/migrate_database.py
```

### 3. Run the Application
```bash
# Start backend
python -m uvicorn api.main:app --reload --port 8000

# Start frontend (in another terminal)
cd web/
npm run dev

# Visit http://localhost:3000
```

## 📁 Project Structure

```
opendiscourse/
├── api/                    # FastAPI backend
│   ├── models/            # Pydantic models
│   ├── routes/            # API endpoints
│   └── main.py            # FastAPI app
├── opendiscourse/         # Core Python package
│   ├── db/               # Database models
│   └── utils/            # Utility functions
├── web/                   # React frontend
│   ├── src/              # Source code
│   ├── public/           # Static assets
│   └── package.json      # Node.js dependencies
├── tests/                 # Test suites
├── docs/                  # Documentation
├── scripts/              # Utility scripts
├── .github/              # GitHub workflows
└── requirements.txt      # Python dependencies
```

## 🛠️ Development Workflow

### 1. Create a Feature Branch
```bash
git checkout -b feature/your-feature-name
```

### 2. Make Your Changes
- Follow our [coding standards](#coding-standards)
- Write tests for new functionality
- Update documentation as needed

### 3. Test Your Changes
```bash
# Run Python tests
pytest tests/

# Run frontend tests
cd web/
npm test

# Run linting
ruff check .
black --check .
npm run lint
```

### 4. Commit and Push
```bash
git add .
git commit -m "feat: add new feature description"
git push origin feature/your-feature-name
```

### 5. Create Pull Request
- Open a PR against the `main` branch
- Fill out the PR template
- Request review from maintainers

## 📋 Coding Standards

### Python Code Style
- **Formatter**: Black (88 character line length)
- **Linter**: Ruff
- **Type Hints**: Required for all functions
- **Docstrings**: Google style for all public functions

```python
def process_document(content: str, metadata: dict[str, Any]) -> ProcessedDocument:
    """Process a document for ingestion.
    
    Args:
        content: The document content as text
        metadata: Additional document metadata
        
    Returns:
        ProcessedDocument with extracted features
        
    Raises:
        ProcessingError: If document processing fails
    """
```

### TypeScript/React Code Style
- **Formatter**: Prettier
- **Linter**: ESLint with Next.js config
- **Components**: Functional components with TypeScript
- **Testing**: Jest + React Testing Library

```typescript
interface SearchProps {
  query: string;
  onResults: (results: SearchResult[]) => void;
}

export function SearchComponent({ query, onResults }: SearchProps) {
  // Component implementation
}
```

### Commit Message Format
We use [Conventional Commits](https://www.conventionalcommits.org/):

```
type(scope): description

feat(api): add semantic search endpoint
fix(web): resolve upload progress display issue
docs(readme): update installation instructions
test(api): add integration tests for task endpoints
```

Types: `feat`, `fix`, `docs`, `test`, `refactor`, `style`, `chore`

## 🧪 Testing Guidelines

### Python Testing
- **Framework**: pytest
- **Coverage**: Aim for 80%+ coverage
- **Test Types**: Unit, integration, and API tests

```python
def test_task_creation():
    """Test task creation with valid data."""
    task_data = {
        "title": "Test Task",
        "description": "Test description",
        "status": "todo"
    }
    task_id = insert_task(task_data)
    assert task_id is not None
```

### Frontend Testing
- **Framework**: Jest + React Testing Library
- **Test Types**: Component, integration, and E2E tests

```typescript
test('renders search interface', () => {
  render(<SearchInterface />);
  expect(screen.getByPlaceholderText(/enter your search query/i)).toBeInTheDocument();
});
```

## 🔧 Common Development Tasks

### Adding a New API Endpoint
1. Define Pydantic models in `api/models/`
2. Create route function in `api/routes/`
3. Add to main router in `api/main.py`
4. Write tests in `tests/`
5. Update OpenAPI docs if needed

### Adding a New React Component
1. Create component in `web/src/components/`
2. Add TypeScript interfaces
3. Write component tests
4. Export from appropriate index file

### Database Schema Changes
1. Update `rag_db_schema.sql`
2. Create migration script
3. Update SQLAlchemy models
4. Test migrations locally

### Adding New Dependencies
```bash
# Python
pip install package-name
pip freeze > requirements.txt

# Node.js
npm install package-name
# Dependencies automatically saved to package.json
```

## 🚨 Troubleshooting

### Common Issues

#### Database Connection Errors
```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Verify connection
psql -h localhost -U opendiscourse -d opendiscourse
```

#### Frontend Build Errors
```bash
# Clear node modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

#### Python Import Errors
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Install in development mode
pip install -e .
```

### Getting Help
- **Documentation**: Check `/docs` directory
- **Issues**: Search GitHub issues for similar problems
- **Discussions**: Use GitHub Discussions for questions
- **Chat**: Join our Discord/Slack (link in README)

## 📚 Key Resources

### Architecture Documentation
- [System Architecture](./ARCHITECTURE.md)
- [API Documentation](../web/api-docs.html)
- [Database Schema](./DATABASE.md)

### Development Tools
- [VS Code Extensions](./.vscode/extensions.json)
- [Pre-commit Hooks](../.pre-commit-config.yaml)
- [GitHub Actions](../.github/workflows/)

### External Resources
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [PostgreSQL + pgvector](https://github.com/pgvector/pgvector)

## 🎯 Your First Contribution

Here are some good first issues to work on:

1. **Documentation**: Improve README or add code comments
2. **Testing**: Add tests for existing functionality
3. **UI/UX**: Improve the frontend components
4. **Bug Fixes**: Look for "good first issue" labels

### Suggested First Tasks
- [ ] Add a new test case to an existing test suite
- [ ] Improve error handling in an API endpoint
- [ ] Add loading states to a React component
- [ ] Fix a documentation typo or add examples

## 🌟 Best Practices

### Code Quality
- Write self-documenting code with clear variable names
- Keep functions small and focused (< 50 lines typically)
- Use type hints extensively in Python
- Handle errors gracefully with appropriate logging

### Performance
- Use database indexes for frequent queries
- Implement pagination for large datasets
- Optimize frontend bundle size
- Cache frequently accessed data

### Security
- Validate all user inputs
- Use parameterized queries to prevent SQL injection
- Implement proper authentication and authorization
- Never commit secrets or API keys

### Collaboration
- Communicate early and often in PRs
- Ask questions when unclear about requirements
- Provide constructive feedback in code reviews
- Document decisions and trade-offs

## 📝 Checklist for New Contributors

### Environment Setup
- [ ] Repository cloned and dependencies installed
- [ ] Database set up and migrations run
- [ ] Development servers running successfully
- [ ] Tests passing locally

### Code Understanding
- [ ] Read through project README and documentation
- [ ] Explored codebase structure
- [ ] Understood coding standards and conventions
- [ ] Familiar with development workflow

### First Contribution
- [ ] Found a suitable first issue
- [ ] Created feature branch
- [ ] Made changes following coding standards
- [ ] Added tests for new functionality
- [ ] Updated documentation as needed
- [ ] Submitted pull request

Welcome to the team! We're excited to have you contributing to OpenDiscourse. If you have any questions, don't hesitate to ask in issues, discussions, or reach out to the maintainers directly.

Happy coding! 🚀
>>>>>>> Stashed changes
