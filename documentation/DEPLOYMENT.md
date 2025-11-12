# Deployment Guide

This document outlines the deployment process for the RAG Chat Application.

## 1. Docker Deployment

### Prerequisites
- Docker and Docker Compose installed
- Access to required container images
- Environment variables configured

### Docker Compose Setup

Create a `docker-compose.yml` file with the following structure:

```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
      - POSTGRES_HOST=postgres
      - POSTGRES_DB=ragchat
      - POSTGRES_USER=ragapp
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - VECTOR_STORE_URL=http://vectorstore:8080
      - VECTOR_STORE_API_KEY=${VECTOR_STORE_API_KEY}
      - LLM_API_KEY=${LLM_API_KEY}
    depends_on:
      - postgres
      - vectorstore
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  postgres:
    image: postgres:14
    environment:
      - POSTGRES_DB=ragchat
      - POSTGRES_USER=ragapp
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ragapp -d ragchat"]
      interval: 10s
      timeout: 5s
      retries: 5

  vectorstore:
    image: weaviate/weaviate
    environment:
      - AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED=false
      - AUTHENTICATION_APIKEY_ENABLED=true
      - AUTHENTICATION_APIKEY_ALLOWED_KEYS=${VECTOR_STORE_API_KEY}
      - PERSISTENCE_DATA_PATH=/var/lib/weaviate
    volumes:
      - vector_data:/var/lib/weaviate
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/v1/meta"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  postgres_data:
  vector_data:
```

## 2. Database Configuration

### PostgreSQL Setup

1. Initialize PostgreSQL:
```bash
docker-compose up -d postgres
```

2. Run migrations:
```bash
docker-compose exec app npm run migrate
```

3. Verify database connection:
```bash
docker-compose exec postgres psql -U ragapp -d ragchat -c "\dt"
```

### Vector Store Initialization

1. Start Weaviate:
```bash
docker-compose up -d vectorstore
```

2. Create schema:
```bash
curl -X POST http://localhost:8080/v1/schema \
  -H "Authorization: Bearer ${VECTOR_STORE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d @schema.json
```

### Backup Procedures

#### PostgreSQL Backup
```bash
# Create backup
docker-compose exec postgres pg_dump -U ragapp ragchat > backup_$(date +%Y%m%d).sql

# Restore backup
cat backup_20240101.sql | docker-compose exec -T postgres psql -U ragapp ragchat
```

#### Vector Store Backup
```bash
# Backup vector store data
docker-compose exec vectorstore tar czf /backup/vector_$(date +%Y%m%d).tar.gz /var/lib/weaviate

# Restore vector store data
docker-compose exec vectorstore tar xzf /backup/vector_20240101.tar.gz -C /
```

## 3. RAG System Deployment

### Document Ingestion Pipeline

1. Configure document sources in `.env`:
```
DOCUMENT_SOURCES=/data/documents
SUPPORTED_FORMATS=pdf,txt,md,doc
MAX_FILE_SIZE=10485760  # 10MB
```

2. Start ingestion process:
```bash
docker-compose exec app npm run ingest
```

### Vector Store Configuration

1. Configure embedding model:
```
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSION=1536
EMBEDDING_BATCH_SIZE=32
```

2. Configure similarity search parameters:
```
VECTOR_SIMILARITY_METRIC=cosine
VECTOR_SEARCH_TOP_K=5
```

### Model Serving Setup

1. Configure LLM settings:
```
LLM_MODEL=gpt-4-turbo
LLM_MAX_TOKENS=2048
LLM_TEMPERATURE=0.7
```

2. API rate limiting:
```
RATE_LIMIT_WINDOW=60000  # 1 minute
RATE_LIMIT_MAX_REQUESTS=60
```

## 4. Production Environment

### Environment Variables

Required environment variables:
```
# App
NODE_ENV=production
PORT=3000

# Database
POSTGRES_HOST=postgres
POSTGRES_DB=ragchat
POSTGRES_USER=ragapp
POSTGRES_PASSWORD=<secure-password>

# Vector Store
VECTOR_STORE_URL=http://vectorstore:8080
VECTOR_STORE_API_KEY=<api-key>

# LLM
LLM_API_KEY=<api-key>
LLM_MODEL=gpt-4-turbo

# Security
JWT_SECRET=<jwt-secret>
COOKIE_SECRET=<cookie-secret>
```

### Security Considerations

1. **API Security**:
   - Enable HTTPS/TLS
   - Use API keys for authentication
   - Implement rate limiting
   - Regular security audits

2. **Data Security**:
   - Encrypt sensitive data at rest
   - Regular backup procedures
   - Access control implementation
   - Secure secret management

### Monitoring Setup

1. **Application Metrics**:
   - Request/response times
   - Error rates
   - Active users
   - Token usage

2. **System Metrics**:
   - CPU/Memory usage
   - Disk space
   - Network I/O

3. **Monitoring Tools**:
   - Prometheus for metrics
   - Grafana for visualization
   - ELK Stack for logs
   - Alert manager for notifications

### Backup Procedures

1. **Regular Backups**:
   - Daily database backups
   - Weekly vector store backups
   - Monthly full system backups

2. **Backup Retention**:
   - Keep daily backups for 7 days
   - Keep weekly backups for 1 month
   - Keep monthly backups for 6 months

### Scaling Guidelines

1. **Horizontal Scaling**:
   - Add app replicas for increased load
   - Scale vector store nodes
   - Use load balancer

2. **Vertical Scaling**:
   - Increase resources for heavy computation
   - Optimize database performance
   - Monitor resource utilization

3. **Performance Optimization**:
   - Implement caching
   - Optimize queries
   - Batch processing for heavy operations
