# Real-Time Progress Monitoring for Bulk Data Ingestion

This module provides comprehensive real-time monitoring capabilities for bulk data ingestion processes across all OpenDiscourse data sources and tables.

## Overview

The monitoring system consists of:
- **Universal Progress Monitor**: Core monitoring engine with delegate pattern
- **Database Schema**: Persistent progress and error tracking
- **Delegate Functions**: Custom logic for different data source/table combinations
- **Rich TUI Display**: Beautiful terminal-based progress visualization
- **API Endpoints**: REST API for external monitoring access

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Data Sources   │───▶│ Progress Monitor │───▶│   Delegates     │
│                 │    │                  │    │                 │
│ • congress.gov  │    │ • Job Tracking   │    │ • congress.gov  │
│ • govinfo.gov   │    │ • Progress Calc  │    │ • govinfo.gov   │
│ • openstates.org│    │ • Error Handling │    │ • entities      │
│ • custom APIs   │    │ • ETA Estimates  │    │ • tasks         │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Database      │    │   TUI Display    │    │   REST API      │
│                 │    │                  │    │                 │
│ • ingestion_jobs│    │ • Progress Bars  │    │ • Job Status    │
│ • ingestion_errors│   │ • Real-time     │    │ • Progress API  │
│ • progress_logs │    │ • Error Summary  │    │ • Metrics       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Quick Start

### 1. Setup Monitoring

```python
from monitoring.progress_monitor import UniversalProgressMonitor
from monitoring.delegates import setup_all_delegates
from opendiscourse.db import get_db

# Initialize monitor with database connection
with get_db() as db:
    monitor = UniversalProgressMonitor(db, display_mode='tui')
    setup_all_delegates(monitor)  # Register all delegate functions
```

### 2. Start an Ingestion Job

```python
# Start monitoring a Congress bills ingestion
job_id = monitor.start_job(
    job_name="Congress 118 Bills",
    data_source="congress.gov",
    table_name="documents",
    record_type="bill",
    total_estimated=5000,
    metadata={'congress': 118}
)
```

### 3. Update Progress During Ingestion

```python
# In your ingestion loop
for bill in bills:
    try:
        # Process the bill
        process_bill(bill)

        # Update progress
        monitor.update_progress(
            job_id=job_id,
            success=True,
            record_id=f"118-{bill['type']}-{bill['number']}"
        )
    except Exception as e:
        monitor.update_progress(
            job_id=job_id,
            success=False,
            record_id=f"118-{bill['type']}-{bill['number']}",
            error_details={'error': str(e), 'error_type': 'processing_error'}
        )
```

## Data Sources & Tables Supported

### Congress.gov API
- **Table**: `documents`
- **Record Types**: bills, resolutions, nominations
- **Delegate**: `congress_bills_delegate`

### GovInfo.gov API
- **Table**: `documents`
- **Record Types**: bills, public laws, congressional records
- **Delegate**: `govinfo_documents_delegate`

### OpenStates.org API
- **Table**: `entities`
- **Record Types**: legislators, committees, districts
- **Delegate**: `membership_ingestion_delegate`

### Custom Entity Ingestion
- **Table**: `entities`
- **Record Types**: persons, organizations, committees
- **Delegate**: `entities_ingestion_delegate`

### Task Management
- **Table**: `tasks`
- **Record Types**: analysis tasks, ingestion tasks
- **Delegate**: `tasks_ingestion_delegate`

## Delegate Function Pattern

Delegate functions allow custom monitoring logic for each data source/table combination:

```python
def custom_delegate(context: IngestionContext, update_data: Dict[str, Any]):
    """
    Custom delegate function for specific data source/table

    Args:
        context: IngestionContext with job metadata
        update_data: Dictionary with:
            - success: bool
            - error_details: Optional[Dict]
            - processed_count: int
            - failed_count: int
            - elapsed_time: float
    """
    if update_data['success']:
        # Custom success handling
        print(f"✅ Processed {context.record_type}: {context.current_record_id}")

        # Calculate custom metrics
        throughput = update_data['processed_count'] / (update_data['elapsed_time'] / 60)
        print(f"📊 Throughput: {throughput:.1f} records/min")
    else:
        # Custom error handling
        error_type = update_data['error_details'].get('error_type', 'unknown')
        print(f"❌ Failed {context.record_type}: {error_type}")
```

Register delegates:

```python
monitor.register_delegate("myapi.com", "custom_table", custom_delegate)
```

## Display Modes

### TUI Mode (Terminal User Interface)
```bash
python -m monitoring.progress_monitor --job-id 123 --display tui
```

Features:
- Real-time progress bars
- Color-coded status indicators
- Throughput graphs
- ETA calculations
- Error summaries

### Simple Mode
```bash
python -m monitoring.progress_monitor --job-id 123 --display simple
```

Features:
- Text-based progress updates
- Basic statistics
- Minimal resource usage

### Silent Mode
```bash
python -m monitoring.progress_monitor --job-id 123 --display silent
```

Features:
- Database-only updates
- No console output
- Suitable for background jobs

## Command Line Interface

### Monitor Existing Jobs
```bash
# Monitor by job ID
python -m monitoring.cli monitor --job-id 123 --display tui

# Monitor all active jobs
python -m monitoring.cli monitor --active --display tui

# Monitor with custom refresh rate
python -m monitoring.cli monitor --job-id 123 --refresh 5
```

### Job Management
```bash
# List all jobs
python -m monitoring.cli jobs list

# Get job details
python -m monitoring.cli jobs show 123

# Cancel a job
python -m monitoring.cli jobs cancel 123

# Clean up old jobs
python -m monitoring.cli jobs cleanup --older-than 30d
```

### Error Analysis
```bash
# Show errors for a job
python -m monitoring.cli errors --job-id 123

# Show error summary by type
python -m monitoring.cli errors --job-id 123 --summary

# Export errors to CSV
python -m monitoring.cli errors --job-id 123 --export errors.csv
```

## API Endpoints

### Get Job Status
```bash
curl http://localhost:8000/api/monitoring/jobs/123
```

Response:
```json
{
  "job_id": 123,
  "job_name": "Congress 118 Bills",
  "status": "running",
  "progress_percent": 67.8,
  "processed_records": 3390,
  "total_records": 5000,
  "throughput_per_minute": 45.2,
  "eta_seconds": 2834,
  "errors": {
    "api_errors": 12,
    "parse_errors": 3,
    "db_errors": 1
  }
}
```

### Get Active Jobs
```bash
curl http://localhost:8000/api/monitoring/jobs/active
```

### Get Error Details
```bash
curl http://localhost:8000/api/monitoring/jobs/123/errors
```

## Integration with Existing Scripts

### For Congress API Ingestion
```python
from opendiscourse.ingestion.congress_api_ingest import BulkDataIngester
from monitoring.progress_monitor import UniversalProgressMonitor
from monitoring.delegates import setup_all_delegates

# Setup monitoring
with get_db() as db:
    monitor = UniversalProgressMonitor(db, display_mode='tui')
    setup_all_delegates(monitor)

# Enhanced ingester
ingester = BulkDataIngester(monitor=monitor)
ingester.ingest_congress_bills(congress_number=118)
```

### For GovInfo Ingestion
```python
from opendiscourse.ingestion.govinfo_ingest import GovInfoIngester

ingester = GovInfoIngester(monitor=monitor)
ingester.ingest_collection(
    collection="BILLS",
    start_date="2024-01-01",
    end_date="2024-12-31"
)
```

## Configuration

Create `config/monitoring.json`:

```json
{
  "database": {
    "url": "postgresql://user:pass@localhost/opendiscourse"
  },
  "display": {
    "default_mode": "tui",
    "refresh_rate": 2,
    "colors": {
      "success": "green",
      "error": "red",
      "warning": "yellow"
    }
  },
  "alerts": {
    "email": {
      "enabled": true,
      "smtp_server": "smtp.gmail.com",
      "recipients": ["admin@opendiscourse.org"]
    },
    "slack": {
      "enabled": false,
      "webhook_url": "https://hooks.slack.com/...",
      "channel": "#ingestion-alerts"
    }
  },
  "cleanup": {
    "job_retention_days": 30,
    "error_retention_days": 90
  }
}
```

## Error Handling

The monitoring system includes robust error handling:

### Automatic Error Categorization
- `network_error`: Connection timeouts, DNS issues
- `api_error`: API rate limits, authentication failures
- `parse_error`: Malformed data, XML/JSON parsing issues
- `db_error`: Database connection, constraint violations
- `processing_error`: Business logic errors

### Retry Logic
- Exponential backoff for transient errors
- Circuit breaker pattern for cascading failures
- Configurable retry limits per error type

### Recovery Mechanisms
- Failed records can be retried individually
- Partial success tracking allows resume from interruption
- Error quarantine for records that consistently fail

## Performance Considerations

### Database Optimization
- Indexes on frequently queried columns
- Partitioning for large job histories
- Connection pooling to prevent exhaustion

### Memory Management
- Streaming progress updates to prevent memory bloat
- Configurable batch sizes for large ingestions
- Garbage collection hints for long-running jobs

### Resource Monitoring
- CPU and memory usage tracking
- Database connection pool monitoring
- API rate limit monitoring

## Troubleshooting

### Common Issues

**TUI Display Not Updating**
- Check database connectivity
- Verify job ID exists and is active
- Ensure display mode is set correctly

**High Memory Usage**
- Reduce refresh rate in TUI mode
- Use simple display mode for background jobs
- Check for memory leaks in delegate functions

**Database Connection Errors**
- Verify database credentials
- Check connection pool settings
- Monitor database server resources

**Slow Progress Updates**
- Check database indexes
- Monitor query performance
- Consider batching updates for high-throughput jobs

## Development

### Adding New Delegates
1. Create delegate function in `monitoring/delegates.py`
2. Register in `setup_all_delegates()` function
3. Add tests in `tests/test_delegates.py`

### Adding New Data Sources
1. Create ingester class inheriting from `BaseIngester`
2. Register with factory function in `monitoring/factory.py`
3. Add delegate for custom logic
4. Update documentation and tests

### Testing
```bash
# Run all monitoring tests
pytest tests/monitoring/

# Run with coverage
pytest --cov=monitoring tests/monitoring/

# Run specific test file
pytest tests/monitoring/test_progress_monitor.py
```

## API Reference

See `monitoring/api.py` for complete API documentation.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

This module is part of the OpenDiscourse project and follows the same license terms.
