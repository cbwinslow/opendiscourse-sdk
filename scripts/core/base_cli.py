"""
Base CLI class with common functionality.

Provides shared features for all OpenDiscourse CLI tools:
- Configuration management
- Database connection handling
- Logging setup
- Error handling
- Progress reporting
"""

import sys
import logging
from typing import Optional, Dict, Any
from pathlib import Path

import psycopg2
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn


# Console for rich output
console = Console()


class BaseCLI:
    """Base class for all CLI tools."""

    def __init__(self, api_name: str):
        """
        Initialize base CLI.

        Args:
            api_name: Name of the API (congress, openstates, govinfo)
        """
        self.api_name = api_name
        self.settings = None
        self.db_conn = None
        self.logger = None

        # Try to load configuration
        self._load_config()

        # Setup logging
        self._setup_logging()

    def _load_config(self):
        """Load configuration from Pydantic settings."""
        try:
            from scripts.core.config import get_settings
            self.settings = get_settings()
            console.print(f"[green]✓[/green] Configuration loaded from .env")
        except ImportError:
            console.print("[yellow]⚠[/yellow] Pydantic not installed, using environment variables")
            self.settings = None
        except Exception as e:
            console.print(f"[yellow]⚠[/yellow] Configuration error: {e}")
            self.settings = None

    def _setup_logging(self):
        """Setup logging configuration."""
        if self.settings and hasattr(self.settings, 'logging'):
            log_config = self.settings.logging
            level = getattr(logging, log_config.level.value)
            format_str = log_config.format
        else:
            import os
            level = getattr(logging, os.getenv('LOG_LEVEL', 'INFO'))
            format_str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

        logging.basicConfig(level=level, format=format_str)
        self.logger = logging.getLogger(f"OpenDiscourse.{self.api_name}")

    def get_database_connection(self) -> psycopg2.extensions.connection:
        """
        Get database connection.

        Returns:
            Database connection
        """
        if self.db_conn and not self.db_conn.closed:
            return self.db_conn

        try:
            if self.settings:
                # Use Pydantic settings
                dsn = self.settings.database.dsn
                self.db_conn = psycopg2.connect(dsn)
            else:
                # Fallback to resource manager
                from scripts.utils.resource_manager import get_connection
                self.db_conn = get_connection()

            self.logger.info("Database connection established")
            return self.db_conn

        except Exception as e:
            console.print(f"[red]✗[/red] Database connection failed: {e}")
            self.logger.error(f"Database connection failed: {e}")
            raise

    def get_api_config(self) -> Dict[str, Any]:
        """
        Get API configuration.

        Returns:
            API configuration dictionary
        """
        if self.settings:
            if self.api_name == 'congress':
                api_config = self.settings.congress_api
            elif self.api_name == 'openstates':
                api_config = self.settings.openstates_api
            elif self.api_name == 'govinfo':
                api_config = self.settings.govinfo_api
            else:
                raise ValueError(f"Unknown API: {self.api_name}")

            return {
                'api_key': api_config.api_key.get_secret_value() if api_config.api_key else None,
                'base_url': api_config.base_url,
                'rate_limit': api_config.rate_limit,
                'max_retries': api_config.max_retries,
                'timeout': api_config.timeout,
            }
        else:
            # Fallback to environment variables
            import os
            from scripts.utils.resource_manager import get_api_key

            return {
                'api_key': get_api_key(self.api_name),
                'base_url': os.getenv(f'{self.api_name.upper()}_API_BASE_URL'),
                'rate_limit': int(os.getenv(f'{self.api_name.upper()}_API_RATE_LIMIT', '10')),
                'max_retries': int(os.getenv('API_MAX_RETRIES', '3')),
                'timeout': int(os.getenv('API_TIMEOUT', '30')),
            }

    def check_database(self, auto_bootstrap: bool = True) -> bool:
        """
        Check if database is set up.

        Args:
            auto_bootstrap: Whether to prompt for bootstrap if not setup

        Returns:
            True if database is ready
        """
        try:
            conn = self.get_database_connection()
            cursor = conn.cursor()

            # Check if schema exists
            cursor.execute(
                "SELECT schema_name FROM information_schema.schemata WHERE schema_name = %s",
                (self.api_name,)
            )

            if not cursor.fetchone():
                console.print(f"[red]✗[/red] Schema '{self.api_name}' not found")

                if auto_bootstrap:
                    console.print("\n[yellow]Database not initialized. Run:[/yellow]")
                    console.print("  [cyan]opendiscourse-bootstrap[/cyan]")

                cursor.close()
                return False

            cursor.close()
            return True

        except Exception as e:
            console.print(f"[red]✗[/red] Database check failed: {e}")

            if auto_bootstrap:
                console.print("\n[yellow]Database connection failed. Please check your configuration:[/yellow]")
                console.print("  1. Ensure PostgreSQL is running")
                console.print("  2. Check .env file database settings")
                console.print("  3. Run: [cyan]opendiscourse-bootstrap[/cyan]")

            return False

    def get_ingestion_config(self) -> Dict[str, Any]:
        """
        Get ingestion configuration.

        Returns:
            Ingestion configuration dictionary
        """
        if self.settings and hasattr(self.settings, 'ingestion'):
            ing_config = self.settings.ingestion
            return {
                'batch_size': ing_config.batch_size,
                'parallel_workers': ing_config.parallel_workers,
                'max_retries': ing_config.max_retries,
                'checkpoint_interval': ing_config.checkpoint_interval,
            }
        else:
            import os
            return {
                'batch_size': int(os.getenv('INGESTION_BATCH_SIZE', '50')),
                'parallel_workers': int(os.getenv('INGESTION_PARALLEL_WORKERS', '4')),
                'max_retries': int(os.getenv('INGESTION_MAX_RETRIES', '3')),
                'checkpoint_interval': int(os.getenv('INGESTION_CHECKPOINT_INTERVAL', '100')),
            }

    def progress_context(self, description: str):
        """
        Create a progress context for long-running operations.

        Args:
            description: Description of the operation

        Returns:
            Progress context manager
        """
        return Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        )

    def cleanup(self):
        """Cleanup resources."""
        if self.db_conn and not self.db_conn.closed:
            self.db_conn.close()
            self.logger.info("Database connection closed")


def verify_prerequisites(api_name: str) -> bool:
    """
    Verify prerequisites for running CLI.

    Args:
        api_name: API name (congress, openstates, govinfo)

    Returns:
        True if prerequisites met
    """
    cli = BaseCLI(api_name)

    # Check API key
    api_config = cli.get_api_config()
    if not api_config.get('api_key'):
        console.print(f"[red]✗[/red] API key for {api_name} not found")
        console.print(f"\n[yellow]Please set {api_name.upper()}_API_KEY in .env file[/yellow]")
        return False

    console.print(f"[green]✓[/green] API key configured")

    # Check database
    if not cli.check_database():
        return False

    console.print(f"[green]✓[/green] Database ready")

    cli.cleanup()
    return True


__all__ = [
    'BaseCLI',
    'console',
    'verify_prerequisites',
]
