# Monitoring API Endpoints

## Overview

The monitoring system provides REST API endpoints for external access to ingestion progress and job management.

## Base URL

```
http://localhost:8000/api/monitoring
```

## Authentication

All endpoints require API key authentication:

```
Authorization: Bearer <api_key>
```

## Endpoints

### Jobs

#### GET `/jobs`

Get list of ingestion jobs with optional filtering.

**Query Parameters:**
- `status` (optional): Filter by status (`running`, `completed`, `failed`)
- `data_source` (optional): Filter by data source
- `limit` (optional): Maximum number of results (default: 50)
- `offset` (optional): Pagination offset (default: 0)

**Response:**
```json
{
  "jobs": [
    {
      "id": 123,
      "job_name": "Congress 118 Bills",
      "data_source": "congress.gov",
      "table_name": "documents",
      "record_type": "bill",
      "status": "running",
      "progress_percent": 67.8,
      "processed_records": 3390,
      "total_records": 5000,
      "failed_records": 15,
      "throughput_per_minute": 45.2,
      "eta_seconds": 2834,
      "started_at": "2024-11-23T10:30:00Z",
      "metadata": {
        "congress": 118
      }
    }
  ],
  "total": 1,
  "limit": 50,
  "offset": 0
}
```

#### GET `/jobs/{job_id}`

Get detailed information about a specific job.

**Response:**
```json
{
  "id": 123,
  "job_name": "Congress 118 Bills",
  "data_source": "congress.gov",
  "table_name": "documents",
  "record_type": "bill",
  "status": "running",
  "progress_percent": 67.8,
  "processed_records": 3390,
  "total_records": 5000,
  "failed_records": 15,
  "throughput_per_minute": 45.2,
  "eta_seconds": 2834,
  "started_at": "2024-11-23T10:30:00Z",
  "completed_at": null,
  "metadata": {
    "congress": 118,
    "bill_types": ["hr", "s"]
  },
  "error_summary": {
    "api_error": 10,
    "parse_error": 3,
    "network_error": 2
  }
}
```

#### POST `/jobs`

Create a new ingestion job.

**Request Body:**
```json
{
  "job_name": "Congress 119 Bills",
  "data_source": "congress.gov",
  "table_name": "documents",
  "record_type": "bill",
  "total_estimated": 6000,
  "metadata": {
    "congress": 119
  }
}
```

**Response:**
```json
{
  "job_id": 124,
  "status": "created",
  "message": "Job created successfully"
}
```

#### PUT `/jobs/{job_id}`

Update job status or metadata.

**Request Body:**
```json
{
  "status": "paused",
  "metadata": {
    "pause_reason": "API maintenance"
  }
}
```

#### DELETE `/jobs/{job_id}`

Cancel and delete a job.

### Progress Updates

#### POST `/jobs/{job_id}/progress`

Update progress for a job.

**Request Body:**
```json
{
  "processed_records": 100,
  "failed_records": 2,
  "throughput_per_minute": 45.2,
  "current_record_id": "118-hr-1234",
  "eta_seconds": 3600
}
```

#### GET `/jobs/{job_id}/progress/stream`

Server-sent events endpoint for real-time progress updates.

**Response:** SSE stream
```
data: {"progress_percent": 67.8, "processed_records": 3390, "throughput": 45.2}

data: {"progress_percent": 68.1, "processed_records": 3405, "throughput": 45.5}
```

### Errors

#### GET `/jobs/{job_id}/errors`

Get errors for a specific job.

**Query Parameters:**
- `resolved` (optional): Include resolved errors (default: false)
- `error_type` (optional): Filter by error type
- `limit` (optional): Maximum number of results (default: 100)

**Response:**
```json
{
  "errors": [
    {
      "id": 456,
      "error_type": "api_error",
      "error_message": "Rate limit exceeded",
      "record_id": "118-hr-1234",
      "retry_count": 2,
      "resolved": false,
      "created_at": "2024-11-23T11:15:00Z",
      "error_metadata": {
        "retry_after": 60,
        "endpoint": "/bill/118/hr/1234"
      }
    }
  ],
  "total": 15,
  "error_summary": {
    "api_error": 10,
    "parse_error": 3,
    "network_error": 2
  }
}
```

#### POST `/jobs/{job_id}/errors`

Record a new error.

**Request Body:**
```json
{
  "error_type": "api_error",
  "error_message": "Rate limit exceeded",
  "record_id": "118-hr-1234",
  "error_metadata": {
    "retry_after": 60,
    "endpoint": "/bill/118/hr/1234"
  }
}
```

#### PUT `/jobs/{job_id}/errors/{error_id}`

Update error status.

**Request Body:**
```json
{
  "resolved": true,
  "resolution_note": "Retried successfully after rate limit reset"
}
```

### Metrics

#### GET `/metrics`

Get aggregated metrics across all jobs.

**Query Parameters:**
- `time_range` (optional): Time range in hours (default: 24)

**Response:**
```json
{
  "time_range_hours": 24,
  "total_jobs": 150,
  "active_jobs": 3,
  "completed_jobs": 145,
  "failed_jobs": 2,
  "total_records_processed": 75000,
  "average_throughput": 42.3,
  "error_rate_percent": 2.1,
  "jobs_by_data_source": {
    "congress.gov": 80,
    "govinfo.gov": 45,
    "openstates.org": 25
  },
  "errors_by_type": {
    "api_error": 1200,
    "network_error": 300,
    "parse_error": 150
  }
}
```

#### GET `/metrics/{data_source}`

Get metrics for a specific data source.

### Health Check

#### GET `/health`

System health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "active_jobs": 3,
  "error_rate_24h": 1.8,
  "timestamp": "2024-11-23T12:00:00Z"
}
```

## Error Responses

All endpoints return standard HTTP status codes:

- `200`: Success
- `201`: Created
- `400`: Bad Request
- `401`: Unauthorized
- `403`: Forbidden
- `404`: Not Found
- `422`: Validation Error
- `500`: Internal Server Error

Error response format:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid job status",
    "details": {
      "allowed_values": ["running", "completed", "failed", "paused"]
    }
  }
}
```

## Rate Limiting

- Jobs endpoints: 100 requests per minute
- Progress updates: 1000 requests per minute
- Metrics endpoints: 60 requests per minute

Rate limit headers:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1637683200
```

## Webhooks

Configure webhooks for job completion and error events:

**Job Completed:**
```json
{
  "event": "job_completed",
  "job_id": 123,
  "job_name": "Congress 118 Bills",
  "processed_records": 5000,
  "failed_records": 15,
  "duration_seconds": 7200,
  "throughput_per_minute": 41.7
}
```

**Error Threshold Exceeded:**
```json
{
  "event": "error_threshold_exceeded",
  "job_id": 123,
  "job_name": "Congress 118 Bills",
  "error_rate_percent": 25.0,
  "threshold_percent": 20.0,
  "time_window_minutes": 60
}
```

## SDK Examples

### Python

```python
import requests

class MonitoringClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {api_key}"}

    def get_active_jobs(self):
        response = requests.get(
            f"{self.base_url}/jobs?status=running",
            headers=self.headers
        )
        return response.json()

    def update_progress(self, job_id: int, processed: int, failed: int):
        data = {
            "processed_records": processed,
            "failed_records": failed
        }
        response = requests.post(
            f"{self.base_url}/jobs/{job_id}/progress",
            json=data,
            headers=self.headers
        )
        return response.json()
```

### JavaScript

```javascript
class MonitoringClient {
    constructor(baseUrl, apiKey) {
        this.baseUrl = baseUrl;
        this.headers = {
            'Authorization': `Bearer ${apiKey}`,
            'Content-Type': 'application/json'
        };
    }

    async getJobStatus(jobId) {
        const response = await fetch(`${this.baseUrl}/jobs/${jobId}`, {
            headers: this.headers
        });
        return response.json();
    }

    async streamProgress(jobId, callback) {
        const response = await fetch(`${this.baseUrl}/jobs/${jobId}/progress/stream`, {
            headers: this.headers
        });

        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value);
            const lines = chunk.split('\n');

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    const data = JSON.parse(line.slice(6));
                    callback(data);
                }
            }
        }
    }
}
```

## Webhook Configuration

Set up webhooks to receive real-time notifications:

```json
{
  "webhooks": {
    "job_completed": {
      "url": "https://api.example.com/webhooks/job-completed",
      "secret": "webhook_secret_key",
      "events": ["job_completed", "job_failed"]
    },
    "error_alerts": {
      "url": "https://api.example.com/webhooks/errors",
      "secret": "error_webhook_secret",
      "events": ["error_threshold_exceeded", "job_failed"]
    }
  }
}
