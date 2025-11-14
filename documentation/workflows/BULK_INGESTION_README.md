# Bulk Data Ingestion Feature

## Overview

The OpenDiscourse repository now includes a comprehensive bulk data ingestion system for importing large volumes of congressional and government documents.

## Quick Start

### 1. Set up API keys

```bash
export GOVINFO_API_KEY="your_govinfo_api_key"
export CONGRESS_API_KEY="your_congress_api_key"
```

### 2. Run bulk ingestion

Ingest bills from GovInfo:
```bash
python congress_api_ingest.py --source govinfo --collection BILLS --limit 10
```

Ingest bills from Congress.gov:
```bash
python congress_api_ingest.py --source congress --congress 118 --bill-type hr --limit 10
```

## Features

- ✅ **Dual Source Support**: GovInfo API and Congress.gov API
- ✅ **Batch Processing**: Process multiple documents efficiently
- ✅ **Rate Limiting**: Automatic rate limiting to respect API guidelines
- ✅ **Retry Logic**: Built-in retry mechanism with exponential backoff
- ✅ **Error Handling**: Graceful error handling with detailed logging
- ✅ **Statistics**: Comprehensive ingestion statistics
- ✅ **Flexible Filtering**: Date ranges, document types, and limits
- ✅ **Multiple Formats**: HTML, TXT, XML, and PDF support

## Documentation

For detailed documentation, see [docs/bulk_ingestion.md](docs/bulk_ingestion.md)

## Files Added/Modified

### New Files
- `congress_api_ingest.py` - Main bulk ingestion implementation
- `tests/test_congress_ingestion.py` - Comprehensive test suite
- `docs/bulk_ingestion.md` - Detailed usage guide

### Modified Files
- `api_config.py` - Added Congress.gov API configuration
- `vector_store/weaviate_manager.py` - Fixed indentation error

## Testing

Run the test suite:
```bash
python -m pytest tests/test_congress_ingestion.py -v
```

All 14 tests pass successfully.

## Command-Line Interface

```
usage: congress_api_ingest.py [-h] --source {govinfo,congress} [--collection COLLECTION] 
                              [--congress CONGRESS] [--bill-type BILL_TYPE] 
                              [--start-date START_DATE] [--end-date END_DATE] 
                              [--limit LIMIT] [--data-dir DATA_DIR]
```

## Examples

### Example 1: Recent Bills
```bash
python congress_api_ingest.py \
  --source govinfo \
  --collection BILLS \
  --start-date 2024-01-01 \
  --limit 50
```

### Example 2: Congressional Records
```bash
python congress_api_ingest.py \
  --source govinfo \
  --collection CREC \
  --start-date 2024-01-01 \
  --end-date 2024-01-31
```

### Example 3: House Bills
```bash
python congress_api_ingest.py \
  --source congress \
  --congress 118 \
  --bill-type hr \
  --limit 100
```

## API Keys

Get your API keys from:
- GovInfo: https://www.govinfo.gov/developers/api
- Congress.gov: https://api.congress.gov/sign-up/

## Statistics Output

After completion, you'll see:

```
============================================================
Bulk Data Ingestion Statistics
============================================================
Total documents processed: 100
Successful ingestions:     95
Failed ingestions:         3
Skipped documents:         2
Success rate:              95.0%
============================================================
```

## Programmatic Usage

```python
from congress_api_ingest import BulkDataIngester

ingester = BulkDataIngester(
    govinfo_api_key="your_key",
    congress_api_key="your_key"
)

stats = ingester.ingest_govinfo_collection(
    collection_code="BILLS",
    limit=50
)

ingester.print_statistics()
```

## Integration with Existing Systems

The bulk ingestion system integrates seamlessly with:
- Existing document storage in PostgreSQL
- Vector database (Weaviate) for semantic search
- Entity extraction pipelines
- RAG (Retrieval-Augmented Generation) capabilities

## Next Steps

1. Set up your API keys
2. Test with a small limit (e.g., `--limit 10`)
3. Review the statistics and logs
4. Scale up to larger ingestion jobs
5. Integrate with your workflows

## Support

For issues or questions:
- Review the [full documentation](docs/bulk_ingestion.md)
- Check the [troubleshooting section](docs/bulk_ingestion.md#troubleshooting)
- Review test cases in `tests/test_congress_ingestion.py`

## License

Same as the main OpenDiscourse project (MIT License)
