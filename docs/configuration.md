# Configuration System Usage Guide

## Quick Start

### 1. Bootstrap Your Database

```bash
# Interactive database setup
opendiscourse-bootstrap

# This will:
# - Test PostgreSQL connection
# - Create database if needed
# - Apply all migrations
# - Verify setup
```

### 2. Configure Environment

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
nano .env
```

**Minimum Required:**
```bash
# Database
DATABASE__HOST=localhost
DATABASE__NAME=opendiscourse
DATABASE__USER=your_username

# API Keys
CONGRESS_API__API_KEY=your_key
OPENSTATES_API__API_KEY=your_key
GOVINFO_API__API_KEY=your_key
```

### 3. Use the CLIs

```bash
# Now you can use the CLI tools
opendiscourse-congress ingest-bills 118
opendiscourse-states ingest-bills ca --years-back 5
opendiscourse-govinfo ingest-collections
```

## Configuration System

### Type-Safe Settings with Pydantic

All configuration is managed via Pydantic models with full type safety:

```python
from scripts.core.config import get_settings

# Get global settings (loads from .env automatically)
settings = get_settings()

# Access nested configuration
print(settings.database.dsn)  # Connection string
print(settings.congress_api.rate_limit)  # 100
print(settings.ingestion.batch_size)  # 50
```

### Configuration Hierarchy

```python
Settings
├── environment: Environment (dev/staging/prod)
├── debug: bool
├── database: DatabaseConfig
│   ├── host, port, name, user, password
│   ├── connection pooling settings
│   └── SSL configuration
├── congress_api: CongressAPIConfig
│   ├── api_key (SecretStr)
│   ├── base_url
│   ├── rate_limit
│   └── retry settings
├── openstates_api: OpenStatesAPIConfig
├── govinfo_api: GovInfoAPIConfig
├── ingestion: IngestionConfig
│   ├── batch_size
│   ├── parallel_workers
│   └── checkpoint_interval
├── export: ExportConfig
│   ├── default_format (JSON/CSV/Parquet)
│   ├── compression (gzip/brotli)
│   └── output_dir
└── logging: LoggingConfig
    ├── level (DEBUG/INFO/WARNING/ERROR)
    └── file path
```

### Environment Variables

Use double underscore `__` for nested configuration:

```bash
# Direct property
DEBUG=true

# Nested: database.host
DATABASE__HOST=localhost

# Nested: congress_api.rate_limit
CONGRESS_API__RATE_LIMIT=100
```

### Enums for Type Safety

```python
from scripts.core.config import Environment, ExportFormat, LogLevel

# Environment
env = Environment.PRODUCTION  # or DEVELOPMENT, STAGING

# Export formats
format = ExportFormat.PARQUET  # or JSON, JSONL, CSV, SQLITE

# Log levels
level = LogLevel.INFO  # or DEBUG, WARNING, ERROR, CRITICAL
```

### Accessing Configuration in CLIs

```python
from scripts.core.config import get_settings

def my_cli_command():
    settings = get_settings()

    # Database connection
    conn = psycopg2.connect(settings.database.dsn)

    # API client
    api_key = settings.congress_api.api_key.get_secret_value()
    rate_limit = settings.congress_api.rate_limit

    # Ingestion settings
    batch_size = settings.ingestion.batch_size
```

## Database Bootstrap

### Interactive Mode

```bash
$ opendiscourse-bootstrap

==============================================================
OpenDiscourse Database Bootstrap
==============================================================

Step 1: Testing PostgreSQL connection...
✅ PostgreSQL server connection successful

Step 2: Checking database status...
⚠️  Database 'opendiscourse' does not exist

Create database 'opendiscourse'? [Y/n]: y

Step 3: Running bootstrap...
📊 Creating database 'opendiscourse'...
✅ Database 'opendiscourse' created successfully
📦 Found 15 pending migration(s)
📝 Applying migration: 001_congress_schema.sql
✅ Migration applied: 001_congress_schema.sql
...
✅ Bootstrap Complete!
```

### Programmatic Usage

```python
from scripts.core.database import DatabaseBootstrap

bootstrap = DatabaseBootstrap()

# Check database exists
if not bootstrap.database_exists():
    bootstrap.create_database()

# Apply migrations
bootstrap.migrate()

# Or do everything
bootstrap.bootstrap(create_db=True)
```

### Migration Management

```python
# Get applied migrations
applied = bootstrap.get_applied_migrations()
print(f"Applied: {len(applied)} migrations")

# Get pending migrations
pending = bootstrap.get_pending_migrations()
print(f"Pending: {len(pending)} migrations")

# Apply a specific migration
bootstrap.apply_migration(Path("migrations/001_congress_schema.sql"))
```

## Advanced Usage

### Multiple Environments

Create environment-specific `.env` files:

```bash
.env.development
.env.staging
.env.production
```

Load specific environment:

```python
from pathlib import Path
from scripts.core.config import Settings

settings = Settings.from_env(Path(".env.production"))
```

### Runtime Configuration Updates

```python
from scripts.core.config import update_settings

# Update specific settings
update_settings(
    debug=True,
    ingestion__batch_size=100
)
```

### Safe Configuration Export

```python
settings = get_settings()

# Export without secrets
safe_config = settings.to_dict_safe()
print(safe_config)  # API keys and passwords redacted
```

### Custom Validation

Settings include validation:

```python
# This will raise ValidationError
DatabaseConfig(port=99999)  # Port must be 1-65535

# This works
DatabaseConfig(port=5432)  # Valid
```

## Migration Files

Migrations are standard SQL files in `migrations/`:

```
migrations/
├── 001_congress_schema.sql
├── 002_govinfo_schema.sql
├── 003_openstates_schema.sql
├── ...
└── 015_congress_extended_schema.sql
```

The bootstrap system:
1. Tracks applied migrations in `schema_migrations` table
2. Applies pending migrations in order
3. Rolls back on failure
4. Reports progress

## Troubleshooting

### Connection Issues

```python
from scripts.core.database import DatabaseBootstrap

bootstrap = DatabaseBootstrap()

# Test connection
if not bootstrap.test_connection():
    print("Check your .env configuration")
```

### View Current Configuration

```python
from scripts.core.config import get_settings

settings = get_settings()
print(settings.to_dict_safe())  # See all settings (secrets redacted)
```

### Reset Configuration

```python
from scripts.core.config import get_settings

# Force reload from .env
settings = get_settings(reload=True)
```

## Example Workflow

```bash
# 1. Setup
cp .env.example .env
nano .env  # Add your API keys and database credentials

# 2. Bootstrap database
opendiscourse-bootstrap

# 3. Start ingesting
opendiscourse-congress ingest-bills 118
opendiscourse-states ingest-bills ca
opendiscourse-govinfo ingest-collections

# 4. Export data
opendiscourse-congress export-bills --format parquet --output bills.parquet
```
