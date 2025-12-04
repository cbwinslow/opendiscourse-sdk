"""
Configuration Management System using Pydantic.

This module provides type-safe configuration management for OpenDiscourse CLI tools.
"""

import os
from enum import Enum
from pathlib import Path
from typing import Optional, Dict, Any

from pydantic import BaseModel, Field, validator, SecretStr
from pydantic_settings import BaseSettings


class Environment(str, Enum):
    """Deployment environment."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class LogLevel(str, Enum):
    """Logging levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class ExportFormat(str, Enum):
    """Export format options."""
    JSON = "json"
    JSONL = "jsonl"
    CSV = "csv"
    PARQUET = "parquet"
    SQLITE = "sqlite"


class CompressionType(str, Enum):
    """Compression types."""
    NONE = "none"
    GZIP = "gzip"
    BROTLI = "br"


class DatabaseConfig(BaseModel):
    """PostgreSQL database configuration."""

    host: str = Field(default="localhost", description="Database host")
    port: int = Field(default=5432, description="Database port")
    name: str = Field(default="opendiscourse", description="Database name")
    user: str = Field(default="postgres", description="Database user")
    password: Optional[SecretStr] = Field(default=None, description="Database password")

    # Connection pooling
    min_connections: int = Field(default=1, description="Minimum pool connections")
    max_connections: int = Field(default=10, description="Maximum pool connections")

    # Timeouts
    connection_timeout: int = Field(default=30, description="Connection timeout (seconds)")
    command_timeout: int = Field(default=300, description="Command timeout (seconds)")

    # SSL
    ssl_mode: str = Field(default="prefer", description="SSL mode")

    @validator('port')
    def validate_port(cls, v):
        if not 1 <= v <= 65535:
            raise ValueError('Port must be between 1 and 65535')
        return v

    @property
    def dsn(self) -> str:
        """Get database connection string."""
        parts = [
            f"host={self.host}",
            f"port={self.port}",
            f"dbname={self.name}",
            f"user={self.user}",
        ]
        if self.password:
            parts.append(f"password={self.password.get_secret_value()}")
        if self.ssl_mode:
            parts.append(f"sslmode={self.ssl_mode}")
        return " ".join(parts)

    def dict_safe(self) -> Dict[str, Any]:
        """Get dict without exposing password."""
        data = self.dict()
        if self.password:
            data['password'] = '***REDACTED***'
        return data


class APIConfig(BaseModel):
    """API client configuration."""

    api_key: Optional[SecretStr] = Field(default=None, description="API key")
    base_url: str = Field(..., description="API base URL")
    rate_limit: int = Field(default=10, description="Requests per second")
    max_retries: int = Field(default=3, description="Maximum retry attempts")
    retry_delay: float = Field(default=2.0, description="Base retry delay (seconds)")
    timeout: int = Field(default=30, description="Request timeout (seconds)")

    @validator('rate_limit')
    def validate_rate_limit(cls, v):
        if v < 1:
            raise ValueError('Rate limit must be at least 1')
        return v


class CongressAPIConfig(APIConfig):
    """Congress.gov API configuration."""

    base_url: str = Field(default="https://api.congress.gov/v3", description="Congress API base URL")
    rate_limit: int = Field(default=100, description="Congress API rate limit")


class OpenStatesAPIConfig(APIConfig):
    """OpenStates API configuration."""

    base_url: str = Field(default="https://v3.openstates.org", description="OpenStates API base URL")
    rate_limit: int = Field(default=20, description="OpenStates API rate limit")
    graph_url: str = Field(default="https://v3.openstates.org/graphql", description="GraphQL endpoint")


class GovInfoAPIConfig(APIConfig):
    """GovInfo API configuration."""

    base_url: str = Field(default="https://api.govinfo.gov", description="GovInfo API base URL")
    rate_limit: int = Field(default=50, description="GovInfo API rate limit")


class IngestionConfig(BaseModel):
    """Data ingestion configuration."""

    batch_size: int = Field(default=50, description="Records per batch")
    parallel_workers: int = Field(default=4, description="Number of parallel workers")
    max_retries: int = Field(default=3, description="Maximum retry attempts")
    checkpoint_interval: int = Field(default=100, description="Checkpoint every N records")

    @validator('batch_size')
    def validate_batch_size(cls, v):
        if not 1 <= v <= 1000:
            raise ValueError('Batch size must be between 1 and 1000')
        return v

    @validator('parallel_workers')
    def validate_parallel_workers(cls, v):
        if not 1 <= v <= 50:
            raise ValueError('Parallel workers must be between 1 and 50')
        return v


class ExportConfig(BaseModel):
    """Export configuration."""

    default_format: ExportFormat = Field(default=ExportFormat.JSON, description="Default export format")
    compression: CompressionType = Field(default=CompressionType.NONE, description="Compression type")
    output_dir: Path = Field(default=Path("./exports"), description="Output directory")
    include_metadata: bool = Field(default=True, description="Include metadata in exports")

    @validator('output_dir')
    def create_output_dir(cls, v):
        v.mkdir(parents=True, exist_ok=True)
        return v


class LoggingConfig(BaseModel):
    """Logging configuration."""

    level: LogLevel = Field(default=LogLevel.INFO, description="Log level")
    format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format"
    )
    file: Optional[Path] = Field(default=None, description="Log file path")
    max_bytes: int = Field(default=10_000_000, description="Max log file size (bytes)")
    backup_count: int = Field(default=5, description="Number of backup files")
    json_logs: bool = Field(default=False, description="Use JSON log format")


class Settings(BaseSettings):
    """Main application settings."""

    # Environment
    environment: Environment = Field(default=Environment.DEVELOPMENT, description="Deployment environment")
    debug: bool = Field(default=False, description="Debug mode")

    # Database
    database: DatabaseConfig = Field(default_factory=DatabaseConfig, description="Database configuration")

    # APIs
    congress_api: CongressAPIConfig = Field(default_factory=CongressAPIConfig, description="Congress API config")
    openstates_api: OpenStatesAPIConfig = Field(default_factory=OpenStatesAPIConfig, description="OpenStates API config")
    govinfo_api: GovInfoAPIConfig = Field(default_factory=GovInfoAPIConfig, description="GovInfo API config")

    # Ingestion
    ingestion: IngestionConfig = Field(default_factory=IngestionConfig, description="Ingestion configuration")

    # Export
    export: ExportConfig = Field(default_factory=ExportConfig, description="Export configuration")

    # Logging
    logging: LoggingConfig = Field(default_factory=LoggingConfig, description="Logging configuration")

    # Paths
    migrations_dir: Path = Field(default=Path("./migrations"), description="Migrations directory")
    data_dir: Path = Field(default=Path("./data"), description="Data directory")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_nested_delimiter = "__"
        case_sensitive = False

        # Allow loading from environment variables
        @classmethod
        def parse_env_var(cls, field_name: str, raw_val: str) -> Any:
            # Handle nested config via __ delimiter
            if '__' in field_name:
                return raw_val
            return cls.json_loads(raw_val) if raw_val else None

    @classmethod
    def from_env(cls, env_file: Optional[Path] = None) -> "Settings":
        """Load settings from environment file."""
        if env_file and env_file.exists():
            return cls(_env_file=env_file)
        return cls()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Settings":
        """Load settings from dictionary."""
        return cls(**data)

    def to_dict_safe(self) -> Dict[str, Any]:
        """Export settings without secrets."""
        data = self.dict()
        # Redact API keys
        for api_name in ['congress_api', 'openstates_api', 'govinfo_api']:
            if api_name in data and 'api_key' in data[api_name]:
                data[api_name]['api_key'] = '***REDACTED***'
        # Redact database password
        if 'database' in data:
            data['database'] = self.database.dict_safe()
        return data


# Global settings instance
_settings: Optional[Settings] = None


def get_settings(reload: bool = False, env_file: Optional[Path] = None) -> Settings:
    """
    Get global settings instance.

    Args:
        reload: Force reload settings
        env_file: Custom .env file path

    Returns:
        Settings instance
    """
    global _settings

    if _settings is None or reload:
        _settings = Settings.from_env(env_file)

    return _settings


def update_settings(**kwargs) -> Settings:
    """
    Update global settings.

    Args:
        **kwargs: Settings to update

    Returns:
        Updated settings instance
    """
    global _settings

    current = get_settings().dict()
    current.update(kwargs)
    _settings = Settings.from_dict(current)

    return _settings
