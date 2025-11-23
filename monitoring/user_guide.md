# User Guide: Real-Time Progress Monitoring for Bulk Data Ingestion

## Overview

This guide provides comprehensive instructions for users and AI agents on how to use the real-time progress monitoring system for bulk data ingestion in OpenDiscourse. The system provides complete visibility into ingestion operations with beautiful real-time displays.

## Quick Start for Users

### 1. Basic Usage

Run any monitored ingestion script with progress display:

```bash
# Congress members ingestion with full monitoring
python scripts/ingest_members_monitored.py \
  --congress-start 118 \
  --congress-end 118 \
  --monitor-mode tui \
  --batch-size 25

# GovInfo documents ingestion
python scripts/ingest_govinfo_monitored.py \
  --collection BILLS \
  --start-date 2024-01-01 \
  --monitor-mode simple
```

### 2. Monitor Active Jobs

Check running ingestion jobs via command line:

```bash
# List all active jobs
python -m monitoring.cli jobs list

# Monitor specific job with TUI
python -m monitoring.cli monitor --job-id 123 --display tui

# Get job status
python -m monitoring.cli jobs show 123
```

### 3. API Access

Monitor jobs programmatically via REST API:

```bash
# Get active jobs
curl http://localhost:8000/api/monitoring/jobs/active

# Get specific job details
curl http://localhost:8000/api/monitoring/jobs/123

# Stream real-time progress updates
curl http://localhost:8000/api/monitoring/jobs/123/progress/stream
```

## Display Modes

### TUI Mode (Terminal User Interface)

Provides the richest monitoring experience with real-time progress bars and detailed metrics.

**Features:**
- Real-time progress bars with percentage completion
- Color-coded status indicators
- Throughput graphs and ETA calculations
- Error summaries with categorization
- Current record being processed

**Example Display:**
```
🔥 Bulk Data Ingestion Monitor
┌─────────────────────────────────────────────────────────────┐
│ 📊 Job: Congress 118 Members                                  │
│ 📅 Congress: 118                                              │
│ 🔗 Source: congress.gov                                       │
│ 📋 Table: congress.members                                   │
│ 📈 Progress: 342 / 545 (62.8%)                               │
│ ⚡ Throughput: 45.2 records/min                               │
│ ⏰ ETA: 04:23:12                                             │
│ ❌ Failed: 3                                                 │
│ 🔄 Current: S001234                                          │
└─────────────────────────────────────────────────────────────┘
```

**Command:**
```bash
python scripts/ingest_members_monitored.py --monitor-mode tui
```

### Simple Mode

Text-based progress updates for environments without rich terminal support or background jobs.

**Features:**
- Text-only progress updates
- Basic statistics display
- Minimal resource usage
- Suitable for logging and automation

**Example Output:**
```
📊 Job: Congress 118 Members
📅 Congress: 118
🔗 Source: congress.gov
📋 Table: congress.members
📈 Progress: 342 / 545 (62.8%)
⚡ Throughput: 45.2 records/min
⏰ ETA: 04:23:12
❌ Failed: 3
```

**Command:**
```bash
python scripts/ingest_members_monitored.py --monitor-mode simple
```

### Silent Mode

No console output, database-only monitoring for production environments or when display is not needed.

**Use Cases:**
- Production deployments
- Background jobs
- Integration with external monitoring systems
- Headless servers

**Command:**
```bash
python scripts/ingest_members_monitored.py --monitor-mode silent
```

## Data Sources and Tables

### Congress.gov API

**Supported Tables:**
- `congress.members` - Member biographical data
- `documents` - Bills, resolutions, and legislative documents

**Delegate Functions:**
- `congress_members_delegate` - Custom display for members with congress number
- `congress_bills_delegate` - Custom display for legislative documents

**Usage Example:**
```bash
# Members data
python scripts/ingest_members_monitored.py \
  --congress-start 115 \
  --congress-end 118 \
  --monitor-mode tui

# Bills data
python scripts/ingest_bills_monitored.py \
  --congress 118 \
  --monitor-mode tui
```

### GovInfo.gov API

**Supported Tables:**
- `documents` - Federal Register, Congressional Record, etc.

**Delegate Functions:**
- `govinfo_documents_delegate` - Custom display for government documents

**Usage Example:**
```bash
python scripts/ingest_govinfo_monitored.py \
  --collection FR \
  --start-date 2024-01-01 \
  --end-date 2024-12-31 \
  --monitor-mode tui
```

### OpenStates.org API

**Supported Tables:**
- `entities` - Legislators, committees, districts

**Delegate Functions:**
- `entities_ingestion_delegate` - Custom display for entity data

**Usage Example:**
```bash
python scripts/ingest_entities_monitored.py \
  --entity-type legislator \
  --state CA \
  --monitor-mode simple
```

## Configuration Options

### Environment Variables

Set these in your `.env` file or environment:

```bash
# Database connection
DB_HOST=localhost
DB_PORT=5432
DB_NAME=opendiscourse
DB_USER=your_user
DB_PASSWORD=your_password

# API Keys
CONGRESS_API_KEY=your_congress_api_key
GOVINFO_API_KEY=your_govinfo_api_key

# Monitoring defaults
MONITORING_ENABLED=true
MONITORING_DEFAULT_MODE=tui
MONITORING_UPDATE_INTERVAL=2
```

### Command Line Options

All monitored scripts support these options:

```bash
# Monitoring control
--enable-monitoring        # Enable progress monitoring (default: True)
--disable-monitoring       # Disable progress monitoring
--monitor-mode MODE        # Display mode: tui, simple, silent (default: tui)

# Performance tuning
--batch-size SIZE          # Records per batch (default: 50)
--request-delay DELAY      # Seconds between API requests (default: 0.5)

# Range specification
--congress-start START     # Starting congress number
--congress-end END         # Ending congress number
--start-date DATE          # Start date (YYYY-MM-DD)
--end-date DATE            # End date (YYYY-MM-DD)

# Output control
--dry-run                  # Test without actual ingestion
--verbose                  # Detailed logging
--quiet                    # Minimal output
```

## Error Handling and Recovery

### Error Categories

The system automatically categorizes errors for better monitoring:

- **Network Errors**: Connection timeouts, DNS issues
- **API Errors**: Rate limits, authentication failures, bad requests
- **Parse Errors**: Malformed data, XML/JSON parsing failures
- **Database Errors**: Connection issues, constraint violations
- **Processing Errors**: Business logic errors, data validation failures

### Recovery Mechanisms

- **Automatic Retries**: Configurable retry attempts with exponential backoff
- **Circuit Breaker**: Prevents cascade failures by temporarily stopping requests
- **Graceful Degradation**: Continues processing other records when individual failures occur
- **Error Quarantine**: Isolates repeatedly failing records

### Monitoring Error Rates

Check error rates through the API:

```bash
# Get error summary for a job
curl http://localhost:8000/api/monitoring/jobs/123/errors

# Get error rate trends
curl http://localhost:8000/api/monitoring/metrics/errors?time_range=24h
```

## Performance Monitoring

### Throughput Metrics

Monitor processing speed and efficiency:

```bash
# Real-time throughput
curl http://localhost:8000/api/monitoring/jobs/123 | jq '.throughput_per_minute'

# Historical performance
curl http://localhost:8000/api/monitoring/metrics/performance?time_range=7d
```

### System Resources

Track resource usage during ingestion:

```bash
# Memory and CPU usage
curl http://localhost:8000/api/monitoring/metrics/system

# Database performance
curl http://localhost:8000/api/monitoring/metrics/database
```

## Troubleshooting

### Common Issues

#### TUI Display Not Appearing
```bash
# Check if Rich library is installed
pip install rich

# Try simple mode instead
python script.py --monitor-mode simple

# Check terminal capabilities
echo $TERM  # Should support colors
```

#### Database Connection Errors
```bash
# Verify database credentials
python -c "import psycopg2; psycopg2.connect('your_connection_string')"

# Check database server status
pg_isready -h localhost -p 5432

# Review connection logs
tail -f /var/log/postgresql/postgresql.log
```

#### API Rate Limiting
```bash
# Increase request delay
python script.py --request-delay 1.0

# Reduce batch size
python script.py --batch-size 10

# Check API status
curl -I https://api.congress.gov/v3
```

#### High Memory Usage
```bash
# Use simple display mode
python script.py --monitor-mode simple

# Reduce batch size
python script.py --batch-size 25

# Monitor memory usage
htop  # or top -p $(pgrep python)
```

### Debugging Commands

```bash
# Enable verbose logging
python script.py --verbose

# Check job status
python -m monitoring.cli jobs show JOB_ID

# View error logs
python -m monitoring.cli errors --job-id JOB_ID

# Test database connectivity
python -c "
import psycopg2
conn = psycopg2.connect('your_connection_string')
print('Database connection successful')
conn.close()
"
```

## Advanced Usage

### Custom Delegate Functions

Create custom monitoring behavior for new data sources:

```python
from monitoring.progress_monitor import IngestionContext
from monitoring.delegates import setup_all_delegates

def custom_data_delegate(context: IngestionContext, update_data: Dict[str, Any]):
    """Custom delegate for specialized data source"""
    source_name = context.metadata.get('source_name', 'Unknown')

    if update_data['success']:
        print(f"🔄 Processing {source_name} record: {context.current_record_id}")
        print(f"   Progress: {update_data['processed_count']} records")
    else:
        error = update_data.get('error_details', {})
        print(f"❌ Failed {source_name} record: {error.get('error_type', 'unknown')}")

# Register custom delegate
monitor = UniversalProgressMonitor(db_connection)
monitor.register_delegate("custom.api", "custom_table", custom_data_delegate)
```

### Batch Processing Optimization

Optimize for large datasets:

```bash
# Large congress range with optimized settings
python scripts/ingest_members_monitored.py \
  --congress-start 101 \
  --congress-end 118 \
  --batch-size 100 \
  --request-delay 0.1 \
  --monitor-mode simple \
  --enable-parallel  # If supported
```

### Monitoring Multiple Jobs

Run and monitor multiple ingestion jobs simultaneously:

```bash
# Start multiple jobs in background
python scripts/ingest_members_monitored.py --congress-start 118 --congress-end 118 --monitor-mode silent &
JOB1_PID=$!

python scripts/ingest_bills_monitored.py --congress 118 --monitor-mode silent &
JOB2_PID=$!

# Monitor all jobs
python -m monitoring.cli monitor --active --display tui

# Cleanup
kill $JOB1_PID $JOB2_PID
```

## Integration with External Systems

### Webhook Notifications

Configure webhooks for job completion and error alerts:

```json
{
  "webhooks": {
    "job_completed": {
      "url": "https://api.example.com/webhooks/ingestion-complete",
      "events": ["job_completed"],
      "headers": {"Authorization": "Bearer token"}
    },
    "error_alerts": {
      "url": "https://api.example.com/webhooks/errors",
      "events": ["error_threshold_exceeded", "job_failed"],
      "threshold": 20
    }
  }
}
```

### Slack/Discord Integration

Send notifications to chat platforms:

```bash
# Configure Slack webhook
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/..."

# Monitor with notifications
python scripts/ingest_members_monitored.py \
  --monitor-mode tui \
  --slack-notifications \
  --slack-channel "#data-ingestion"
```

### Prometheus/Grafana

Export metrics for centralized monitoring:

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'opendiscourse-monitoring'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/api/monitoring/metrics/prometheus'
```

## Best Practices

### For Large Datasets
- Use `simple` or `silent` display modes
- Increase batch sizes for better throughput
- Enable parallel processing if available
- Monitor system resources closely

### For Real-Time Monitoring
- Use `tui` mode for interactive sessions
- Enable webhooks for external notifications
- Set up alerts for error thresholds
- Regular cleanup of old job data

### For Production Deployments
- Use `silent` mode to reduce resource usage
- Enable comprehensive logging
- Set up automated error recovery
- Implement proper backup strategies

## API Reference for Agents

### Job Management

```python
import requests

class MonitoringClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url

    def get_active_jobs(self):
        """Get all active ingestion jobs"""
        response = requests.get(f"{self.base_url}/api/monitoring/jobs/active")
        return response.json()

    def get_job_status(self, job_id: int):
        """Get detailed status for specific job"""
        response = requests.get(f"{self.base_url}/api/monitoring/jobs/{job_id}")
        return response.json()

    def update_job_metadata(self, job_id: int, metadata: dict):
        """Update job metadata"""
        response = requests.put(
            f"{self.base_url}/api/monitoring/jobs/{job_id}",
            json={"metadata": metadata}
        )
        return response.json()

    def cancel_job(self, job_id: int):
        """Cancel a running job"""
        response = requests.delete(f"{self.base_url}/api/monitoring/jobs/{job_id}")
        return response.json()
```

### Progress Streaming

```python
import json

def stream_progress(job_id: int):
    """Stream real-time progress updates"""
    response = requests.get(
        f"{base_url}/api/monitoring/jobs/{job_id}/progress/stream",
        stream=True
    )

    for line in response.iter_lines():
        if line.startswith(b'data: '):
            data = json.loads(line[6:])
            yield data
```

### Error Monitoring

```python
def monitor_errors(job_id: int, error_threshold: int = 10):
    """Monitor error rates and alert if threshold exceeded"""
    errors = requests.get(f"{base_url}/api/monitoring/jobs/{job_id}/errors").json()

    if len(errors['errors']) > error_threshold:
        # Send alert
        send_alert(f"Job {job_id} has {len(errors['errors'])} errors")

    return errors
```

This comprehensive guide ensures users and AI agents can effectively utilize the real-time progress monitoring system for all bulk data ingestion operations in OpenDiscourse.
