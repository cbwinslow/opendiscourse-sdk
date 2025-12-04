"""Core modules for OpenDiscourse."""

from scripts.core.config import (
    Settings,
    DatabaseConfig,
    APIConfig,
    Settings,
    get_settings,
)

# Database
from scripts.core.database import (
    DatabaseBootstrap,
    bootstrap_interactive,
)

# Deduplication
from scripts.core.deduplication import (
    DeduplicationEngine,
    DeduplicationStrategy,
    Fingerprint,
)

# Database Adapters
from scripts.core.database_adapter import (
    DatabaseBackend,
    DatabaseAdapter,
    PostgreSQLAdapter,
    MySQLAdapter,
    SQLiteAdapter,
    AdapterFactory,
)

# Worker Pool
from scripts.core.worker_pool import (
    WorkerPool,
    Job,
    JobResult,
    WorkerStatus,
    JobStatus,
)

# Feature Flags
from scripts.core.feature_flags import (
    FeatureFlag,
    FeatureFlagManager,
    flags,
    feature_flag,
)

# Advanced Decorators
from scripts.core.advanced_decorators import (
    cache,
    validate_params,
    measure_performance,
    conditional,
    rate_limit,
    memoize,
)

# Output Formatters
from scripts.core.output_formatters import (
    OutputFormat,
    Formatter,
    JSONFormatter,
    JSONLFormatter,
    CSVFormatter,
    ParquetFormatter,
    SQLiteFormatter,
    FormatterFactory,
)


__all__ = [
    "APIConfig",
    "CongressAPIConfig",
    "OpenStatesAPIConfig",
    "GovInfoAPIConfig",
    "IngestionConfig",
    "ExportConfig",
    "LoggingConfig",

    # Database
    "DatabaseBootstrap",
    "bootstrap_interactive",
]
