# RAG Database Scripts Documentation

This document provides comprehensive documentation for the RAG (Retrieval-Augmented Generation) database script suite that enables advanced NLP operations, data management, querying, and reporting capabilities.

## Overview

The RAG script suite consists of four main components:

1. **rag_nlp_operations.py** - NLP analysis and entity processing
2. **rag_data_management.py** - Data validation, cleaning, and migration
3. **rag_query_reporting.py** - Querying and report generation
4. **rag_orchestrator.py** - Script coordination and automation

## Scripts Overview

### 1. rag_nlp_operations.py

**Purpose**: Comprehensive NLP operations for document analysis, entity extraction, sentiment analysis, and embeddings generation.

**Key Features**:
- Entity extraction and storage using spaCy
- Sentiment analysis with emotion indicators
- Text embeddings generation (SentenceTransformers + OpenAI)
- Document re-ranking and semantic similarity
- Natural language understanding and meaning extraction
- Semantic role extraction and linguistic pattern analysis

**Usage Examples**:
```bash
# Process a specific document
python3 rag_nlp_operations.py --document-id 123

# Process all documents
python3 rag_nlp_operations.py --all-documents

# Extract entities only
python3 rag_nlp_operations.py --document-id 123 --entities-only

# Generate embeddings only
python3 rag_nlp_operations.py --document-id 123 --embeddings-only

# Sentiment analysis only
python3 rag_nlp_operations.py --document-id 123 --sentiment-only
```

**Output**: JSON containing:
- Extracted entities with database IDs
- Sentiment analysis results
- Semantic meaning and key concepts
- Linguistic patterns and dependency relations
- Processing metadata and timestamps

### 2. rag_data_management.py

**Purpose**: Data quality management, validation, cleaning, and database migration utilities.

**Key Features**:
- Comprehensive data validation (documents, entities, embeddings)
- Duplicate detection using content hashing and semantic similarity
- Data cleaning and normalization
- Schema migration management
- Data quality reporting with recommendations
- Performance optimization suggestions

**Usage Examples**:
```bash
# Run complete data validation
python3 rag_data_management.py --validate

# Detect duplicate documents
python3 rag_data_management.py --detect-duplicates

# Clean data (dry run)
python3 rag_data_management.py --clean --dry-run

# Clean data (actual changes)
python3 rag_data_management.py --clean

# Migrate to schema version 1.2.0
python3 rag_data_management.py --migrate 1.2.0

# Generate comprehensive quality report
python3 rag_data_management.py --quality-report
```

**Output**: JSON reports containing:
- Validation results with issue details
- Duplicate analysis with similarity scores
- Cleaning operation summaries
- Migration status and applied changes
- Quality metrics and recommendations

### 3. rag_query_reporting.py

**Purpose**: Advanced querying, search capabilities, and comprehensive reporting for the RAG database.

**Key Features**:
- Semantic search using embeddings and full-text search
- Entity-based queries and analytics
- Document analytics and insights generation
- Performance monitoring and database statistics
- Data export in multiple formats (JSON, CSV)
- Custom report generation with configurable sections

**Usage Examples**:
```bash
# Perform semantic search
python3 rag_query_reporting.py --search "climate change policy"

# Search for specific entities
python3 rag_query_reporting.py --entity-search "Biden" --entity-type "PERSON"

# Get analytics for specific document
python3 rag_query_reporting.py --document-analytics 123

# Generate content insights for last 30 days
python3 rag_query_reporting.py --content-insights 30

# Generate performance report
python3 rag_query_reporting.py --performance-report

# Export data to JSON
python3 rag_query_reporting.py --export json --output export.json

# Export with custom query
python3 rag_query_reporting.py --export csv --query "SELECT title, content FROM documents LIMIT 100"
```

**Output**: JSON containing:
- Search results with similarity scores
- Entity information and document relationships
- Analytics data and performance metrics
- Content insights and trend analysis
- Export file paths and record counts

### 4. rag_orchestrator.py

**Purpose**: Orchestration and automation of all RAG operations with scheduling, monitoring, and pipeline management.

**Key Features**:
- Automated document processing pipelines
- Scheduled task management
- Script coordination and dependency handling
- System health monitoring
- Batch processing with parallel execution
- Maintenance task automation

**Usage Examples**:
```bash
# Process new documents
python3 rag_orchestrator.py --process-new

# Run data validation
python3 rag_orchestrator.py --validate

# Run maintenance tasks
python3 rag_orchestrator.py --maintenance

# Generate daily report
python3 rag_orchestrator.py --daily-report

# Run complete processing pipeline
python3 rag_orchestrator.py --full-pipeline

# Check system health
python3 rag_orchestrator.py --health-check

# Start scheduled task runner (blocking)
python3 rag_orchestrator.py --schedule

# Run specific script with arguments
python3 rag_orchestrator.py --run-script rag_nlp_operations.py --script-args --document-id 123
```

**Output**: JSON containing:
- Processing results and statistics
- Task execution status and timing
- System health metrics
- Error logs and recommendations
- Pipeline stage results

## Integration with TypeScript RAG Service

The TypeScript RAG service (`src/services/rag/ragService.ts`) has been updated to integrate with these Python scripts:

**New Methods**:
- `analyzeDocument()` - Returns comprehensive NLP analysis
- `extractMetadata()` - Enhanced metadata extraction with sentiment
- `processChunk()` - Semantic document chunking
- `validateData()` - Data validation interface
- `cleanData()` - Data cleaning interface
- `generateReport()` - Report generation interface
- `searchSemantic()` - Semantic search interface
- `searchEntities()` - Entity search interface

**Usage in TypeScript**:
```typescript
const ragService = new RAGService();

// Analyze a document
const analysis = await ragService.analyzeDocument('123');
console.log(analysis.sentiment, analysis.entities);

// Generate insights report
const report = await ragService.generateReport('content-insights', 7);

// Perform semantic search
const results = await ragService.searchSemantic('climate policy', 10);

// Validate data
const validation = await ragService.validateData();
```

## Database Schema Requirements

The scripts expect the following database tables:

### Core Tables
```sql
-- Documents table
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    content TEXT,
    title TEXT,
    source_url TEXT,
    source_id TEXT,
    source_type TEXT,
    source_date TIMESTAMP,
    content_vector VECTOR(1536), -- pgvector extension
    metadata JSONB,
    is_deleted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Entities table
CREATE TABLE entities (
    id SERIAL PRIMARY KEY,
    text TEXT,
    label TEXT,
    kb_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Document-Entity mapping
CREATE TABLE document_entity_map (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id),
    entity_id INTEGER REFERENCES entities(id),
    start_char INTEGER,
    end_char INTEGER,
    confidence FLOAT DEFAULT 1.0,
    UNIQUE(document_id, entity_id, start_char)
);
```

### Analytics Tables (Added by migrations)
```sql
-- Document analytics (v1.2.0)
CREATE TABLE document_analytics (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id),
    sentiment_score FLOAT,
    complexity_score FLOAT,
    readability_score FLOAT,
    topic_keywords TEXT[],
    analysis_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Processing metadata (v1.2.0)
CREATE TABLE processing_metadata (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id),
    processing_stage VARCHAR(50),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    status VARCHAR(20),
    error_message TEXT,
    metadata JSONB
);

-- Schema versioning
CREATE TABLE schema_version (
    version VARCHAR(50) PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Required Indexes
```sql
-- Vector similarity search
CREATE INDEX idx_documents_content_vector 
ON documents USING ivfflat (content_vector vector_cosine_ops) 
WITH (lists = 100);

-- Full-text search
CREATE INDEX idx_documents_content_fts 
ON documents USING gin(to_tsvector('english', content));

-- Entity indexes
CREATE INDEX idx_entities_text ON entities(text);
CREATE INDEX idx_entities_label ON entities(label);
CREATE INDEX idx_document_entity_map_document_id ON document_entity_map(document_id);
CREATE INDEX idx_document_entity_map_entity_id ON document_entity_map(entity_id);
```

## Environment Configuration

Create a `.env` file with the following variables:

```env
# Database Configuration
POSTGRES_DB=opendiscourse
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# API Keys (optional)
OPENAI_API_KEY=your_openai_api_key

# Processing Configuration
MAX_WORKERS=5
BATCH_SIZE=10
CHUNK_SIZE=1000
```

## Dependencies

### Python Dependencies
```bash
pip install psycopg2-binary python-dotenv spacy sentence-transformers 
pip install openai numpy schedule
python3 -m spacy download en_core_web_lg
```

### Node.js Dependencies
```bash
npm install
```

### System Dependencies
- PostgreSQL 12+ with pgvector extension
- Python 3.8+
- Node.js 16+

## Monitoring and Logging

All scripts generate detailed logs:

- `rag_nlp_operations.log` - NLP processing logs
- `rag_data_management.log` - Data management operation logs
- `rag_query_reporting.log` - Query and reporting logs
- `rag_orchestrator.log` - Orchestration and automation logs

Log levels can be configured, and logs include:
- Timestamp and operation details
- Performance metrics
- Error details and stack traces
- Processing statistics
- Recommendations and warnings

## Performance Considerations

### Batch Processing
- Documents are processed in configurable batches (default: 10)
- Parallel processing using ThreadPoolExecutor (max 5 workers)
- Memory-efficient streaming for large datasets

### Database Optimization
- Vector indexes for fast similarity search
- Full-text search indexes for text queries
- Proper foreign key constraints and indexes
- Regular VACUUM ANALYZE recommended

### Caching and Performance
- Embedding models are loaded once per script execution
- Database connections are pooled and reused
- Prepared statements for frequent queries
- Configurable timeouts and retry logic

## Scheduling and Automation

The orchestrator supports automated scheduling:

- **Daily 2:00 AM**: Process new documents
- **Daily 8:00 AM**: Generate daily reports
- **Every 6 hours**: Data validation
- **Weekly Sunday 3:00 AM**: Maintenance tasks

Custom schedules can be configured in the orchestrator script.

## Error Handling and Recovery

### Robust Error Handling
- Graceful degradation when optional services fail
- Retry logic for transient failures
- Detailed error logging with context
- Fallback implementations for critical operations

### Data Recovery
- Transaction-based operations with rollback
- Backup recommendations before migrations
- Validation before destructive operations
- Recovery procedures documented in logs

## Security Considerations

### Data Protection
- Prepared statements prevent SQL injection
- Input validation and sanitization
- Secure handling of API keys and credentials
- Access control recommendations

### Privacy
- Configurable data retention policies
- Anonymization options for sensitive data
- Audit logging for data access
- Compliance support for regulations

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all Python dependencies are installed
2. **Database Connection**: Check PostgreSQL service and credentials
3. **Memory Issues**: Reduce batch sizes for large datasets
4. **Permission Errors**: Ensure proper file permissions on scripts
5. **Model Loading**: Verify spaCy models are downloaded

### Debugging

Enable debug logging by modifying the logging level in each script:
```python
logging.basicConfig(level=logging.DEBUG, ...)
```

### Performance Issues

1. Check database indexes and statistics
2. Monitor memory usage during processing
3. Adjust batch sizes and worker counts
4. Review query performance in logs
5. Consider hardware scaling for large datasets

## Future Enhancements

### Planned Features
- Real-time processing pipelines
- Advanced ML model integration
- Multi-language support expansion
- Enhanced visualization and dashboards
- API endpoint for real-time operations
- Streaming data processing
- Advanced anomaly detection
- Integration with external knowledge bases

### Extensibility
The modular design allows for easy extension:
- New NLP models can be added to the strategy pattern
- Custom validation rules can be configured
- Additional report types can be implemented
- New data sources can be integrated
- Custom scheduling logic can be added

This comprehensive script suite provides a robust foundation for RAG database operations with advanced NLP capabilities, data management, and automation features.