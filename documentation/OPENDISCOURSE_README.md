# OpenDiscourse - Political Document Analysis Platform

[![Next.js](https://img.shields.io/badge/Next.js-14.2-blue.svg)](https://nextjs.org)
[![Python](https://img.shields.io/badge/Python-3.12+-green.svg)](https://python.org)
[![Supabase](https://img.shields.io/badge/Supabase-PostgreSQL-orange.svg)](https://supabase.com)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

OpenDiscourse is a comprehensive platform for analyzing political documents using advanced AI and natural language processing. The platform combines document ingestion from government sources, sophisticated NLP analysis, vector search capabilities, and an intuitive web interface for exploring political discourse.

## 🚀 Features

### Core Capabilities
- **📄 Multi-format Document Processing**: PDF, DOC, DOCX, TXT, MD, XML support
- **🏛️ Government Data Integration**: Automated ingestion from govinfo.gov API
- **🤖 Advanced NLP Analysis**: Entity extraction, sentiment analysis, relationship mapping
- **🔍 Semantic Search**: Vector-based similarity search with natural language queries
- **💬 RAG (Retrieval Augmented Generation)**: AI-powered question answering over document corpus
- **📊 Analytics Dashboard**: Document statistics and usage insights
- **🔗 Entity Relationship Mapping**: Network analysis of political entities and relationships

### Technical Stack
- **Frontend**: Next.js 14 with TypeScript, Tailwind CSS
- **Backend**: FastAPI with Python 3.12+
- **Database**: Supabase (PostgreSQL) with pgvector extension
- **Vector Databases**: Qdrant, Weaviate, ChromaDB support
- **NLP**: spaCy, Transformers, sentence-transformers
- **Deployment**: Docker Compose with self-contained infrastructure

## 📋 Prerequisites

- **Node.js** 18+ and npm
- **Python** 3.12+
- **Docker** and Docker Compose
- **Git** for version control

## 🚀 Quick Start

### 1. Clone and Setup
```bash
git clone <repository-url>
cd opendiscourse
```

### 2. One-Command Deployment
```bash
./deploy-local.sh
```

This script will:
- ✅ Check all prerequisites
- 📦 Install Python and Node.js dependencies
- 🐳 Start all infrastructure services (Supabase, vector databases)
- 🗄️ Set up database schema and migrations
- 🔧 Start the FastAPI backend
- 🌐 Launch the Next.js frontend

### 3. Access the Application

After deployment completes, access:
- **Web Interface**: http://localhost:3000
- **API Documentation**: http://localhost:8000/docs
- **Supabase Studio**: http://localhost:54321
- **Qdrant Dashboard**: http://localhost:6333/dashboard

## 📊 Service Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Next.js Web   │────│   FastAPI API   │────│   PostgreSQL    │
│   Frontend      │    │   Backend       │    │   (Supabase)    │
│   :3000         │    │   :8000         │    │   :54322        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                        │                        │
         │                        ▼                        │
         │              ┌─────────────────┐                │
         │              │ Vector Databases │                │
         │              │ Qdrant :6333    │                │
         │              │ Weaviate :8080  │                │
         └──────────────│ ChromaDB :8001  │────────────────┘
                        └─────────────────┘
```

## 🏗️ Project Structure

```
opendiscourse/
├── webui/                     # Next.js frontend application
│   ├── pages/                 # Next.js pages and API routes
│   ├── components/            # React components
│   ├── lib/                   # Utility libraries (Supabase, API)
│   └── styles/                # Tailwind CSS styles
├── scripts/                   # Python processing scripts
│   ├── govinfo_ingestor.py    # Government data ingestion
│   ├── nlp_processor.py       # NLP processing pipeline
│   └── tests/                 # Test scripts
├── supabase/                  # Supabase configuration
│   ├── migrations/            # Database schema migrations
│   └── docker/                # Docker volumes and configs
├── opendiscourse/             # FastAPI backend (if present)
├── tests/                     # Comprehensive test suite
├── docker-compose.supabase.yml # Infrastructure services
├── deploy-local.sh            # One-command deployment
├── run-tests.sh              # Test runner
└── stop-dev.sh               # Stop all services
```

## 📚 User Guide

### Uploading Documents
1. Navigate to **Upload** page
2. Drag and drop or select documents (PDF, DOC, TXT, MD, XML)
3. Documents are automatically processed with NLP analysis
4. View processing results and extracted entities

### Government Data Ingestion
1. Go to **Government Data** page
2. Select data sources (Congressional Bills, Federal Register, etc.)
3. Click **Sync Now** to ingest latest documents
4. Monitor sync progress and document counts

### Semantic Search
1. Use the **Search** page for document discovery
2. Enter natural language questions
3. Get AI-powered answers with source citations
4. View extracted entities and relationships

### Document Management
1. Browse all documents in **Documents** page
2. Filter by source, type, and processing status
3. View document details and analysis results
4. Export data for further analysis

## 🛠️ Development

### Environment Setup
```bash
# Copy environment template
cp webui/.env.example webui/.env.local

# Edit with your configuration
nano webui/.env.local
```

### Running Individual Services

**Frontend only:**
```bash
cd webui
npm run dev
```

**Backend only:**
```bash
source venv/bin/activate
cd opendiscourse
uvicorn main:app --reload
```

**Infrastructure only:**
```bash
docker-compose -f docker-compose.supabase.yml up -d
```

### Adding New Features

1. **Frontend Components**: Add to `webui/components/`
2. **API Routes**: Add to `webui/pages/api/`
3. **Backend Endpoints**: Add to `opendiscourse/api/`
4. **Database Schema**: Add migrations to `supabase/migrations/`
5. **Processing Scripts**: Add to `scripts/`

## 🧪 Testing

### Run All Tests
```bash
./run-tests.sh
```

### Specific Test Categories
```bash
./run-tests.sh basic        # Basic functionality
./run-tests.sh integration  # End-to-end tests
./run-tests.sh api          # API endpoints
./run-tests.sh database     # Database connectivity
./run-tests.sh processing   # NLP processing
```

### Test Coverage
```bash
./run-tests.sh report       # Generate HTML coverage report
```

## 📖 API Documentation

### Document Management
- `POST /api/v1/documents/upload` - Upload and process documents
- `GET /api/v1/documents/` - List documents with filtering
- `GET /api/v1/documents/{id}` - Get specific document
- `POST /api/v1/documents/{id}/analyze` - Trigger analysis

### Search and RAG
- `POST /api/v1/search/semantic` - Semantic document search
- `POST /api/v1/rag/query` - RAG-based question answering
- `GET /api/v1/rag/history` - Query history

### Government Data
- `POST /api/v1/govdata/ingest` - Trigger data ingestion
- `GET /api/v1/govdata/sources` - List available sources
- `GET /api/v1/govdata/status` - Ingestion status

Visit http://localhost:8000/docs for interactive API documentation.

## 🗄️ Database Schema

### Core Tables
- **documents**: Document metadata and content
- **entities**: Extracted named entities
- **entity_relationships**: Relationships between entities
- **analysis_results**: NLP analysis outputs
- **rag_queries**: Question-answering history

### Vector Search
- **document_chunks**: Text chunks with embeddings
- **search_cache**: Cached search results
- pgvector extension for similarity search

See `supabase/migrations/001_initial_schema.sql` for complete schema.

## 🚢 Deployment

### Local Development
```bash
./deploy-local.sh
```

### Production Deployment
1. **Environment Configuration**: Update production environment variables
2. **Database Setup**: Deploy PostgreSQL with pgvector
3. **Vector Databases**: Deploy Qdrant/Weaviate clusters
4. **Container Deployment**: Use Docker Compose or Kubernetes
5. **SSL/TLS**: Configure HTTPS and certificates
6. **Monitoring**: Set up logging and monitoring

### Environment Variables

#### Required
```bash
# Database
POSTGRES_HOST=localhost
POSTGRES_PORT=54322
POSTGRES_DB=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

# Supabase
SUPABASE_URL=http://localhost:54321
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# Vector Databases
QDRANT_URL=http://localhost:6333
WEAVIATE_URL=http://localhost:8080
CHROMA_HOST=localhost
CHROMA_PORT=8001
```

#### Optional
```bash
# Government Data API
GOVINFO_API_KEY=your-api-key

# AI/ML Services
OPENAI_API_KEY=your-openai-key
HUGGINGFACE_API_KEY=your-hf-key
```

## 🔧 Configuration

### NLP Processing
- **spaCy Models**: English model (`en_core_web_sm`)
- **Embeddings**: sentence-transformers/all-mpnet-base-v2
- **Sentiment**: cardiffnlp/twitter-roberta-base-sentiment-latest
- **Summarization**: facebook/bart-large-cnn

### Vector Databases
- **Qdrant**: High-performance vector search
- **Weaviate**: Semantic search with modules
- **ChromaDB**: Simple vector database

### Government Data Sources
- Congressional Bills (BILLS)
- Congressional Record (CREC)
- Federal Register (FR)
- Code of Federal Regulations (CFR)
- Government Publications (GOVPUB)

## 🐛 Troubleshooting

### Common Issues

**Services Not Starting**
```bash
# Check Docker status
docker ps

# View service logs
docker-compose -f docker-compose.supabase.yml logs

# Restart services
./stop-dev.sh && ./deploy-local.sh
```

**Database Connection Errors**
```bash
# Test PostgreSQL connection
psql -h localhost -p 54322 -U postgres -d postgres

# Check Supabase status
curl http://localhost:54321
```

**Frontend Build Errors**
```bash
cd webui
rm -rf .next node_modules
npm install
npm run build
```

**Python Dependencies**
```bash
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### Performance Optimization

1. **Database Indexing**: Ensure vector indexes are created
2. **Memory Allocation**: Increase Docker memory limits
3. **Batch Processing**: Process documents in smaller batches
4. **Caching**: Enable search result caching
5. **Embeddings**: Use GPU acceleration if available

## 🤝 Contributing

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make changes and test**: `./run-tests.sh`
4. **Commit changes**: `git commit -m 'Add amazing feature'`
5. **Push to branch**: `git push origin feature/amazing-feature`
6. **Create Pull Request**

### Development Guidelines
- Follow PEP 8 for Python code
- Use TypeScript for frontend development
- Add tests for new functionality
- Update documentation for API changes
- Use conventional commit messages

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Next.js](https://nextjs.org) for the frontend framework
- [Supabase](https://supabase.com) for the backend infrastructure
- [spaCy](https://spacy.io) for natural language processing
- [Transformers](https://huggingface.co/transformers) for AI models
- [govinfo.gov](https://govinfo.gov) for government data access

## 📞 Support

- **Documentation**: Check this README and inline code comments
- **Issues**: Create GitHub issues for bugs and feature requests
- **Testing**: Use `./run-tests.sh` to diagnose problems
- **Logs**: Check service logs in Docker Compose

---

**Built with ❤️ for transparent political discourse analysis**