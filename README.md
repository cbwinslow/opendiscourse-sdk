# OpenDiscourse

[![Python Version](https://img.shields.io/badge/python-3.13+-blue.svg)](https://python.org)
[![PostgreSQL](https://img.shields.io/badge/postgresql-14+-blue.svg)](https://postgresql.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Build Status](https://img.shields.io/github/workflow/status/cbwinslow/opendiscourse/CI)](https://github.com/cbwinslow/opendiscourse/actions)

OpenDiscourse is a comprehensive platform for analyzing and processing both media intelligence and government documents. The platform combines advanced data processing capabilities with modern web technologies to deliver intelligent document analysis and retrieval-augmented generation (RAG) capabilities.

> **Note**: The repository structure was recently reorganized for better maintainability. See [REORGANIZATION_SUMMARY.md](documentation/REORGANIZATION_SUMMARY.md) for details about the new structure and migration guide.

## Key Features

- 🔍 **Semantic Search**: Vector-based similarity search with natural language query processing
- 📄 **Document Processing**: Multi-format document ingestion (PDF, DOC, TXT, etc.)
- 🏛️ **Government Data**: Automated GovInfo API integration and legislative document processing
- 🤖 **RAG Capabilities**: Question-answering over document corpus with contextual response generation
- 🔗 **Entity Extraction**: Named entity recognition and relationship mapping
- 📊 **Analytics**: Document analytics and usage insights
- 🚀 **Scalable**: Kubernetes-ready deployment with horizontal scaling
- 🔒 **Secure**: Enterprise-grade security with comprehensive input validation

## Quick Start

### Prerequisites

- Python 3.13+
- PostgreSQL 14+ with pgvector extension
- Docker (optional, for containerized deployment)
- Node.js 18+ (for frontend development)

### Installation

1. **Clone the repository**:
   ```bash
   git clone <repo_url>
   cd opendiscourse
   ```

2. **Set up Python environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements-dev.txt
   ```

3. **Configure environment**:
   ```bash
   cp config/environments/.env.example config/environments/.env
   # Edit .env with your database credentials and API keys
   ```

4. **Initialize database**:
   ```bash
   python scripts/setup/init_db.py
   ```

5. **Run the application**:
   ```bash
   python -m opendiscourse
   ```

## Project Structure

```text
opendiscourse/
├── config/                    # Configuration files
│   └── environments/         # Environment-specific settings
│       ├── development.toml  # Development settings
│       ├── production.toml   # Production settings
│       └── testing.toml      # Testing settings
├── data/                     # Data files (not version controlled)
│   ├── raw/                  # Raw data
│   └── processed/            # Processed data
├── docs/                     # Documentation
│   ├── api/                  # API documentation
│   └── guides/               # Development guides
├── infrastructure/           # Infrastructure as code
│   ├── database/             # Database configurations
│   ├── middleware/           # Middleware configurations
│   └── networking/           # Network configurations
├── opendiscourse/            # Main Python package
│   ├── api/                  # API endpoints
│   │   ├── v1/               # API version 1
│   │   └── v2/               # API version 2
│   ├── core/                 # Core functionality
│   ├── db/                   # Database models and migrations
│   ├── services/             # Business logic services
│   │   ├── scraping/         # Web scraping services
│   │   ├── search/           # Search functionality
│   │   └── storage/          # Data storage services
│   └── utils/                # Utility functions
├── scripts/                  # Utility scripts
│   ├── checks/               # System health checks
│   ├── database/             # Database maintenance
│   ├── deployment/           # Deployment scripts
│   └── setup/                # Setup and installation
└── tests/                    # Test suite
    ├── integration/          # Integration tests
    └── unit/                 # Unit tests
        ├── data/             # Test data
        └── mocks/            # Test mocks
```

## Development Setup

1. Clone the repository

2. Install dependencies:

   ```bash
   pip install -r requirements-dev.txt
   ```

3. Set up environment variables:

   ```bash
   cp config/environments/.env.example config/environments/.env
   # Edit the .env file with your configuration
   ```

4. Run the development server:

   ```bash
   python -m opendiscourse
   ```

## API Documentation

### Core Endpoints

#### Document Management
- `POST /api/v1/documents/` - Upload and process documents
- `GET /api/v1/documents/{id}` - Retrieve document by ID
- `GET /api/v1/documents/` - List documents with filtering
- `DELETE /api/v1/documents/{id}` - Delete document

#### Search and RAG
- `POST /api/v1/search/semantic` - Semantic search across documents
- `POST /api/v1/search/vector` - Vector similarity search
- `POST /api/v1/rag/query` - RAG-based question answering
- `GET /api/v1/rag/history` - Query history

#### Government Data
- `POST /api/v1/govdata/ingest` - Ingest government documents
- `GET /api/v1/govdata/sources` - List available data sources
- `POST /api/v1/govdata/scrape` - Trigger data scraping

### API Authentication

All API endpoints require authentication. Include your API key in the header:

```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
     -H "Content-Type: application/json" \
     https://api.opendiscourse.com/v1/documents/
```

For detailed API documentation, visit `/docs` when running the server.

## Deployment

### Development Deployment

Use the provided Docker setup for quick development deployment:

```bash
# Using the development script
./run-dev.sh

# Or manually with Docker Compose
docker-compose up -d
```

The application will be available at:
- **Web Interface**: http://localhost:3000
- **API**: http://localhost:3000/api
- **Documentation**: http://localhost:3000/docs

### Production Deployment

For production deployment with Kubernetes:

```bash
# Deploy to Kubernetes cluster
./deploy/deploy.sh

# Or deploy manually
kubectl apply -f k8s/
```

See [README-DEPLOYMENT.md](README-DEPLOYMENT.md) for comprehensive production deployment guides.

### Environment Configuration

Configure the application using environment-specific TOML files:

```toml
# config/environments/production.toml
[database]
url = "postgresql://user:pass@host:5432/opendiscourse"
pool_size = 20
echo = false

[api]
host = "0.0.0.0"
port = 8000
workers = 4

[security]
secret_key = "your-secret-key"
api_key_header = "X-API-Key"

[features]
rag_enabled = true
vector_search = true
government_data = true
```

## Testing

Run the complete test suite:

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=opendiscourse tests/

# Run specific test categories
pytest tests/unit/          # Unit tests only
pytest tests/integration/   # Integration tests only

# Run performance tests
pytest tests/performance/
```

### Test Configuration

Configure testing environment:

```bash
# Set test database URL
export TEST_DATABASE_URL="postgresql://test:test@localhost:5432/opendiscourse_test"

# Run tests with custom settings
pytest --env=testing tests/
```

## Development Workflow

### Code Quality Standards

Before submitting changes, ensure code quality:

```bash
# Format code
black opendiscourse/ tests/

# Type checking
mypy opendiscourse/

# Linting
flake8 opendiscourse/ tests/

# Import sorting
isort opendiscourse/ tests/

# Run all quality checks
./scripts/quality-check.sh
```

### Pre-commit Hooks

Install pre-commit hooks for automatic code quality checks:

```bash
pre-commit install
```

## Contributing

We welcome contributions! Please follow these guidelines:

### Getting Started

1. **Fork the repository**
2. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Set up development environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements-dev.txt
   ```

### Development Process

1. **Make your changes** following the coding standards
2. **Add tests** for new functionality
3. **Update documentation** as needed
4. **Run the test suite**:
   ```bash
   pytest tests/
   ```
5. **Check code quality**:
   ```bash
   ./scripts/quality-check.sh
   ```

### Submitting Changes

1. **Commit your changes**:
   ```bash
   git add .
   git commit -m "feat: add new feature description"
   ```
2. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```
3. **Create a Pull Request** with:
   - Clear description of changes
   - Reference to related issues
   - Screenshots if applicable
   - Test results

### Contribution Guidelines

- **Code Style**: Follow PEP 8 and use Black formatter
- **Type Hints**: All Python code must include type hints
- **Documentation**: Update relevant documentation
- **Tests**: Maintain or improve test coverage (minimum 80%)
- **Commit Messages**: Use conventional commit format
- **Issue Tracking**: Link PRs to relevant issues

### Types of Contributions

- 🐛 **Bug Fixes**: Fix existing functionality
- ✨ **Features**: Add new functionality
- 📚 **Documentation**: Improve documentation
- 🔧 **Maintenance**: Code refactoring, dependency updates
- 🧪 **Testing**: Improve test coverage
- 🚀 **Performance**: Optimize existing functionality

## Support and Community

- **Issues**: Report bugs and request features via [GitHub Issues](https://github.com/cbwinslow/opendiscourse/issues)
- **Discussions**: Join community discussions in [GitHub Discussions](https://github.com/cbwinslow/opendiscourse/discussions)
- **Documentation**: Comprehensive docs available in the `/docs` directory
- **Examples**: Check the `/examples` directory for usage examples

## Roadmap

See [PROJECT_PLAN.md](PROJECT_PLAN.md) for detailed development roadmap and feature planning.

### Upcoming Features

- **v1.1.0**: Enhanced document processing workflows
- **v1.2.0**: NVIDIA NIM integration for production RAG
- **v1.3.0**: Enhanced React frontend
- **v2.0.0**: Microservices architecture and production scaling

## Security

For security concerns, please email security@opendiscourse.com instead of opening a public issue.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/) for the API framework
- [PostgreSQL](https://postgresql.org/) with [pgvector](https://github.com/pgvector/pgvector) for vector search
- [Sentence Transformers](https://www.sbert.net/) for embeddings generation
- [React](https://reactjs.org/) for the frontend interface

---

**Maintained by**: Development Team  
**Last Updated**: June 26, 2025  
**Version**: 1.0.1
