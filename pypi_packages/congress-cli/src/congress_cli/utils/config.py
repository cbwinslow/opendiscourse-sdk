"""
Configuration management for Congress CLI.
"""

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

from dotenv import load_dotenv

from ..models.api_models import APIConfig, DatabaseConfig

# Load environment variables
load_dotenv()


@dataclass
class Config:
    """Main configuration class."""

    database: DatabaseConfig = field(default_factory=lambda: DatabaseConfig(
        host=os.getenv('DB_HOST', 'localhost'),
        port=int(os.getenv('DB_PORT', 5432)),
        database=os.getenv('DB_NAME', 'congress_data'),
        username=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', ''),
        ssl_mode=os.getenv('DB_SSL_MODE', 'prefer')
    ))

    api: APIConfig = field(default_factory=lambda: APIConfig(
        api_key=os.getenv('CONGRESS_API_KEY', ''),
        base_url='https://api.congress.gov/v3',
        timeout_seconds=int(os.getenv('API_TIMEOUT', 30)),
        rate_limit_per_second=int(os.getenv('API_RATE_LIMIT', 10)),
        max_retries=int(os.getenv('API_MAX_RETRIES', 3)),
        retry_backoff_factor=float(os.getenv('API_RETRY_BACKOFF', 2.0))
    ))

    batch_size: int = int(os.getenv('BATCH_SIZE', 100))
    max_workers: int = int(os.getenv('MAX_WORKERS', 4))
    checkpoint_interval: int = int(os.getenv('CHECKPOINT_INTERVAL', 1000))
    enable_monitoring: bool = os.getenv('ENABLE_MONITORING', 'true').lower() == 'true'
    log_level: str = os.getenv('LOG_LEVEL', 'INFO')

    # Runtime properties
    database_url: Optional[str] = None

    def __post_init__(self):
        """Post-initialization setup."""
        if not self.database_url:
            self.database_url = self.database.get_connection_string()

    @classmethod
    def from_file(cls, config_file: str) -> 'Config':
        """Load configuration from JSON file."""
        config_path = Path(config_file)

        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_file}")

        with open(config_path) as f:
            config_data = json.load(f)

        # Parse configuration
        database_config = DatabaseConfig(**config_data.get('database', {}))
        api_config = APIConfig(**config_data.get('api', {}))

        return cls(
            database=database_config,
            api=api_config,
            batch_size=config_data.get('batch_size', 100),
            max_workers=config_data.get('max_workers', 4),
            checkpoint_interval=config_data.get('checkpoint_interval', 1000),
            enable_monitoring=config_data.get('enable_monitoring', True),
            log_level=config_data.get('log_level', 'INFO')
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            'database': self.database.dict(),
            'api': self.api.dict(),
            'batch_size': self.batch_size,
            'max_workers': self.max_workers,
            'checkpoint_interval': self.checkpoint_interval,
            'enable_monitoring': self.enable_monitoring,
            'log_level': self.log_level
        }

    def save_to_file(self, config_file: str):
        """Save configuration to JSON file."""
        config_path = Path(config_file)
        config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(config_path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

    def validate(self) -> Dict[str, Any]:
        """Validate configuration and return validation results."""
        errors = []
        warnings = []

        # Validate database config
        if not self.database.host:
            errors.append("Database host is required")

        if not self.database.database:
            errors.append("Database name is required")

        if not self.database.username:
            errors.append("Database username is required")

        if not self.database.password:
            warnings.append("Database password is not set")

        # Validate API config
        if not self.api.api_key:
            errors.append("Congress API key is required")
        elif self.api.api_key == 'YOUR_CONGRESS_API_KEY':
            errors.append("Please set a real Congress API key")

        # Validate batch size
        if self.batch_size < 1 or self.batch_size > 10000:
            errors.append("Batch size must be between 1 and 10000")

        # Validate max workers
        if self.max_workers < 1 or self.max_workers > 32:
            errors.append("Max workers must be between 1 and 32")

        # Validate log level
        valid_log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if self.log_level.upper() not in valid_log_levels:
            errors.append(f"Log level must be one of: {valid_log_levels}")

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }


def get_config(config_file: Optional[str] = None) -> Config:
    """Get configuration instance."""
    if config_file:
        return Config.from_file(config_file)
    else:
        return Config()


def create_sample_config(output_file: str = "congress-cli-config.json"):
    """Create a sample configuration file."""
    config = Config()
    config.save_to_file(output_file)
    print(f"Sample configuration saved to: {output_file}")


def validate_environment() -> bool:
    """Validate environment variables."""
    required_vars = [
        'CONGRESS_API_KEY',
        'DB_HOST',
        'DB_NAME',
        'DB_USER'
    ]

    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        print(f"Missing required environment variables: {', '.join(missing_vars)}")
        return False

    return True
