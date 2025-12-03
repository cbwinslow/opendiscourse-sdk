# API Reference - OpenDiscourse v1.0.1

## Overview

The OpenDiscourse API provides comprehensive endpoints for document management, semantic search, RAG capabilities, and government data integration. All endpoints follow RESTful conventions and return JSON responses.

**Base URL**: `https://api.opendiscourse.com`  
**API Version**: v1 (current), v2 (beta)  
**Authentication**: Bearer token required for all endpoints

## Authentication

Include your API key in the Authorization header:

```bash
Authorization: Bearer YOUR_API_KEY
```

Get your API key from the [dashboard](https://opendiscourse.com/dashboard/api-keys).

## Rate Limiting

- **Free Tier**: 1,000 requests/hour
- **Pro Tier**: 10,000 requests/hour  
- **Enterprise**: Custom limits

Rate limit headers are included in all responses:
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1640995200
```

## Error Handling

All errors follow the standard HTTP status codes with detailed error messages:

```json
{
  "error": {
    "code": "INVALID_REQUEST",
    "message": "Document format not supported",
    "details": {
      "supported_formats": ["pdf", "doc", "docx", "txt", "html"]
    }
  },
  "request_id": "req_1234567890"
}
```

### Common Error Codes

| Code | Description |
|------|-------------|
| `INVALID_REQUEST` | Request parameters are invalid |
| `UNAUTHORIZED` | Invalid or missing API key |
| `RATE_LIMITED` | Rate limit exceeded |
| `NOT_FOUND` | Resource not found |
| `PROCESSING_ERROR` | Document processing failed |
| `QUOTA_EXCEEDED` | Account quota exceeded |

---

## Document Management

### Upload Document

**POST** `/api/v1/documents/`

Upload and process a document for indexing and search.

#### Request

```bash
curl -X POST "https://api.opendiscourse.com/api/v1/documents/" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@document.pdf" \
  -F "metadata={\"title\":\"Sample Document\",\"category\":\"research\"}"
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file` | File | Yes | Document file (PDF, DOC, DOCX, TXT, HTML) |
| `metadata` | JSON | No | Additional metadata for the document |
| `extract_entities` | Boolean | No | Enable entity extraction (default: true) |
| `generate_embeddings` | Boolean | No | Generate vector embeddings (default: true) |

#### Response

```json
{
  "id": "doc_1234567890",
  "title": "Sample Document",
  "filename": "document.pdf",
  "size": 1024000,
  "format": "pdf",
  "status": "processing",
  "created_at": "2025-06-26T17:22:59Z",
  "metadata": {
    "title": "Sample Document",
    "category": "research",
    "pages": 15,
    "language": "en"
  },
  "processing": {
    "text_extraction": "pending",
    "entity_extraction": "pending",
    "embedding_generation": "pending"
  }
}
```

### Get Document

**GET** `/api/v1/documents/{document_id}`

Retrieve document details and processing status.

#### Response

```json
{
  "id": "doc_1234567890",
  "title": "Sample Document",
  "filename": "document.pdf",
  "size": 1024000,
  "format": "pdf",
  "status": "completed",
  "created_at": "2025-06-26T17:22:59Z",
  "updated_at": "2025-06-26T17:25:12Z",
  "content": {
    "text": "Full extracted text content...",
    "summary": "AI-generated summary of the document...",
    "word_count": 5000,
    "page_count": 15
  },
  "entities": [
    {
      "text": "John Doe",
      "type": "PERSON",
      "confidence": 0.95,
      "position": 150
    }
  ],
  "metadata": {
    "title": "Sample Document",
    "category": "research",
    "language": "en",
    "keywords": ["AI", "machine learning", "research"]
  }
}
```

### List Documents

**GET** `/api/v1/documents/`

List documents with filtering and pagination.

#### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | Integer | 1 | Page number |
| `limit` | Integer | 20 | Results per page (max 100) |
| `status` | String | all | Filter by status: `pending`, `processing`, `completed`, `failed` |
| `format` | String | all | Filter by format: `pdf`, `doc`, `txt`, etc. |
| `category` | String | all | Filter by category |
| `search` | String | - | Search in title and content |
| `sort` | String | created_at | Sort by: `created_at`, `updated_at`, `title`, `size` |
| `order` | String | desc | Sort order: `asc`, `desc` |

#### Response

```json
{
  "documents": [
    {
      "id": "doc_1234567890",
      "title": "Sample Document",
      "filename": "document.pdf",
      "status": "completed",
      "created_at": "2025-06-26T17:22:59Z",
      "metadata": {
        "category": "research",
        "language": "en"
      }
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 150,
    "pages": 8,
    "has_next": true,
    "has_prev": false
  }
}
```

### Delete Document

**DELETE** `/api/v1/documents/{document_id}`

Delete a document and all associated data.

#### Response

```json
{
  "success": true,
  "message": "Document deleted successfully",
  "deleted_at": "2025-06-26T17:30:00Z"
}
```

---

## Search & RAG

### Semantic Search

**POST** `/api/v1/search/semantic`

Perform semantic search across documents using natural language queries.

#### Request

```json
{
  "query": "What are the benefits of machine learning in healthcare?",
  "filters": {
    "category": ["research", "healthcare"],
    "language": "en",
    "date_range": {
      "start": "2024-01-01",
      "end": "2025-06-26"
    }
  },
  "options": {
    "limit": 10,
    "threshold": 0.7,
    "include_snippets": true,
    "highlight": true
  }
}
```

#### Response

```json
{
  "query": "What are the benefits of machine learning in healthcare?",
  "results": [
    {
      "document_id": "doc_1234567890",
      "title": "AI in Healthcare: A Comprehensive Review",
      "score": 0.92,
      "snippet": "Machine learning has revolutionized <mark>healthcare</mark> by enabling predictive analytics...",
      "metadata": {
        "category": "healthcare",
        "publication_date": "2024-05-15"
      },
      "position": {
        "page": 3,
        "paragraph": 2
      }
    }
  ],
  "stats": {
    "total_results": 25,
    "max_score": 0.92,
    "processing_time": 0.145
  }
}
```

### Vector Search

**POST** `/api/v1/search/vector`

Perform vector similarity search using embedding vectors.

#### Request

```json
{
  "vector": [0.1, 0.2, -0.3, ...],
  "filters": {
    "document_ids": ["doc_123", "doc_456"],
    "categories": ["research"]
  },
  "options": {
    "limit": 5,
    "threshold": 0.8
  }
}
```

### RAG Query

**POST** `/api/v1/rag/query`

Submit a question for RAG (Retrieval-Augmented Generation) processing.

#### Request

```json
{
  "question": "How does climate change affect agricultural productivity?",
  "context": {
    "document_ids": ["doc_123", "doc_456"],
    "categories": ["environment", "agriculture"],
    "max_context_length": 4000
  },
  "options": {
    "model": "gpt-4",
    "temperature": 0.7,
    "include_sources": true,
    "streaming": false
  }
}
```

#### Response

```json
{
  "question": "How does climate change affect agricultural productivity?",
  "answer": "Climate change significantly impacts agricultural productivity through multiple mechanisms...",
  "sources": [
    {
      "document_id": "doc_123",
      "title": "Climate Impact on Agriculture",
      "relevance_score": 0.89,
      "excerpt": "Rising temperatures and changing precipitation patterns..."
    }
  ],
  "metadata": {
    "model_used": "gpt-4",
    "processing_time": 2.34,
    "context_length": 3500,
    "confidence_score": 0.85
  }
}
```

### Query History

**GET** `/api/v1/rag/history`

Retrieve RAG query history with optional filtering.

#### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | Integer | 1 | Page number |
| `limit` | Integer | 20 | Results per page |
| `date_from` | Date | - | Filter queries from date |
| `date_to` | Date | - | Filter queries to date |

---

## Government Data

### Ingest Government Documents

**POST** `/api/v1/govdata/ingest`

Trigger ingestion of government documents from specified sources.

#### Request

```json
{
  "sources": ["govinfo", "congress", "regulations"],
  "filters": {
    "document_types": ["bill", "law", "regulation"],
    "date_range": {
      "start": "2024-01-01",
      "end": "2025-06-26"
    },
    "committees": ["judiciary", "finance"]
  },
  "options": {
    "batch_size": 100,
    "priority": "normal"
  }
}
```

#### Response

```json
{
  "job_id": "job_1234567890",
  "status": "queued",
  "estimated_documents": 250,
  "estimated_completion": "2025-06-26T18:00:00Z",
  "sources_queued": [
    {
      "source": "govinfo",
      "document_count": 150
    },
    {
      "source": "congress",
      "document_count": 100
    }
  ]
}
```

### List Data Sources

**GET** `/api/v1/govdata/sources`

Get available government data sources and their status.

#### Response

```json
{
  "sources": [
    {
      "id": "govinfo",
      "name": "GovInfo API",
      "description": "Official government documents from GPO",
      "status": "active",
      "last_update": "2025-06-26T16:00:00Z",
      "document_count": 1500000,
      "supported_types": ["bill", "law", "regulation", "hearing"]
    }
  ]
}
```

### Trigger Data Scraping

**POST** `/api/v1/govdata/scrape`

Manually trigger data scraping for specific sources.

#### Request

```json
{
  "source": "govinfo",
  "target_date": "2025-06-26",
  "document_types": ["bill"],
  "force_refresh": false
}
```

---

## Analytics & Monitoring

### Usage Statistics

**GET** `/api/v1/analytics/usage`

Get API usage statistics and metrics.

#### Response

```json
{
  "period": "last_30_days",
  "requests": {
    "total": 15000,
    "by_endpoint": {
      "/documents/": 8000,
      "/search/semantic": 5000,
      "/rag/query": 2000
    }
  },
  "documents": {
    "uploaded": 500,
    "processed": 485,
    "failed": 15
  },
  "usage_quota": {
    "current": 15000,
    "limit": 50000,
    "percentage": 30
  }
}
```

### Health Check

**GET** `/api/v1/health`

Check API health and service status.

#### Response

```json
{
  "status": "healthy",
  "timestamp": "2025-06-26T17:22:59Z",
  "services": {
    "database": "healthy",
    "vector_store": "healthy",
    "ai_models": "healthy",
    "document_processor": "healthy"
  },
  "performance": {
    "avg_response_time": 145,
    "uptime": "99.9%"
  }
}
```

---

## Webhooks

Configure webhooks to receive real-time notifications about document processing and other events.

### Setup Webhook

**POST** `/api/v1/webhooks/`

Create a new webhook endpoint.

#### Request

```json
{
  "url": "https://your-app.com/webhooks/opendiscourse",
  "events": ["document.processed", "document.failed", "rag.completed"],
  "secret": "your_webhook_secret"
}
```

### Webhook Events

| Event | Description |
|-------|-------------|
| `document.uploaded` | Document upload completed |
| `document.processed` | Document processing completed |
| `document.failed` | Document processing failed |
| `search.completed` | Search query completed |
| `rag.completed` | RAG query completed |

### Webhook Payload Example

```json
{
  "event": "document.processed",
  "timestamp": "2025-06-26T17:22:59Z",
  "data": {
    "document_id": "doc_1234567890",
    "status": "completed",
    "processing_time": 45.2
  }
}
```

---

## SDKs and Libraries

### Python SDK

```bash
pip install opendiscourse-python
```

```python
from opendiscourse import Client

client = Client(api_key="your_api_key")

# Upload document
document = client.documents.upload("document.pdf")

# Semantic search
results = client.search.semantic("machine learning benefits")

# RAG query
answer = client.rag.query("What are the key findings?")
```

### JavaScript/Node.js SDK

```bash
npm install @opendiscourse/sdk
```

```javascript
import { OpenDiscourse } from '@opendiscourse/sdk';

const client = new OpenDiscourse({ apiKey: 'your_api_key' });

// Upload document
const document = await client.documents.upload('./document.pdf');

// Semantic search
const results = await client.search.semantic('machine learning benefits');
```

---

## Versioning

The API uses semantic versioning. Breaking changes will increment the major version number.

- **v1**: Current stable version
- **v2**: Beta version with enhanced features
- **Legacy**: v0 (deprecated, will be sunset on 2025-12-31)

To use a specific version, include it in the URL path:
```
https://api.opendiscourse.com/api/v2/documents/
```

---

## Support

- **Documentation**: [docs.opendiscourse.com](https://docs.opendiscourse.com)
- **Status Page**: [status.opendiscourse.com](https://status.opendiscourse.com)
- **Support Email**: support@opendiscourse.com
- **Community**: [community.opendiscourse.com](https://community.opendiscourse.com)

---

**API Version**: 1.0.1  
**Last Updated**: June 26, 2025  
**Next Update**: Quarterly reviews

