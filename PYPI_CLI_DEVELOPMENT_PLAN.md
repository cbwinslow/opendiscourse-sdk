# 🚀 PyPI CLI Tools Development Plan

## 📋 **PROJECT OVERVIEW**

Creating 3 separate CLI tools for PyPI distribution that provide complete bulk data ingestion capabilities with SQL bootstrap, API management, and sophisticated monitoring.

---

## 🎯 **CLI PACKAGES ARCHITECTURE**

### **Package 1: `openstates-cli`**
```bash
pip install openstates-cli
openstates-cli --help
```

**Features:**
- ✅ SQL bootstrap for OpenStates schema
- ✅ API key management and validation
- ✅ Bulk people and bills ingestion
- ✅ Incremental ingestion with offset tracking
- ✅ Real-time monitoring and progress tracking
- ✅ Pydantic models for data validation
- ✅ Sophisticated error handling and retry logic

### **Package 2: `govinfo-cli`**
```bash
pip install govinfo-cli
govinfo-cli --help
```

**Features:**
- ✅ SQL bootstrap for GovInfo schema
- ✅ API key management and validation
- ✅ Bulk bills and packages ingestion
- ✅ Collection-based ingestion with granule processing
- ✅ Rate limiting and monitoring
- ✅ Pydantic models and data structures
- ✅ Incremental ingestion with checkpoint tracking

### **Package 3: `congress-cli`**
```bash
pip install congress-cli
congress-cli --help
```

**Features:**
- ✅ SQL bootstrap for Congress schema
- ✅ API key management and validation
- ✅ Bulk members and bills ingestion
- ✅ Pagination-based ingestion with offset tracking
- ✅ Real-time monitoring and progress tracking
- ✅ Pydantic models for data validation
- ✅ Sophisticated error handling and retry logic

---

## 🏗️ **TECHNICAL ARCHITECTURE**

### **Core Components per Package**

```
Package Structure:
├── setup.py / pyproject.toml
├── README.md
├── LICENSE
├── src/
│   └── {package_name}/
│       ├── __init__.py
│       ├── cli.py              # Main CLI interface
│       ├── models/             # Pydantic models
│       │   ├── __init__.py
│       │   ├── api_models.py   # API response models
│       │   ├── db_models.py    # Database models
│       │   └── config_models.py # Configuration models
│       ├── api/                # API abstraction layer
│       │   ├── __init__.py
│       │   ├── client.py       # API client
│       │   ├── endpoints.py    # API endpoints
│       │   └── validators.py   # API validation
│       ├── database/           # Database operations
│       │   ├── __init__.py
│       │   ├── migrations.py   # SQL bootstrap
│       │   ├── operations.py   # CRUD operations
│       │   └── checkpoints.py  # Incremental tracking
│       ├── ingestion/          # Data ingestion logic
│       │   ├── __init__.py
│       │   ├── bulk_ingestor.py # Main ingestion engine
│       │   ├── incremental.py  # Incremental ingestion
│       │   ├── offset_manager.py # Offset tracking
│       │   └── retry_handler.py # Retry logic
│       ├── monitoring/         # Monitoring and logging
│       │   ├── __init__.py
│       │   ├── progress.py     # Progress tracking
│       │   ├── metrics.py      # Performance metrics
│       │   └── alerts.py       # Alert system
│       └── utils/              # Utilities
│           ├── __init__.py
│           ├── config.py       # Configuration management
│           ├── logger.py       # Logging setup
│           └── helpers.py      # Helper functions
├── tests/                      # Test suite
└── docs/                       # Documentation
```

---

## 📊 **DATA MODELS & PYDANTIC INTEGRATION**

### **Pydantic Models Architecture**

```python
# Example: congress-cli/src/congress_cli/models/api_models.py
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class CongressMember(BaseModel):
    """Congress member data model"""
    bioguide_id: str = Field(..., description="Bioguide ID")
    full_name: str = Field(..., description="Full name")
    state: str = Field(..., description="State")
    district: Optional[str] = Field(None, description="District")
    party: Optional[str] = Field(None, description="Party")
    term_start: datetime = Field(..., description="Term start date")
    term_end: Optional[datetime] = Field(None, description="Term end date")

    @validator('state')
    def validate_state(cls, v):
        if len(v) != 2:
            raise ValueError('State must be 2-character code')
        return v.upper()

class CongressBill(BaseModel):
    """Congress bill data model"""
    bill_id: str = Field(..., description="Bill ID")
    title: str = Field(..., description="Bill title")
    congress: int = Field(..., description="Congress number")
    bill_type: str = Field(..., description="Bill type")
    introduced_date: datetime = Field(..., description="Introduction date")
    sponsor_bioguide_id: Optional[str] = Field(None, description="Sponsor bioguide ID")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class APIResponse(BaseModel):
    """Generic API response model"""
    count: int = Field(..., description="Total count")
    next_offset: Optional[str] = Field(None, description="Next offset for pagination")
    results: List[Dict[str, Any]] = Field(..., description="API results")

    @validator('results')
    def validate_results_not_empty(cls, v):
        if not v:
            raise ValueError('Results cannot be empty')
        return v
```

### **Sophisticated Data Structures**

```python
# Example: Lambda functions and delegates
from typing import Callable, Any
from dataclasses import dataclass
from functools import wraps

@dataclass
class IngestionConfig:
    """Configuration for ingestion process"""
    api_key: str
    database_url: str
    batch_size: int = 100
    max_retries: int = 3
    timeout_seconds: int = 30
    rate_limit_per_second: int = 10

    # Lambda functions for custom processing
    data_transformer: Callable[[Dict], Dict] = lambda x: x
    error_handler: Callable[[Exception, Dict], bool] = lambda e, d: False
    progress_callback: Callable[[int, int], None] = lambda c, t: None

class OffsetManager:
    """Sophisticated offset management with lambda functions"""

    def __init__(self, initial_offset: str = "0"):
        self.current_offset = initial_offset
        self.offset_history: List[str] = []
        self.offset_transformers: List[Callable[[str], str]] = []

    def add_transformer(self, transformer: Callable[[str], str]):
        """Add lambda function to transform offsets"""
        self.offset_transformers.append(transformer)

    def get_next_offset(self, response_data: Dict) -> str:
        """Get next offset with transformation pipeline"""
        raw_offset = response_data.get('next_offset', self.current_offset)

        # Apply all transformers
        for transformer in self.offset_transformers:
            raw_offset = transformer(raw_offset)

        self.offset_history.append(raw_offset)
        self.current_offset = raw_offset
        return raw_offset

class RetryHandler:
    """Sophisticated retry logic with delegate functions"""

    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries
        self.retry_strategies: List[Callable[[Exception], bool]] = []
        self.retry_callbacks: List[Callable[[int, Exception], None]] = []

    def add_strategy(self, strategy: Callable[[Exception], bool]):
        """Add retry strategy delegate function"""
        self.retry_strategies.append(strategy)

    def add_callback(self, callback: Callable[[int, Exception], None]):
        """Add retry callback delegate function"""
        self.retry_callbacks.append(callback)

    def execute_with_retry(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with retry logic"""
        for attempt in range(self.max_retries + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if attempt == self.max_retries:
                    raise

                # Check retry strategies
                should_retry = any(strategy(e) for strategy in self.retry_strategies)

                if should_retry:
                    # Call retry callbacks
                    for callback in self.retry_callbacks:
                        callback(attempt + 1, e)

                    # Exponential backoff
                    time.sleep(2 ** attempt)
                    continue
                else:
                    raise
```

---

## 🔧 **API ABSTRACTION LAYER**

### **Unified API Client Architecture**

```python
# Example: congress-cli/src/congress_cli/api/client.py
import requests
from typing import Dict, Any, Optional, List
from ..models.api_models import APIResponse, CongressMember, CongressBill
from ..utils.config import get_config
from ..utils.logger import get_logger

class CongressAPIClient:
    """Abstracted Congress.gov API client"""

    def __init__(self, api_key: Optional[str] = None):
        self.config = get_config()
        self.api_key = api_key or self.config.api_key
        self.base_url = "https://api.congress.gov/v3"
        self.session = requests.Session()
        self.session.headers.update({
            'X-API-Key': self.api_key,
            'Accept': 'application/json',
            'User-Agent': f'congress-cli/{self.config.version}'
        })
        self.logger = get_logger(__name__)

    def _make_request(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make API request with error handling and retry logic"""
        url = f"{self.base_url}/{endpoint}"

        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"API request failed: {e}")
            raise

    def get_members(self, congress: int, offset: int = 0) -> APIResponse:
        """Get Congress members with pagination"""
        params = {
            'limit': 250,
            'offset': offset
        }

        data = self._make_request(f"member/congress/{congress}", params)
        return APIResponse(**data)

    def get_bills(self, congress: int, offset: int = 0) -> APIResponse:
        """Get Congress bills with pagination"""
        params = {
            'limit': 250,
            'offset': offset
        }

        data = self._make_request(f"bill/congress/{congress}", params)
        return APIResponse(**data)

    def get_bill_details(self, bill_id: str) -> CongressBill:
        """Get detailed bill information"""
        data = self._make_request(f"bill/{bill_id}")
        return CongressBill(**data)
```

---

## 🗄️ **SQL BOOTSTRAP SYSTEM**

### **Database Migration Architecture**

```python
# Example: congress-cli/src/congress_cli/database/migrations.py
from pathlib import Path
import psycopg2
from typing import Dict, Any
from ..utils.config import get_config
from ..utils.logger import get_logger

class DatabaseBootstrap:
    """Database bootstrap and migration system"""

    def __init__(self):
        self.config = get_config()
        self.logger = get_logger(__name__)
        self.migrations_dir = Path(__file__).parent / "migrations"

    def bootstrap_database(self, drop_existing: bool = False) -> bool:
        """Bootstrap database with all tables"""
        try:
            conn = psycopg2.connect(self.config.database_url)
            cursor = conn.cursor()

            if drop_existing:
                self._drop_all_tables(cursor)

            # Create schema
            cursor.execute("CREATE SCHEMA IF NOT EXISTS congress;")
            cursor.execute("CREATE SCHEMA IF NOT EXISTS incremental;")

            # Run migrations in order
            migration_files = sorted(self.migrations_dir.glob("*.sql"))

            for migration_file in migration_files:
                self.logger.info(f"Running migration: {migration_file.name}")
                self._run_migration(cursor, migration_file)

            conn.commit()
            cursor.close()
            conn.close()

            self.logger.info("Database bootstrap completed successfully")
            return True

        except Exception as e:
            self.logger.error(f"Database bootstrap failed: {e}")
            return False

    def _run_migration(self, cursor, migration_file: Path):
        """Run a single migration file"""
        with open(migration_file, 'r') as f:
            migration_sql = f.read()

        cursor.execute(migration_sql)

    def _drop_all_tables(self, cursor):
        """Drop all existing tables"""
        cursor.execute("DROP SCHEMA IF EXISTS congress CASCADE;")
        cursor.execute("DROP SCHEMA IF EXISTS incremental CASCADE;")

# Migration files:
# migrations/001_create_congress_schema.sql
# migrations/002_create_incremental_schema.sql
# migrations/003_create_indexes.sql
```

### **Example Migration SQL**

```sql
-- migrations/001_create_congress_schema.sql
CREATE TABLE congress.members (
    bioguide_id VARCHAR(20) PRIMARY KEY,
    full_name VARCHAR(255) NOT NULL,
    state VARCHAR(2) NOT NULL,
    district VARCHAR(10),
    party VARCHAR(50),
    term_start DATE NOT NULL,
    term_end DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE congress.bills (
    bill_id VARCHAR(50) PRIMARY KEY,
    title TEXT NOT NULL,
    congress INTEGER NOT NULL,
    bill_type VARCHAR(20) NOT NULL,
    introduced_date DATE NOT NULL,
    sponsor_bioguide_id VARCHAR(20),
    data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sponsor_bioguide_id) REFERENCES congress.members(bioguide_id)
);

-- migrations/002_create_incremental_schema.sql
CREATE TABLE incremental.ingestion_checkpoints (
    id SERIAL PRIMARY KEY,
    data_source VARCHAR(50) NOT NULL,
    data_type VARCHAR(50) NOT NULL,
    category VARCHAR(50),
    offset VARCHAR(100) NOT NULL DEFAULT '0',
    total_processed INTEGER NOT NULL DEFAULT 0,
    last_ingestion_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(data_source, data_type, category)
);

CREATE TABLE incremental.ingestion_logs (
    id SERIAL PRIMARY KEY,
    data_source VARCHAR(50) NOT NULL,
    data_type VARCHAR(50) NOT NULL,
    log_level VARCHAR(10) NOT NULL,
    message TEXT,
    details JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 📈 **MONITORING & INCREMENTAL INGESTION**

### **Progress Tracking System**

```python
# Example: congress-cli/src/congress_cli/monitoring/progress.py
import time
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from ..utils.logger import get_logger

@dataclass
class ProgressMetrics:
    """Progress tracking metrics"""
    total_items: int = 0
    processed_items: int = 0
    failed_items: int = 0
    start_time: datetime = field(default_factory=datetime.now)
    last_update: datetime = field(default_factory=datetime.now)
    current_rate: float = 0.0  # items per second

    @property
    def completion_percentage(self) -> float:
        """Calculate completion percentage"""
        if self.total_items == 0:
            return 0.0
        return (self.processed_items / self.total_items) * 100

    @property
    def elapsed_time(self) -> timedelta:
        """Calculate elapsed time"""
        return datetime.now() - self.start_time

    @property
    def estimated_remaining_time(self) -> Optional[timedelta]:
        """Estimate remaining time"""
        if self.current_rate == 0:
            return None

        remaining_items = self.total_items - self.processed_items
        remaining_seconds = remaining_items / self.current_rate
        return timedelta(seconds=remaining_seconds)

class ProgressTracker:
    """Sophisticated progress tracking with callbacks"""

    def __init__(self, total_items: int):
        self.metrics = ProgressMetrics(total_items=total_items)
        self.callbacks: List[Callable[[ProgressMetrics], None]] = []
        self.logger = get_logger(__name__)
        self.last_log_time = datetime.now()

    def add_callback(self, callback: Callable[[ProgressMetrics], None]):
        """Add progress callback"""
        self.callbacks.append(callback)

    def update(self, processed: int, failed: int = 0):
        """Update progress metrics"""
        self.metrics.processed_items += processed
        self.metrics.failed_items += failed
        self.metrics.last_update = datetime.now()

        # Calculate current rate
        elapsed = self.metrics.elapsed_time.total_seconds()
        if elapsed > 0:
            self.metrics.current_rate = self.metrics.processed_items / elapsed

        # Call callbacks
        for callback in self.callbacks:
            try:
                callback(self.metrics)
            except Exception as e:
                self.logger.warning(f"Progress callback failed: {e}")

        # Log progress periodically
        if (datetime.now() - self.last_log_time).total_seconds() > 30:
            self._log_progress()
            self.last_log_time = datetime.now()

    def _log_progress(self):
        """Log progress information"""
        metrics = self.metrics
        self.logger.info(
            f"Progress: {metrics.processed_items}/{metrics.total_items} "
            f"({metrics.completion_percentage:.1f}%) "
            f"Rate: {metrics.current_rate:.1f} items/sec "
            f"Failed: {metrics.failed_items}"
        )
```

### **Incremental Ingestion Engine**

```python
# Example: congress-cli/src/congress_cli/ingestion/incremental.py
from typing import Dict, Any, Optional, Callable
from ..database.operations import DatabaseOperations
from ..monitoring.progress import ProgressTracker
from ..api.client import CongressAPIClient
from ..utils.logger import get_logger

class IncrementalIngestor:
    """Sophisticated incremental ingestion engine"""

    def __init__(self):
        self.db_ops = DatabaseOperations()
        self.api_client = CongressAPIClient()
        self.logger = get_logger(__name__)
        self.progress_tracker: Optional[ProgressTracker] = None

        # Delegate functions for custom processing
        self.data_processors: Dict[str, Callable] = {}
        self.error_handlers: Dict[str, Callable] = {}

    def register_processor(self, data_type: str, processor: Callable[[Dict], Dict]):
        """Register data processor delegate"""
        self.data_processors[data_type] = processor

    def register_error_handler(self, error_type: str, handler: Callable[[Exception, Dict], bool]):
        """Register error handler delegate"""
        self.error_handlers[error_type] = handler

    def ingest_members(self, congress: int, resume: bool = True) -> Dict[str, Any]:
        """Ingest Congress members with incremental support"""
        try:
            # Get checkpoint
            checkpoint = self.db_ops.get_checkpoint('congress', 'members', str(congress))
            start_offset = checkpoint.offset if resume and checkpoint else "0"

            # Get total count
            initial_response = self.api_client.get_members(congress, 0)
            total_members = initial_response.count

            # Setup progress tracking
            self.progress_tracker = ProgressTracker(total_members)
            self.progress_tracker.add_callback(self._progress_callback)

            # Ingest with offset loop
            current_offset = int(start_offset)
            processed_count = 0

            while True:
                self.logger.info(f"Fetching members with offset {current_offset}")

                # Get data
                response = self.api_client.get_members(congress, current_offset)

                if not response.results:
                    break

                # Process batch
                batch_processed = self._process_member_batch(response.results)
                processed_count += batch_processed

                # Update progress
                self.progress_tracker.update(batch_processed)

                # Update checkpoint
                next_offset = str(current_offset + len(response.results))
                self.db_ops.update_checkpoint(
                    'congress', 'members', str(congress),
                    next_offset, processed_count
                )

                # Check if we're done
                if current_offset + len(response.results) >= total_members:
                    break

                # Move to next offset
                current_offset += len(response.results)

            return {
                'status': 'completed',
                'total_processed': processed_count,
                'total_expected': total_members,
                'completion_percentage': 100.0
            }

        except Exception as e:
            self.logger.error(f"Members ingestion failed: {e}")
            raise

    def _process_member_batch(self, members_data: List[Dict]) -> int:
        """Process a batch of member data"""
        processed_count = 0

        for member_data in members_data:
            try:
                # Apply data processor if registered
                if 'members' in self.data_processors:
                    member_data = self.data_processors['members'](member_data)

                # Save to database
                self.db_ops.save_member(member_data)
                processed_count += 1

            except Exception as e:
                # Handle error
                error_handled = False
                error_type = type(e).__name__

                if error_type in self.error_handlers:
                    error_handled = self.error_handlers[error_type](e, member_data)

                if not error_handled:
                    self.logger.error(f"Failed to process member: {e}")
                    raise

        return processed_count

    def _progress_callback(self, metrics: ProgressMetrics):
        """Progress callback function"""
        eta = metrics.estimated_remaining_time
        eta_str = str(eta).split('.')[0] if eta else "Unknown"

        self.logger.info(
            f"Members ingestion: {metrics.processed_items}/{metrics.total_items} "
            f"({metrics.completion_percentage:.1f}%) "
            f"ETA: {eta_str}"
        )
```

---

## 🚀 **CLI INTERFACE DESIGN**

### **Main CLI Commands**

```python
# Example: congress-cli/src/congress_cli/cli.py
import click
from typing import Optional
from ..database.migrations import DatabaseBootstrap
from ..ingestion.incremental import IncrementalIngestor
from ..utils.config import Config
from ..utils.logger import setup_logging

@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.option('--config', '-c', help='Configuration file path')
@click.pass_context
def cli(ctx, verbose, config):
    """Congress CLI - Bulk data ingestion tool for Congress.gov"""
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    ctx.obj['config'] = config

    setup_logging(verbose)

@cli.command()
@click.option('--drop-existing', is_flag=True, help='Drop existing tables')
@click.pass_context
def bootstrap(ctx, drop_existing):
    """Bootstrap database with Congress schema"""
    click.echo("🚀 Bootstrapping Congress database...")

    bootstrap = DatabaseBootstrap()
    success = bootstrap.bootstrap_database(drop_existing)

    if success:
        click.echo("✅ Database bootstrap completed successfully")
    else:
        click.echo("❌ Database bootstrap failed")
        ctx.exit(1)

@cli.command()
@click.option('--api-key', help='Congress.gov API key')
@click.option('--congress', default=118, help='Congress number to ingest')
@click.option('--resume', is_flag=True, default=True, help='Resume from checkpoint')
@click.option('--batch-size', default=100, help='Batch size for processing')
@click.pass_context
def ingest_members(ctx, api_key, congress, resume, batch_size):
    """Ingest Congress members data"""
    click.echo(f"🔄 Ingesting Congress {congress} members...")

    if api_key:
        Config.set_api_key(api_key)

    ingestor = IncrementalIngestor()

    try:
        result = ingestor.ingest_members(congress, resume)

        click.echo(f"✅ Members ingestion completed:")
        click.echo(f"   Total processed: {result['total_processed']}")
        click.echo(f"   Total expected: {result['total_expected']}")
        click.echo(f"   Completion: {result['completion_percentage']:.1f}%")

    except Exception as e:
        click.echo(f"❌ Members ingestion failed: {e}")
        ctx.exit(1)

@cli.command()
@click.option('--api-key', help='Congress.gov API key')
@click.option('--congress', default=118, help='Congress number to ingest')
@click.option('--resume', is_flag=True, default=True, help='Resume from checkpoint')
@click.pass_context
def ingest_bills(ctx, api_key, congress, resume):
    """Ingest Congress bills data"""
    click.echo(f"🔄 Ingesting Congress {congress} bills...")

    if api_key:
        Config.set_api_key(api_key)

    ingestor = IncrementalIngestor()

    try:
        result = ingestor.ingest_bills(congress, resume)

        click.echo(f"✅ Bills ingestion completed:")
        click.echo(f"   Total processed: {result['total_processed']}")
        click.echo(f"   Total expected: {result['total_expected']}")
        click.echo(f"   Completion: {result['completion_percentage']:.1f}%")

    except Exception as e:
        click.echo(f"❌ Bills ingestion failed: {e}")
        ctx.exit(1)

@cli.command()
@click.pass_context
def status(ctx):
    """Show ingestion status and checkpoints"""
    click.echo("📊 Ingestion Status:")

    # Implementation for status display
    pass

if __name__ == '__main__':
    cli()
```

---

## 📦 **PACKAGING & DISTRIBUTION**

### **PyPI Package Configuration**

```python
# Example: congress-cli/pyproject.toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "congress-cli"
version = "1.0.0"
description = "CLI tool for bulk data ingestion from Congress.gov"
readme = "README.md"
license = {file = "LICENSE"}
authors = [
    {name = "OpenDiscourse Team", email = "team@opendiscourse.org"}
]
classifiers = [
    "Development Status :: 5 - Production/Stable",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
]
requires-python = ">=3.8"
dependencies = [
    "click>=8.0.0",
    "pydantic>=1.10.0",
    "requests>=2.28.0",
    "psycopg2-binary>=2.9.0",
    "python-dotenv>=0.19.0",
    "rich>=12.0.0",
    "tqdm>=4.64.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "black>=22.0.0",
    "flake8>=5.0.0",
    "mypy>=0.991",
    "pre-commit>=2.20.0",
]

[project.urls]
Homepage = "https://github.com/opendiscourse/congress-cli"
Documentation = "https://congress-cli.readthedocs.io/"
Repository = "https://github.com/opendiscourse/congress-cli.git"
"Bug Tracker" = "https://github.com/opendiscourse/congress-cli/issues"

[project.scripts]
congress-cli = "congress_cli.cli:cli"

[tool.setuptools.packages.find]
where = ["src"]

[tool.setuptools.package-data]
congress_cli = ["migrations/*.sql", "config/*.toml"]
```

---

## 📋 **DEVELOPMENT ROADMAP**

### **Phase 1: Foundation (Week 1-2)**
- ✅ Create package structure for all 3 CLIs
- ✅ Implement Pydantic models for each data source
- ✅ Create API abstraction layer
- ✅ Implement SQL bootstrap system
- ✅ Setup CI/CD pipeline

### **Phase 2: Core Features (Week 3-4)**
- ✅ Implement incremental ingestion engine
- ✅ Add monitoring and progress tracking
- ✅ Create sophisticated error handling
- ✅ Implement CLI interface with Click
- ✅ Add configuration management

### **Phase 3: Advanced Features (Week 5-6)**
- ✅ Add lambda function and delegate support
- ✅ Implement advanced retry logic
- ✅ Add real-time monitoring dashboard
- ✅ Create comprehensive test suite
- ✅ Optimize performance

### **Phase 4: Polish & Release (Week 7-8)**
- ✅ Complete documentation
- ✅ Add examples and tutorials
- ✅ Security audit and hardening
- ✅ Performance testing and optimization
- ✅ Release to PyPI

---

## 🎯 **GITHUB PROJECT MANAGEMENT**

### **Project V2 Setup**

```yaml
# GitHub Project: PyPI CLI Tools Development
title: "PyPI CLI Tools Development"
description: "Development of 3 separate CLI tools for bulk data ingestion"

# Columns:
- Backlog
- In Progress
- Review
- Testing
- Done

# Labels:
- priority:critical
- priority:high
- priority:medium
- priority:low
- type:feature
- type:bug
- type:enhancement
- component:congress-cli
- component:govinfo-cli
- component:openstates-cli
```

### **Issues to Create**

1. **#1: Create package structure for congress-cli**
2. **#2: Implement Pydantic models for Congress API**
3. **#3: Create API abstraction layer for Congress.gov**
4. **#4: Implement SQL bootstrap for Congress schema**
5. **#5: Create incremental ingestion engine**
6. **#6: Add monitoring and progress tracking**
7. **#7: Implement CLI interface with Click**
8. **#8: Add comprehensive testing**
9. **#9: Create documentation and examples**
10. **#10: Release to PyPI**

*(Similar issues for govinfo-cli and openstates-cli)*

---

## 🚀 **NEXT STEPS**

### **Immediate Actions (Today)**
1. **Create GitHub Project V2** for CLI development
2. **Set up package repositories** for all 3 CLIs
3. **Create initial issues** with detailed requirements
4. **Setup CI/CD pipeline** for automated testing
5. **Begin Phase 1 development** with package structure

### **This Week**
1. **Complete package structure** for all 3 CLIs
2. **Implement Pydantic models** for each data source
3. **Create API abstraction layer** with error handling
4. **Implement SQL bootstrap system** with migrations
5. **Setup automated testing pipeline**

### **Next Week**
1. **Implement incremental ingestion** with offset tracking
2. **Add monitoring and progress** tracking system
3. **Create CLI interface** with comprehensive commands
4. **Add configuration management** and validation
5. **Begin integration testing**

---

## 📊 **SUCCESS METRICS**

### **Development Metrics**
- ✅ **3 CLI packages** released to PyPI
- ✅ **100% test coverage** for core functionality
- ✅ **Complete documentation** with examples
- ✅ **CI/CD pipeline** with automated testing
- ✅ **Performance benchmarks** meeting targets

### **Usage Metrics**
- ✅ **1000+ downloads** per month
- ✅ **Active community** with contributions
- ✅ **Positive feedback** from users
- ✅ **Regular updates** and maintenance
- ✅ **Integration examples** and tutorials

---

**🎯 This comprehensive plan will create 3 powerful, production-ready CLI tools that provide complete bulk data ingestion capabilities with sophisticated monitoring, error handling, and database management. Each tool will be a standalone PyPI package with full API abstraction and professional-grade features.**
