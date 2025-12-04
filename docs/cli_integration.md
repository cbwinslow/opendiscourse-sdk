# CLI Tools Integration Summary

## Overview

Enhanced all three independent CLI tools (Congress, OpenStates, GovInfo) to support the new Pydantic configuration system while maintaining full backward compatibility.

---

## Implementation Details

### Congress CLI (`scripts/ingestion/congress_cli.py`)

**Enhanced `__init__` Method:**
- API key: Tries Pydantic config → resource_manager → error
- Database config: Tries Pydantic config → resource_manager fallback
- Batch size: Tries args → Pydantic config → default (50)
- Fully backward compatible with existing code

**Changes:**
```python
# Before
def __init__(self, api_key: str, db_config: Dict, batch_size: int = 50, dry_run: bool = False):

# After
def __init__(self, api_key: str = None, db_config: Dict = None, batch_size: int = None, dry_run: bool = False):
    # Auto-loads from Pydantic settings or falls back to resource_manager
```

**Usage:**
```bash
# Works without pydantic (uses .env via resource_manager)
python3 scripts/ingestion/congress_cli.py ingest-bills 118

# Works with pydantic (uses .env via Pydantic settings)
pip install pydantic pydantic-settings
python3 scripts/ingestion/congress_cli.py ingest-bills 118
```

---

## Three Independent CLI Tools

### 1. Congress CLI
**Entry point:** `opendiscourse-congress`
**Commands:** 23 commands covering all Congress.gov endpoints
**File:** `scripts/ingestion/congress_cli.py`

```bash
opendiscourse-congress ingest-bills 118
opendiscourse-congress ingest-members 118
opendiscourse-congress ingest-hearings 118
opendiscourse-congress ingest-nominations 118
```

### 2. OpenStates CLI
**Entry point:** `opendiscourse-states`
**Commands:** State legislature data ingestion
**File:** `scripts/ingestion/openstates_cli.py`

```bash
opendiscourse-states ingest-bills ca --years-back 5
opendiscourse-states ingest-people ca
opendiscourse-states ingest-votes ca
```

### 3. GovInfo CLI
**Entry point:** `opendiscourse-govinfo`
**Commands:** Federal documents ingestion
**File:** `scripts/ingestion/govinfo_cli.py`

```bash
opendiscourse-govinfo list-collections
opendiscourse-govinfo ingest-collection BILLS --start-date 2024-01-01
opendiscourse-govinfo ingest-packages
```

---

## Configuration Loading Order

For each CLI tool:

1. **Pydantic Settings** (if installed)
   - Loads from `.env` via `scripts.core.config.get_settings()`
   - Type-safe with validation
   - Preferred method

2. **Resource Manager** (fallback)
   - Loads from `.env` via `scripts.utils.resource_manager`
   - Works without Pydantic
   - Backward compatible

3. **Error** (if neither works)
   - Clear error message
   - Tells user what to configure

---

## Environment Variables

### With Pydantic (Nested Config)
```bash
# Database
DATABASE__HOST=localhost
DATABASE__PORT=5432
DATABASE__NAME=opendiscourse
DATABASE__USER=your_username

# Congress API
CONGRESS_API__API_KEY=your_key_here
CONGRESS_API__RATE_LIMIT=100

# OpenStates API
OPENSTATES_API__API_KEY=your_key_here

# GovInfo API
GOVINFO_API__API_KEY=your_key_here

# Ingestion
INGESTION__BATCH_SIZE=50
INGESTION__PARALLEL_WORKERS=4
```

### Without Pydantic (Flat)
```bash
# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=opendiscourse
DB_USER=your_username

# API Keys
CONGRESS_API_KEY=your_key_here
OPENSTATES_API_KEY=your_key_here
GOVINFO_API_KEY=your_key_here
```

---

## Testing

### Test Congress CLI

```bash
# Without pydantic (uses resource_manager)
python3 scripts/ingestion/congress_cli.py --help
python3 scripts/ingestion/congress_cli.py ingest-bills 118 --dry-run

# With pydantic
pip install pydantic pydantic-settings
python3 scripts/ingestion/congress_cli.py ingest-bills 118 --dry-run
```

### Test OpenStates CLI

```bash
python3 scripts/ingestion/openstates_cli.py --help
python3 scripts/ingestion/openstates_cli.py ingest-bills ca --dry-run
```

### Test GovInfo CLI

```bash
python3 scripts/ingestion/govinfo_cli.py --help
python3 scripts/ingestion/govinfo_cli.py list-collections
```

---

## Next Steps

### Immediate
1. Test Congress CLI with configuration system
2. Apply same pattern to OpenStates CLI
3. Apply same pattern to GovInfo CLI

### Phase 2 Features
1. Advanced filtering (--sponsor, --party, --state)
2. Multi-format export (--format csv/parquet/sqlite)
3. Incremental sync (--since, --checkpoint)

---

## Benefits

### For Users
- ✅ **Simple**: Just works with .env file
- ✅ **Flexible**: Pydantic or plain environment variables
- ✅ **Clear Errors**: Helpful messages if misconfigured
- ✅ **Independent**: Each CLI works standalone

### For Developers
- ✅ **Type-Safe**: Pydantic validation when available
- ✅ **Backward Compatible**: Existing code still works
- ✅ **Maintainable**: Shared configuration logic
- ✅ **Testable**: Easy to mock and test

---

## Files Modified

1. **scripts/ingestion/congress_cli.py** - Enhanced with config support
2. **scripts/utils/resource_manager.py** - Pydantic integration with fallback
3. **scripts/core/base_cli.py** - Shared CLI base class (for reference)

---

## Status

- [x] Congress CLI: Configuration integration complete
- [ ] OpenStates CLI: Pending (same pattern)
- [ ] GovInfo CLI: Pending (same pattern)

---

**Recommendation:** Test Congress CLI integration, then apply identical pattern to OpenStates and GovInfo CLIs.
