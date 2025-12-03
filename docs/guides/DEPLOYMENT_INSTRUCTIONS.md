# Deployment Instructions - OpenDiscourse

## Overview

This document provides comprehensive deployment instructions for OpenDiscourse across different environments. It covers everything from local development to production Kubernetes deployments.

## Table of Contents

1. [Environment Types](#environment-types)
2. [Prerequisites](#prerequisites)
3. [Local Development](#local-development)
4. [Docker Deployment](#docker-deployment)
5. [Staging Environment](#staging-environment)
6. [Production Deployment](#production-deployment)
7. [Kubernetes Deployment](#kubernetes-deployment)
8. [CI/CD Pipeline](#cicd-pipeline)
9. [Monitoring & Maintenance](#monitoring--maintenance)
10. [Troubleshooting](#troubleshooting)

---

## Environment Types

### Development
- **Purpose**: Local development and testing
- **Resources**: Minimal (2GB RAM, 1 CPU)
- **Database**: Local PostgreSQL
- **Storage**: Local filesystem
- **Scaling**: Single instance

### Staging
- **Purpose**: Pre-production testing and validation
- **Resources**: Moderate (4GB RAM, 2 CPUs)
- **Database**: Managed PostgreSQL
- **Storage**: Cloud storage
- **Scaling**: Limited horizontal scaling

### Production
- **Purpose**: Live application serving users
- **Resources**: High (8GB+ RAM, 4+ CPUs)
- **Database**: High-availability PostgreSQL cluster
- **Storage**: Distributed storage (Ceph/S3)
- **Scaling**: Full horizontal scaling

---

## Prerequisites

### General Requirements

1. **Operating System**: Linux (Ubuntu 22.04+ recommended), macOS 12+, or Windows 11 with WSL2
2. **Container Runtime**: Docker 20.10+ and Docker Compose v2
3. **Kubernetes**: kubectl and helm (for K8s deployments)
4. **Version Control**: Git with repository access
5. **Package Managers**: npm/yarn for frontend, pip for Python

### Cloud Requirements (Production)

1. **Container Registry**: Docker Hub, AWS ECR, or private registry
2. **Kubernetes Cluster**: EKS, GKE, AKS, or on-premises
3. **Database**: Managed PostgreSQL (AWS RDS, GCP Cloud SQL, etc.)
4. **Storage**: Object storage (S3, GCS) and persistent volumes
5. **Load Balancer**: Cloud load balancer or ingress controller
6. **DNS**: Domain name and SSL certificates

---

## Local Development

### Quick Start

```bash
# Clone repository
git clone https://github.com/cbwinslow/opendiscourse.git
cd opendiscourse

# Run development environment
./run-dev.sh
```

### Manual Setup

```bash
# 1. Set up environment
cp config/environments/.env.example config/environments/.env
# Edit .env with your configuration

# 2. Start services
docker-compose up -d postgres redis chroma

# 3. Set up Python environment
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt

# 4. Initialize database
python scripts/setup/init_db.py

# 5. Start application
python -m opendiscourse

# 6. Start frontend (optional)
cd frontend && npm install && npm run dev
```

### Verification

```bash
# Check API health
curl http://localhost:8000/api/v1/health

# Check frontend
open http://localhost:3000

# Run tests
pytest tests/
```

---

## Docker Deployment

### Single Container (Development)

```dockerfile
# Build image
docker build -t opendiscourse:latest .

# Run container
docker run -d \
  --name opendiscourse \
  -p 8000:8000 \
  -e DATABASE_URL=postgresql://user:pass@host:5432/db \
  -e SECRET_KEY=your-secret-key \
  opendiscourse:latest
```

### Docker Compose (Recommended)

```yaml
# docker-compose.yml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://opendiscourse:password@postgres:5432/opendiscourse
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - postgres
      - redis
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs

  postgres:
    image: pgvector/pgvector:pg14
    environment:
      POSTGRES_DB: opendiscourse
      POSTGRES_USER: opendiscourse
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  chroma:
    image: ghcr.io/chroma-core/chroma:latest
    ports:
      - "8000:8000"
    volumes:
      - chroma_data:/chroma/chroma

volumes:
  postgres_data:
  redis_data:
  chroma_data:
```

### Deployment Commands

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f app

# Scale application
docker-compose up -d --scale app=3

# Update application
docker-compose pull app
docker-compose up -d app

# Backup database
docker-compose exec postgres pg_dump -U opendiscourse opendiscourse > backup.sql

# Stop services
docker-compose down
```

---

## Staging Environment

### Environment Setup

```bash
# 1. Create staging environment file
cp config/environments/.env.example config/environments/staging.env

# 2. Configure staging settings
cat > config/environments/staging.env << EOF
ENVIRONMENT=staging
DEBUG=false
DATABASE_URL=postgresql://user:pass@staging-db:5432/opendiscourse_staging
REDIS_URL=redis://staging-redis:6379/0
SECRET_KEY=staging-secret-key
API_BASE_URL=https://staging-api.opendiscourse.com
CORS_ORIGINS=https://staging.opendiscourse.com
LOG_LEVEL=INFO
EOF
```

### Deployment Process

```bash
# 1. Build and tag image
docker build -t opendiscourse:staging .
docker tag opendiscourse:staging registry.example.com/opendiscourse:staging

# 2. Push to registry
docker push registry.example.com/opendiscourse:staging

# 3. Deploy to staging server
ssh staging-server << 'EOF'
  docker pull registry.example.com/opendiscourse:staging
  docker-compose -f docker-compose.staging.yml up -d
EOF

# 4. Run migrations
docker-compose -f docker-compose.staging.yml exec app python scripts/database/migrate.py

# 5. Verify deployment
curl https://staging-api.opendiscourse.com/api/v1/health
```

### Staging-Specific Configuration

```yaml
# docker-compose.staging.yml
version: '3.8'

services:
  app:
    image: registry.example.com/opendiscourse:staging
    restart: unless-stopped
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=staging
    env_file:
      - config/environments/staging.env
    volumes:
      - /opt/opendiscourse/data:/app/data
      - /opt/opendiscourse/logs:/app/logs

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/staging.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/ssl/certs
    depends_on:
      - app
```

---

## Production Deployment

### Infrastructure Requirements

#### Compute Resources
- **Minimum**: 4 vCPUs, 8GB RAM per instance
- **Recommended**: 8 vCPUs, 16GB RAM per instance
- **Scaling**: 3-10 instances depending on load

#### Database Requirements
- **PostgreSQL**: 14+ with pgvector extension
- **Storage**: 100GB+ SSD storage
- **Connections**: 100+ concurrent connections
- **Backup**: Automated daily backups with point-in-time recovery

#### Storage Requirements
- **Object Storage**: S3-compatible for file uploads
- **Persistent Volumes**: For application data
- **Backup Storage**: For database and application backups

### Production Environment Setup

```bash
# 1. Create production environment
cp config/environments/.env.example config/environments/production.env

# 2. Configure production settings
cat > config/environments/production.env << EOF
ENVIRONMENT=production
DEBUG=false
DATABASE_URL=postgresql://prod_user:secure_password@prod-db-cluster:5432/opendiscourse
REDIS_URL=redis://prod-redis-cluster:6379/0
SECRET_KEY=super-secure-production-secret
API_BASE_URL=https://api.opendiscourse.com
CORS_ORIGINS=https://opendiscourse.com,https://app.opendiscourse.com
LOG_LEVEL=WARNING
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project
METRICS_ENABLED=true
AUDIT_LOGGING=true
EOF
```

### Security Configuration

```bash
# 1. SSL/TLS certificates
certbot certonly --dns-cloudflare \
  --dns-cloudflare-credentials ~/.secrets/cloudflare.ini \
  -d opendiscourse.com \
  -d *.opendiscourse.com

# 2. Security headers configuration
cat > nginx/security.conf << EOF
# Security headers
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';" always;

# Rate limiting
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
limit_req zone=api burst=20 nodelay;
EOF
```

### Deployment Process

```bash
# 1. Build production image
docker build -f Dockerfile.prod -t opendiscourse:v1.0.1 .

# 2. Security scan
docker scan opendiscourse:v1.0.1

# 3. Tag and push
docker tag opendiscourse:v1.0.1 registry.example.com/opendiscourse:v1.0.1
docker push registry.example.com/opendiscourse:v1.0.1

# 4. Deploy with zero downtime
./scripts/deploy-production.sh v1.0.1
```

---

## Kubernetes Deployment

### Namespace Setup

```bash
# Create namespace
kubectl create namespace opendiscourse

# Create secrets
kubectl create secret generic opendiscourse-secrets \
  --from-env-file=config/environments/production.env \
  -n opendiscourse

# Create config map
kubectl create configmap opendiscourse-config \
  --from-file=config/ \
  -n opendiscourse
```

### Deployment Manifests

#### Application Deployment

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: opendiscourse-app
  namespace: opendiscourse
spec:
  replicas: 3
  selector:
    matchLabels:
      app: opendiscourse-app
  template:
    metadata:
      labels:
        app: opendiscourse-app
    spec:
      containers:
      - name: app
        image: registry.example.com/opendiscourse:v1.0.1
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: opendiscourse-secrets
              key: DATABASE_URL
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /api/v1/health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /api/v1/health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

#### Service Configuration

```yaml
# k8s/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: opendiscourse-service
  namespace: opendiscourse
spec:
  selector:
    app: opendiscourse-app
  ports:
  - port: 80
    targetPort: 8000
  type: ClusterIP
```

#### Ingress Configuration

```yaml
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: opendiscourse-ingress
  namespace: opendiscourse
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - api.opendiscourse.com
    secretName: opendiscourse-tls
  rules:
  - host: api.opendiscourse.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: opendiscourse-service
            port:
              number: 80
```

#### Database Configuration

```yaml
# k8s/postgres.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
  namespace: opendiscourse
spec:
  serviceName: postgres
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: pgvector/pgvector:pg14
        env:
        - name: POSTGRES_DB
          value: opendiscourse
        - name: POSTGRES_USER
          value: opendiscourse
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: postgres-secret
              key: password
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
  volumeClaimTemplates:
  - metadata:
      name: postgres-storage
    spec:
      accessModes: ["ReadWriteOnce"]
      storageClassName: fast-ssd
      resources:
        requests:
          storage: 100Gi
```

### Deployment Commands

```bash
# Apply all manifests
kubectl apply -f k8s/

# Check deployment status
kubectl get pods -n opendiscourse
kubectl get services -n opendiscourse
kubectl get ingress -n opendiscourse

# Scale deployment
kubectl scale deployment opendiscourse-app --replicas=5 -n opendiscourse

# Update deployment
kubectl set image deployment/opendiscourse-app app=registry.example.com/opendiscourse:v1.0.2 -n opendiscourse

# Rollback deployment
kubectl rollout undo deployment/opendiscourse-app -n opendiscourse
```

### Horizontal Pod Autoscaler

```yaml
# k8s/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: opendiscourse-hpa
  namespace: opendiscourse
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: opendiscourse-app
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

---

## CI/CD Pipeline

### GitHub Actions Workflow

```yaml
# .github/workflows/deploy.yml
name: Deploy OpenDiscourse

on:
  push:
    branches: [main]
    tags: ['v*']
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.13'
    
    - name: Install dependencies
      run: |
        pip install -r requirements-dev.txt
    
    - name: Run tests
      run: |
        pytest --cov=opendiscourse tests/
    
    - name: Code quality checks
      run: |
        black --check opendiscourse/
        flake8 opendiscourse/
        mypy opendiscourse/

  build:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main' || startsWith(github.ref, 'refs/tags/v')
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v2
    
    - name: Login to Container Registry
      uses: docker/login-action@v2
      with:
        registry: ${{ secrets.REGISTRY_URL }}
        username: ${{ secrets.REGISTRY_USERNAME }}
        password: ${{ secrets.REGISTRY_PASSWORD }}
    
    - name: Build and push
      uses: docker/build-push-action@v4
      with:
        context: .
        push: true
        tags: |
          ${{ secrets.REGISTRY_URL }}/opendiscourse:latest
          ${{ secrets.REGISTRY_URL }}/opendiscourse:${{ github.sha }}

  deploy-staging:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    environment: staging
    
    steps:
    - name: Deploy to staging
      run: |
        # Deploy to staging environment
        kubectl set image deployment/opendiscourse-app \
          app=${{ secrets.REGISTRY_URL }}/opendiscourse:${{ github.sha }} \
          -n opendiscourse-staging

  deploy-production:
    needs: build
    runs-on: ubuntu-latest
    if: startsWith(github.ref, 'refs/tags/v')
    environment: production
    
    steps:
    - name: Deploy to production
      run: |
        # Deploy to production environment
        kubectl set image deployment/opendiscourse-app \
          app=${{ secrets.REGISTRY_URL }}/opendiscourse:${{ github.sha }} \
          -n opendiscourse
```

### GitLab CI/CD Pipeline

```yaml
# .gitlab-ci.yml
stages:
  - test
  - build
  - deploy

variables:
  DOCKER_IMAGE: $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA

test:
  stage: test
  image: python:3.13
  services:
    - postgres:14
  variables:
    DATABASE_URL: postgresql://postgres:postgres@postgres:5432/test
  script:
    - pip install -r requirements-dev.txt
    - pytest --cov=opendiscourse tests/
    - black --check opendiscourse/
    - flake8 opendiscourse/

build:
  stage: build
  image: docker:latest
  services:
    - docker:dind
  script:
    - docker build -t $DOCKER_IMAGE .
    - docker push $DOCKER_IMAGE
  only:
    - main
    - tags

deploy-staging:
  stage: deploy
  image: bitnami/kubectl:latest
  script:
    - kubectl set image deployment/opendiscourse-app app=$DOCKER_IMAGE -n staging
  environment:
    name: staging
    url: https://staging.opendiscourse.com
  only:
    - main

deploy-production:
  stage: deploy
  image: bitnami/kubectl:latest
  script:
    - kubectl set image deployment/opendiscourse-app app=$DOCKER_IMAGE -n production
  environment:
    name: production
    url: https://opendiscourse.com
  when: manual
  only:
    - tags
```

---

## Monitoring & Maintenance

### Health Checks

```bash
# API health check
curl -f http://localhost:8000/api/v1/health || exit 1

# Database health check
python scripts/checks/db_health.py

# Service dependencies check
python scripts/checks/dependencies.py
```

### Monitoring Stack

#### Prometheus Configuration

```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'opendiscourse'
    static_configs:
      - targets: ['opendiscourse-service:8000']
    metrics_path: /metrics
    scrape_interval: 30s
```

#### Grafana Dashboard

```json
{
  "dashboard": {
    "title": "OpenDiscourse Metrics",
    "panels": [
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])"
          }
        ]
      },
      {
        "title": "Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))"
          }
        ]
      }
    ]
  }
}
```

### Log Management

```bash
# Centralized logging with ELK stack
docker run -d \
  --name elasticsearch \
  -p 9200:9200 \
  -e "discovery.type=single-node" \
  elasticsearch:7.14.0

docker run -d \
  --name kibana \
  -p 5601:5601 \
  --link elasticsearch:elasticsearch \
  kibana:7.14.0

# Logstash configuration for application logs
input {
  file {
    path => "/app/logs/*.log"
    type => "application"
  }
}

filter {
  if [type] == "application" {
    json {
      source => "message"
    }
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "opendiscourse-%{+YYYY.MM.dd}"
  }
}
```

### Backup Procedures

```bash
# Database backup
#!/bin/bash
BACKUP_DIR="/backups/$(date +%Y%m%d)"
mkdir -p $BACKUP_DIR

# Full database backup
pg_dump -h $DB_HOST -U $DB_USER $DB_NAME | gzip > $BACKUP_DIR/database.sql.gz

# Application data backup
tar -czf $BACKUP_DIR/app-data.tar.gz /app/data

# Upload to cloud storage
aws s3 cp $BACKUP_DIR/ s3://backups/opendiscourse/ --recursive

# Cleanup old backups
find /backups -type d -mtime +30 -exec rm -rf {} \;
```

---

## Troubleshooting

### Common Issues

#### Application Won't Start

```bash
# Check application logs
docker logs opendiscourse-app

# Check configuration
python -c "from opendiscourse.core.config import settings; print(settings)"

# Verify dependencies
pip check
docker-compose ps
```

#### Database Connection Issues

```bash
# Test database connectivity
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "SELECT 1;"

# Check database logs
docker logs postgres

# Verify network connectivity
telnet $DB_HOST 5432
```

#### Performance Problems

```bash
# Monitor resource usage
htop
docker stats

# Check slow queries
tail -f /var/log/postgresql/postgresql.log | grep "slow query"

# Profile application
python -m cProfile -s tottime -m opendiscourse
```

#### SSL/TLS Issues

```bash
# Test SSL certificate
openssl s_client -connect api.opendiscourse.com:443 -servername api.opendiscourse.com

# Check certificate expiry
echo | openssl s_client -connect api.opendiscourse.com:443 2>/dev/null | openssl x509 -noout -dates

# Renew Let's Encrypt certificate
certbot renew --dry-run
```

### Emergency Procedures

#### Rolling Back Deployment

```bash
# Kubernetes rollback
kubectl rollout undo deployment/opendiscourse-app -n opendiscourse

# Docker Compose rollback
docker-compose down
docker-compose up -d --scale app=0
docker tag opendiscourse:previous opendiscourse:latest
docker-compose up -d
```

#### Database Recovery

```bash
# Point-in-time recovery
pg_basebackup -h $DB_HOST -U $DB_USER -D /recovery -Ft -z -P

# Restore from backup
gunzip -c database.sql.gz | psql -h $DB_HOST -U $DB_USER $DB_NAME
```

### Support Contacts

- **Emergency**: ops-emergency@opendiscourse.com
- **DevOps Team**: devops@opendiscourse.com
- **On-call**: +1-555-0199 (24/7)
- **Status Page**: https://status.opendiscourse.com

---

**Deployment Guide Version**: 1.0  
**Last Updated**: June 26, 2025  
**Compatible with**: OpenDiscourse v1.0.1+

