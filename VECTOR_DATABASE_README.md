# Vector Database Installation Guide

This guide provides comprehensive instructions for installing and configuring vector databases (pgvector and Qdrant) for the Open Discourse project.

## Overview

This installation includes two powerful vector databases:

- **pgvector**: PostgreSQL extension for vector similarity search
- **Qdrant**: High-performance vector database optimized for production use

Both databases support:
- Vector embeddings storage and retrieval
- Similarity search with configurable distance metrics
- Metadata filtering
- Scalable architecture
- Python client libraries

## Quick Installation

Run the automated installation script:

```bash
python install_vector_databases.py
```

This script will:
1. Install required Python dependencies
2. Check Docker and Docker Compose
3. Start vector database services
4. Verify installation
5. Create a test script

## Manual Installation

If you prefer to install manually, follow these steps:

### 1. Install Python Dependencies

```bash
pip install psycopg2-binary pgvector qdrant-client numpy pydantic
```

### 2. Start Services with Docker

```bash
docker-compose -f docker-compose.infrastructure.yml up -d
```

### 3. Verify Installation

```bash
python test_vector_databases.py
```

## Configuration

### Vector Store Configuration

The main configuration file is located at:
- `config/vector_store/config.json`

This file contains settings for all vector stores including:
- Vector dimensions
- Distance metrics (cosine, euclidean, dot product)
- Connection settings for each database
- Performance tuning parameters

### Database Credentials

Credential files are stored in:
- `config/vector_store/credentials/postgres.json` - PostgreSQL/pgvector
- `config/vector_store/credentials/qdrant.json` - Qdrant

### Database Initialization

The PostgreSQL database is automatically initialized with:
- pgvector extension enabled
- Document vectors table with proper indexes
- Search function for similarity queries

## Usage Examples

### pgvector Client

```python
from api.vector_stores.pgvector_client import create_pgvector_client
import numpy as np

# Create client
client = create_pgvector_client("config/vector_store/credentials/postgres.json")

# Insert vectors
vectors = [np.random.rand(768).tolist() for _ in range(3)]
metadatas = [
    {"document_hash": "doc1", "chunk_index": 0, "content": "Document 1"},
    {"document_hash": "doc1", "chunk_index": 1, "content": "Document 1 continued"},
    {"document_hash": "doc2", "chunk_index": 0, "content": "Document 2"}
]

client.insert_vectors(vectors, metadatas)

# Search similar vectors
query_vector = np.random.rand(768).tolist()
results = client.search_similar(query_vector, top_k=5)

for result in results:
    print(f"Similarity: {result['similarity']:.3f}")
    print(f"Content: {result['content']}")
    print("---")

client.close()
```

### Qdrant Client

```python
from api.vector_stores.qdrant_client import create_qdrant_client
import numpy as np

# Create client
client = create_qdrant_client("config/vector_store/credentials/qdrant.json")

# Create collection
client.create_collection("my_collection", 768)

# Insert vectors
vectors = [np.random.rand(768).tolist() for _ in range(3)]
metadatas = [
    {"document_hash": "doc1", "chunk_index": 0, "content": "Document 1"},
    {"document_hash": "doc1", "chunk_index": 1, "content": "Document 1 continued"},
    {"document_hash": "doc2", "chunk_index": 0, "content": "Document 2"}
]

client.insert_vectors(vectors, metadatas, collection_name="my_collection")

# Search similar vectors
query_vector = np.random.rand(768).tolist()
results = client.search_similar(query_vector, top_k=5, collection_name="my_collection")

for result in results:
    print(f"Similarity: {result['similarity']:.3f}")
    print(f"Content: {result['content']}")
    print("---")

client.close()
```

## Database Endpoints

After installation, the databases are accessible at:

- **PostgreSQL (pgvector)**: `localhost:5432`
- **Qdrant HTTP**: `localhost:6333`
- **Qdrant gRPC**: `localhost:6334`

## API Integration

### Vector Store Configuration Integration

The vector store configuration system in `config/vector_store_config.py` has been updated to support both pgvector and Qdrant:

```python
from config.vector_store_config import VectorStoreConfig
from api.vector_stores.pgvector_client import create_pgvector_client
from api.vector_stores.qdrant_client import create_qdrant_client

# Load configuration
config = VectorStoreConfig("config/vector_store/config.json")

# Create clients based on configuration
pgvector_client = create_pgvector_client("config/vector_store/credentials/postgres.json")
qdrant_client = create_qdrant_client("config/vector_store/credentials/qdrant.json")
```

## Performance Considerations

### pgvector

- Uses IVFFLAT index for fast similarity search
- Configurable index parameters (lists, proximity)
- Integrates with PostgreSQL ecosystem
- Supports complex queries with joins

### Qdrant

- Optimized for high-performance vector search
- Built-in sharding and replication
- HTTP and gRPC interfaces
- Payload filtering and indexing

## Monitoring and Health Checks

Both clients provide health check methods:

```python
# Check pgvector health
if client.health_check():
    print("pgvector is healthy")

# Check Qdrant health
if client.health_check():
    print("Qdrant is healthy")
```

## Troubleshooting

### Common Issues

1. **Docker services not starting**
   - Check Docker daemon is running
   - Verify ports 5432, 6333, 6334 are available

2. **Connection refused errors**
   - Wait for services to fully start (may take 10-30 seconds)
   - Check firewall settings

3. **pgvector extension not found**
   - Ensure using pgvector/pgvector:pg15 image
   - Check database initialization logs

4. **Import errors for clients**
   - Install required dependencies: `pip install psycopg2-binary pgvector qdrant-client`

### Logs

Check logs for debugging:

```bash
# PostgreSQL logs
docker logs opendiscourse_postgres

# Qdrant logs
docker logs opendiscourse_qdrant
```

### Testing

Run the test script to verify everything is working:

```bash
python test_vector_databases.py
```

## Security Considerations

- Change default passwords in credential files
- Use environment variables for sensitive data
- Configure SSL for production deployments
- Implement proper access controls

## Production Deployment

For production deployments:

1. **Update credential files** with secure passwords
2. **Configure SSL/TLS** for database connections
3. **Set up monitoring** and alerting
4. **Configure backups** for vector data
5. **Scale horizontally** as needed

## Integration with Existing Code

The vector store clients are designed to integrate seamlessly with the existing codebase:

- Use the same configuration system in `config/vector_store_config.py`
- Follow the same patterns as existing database clients
- Compatible with the health monitoring system
- Support for the same metadata and filtering features

## Next Steps

After installation:

1. **Run tests**: `python test_vector_databases.py`
2. **Review configuration**: Check `config/vector_store/config.json`
3. **Integrate with application**: Use clients in your vector operations
4. **Monitor performance**: Set up logging and metrics collection
5. **Scale as needed**: Add more instances or configure sharding

## Support

For issues and questions:

1. Check the troubleshooting section
2. Review database logs
3. Run the test script to isolate issues
4. Check configuration files for errors

## Files Created

This installation creates the following key files:

- `docker-compose.infrastructure.yml` - Docker services configuration
- `database/init/01_enable_extensions.sql` - PostgreSQL initialization
- `api/vector_stores/pgvector_client.py` - pgvector Python client
- `api/vector_stores/qdrant_client.py` - Qdrant Python client
- `config/vector_store/credentials/postgres.json` - PostgreSQL credentials
- `config/vector_store/credentials/qdrant.json` - Qdrant credentials
- `install_vector_databases.py` - Installation script
- `test_vector_databases.py` - Test script
- `VECTOR_DATABASE_README.md` - This documentation

The vector store configuration in `config/vector_store/config.json` has been updated to include both new databases alongside the existing ones (ChromaDB, Elasticsearch, Pinecone).
