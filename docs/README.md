# OpenDiscourse Documentation

Welcome to the comprehensive documentation for OpenDiscourse v1.0.1. This documentation covers everything you need to know about setting up, developing, deploying, and maintaining the OpenDiscourse platform.

## 📚 Documentation Overview

### Quick Navigation

| Document | Description | Audience |
|----------|-------------|----------|
| [Project Overview](../README.md) | High-level project introduction and features | Everyone |
| [Onboarding Guide](ONBOARDING.md) | Steps for new contributors | Everyone |
| [Development Setup](guides/DEVELOPMENT_SETUP.md) | Complete development environment setup | Developers |
| [API Reference](api/API_REFERENCE.md) | Comprehensive API documentation | Developers, Integrators |
| [Deployment Instructions](guides/DEPLOYMENT_INSTRUCTIONS.md) | Deployment across all environments | DevOps, SysAdmins |
| [Project Plan](../PROJECT_PLAN.md) | Development roadmap and milestones | Product Managers, Stakeholders |
| [Software Requirements](../SRS.md) | Technical specifications and requirements | Architects, Developers |
| [ERD Diagrams](erd/main_schema.puml) | Database entity relationship diagrams | Architects, Developers |
| [Changelog](../CHANGELOG.md) | Version history and release notes | Everyone |

---

## 🚀 Getting Started

### For Developers

1. **Start Here**: [Development Setup Guide](guides/DEVELOPMENT_SETUP.md)
2. **Understand the API**: [API Reference](api/API_REFERENCE.md)
3. **Learn the Architecture**: [Project Structure](../PROJECT_STRUCTURE.md)
4. **Follow Standards**: [Contribution Guidelines](../README.md#contributing)

### For DevOps/SysAdmins

1. **Deployment Overview**: [Deployment Instructions](guides/DEPLOYMENT_INSTRUCTIONS.md)
2. **Production Setup**: [Production Deployment](guides/DEPLOYMENT_INSTRUCTIONS.md#production-deployment)
3. **Kubernetes Guide**: [Kubernetes Deployment](guides/DEPLOYMENT_INSTRUCTIONS.md#kubernetes-deployment)
4. **Monitoring Setup**: [Monitoring & Maintenance](guides/DEPLOYMENT_INSTRUCTIONS.md#monitoring--maintenance)

### For Product Managers

1. **Project Roadmap**: [Project Plan](../PROJECT_PLAN.md)
2. **Feature Specifications**: [Software Requirements](../SRS.md)
3. **Progress Tracking**: [Project Tracking](../PROJECT_TRACKING.md)
4. **Release History**: [Changelog](../CHANGELOG.md)

### For API Users

1. **API Documentation**: [API Reference](api/API_REFERENCE.md)
2. **Authentication Guide**: [API Authentication](api/API_REFERENCE.md#authentication)
3. **SDK Documentation**: [SDKs and Libraries](api/API_REFERENCE.md#sdks-and-libraries)
4. **Rate Limiting**: [Rate Limits](api/API_REFERENCE.md#rate-limiting)

---

## 📖 Core Documentation

### Architecture & Design

#### System Architecture
- **Backend**: FastAPI with Python 3.13+
- **Database**: PostgreSQL 14+ with pgvector extension
- **AI/ML**: NVIDIA NIM, Sentence Transformers, Custom embeddings
- **Frontend**: React 18+ with TypeScript
- **Infrastructure**: Kubernetes-ready containerized deployment

#### Key Components
- **Document Management**: Multi-format ingestion and processing
- **Semantic Search**: Vector-based similarity search
- **RAG System**: Retrieval-augmented generation capabilities
- **Government Data**: Automated GovInfo API integration
- **Entity Extraction**: Named entity recognition and relationships

### Development Workflow

#### Code Quality Standards
- **Type Safety**: Full type hints for Python code
- **Testing**: 80%+ code coverage requirement
- **Linting**: Black, flake8, mypy for code quality
- **Pre-commit**: Automated quality checks
- **Documentation**: Comprehensive inline and external docs

#### Development Process
1. **Feature Planning**: Requirements analysis and design
2. **Implementation**: Following coding standards and best practices
3. **Testing**: Unit, integration, and performance tests
4. **Review**: Code review and quality assurance
5. **Deployment**: Automated CI/CD pipeline

### API Design

#### RESTful Principles
- **Resource-based URLs**: Clear, hierarchical structure
- **HTTP Methods**: Proper use of GET, POST, PUT, DELETE
- **Status Codes**: Standard HTTP response codes
- **Versioning**: API versioning for backward compatibility

#### Key Endpoints
- **Documents**: `/api/v1/documents/` - Document management
- **Search**: `/api/v1/search/` - Semantic and vector search
- **RAG**: `/api/v1/rag/` - Question-answering system
- **Government Data**: `/api/v1/govdata/` - Government document integration

---

## 🛠 Setup & Installation

### Prerequisites Checklist

#### System Requirements
- [ ] **OS**: Linux (Ubuntu 22.04+), macOS 12+, or Windows 11 with WSL2
- [ ] **RAM**: Minimum 8GB, recommended 16GB+
- [ ] **Storage**: 20GB free space for development
- [ ] **Network**: Stable internet connection

#### Software Dependencies
- [ ] **Python**: 3.13+ with pip
- [ ] **PostgreSQL**: 14+ with pgvector extension
- [ ] **Node.js**: 18+ for frontend development
- [ ] **Docker**: 20.10+ for containerization
- [ ] **Git**: Latest version for version control

#### API Keys (Optional)
- [ ] **OpenAI**: For GPT model access
- [ ] **NVIDIA NIM**: For production RAG capabilities
- [ ] **GovInfo**: For government data integration
- [ ] **Anthropic**: For Claude model access (optional)

### Quick Start Commands

```bash
# 1. Clone and navigate
git clone https://github.com/cbwinslow/opendiscourse.git
cd opendiscourse

# 2. Set up environment
cp config/environments/.env.example config/environments/.env
# Edit .env with your configuration

# 3. Install dependencies
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt

# 4. Initialize database
python scripts/setup/init_db.py

# 5. Start development server
python -m opendiscourse
```

### Verification Steps

```bash
# Check API health
curl http://localhost:8000/api/v1/health

# Run test suite
pytest tests/

# Verify database connection
python -c "from opendiscourse.db.session import get_db; print('Database OK')"
```

---

## 🚀 Deployment Guide

### Environment Types

#### Development Environment
- **Purpose**: Local development and testing
- **Setup**: [Development Setup Guide](guides/DEVELOPMENT_SETUP.md)
- **Resources**: 2GB RAM, 1 CPU minimum
- **Database**: Local PostgreSQL instance

#### Staging Environment
- **Purpose**: Pre-production testing and validation
- **Setup**: [Staging Deployment](guides/DEPLOYMENT_INSTRUCTIONS.md#staging-environment)
- **Resources**: 4GB RAM, 2 CPUs recommended
- **Database**: Cloud-managed PostgreSQL

#### Production Environment
- **Purpose**: Live application serving users
- **Setup**: [Production Deployment](guides/DEPLOYMENT_INSTRUCTIONS.md#production-deployment)
- **Resources**: 8GB+ RAM, 4+ CPUs recommended
- **Database**: High-availability PostgreSQL cluster

### Deployment Options

#### Docker Deployment
```bash
# Quick start with Docker Compose
docker-compose up -d

# Production deployment
docker build -f Dockerfile.prod -t opendiscourse:prod .
docker run -d -p 8000:8000 opendiscourse:prod
```

#### Kubernetes Deployment
```bash
# Apply all manifests
kubectl apply -f k8s/

# Check deployment status
kubectl get pods -n opendiscourse
```

#### Manual Deployment
```bash
# Traditional server deployment
./scripts/deploy-production.sh
```

---

## 📊 API Documentation

### Authentication & Security

#### API Key Authentication
```bash
# Include API key in headers
curl -H "Authorization: Bearer YOUR_API_KEY" \
     https://api.opendiscourse.com/v1/documents/
```

#### Rate Limiting
- **Free Tier**: 1,000 requests/hour
- **Pro Tier**: 10,000 requests/hour
- **Enterprise**: Custom limits

### Core Endpoints

#### Document Management
- `POST /api/v1/documents/` - Upload documents
- `GET /api/v1/documents/{id}` - Retrieve document
- `GET /api/v1/documents/` - List documents
- `DELETE /api/v1/documents/{id}` - Delete document

#### Search & RAG
- `POST /api/v1/search/semantic` - Semantic search
- `POST /api/v1/search/vector` - Vector similarity search
- `POST /api/v1/rag/query` - RAG question-answering
- `GET /api/v1/rag/history` - Query history

#### Government Data
- `POST /api/v1/govdata/ingest` - Ingest government documents
- `GET /api/v1/govdata/sources` - List data sources
- `POST /api/v1/govdata/scrape` - Trigger data scraping

### Response Formats

#### Success Response
```json
{
  "data": { ... },
  "meta": {
    "timestamp": "2025-06-26T17:22:59Z",
    "version": "1.0.1"
  }
}
```

#### Error Response
```json
{
  "error": {
    "code": "INVALID_REQUEST",
    "message": "Document format not supported",
    "details": { ... }
  },
  "request_id": "req_1234567890"
}
```

---

## 🧪 Testing & Quality Assurance

### Testing Strategy

#### Test Categories
- **Unit Tests**: Individual component testing
- **Integration Tests**: Component interaction testing
- **API Tests**: Endpoint functionality testing
- **Performance Tests**: Load and stress testing

#### Coverage Requirements
- **Minimum**: 80% code coverage
- **Target**: 90%+ code coverage
- **Critical Paths**: 100% coverage required

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=opendiscourse --cov-report=html

# Run specific categories
pytest tests/unit/          # Unit tests only
pytest tests/integration/   # Integration tests only
pytest tests/performance/   # Performance tests
```

### Code Quality

```bash
# Format code
black opendiscourse/ tests/

# Type checking
mypy opendiscourse/

# Linting
flake8 opendiscourse/ tests/

# Import sorting
isort opendiscourse/ tests/

# Combined quality check
./scripts/quality-check.sh
```

---

## 📈 Monitoring & Observability

### Health Monitoring

#### Application Health
- **Endpoint**: `/api/v1/health`
- **Metrics**: Response time, error rates, throughput
- **Alerts**: Automated alerting for anomalies

#### Infrastructure Health
- **Database**: Connection pools, query performance
- **Cache**: Redis performance and memory usage
- **Storage**: Disk usage and I/O metrics
- **Network**: Latency and bandwidth utilization

### Performance Metrics

#### Key Performance Indicators (KPIs)
- **API Response Time**: <200ms (95th percentile)
- **Search Accuracy**: >90%
- **System Uptime**: >99.9%
- **Processing Throughput**: 1000+ docs/hour

#### Monitoring Tools
- **Prometheus**: Metrics collection
- **Grafana**: Visualization and dashboards
- **Sentry**: Error tracking and reporting
- **ELK Stack**: Centralized logging

### Alerting

#### Critical Alerts
- **System Down**: API unavailable
- **High Error Rate**: >5% error rate
- **Database Issues**: Connection failures
- **Resource Exhaustion**: Memory/CPU/Disk limits

#### Alert Channels
- **Email**: Critical alerts to ops team
- **Slack**: Real-time notifications
- **PagerDuty**: On-call escalation
- **SMS**: Emergency notifications

---

## 🔧 Troubleshooting

### Common Issues

#### Application Issues
- **Startup Failures**: [Debug startup issues](guides/DEVELOPMENT_SETUP.md#troubleshooting)
- **Performance Problems**: [Performance optimization](guides/DEPLOYMENT_INSTRUCTIONS.md#performance-problems)
- **Memory Issues**: [Memory management](guides/DEVELOPMENT_SETUP.md#memory-issues)

#### Database Issues
- **Connection Problems**: [Database troubleshooting](guides/DEVELOPMENT_SETUP.md#database-connection-issues)
- **Slow Queries**: [Query optimization](guides/DEPLOYMENT_INSTRUCTIONS.md#slow-database-queries)
- **Migration Failures**: [Migration troubleshooting](guides/DEVELOPMENT_SETUP.md#database-development)

#### Deployment Issues
- **Container Problems**: [Docker troubleshooting](guides/DEPLOYMENT_INSTRUCTIONS.md#common-issues)
- **Kubernetes Issues**: [K8s troubleshooting](guides/DEPLOYMENT_INSTRUCTIONS.md#kubernetes-deployment)
- **SSL/TLS Problems**: [Certificate issues](guides/DEPLOYMENT_INSTRUCTIONS.md#ssltls-issues)

### Getting Help

#### Documentation Resources
- **FAQ**: Common questions and answers
- **Troubleshooting Guides**: Step-by-step problem resolution
- **Best Practices**: Recommended approaches and patterns
- **Examples**: Code samples and usage examples

#### Community Support
- **GitHub Issues**: [Report bugs](https://github.com/cbwinslow/opendiscourse/issues)
- **Discussions**: [Community help](https://github.com/cbwinslow/opendiscourse/discussions)
- **Stack Overflow**: Tag questions with `opendiscourse`
- **Discord**: Real-time community chat

#### Professional Support
- **Email**: support@opendiscourse.com
- **Enterprise Support**: enterprise@opendiscourse.com
- **Training**: training@opendiscourse.com
- **Consulting**: consulting@opendiscourse.com

---

## 📋 Appendices

### Configuration Reference

#### Environment Variables
- [Complete Configuration Template](../config/environments/.env.example)
- [Development Settings](guides/DEVELOPMENT_SETUP.md#environment-variables)
- [Production Settings](guides/DEPLOYMENT_INSTRUCTIONS.md#production-environment-setup)

#### Security Configuration
- [Authentication Setup](api/API_REFERENCE.md#authentication)
- [SSL/TLS Configuration](guides/DEPLOYMENT_INSTRUCTIONS.md#security-configuration)
- [Security Headers](guides/DEPLOYMENT_INSTRUCTIONS.md#security-configuration)

### Performance Tuning

#### Database Optimization
- **Indexing**: Vector and full-text search indexes
- **Connection Pooling**: Optimal pool size configuration
- **Query Optimization**: Slow query identification and optimization

#### Application Optimization
- **Caching**: Redis caching strategies
- **Resource Management**: Memory and CPU optimization
- **Scaling**: Horizontal and vertical scaling approaches

### Migration Guides

#### Version Upgrades
- **v1.0.0 to v1.0.1**: [Migration Guide](../CHANGELOG.md#migration-notes)
- **Database Migrations**: Schema change procedures
- **Configuration Updates**: Environment variable changes

#### Platform Migrations
- **Docker to Kubernetes**: Container orchestration migration
- **Database Migration**: PostgreSQL migration procedures
- **Cloud Migration**: Cloud provider migration strategies

---

## 📞 Support & Community

### Getting Help

#### Self-Service Resources
1. **Search Documentation**: Use the search function
2. **Check FAQ**: Common questions and solutions
3. **Review Examples**: Code samples and tutorials
4. **Troubleshooting**: Step-by-step problem resolution

#### Community Channels
1. **GitHub Issues**: Bug reports and feature requests
2. **GitHub Discussions**: General questions and help
3. **Stack Overflow**: Technical Q&A with `opendiscourse` tag
4. **Discord**: Real-time community chat and support

#### Professional Support
1. **Email Support**: support@opendiscourse.com
2. **Enterprise Support**: Dedicated support for enterprise customers
3. **Training Services**: Custom training and workshops
4. **Consulting Services**: Implementation and optimization consulting

### Contributing

#### Ways to Contribute
- **Code Contributions**: Bug fixes, features, improvements
- **Documentation**: Writing, editing, translating
- **Testing**: Bug reports, test case creation
- **Community**: Helping others, answering questions

#### Contribution Process
1. **Read Guidelines**: [Contributing Guide](../README.md#contributing)
2. **Find Issues**: Check open issues or create new ones
3. **Submit PRs**: Follow the pull request process
4. **Review Process**: Participate in code reviews

---

**Documentation Version**: 1.0  
**Last Updated**: June 26, 2025  
**Compatible with**: OpenDiscourse v1.0.1+  
**Next Review**: September 26, 2025

