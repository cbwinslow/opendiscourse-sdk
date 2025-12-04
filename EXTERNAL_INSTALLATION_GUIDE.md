# External Vector Database Installation Guide

When Docker isn't available, you can install and run pgvector and Qdrant using alternative methods.

## PostgreSQL with pgvector

### Option 1: Install PostgreSQL Locally

#### Ubuntu/Debian
```bash
# Add PostgreSQL repository
sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
sudo apt-get update

# Install PostgreSQL 15 with pgvector
sudo apt-get install postgresql-15 postgresql-client-15
sudo apt-get install postgresql-15-pgvector

# Start PostgreSQL service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database and user
sudo -u postgres psql
CREATE DATABASE opendiscourse;
CREATE USER user WITH PASSWORD 'password';
GRANT ALL PRIVILEGES ON DATABASE opendiscourse TO user;
\q
```

#### macOS
```bash
# Using Homebrew
brew install postgresql@15
brew install pgvector

# Start PostgreSQL
brew services start postgresql@15

# Create database
createdb opendiscourse
```

#### Windows
1. Download PostgreSQL 15 installer from postgresql.org
2. During installation, check "pgvector" extension
3. Create database "opendiscourse" and user "user" with password "password"

### Option 2: Cloud PostgreSQL Services

#### AWS RDS
```bash
# Create RDS instance with pgvector support
aws rds create-db-instance \
    --db-instance-identifier opendiscourse-pgvector \
    --db-instance-class db.t3.micro \
    --engine postgres \
    --engine-version 15.3 \
    --master-username admin \
    --master-user-password yourpassword \
    --allocated-storage 20 \
    --db-name opendiscourse
```

#### Supabase
1. Create new project at supabase.com
2. Go to SQL Editor
3. Enable pgvector extension:
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

#### Neon
1. Create project at neon.tech
2. In SQL Editor, enable pgvector:
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

## Qdrant

### Option 1: Install Qdrant Locally

#### Linux
```bash
# Download and install Qdrant
wget https://github.com/qdrant/qdrant/releases/latest/download/qdrant-linux-amd64.tar.gz
tar -xzf qdrant-linux-amd64.tar.gz
sudo mv qdrant /usr/local/bin/

# Create data directory
sudo mkdir -p /var/lib/qdrant
sudo chown $USER:$USER /var/lib/qdrant

# Run Qdrant
qdrant --host 0.0.0.0 --port 6333 --grpc-port 6334 --storage-path /var/lib/qdrant
```

#### macOS
```bash
# Using Homebrew
brew install qdrant

# Start Qdrant
brew services start qdrant
```

#### Docker (Alternative)
```bash
# Run Qdrant in Docker (if Docker is available)
docker run -p 6333:6333 -p 6334:6334 qdrant/qdrant:latest
```

### Option 2: Qdrant Cloud

#### Qdrant Cloud (Managed Service)
1. Sign up at qdrant.cloud
2. Create cluster
3. Get connection details
4. Update `config/vector_store/credentials/qdrant.json`:
```json
{
  "host": "your-cluster.qdrant.io",
  "port": 6333,
  "grpc_port": 6334,
  "api_key": "your-api-key",
  "https": true
}
```

## Update Credential Files

### PostgreSQL Credentials (`config/vector_store/credentials/postgres.json`)

For cloud instances, update with your connection details:

```json
{
  "database": "your-database-name",
  "user": "your-username",
  "password": "your-password",
  "host": "your-host",
  "port": 5432,
  "connection_pool_size": 10,
  "connection_timeout": 30,
  "ssl_mode": "require"
}
```

### Qdrant Credentials (`config/vector_store/credentials/qdrant.json`)

For cloud instances:

```json
{
  "host": "your-qdrant-host",
  "port": 443,
  "grpc_port": 443,
  "api_key": "your-api-key",
  "prefer_grpc": true,
  "https": true
}
```

## Initialize Database

### PostgreSQL/pgvector Setup

```sql
-- Connect to your PostgreSQL instance
psql -h your-host -U your-user -d your-database

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Create vectors table
CREATE TABLE IF NOT EXISTS document_vectors (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    document_hash uuid NOT NULL,
    chunk_index integer NOT NULL,
    content text NOT NULL,
    embedding vector(768),
    metadata jsonb DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_document_vectors_embedding
ON document_vectors
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_document_vectors_hash
ON document_vectors (document_hash);

-- Create search function
CREATE OR REPLACE FUNCTION search_similar_documents(
    query_embedding vector(768),
    match_threshold float DEFAULT 0.8,
    match_count int DEFAULT 10
)
RETURNS TABLE (
    id uuid,
    document_hash uuid,
    chunk_index integer,
    content text,
    similarity float,
    metadata jsonb
)
LANGUAGE sql
AS $$
    SELECT
        dv.id,
        dv.document_hash,
        dv.chunk_index,
        dv.content,
        1 - (dv.embedding <=> query_embedding) AS similarity,
        dv.metadata
    FROM document_vectors dv
    WHERE 1 - (dv.embedding <=> query_embedding) > match_threshold
    ORDER BY similarity DESC
    LIMIT match_count;
$$;
```

### Qdrant Collection Setup

```python
# Run this Python script to set up Qdrant collections
from api.vector_stores.qdrant_client import create_qdrant_client

client = create_qdrant_client("config/vector_store/credentials/qdrant.json")

# Create collections for different use cases
collections = [
    ("documents", 768),
    ("legislation", 768),
    ("speeches", 768),
    ("meetings", 768)
]

for name, dimension in collections:
    if client.create_collection(name, dimension):
        print(f"Created collection: {name}")
        # Create payload indexes for common fields
        client.create_payload_index("document_hash", name)
        client.create_payload_index("chamber_code", name)
        client.create_payload_index("state_code", name)
        print(f"Created indexes for: {name}")
    else:
        print(f"Collection {name} may already exist")

client.close()
```

## Test External Installation

After setting up external databases, test the connection:

```python
# test_external_databases.py
from api.vector_stores.pgvector_client import create_pgvector_client
from api.vector_stores.qdrant_client import create_qdrant_client
import numpy as np

def test_external_setup():
    print("Testing external vector database setup...")

    # Test PostgreSQL
    try:
        client = create_pgvector_client("config/vector_store/credentials/postgres.json")
        if client.health_check():
            print("✓ External PostgreSQL/pgvector is accessible")
        else:
            print("✗ PostgreSQL/pgvector health check failed")
    except Exception as e:
        print(f"✗ PostgreSQL/pgvector connection failed: {e}")

    # Test Qdrant
    try:
        client = create_qdrant_client("config/vector_store/credentials/qdrant.json")
        if client.health_check():
            print("✓ External Qdrant is accessible")
        else:
            print("✗ Qdrant health check failed")
    except Exception as e:
        print(f"✗ Qdrant connection failed: {e}")

if __name__ == "__main__":
    test_external_setup()
```

## Environment Variables

For production, use environment variables instead of credential files:

```bash
# .env file
POSTGRES_HOST=your-host
POSTGRES_PORT=5432
POSTGRES_DB=your-db
POSTGRES_USER=your-user
POSTGRES_PASSWORD=your-password

QDRANT_HOST=your-qdrant-host
QDRANT_PORT=6333
QDRANT_GRPC_PORT=6334
QDRANT_API_KEY=your-key
```

Update the clients to use environment variables:

```python
# client_factory.py
import os
from api.vector_stores.pgvector_client import PGVectorClient
from api.vector_stores.qdrant_client import QdrantVectorClient

def create_pgvector_client_from_env():
    config = {
        'host': os.getenv('POSTGRES_HOST', 'localhost'),
        'port': int(os.getenv('POSTGRES_PORT', 5432)),
        'database': os.getenv('POSTGRES_DB', 'opendiscourse'),
        'user': os.getenv('POSTGRES_USER', 'user'),
        'password': os.getenv('POSTGRES_PASSWORD', 'password'),
        'settings': {
            'table_name': 'document_vectors',
            'embedding_column': 'embedding'
        }
    }
    return PGVectorClient(config)

def create_qdrant_client_from_env():
    config = {
        'host': os.getenv('QDRANT_HOST', 'localhost'),
        'port': int(os.getenv('QDRANT_PORT', 6333)),
        'grpc_port': int(os.getenv('QDRANT_GRPC_PORT', 6334)),
        'api_key': os.getenv('QDRANT_API_KEY'),
        'settings': {
            'collection_name': 'documents',
            'vector_size': 768,
            'distance_metric': 'cosine'
        }
    }
    return QdrantVectorClient(config)
```

## Next Steps

1. **Choose your preferred installation method** for each database
2. **Update credential files** with your connection details
3. **Run the initialization scripts** to set up schemas
4. **Test the connections** using the test scripts
5. **Update your application code** to use the vector database clients
6. **Monitor and scale** as needed

The vector databases are now ready to power semantic search and similarity matching for your legislative data and documents!
