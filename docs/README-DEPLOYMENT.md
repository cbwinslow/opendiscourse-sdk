# Media Intelligence Platform - Production Deployment Guide

## NVIDIA NIM RAG System for Kubernetes/Ceph Clusters

This guide covers deploying the media intelligence platform with NVIDIA NIM models for production-scale RAG capabilities across multiple computers.

## Architecture Overview

The system is designed for horizontal scaling with the following components:

- **Frontend/Backend**: React + Express application with TypeScript
- **RAG Engine**: NVIDIA NIM models for embeddings and text generation
- **Vector Database**: PostgreSQL with pgvector extension
- **Background Workers**: Kubernetes-native document processing
- **Storage**: Ceph cluster for persistent volumes
- **Orchestration**: Kubernetes for container management

## Prerequisites

### Infrastructure Requirements

1. **Kubernetes Cluster** (v1.24+)
   - Multiple nodes for horizontal scaling
   - RBAC enabled
   - Ingress controller (nginx recommended)

2. **Ceph Storage Cluster**
   - RBD for database persistence
   - CephFS for shared file storage

3. **Container Registry**
   - Docker Hub, Harbor, or private registry
   - Access from all Kubernetes nodes

### Required API Keys

Before deployment, you need:

1. **NVIDIA NIM API Key**
   - Sign up at https://build.nvidia.com/
   - Generate API key for production use

2. **Database Credentials**
   - PostgreSQL user/password for the application

## Quick Start Deployment

### 1. Clone and Configure

```bash
git clone <your-repo>
cd media-intelligence-platform

# Copy and edit environment configuration
cp .env.production .env.local
# Edit .env.local with your actual API keys and credentials
```

### 2. Update Kubernetes Manifests

Edit the following files with your specific configuration:

**k8s/secrets.yaml**:
```yaml
stringData:
  NIM_API_KEY: "your-actual-nvidia-nim-key"
  DATABASE_URL: "postgresql://username:password@postgres-service:5432/media_intelligence"
```

**k8s/deployment.yaml**:
```yaml
# Update image registry if using private registry
image: your-registry.com/media-intelligence:latest
```

### 3. Deploy to Kubernetes

Make the deployment script executable and run:

```bash
chmod +x deploy/deploy.sh
./deploy/deploy.sh
```

This will:
- Build and push Docker images
- Deploy PostgreSQL with pgvector
- Deploy the application with auto-scaling
- Set up RAG workers for background processing
- Configure ingress for external access

## Scaling Configuration

### Horizontal Pod Autoscaling

The deployment includes HPA for automatic scaling based on CPU/memory:

```bash
# Scale web application (3-10 replicas)
kubectl autoscale deployment media-intelligence-app \
  --namespace=media-intelligence \
  --min=3 --max=10 \
  --cpu-percent=70

# Scale RAG workers (5-20 replicas)
kubectl autoscale deployment rag-worker \
  --namespace=media-intelligence \
  --min=5 --max=20 \
  --cpu-percent=80
```

### Manual Scaling

```bash
# Scale web app replicas
kubectl scale deployment media-intelligence-app --replicas=6 -n media-intelligence

# Scale RAG workers for heavy processing
kubectl scale deployment rag-worker --replicas=15 -n media-intelligence
```

## NVIDIA NIM Configuration

### Model Selection

Configure models in `k8s/configmap.yaml`:

```yaml
data:
  # For high-throughput text generation
  NIM_MODEL: "nvidia/llama-3.1-nemotron-70b-instruct"
  
  # For efficient embeddings
  NIM_EMBEDDING_MODEL: "nvidia/nv-embedqa-e5-v5"
  
  # Alternative models:
  # NIM_MODEL: "nvidia/llama-3.1-nemotron-51b-instruct"
  # NIM_EMBEDDING_MODEL: "nvidia/nv-embed-v1"
```

### Rate Limiting and Quotas

Monitor NVIDIA NIM API usage and configure rate limits:

```yaml
# In configmap.yaml
RAG_BATCH_SIZE: "20"           # Documents per batch
RAG_MAX_CONCURRENCY: "5"      # Concurrent API calls
EMBEDDING_CACHE_TTL: "3600"   # Cache embeddings for 1 hour
```

## Storage Configuration

### Ceph Integration

**Database Storage (RBD)**:
```yaml
# In k8s/postgres.yaml
spec:
  storageClassName: ceph-rbd  # High-performance block storage
  resources:
    requests:
      storage: 100Gi
```

**File Uploads (CephFS)**:
```yaml
# In k8s/rag-workers.yaml
spec:
  storageClassName: cephfs    # Shared filesystem
  resources:
    requests:
      storage: 50Gi
```

## Monitoring and Operations

### Health Checks

```bash
# Check overall system health
./deploy/deploy.sh --health-check

# Monitor application logs
kubectl logs -f deployment/media-intelligence-app -n media-intelligence

# Monitor RAG worker logs
kubectl logs -f deployment/rag-worker -n media-intelligence
```

### Performance Monitoring

```bash
# Check resource usage
kubectl top pods -n media-intelligence

# Check RAG processing queue
kubectl exec -n media-intelligence deployment/media-intelligence-app -- \
  curl -s http://localhost:5000/api/nim-rag/stats
```

### Database Operations

```bash
# Connect to PostgreSQL
kubectl exec -it deployment/postgres -n media-intelligence -- \
  psql -U media_user -d media_intelligence

# Check vector index performance
kubectl exec -it deployment/postgres -n media-intelligence -- \
  psql -U media_user -d media_intelligence \
  -c "SELECT count(*) FROM document_vectors;"
```

## Troubleshooting

### Common Issues

1. **NVIDIA NIM API Rate Limits**
   ```bash
   # Check API key status
   kubectl logs deployment/rag-worker -n media-intelligence | grep "NIM API error"
   
   # Reduce concurrency
   kubectl patch configmap media-intelligence-config -n media-intelligence \
     --patch '{"data":{"RAG_MAX_CONCURRENCY":"3"}}'
   ```

2. **Database Connection Issues**
   ```bash
   # Check PostgreSQL status
   kubectl get pods -n media-intelligence -l app=postgres
   
   # Check database connectivity
   kubectl exec deployment/media-intelligence-app -n media-intelligence -- \
     npm run db:push
   ```

3. **Storage Issues**
   ```bash
   # Check Ceph cluster status
   kubectl get pv,pvc -n media-intelligence
   
   # Check storage classes
   kubectl get storageclass
   ```

### Log Analysis

```bash
# Application errors
kubectl logs deployment/media-intelligence-app -n media-intelligence --previous

# RAG processing errors
kubectl logs deployment/rag-worker -n media-intelligence | grep ERROR

# Database errors
kubectl logs deployment/postgres -n media-intelligence
```

## Security Considerations

1. **API Keys**: Store in Kubernetes secrets, never in code
2. **Network Policies**: Implement pod-to-pod communication restrictions
3. **RBAC**: Configure service accounts with minimal permissions
4. **TLS**: Enable HTTPS with cert-manager for external access
5. **Database**: Use strong passwords and connection encryption

## Performance Tuning

### Database Optimization

```sql
-- Optimize vector search performance
CREATE INDEX CONCURRENTLY IF NOT EXISTS document_vectors_embedding_cosine_idx 
ON document_vectors USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 1000);

-- Optimize full-text search
CREATE INDEX CONCURRENTLY IF NOT EXISTS document_content_gin_idx 
ON documents USING gin(to_tsvector('english', content));
```

### NVIDIA NIM Optimization

```yaml
# Optimize for throughput vs latency
RAG_BATCH_SIZE: "30"           # Larger batches for throughput
RAG_MAX_CONCURRENCY: "8"      # Higher concurrency if API allows
VECTOR_SIMILARITY_THRESHOLD: "0.8"  # Higher threshold for precision
```

## Backup and Recovery

```bash
# Database backup
kubectl exec deployment/postgres -n media-intelligence -- \
  pg_dump -U media_user media_intelligence > backup.sql

# Restore database
kubectl exec -i deployment/postgres -n media-intelligence -- \
  psql -U media_user media_intelligence < backup.sql
```

## Support

For deployment issues:
1. Check logs using the commands above
2. Verify API keys are correctly configured
3. Ensure Kubernetes cluster has sufficient resources
4. Contact NVIDIA support for NIM API issues