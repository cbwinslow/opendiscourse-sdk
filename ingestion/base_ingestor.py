"""
Base class for all ingestion scripts
Provides centralized configuration, database connections, and common functionality
"""

import os
import logging
import time
from datetime import datetime
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod

# Import centralized configurations
import sys
import os

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".."))

from config.database import DatabaseManager, get_db_cursor, get_db_connection
from config.api_config import APIManager, get_api_config, APIProvider

logger = logging.getLogger(__name__)


class BaseIngestor(ABC):
    """Base class for all data ingestion scripts"""

    def __init__(self, data_source: str, batch_size: int = 50):
        self.data_source = data_source
        self.batch_size = batch_size
        self.start_time = None
        self.processed_count = 0
        self.error_count = 0

        # Initialize centralized managers
        self.db_manager = DatabaseManager()
        self.api_manager = APIManager()

        # Progress monitoring (optional)
        self.monitor = None
        try:
            from monitoring.delegates import setup_all_delegates

            self.monitor = setup_all_delegates()
        except Exception as e:
            logger.warning(f"Could not initialize progress monitor: {e}")

    def get_db_cursor(self, dict_cursor: bool = False):
        """Get database cursor using centralized config"""
        return get_db_cursor(dict_cursor=dict_cursor)

    def get_db_connection(self):
        """Get database connection using centralized config"""
        return get_db_connection()

    def get_api_config(self, provider: APIProvider):
        """Get API configuration using centralized config"""
        return get_api_config(provider)

    def start_timing(self):
        """Start timing for performance measurement"""
        self.start_time = time.time()
        logger.info(f"Starting {self.data_source} ingestion")

    def log_progress(self, message: str, level: str = "info"):
        """Log progress with timing information"""
        if self.start_time:
            elapsed = time.time() - self.start_time
            rate = self.processed_count / max(elapsed / 60, 0.01) if elapsed > 0 else 0
            logger.log(
                getattr(logging, level.upper()), f"[{elapsed:.1f}s, {rate:.1f}/min] {message}"
            )
        else:
            logger.log(getattr(logging, level.upper()), message)

    def log_error(self, error: Exception, context: str = ""):
        """Log error with context"""
        self.error_count += 1
        logger.error(f"Error in {self.data_source} {context}: {str(error)}")

        # Update progress monitor if available
        if self.monitor:
            try:
                # Try to update progress monitor with error
                if hasattr(self.monitor, "add_progress"):
                    self.monitor.add_progress(0)  # Indicate error
            except Exception as monitor_error:
                logger.warning(f"Could not update progress monitor: {monitor_error}")

    def log_success(self, item_type: str, count: int = 1):
        """Log successful processing"""
        self.processed_count += count
        logger.info(f"Processed {count} {item_type} from {self.data_source}")

        # Update progress monitor if available
        if self.monitor:
            try:
                if hasattr(self.monitor, "add_progress"):
                    self.monitor.add_progress(count)
            except Exception as monitor_error:
                logger.warning(f"Could not update progress monitor: {monitor_error}")

    def get_stats(self) -> Dict[str, Any]:
        """Get ingestion statistics"""
        elapsed = time.time() - self.start_time if self.start_time else 0
        rate = self.processed_count / max(elapsed / 60, 0.01) if elapsed > 0 else 0

        return {
            "data_source": self.data_source,
            "processed_count": self.processed_count,
            "error_count": self.error_count,
            "elapsed_time": elapsed,
            "rate_per_minute": rate,
            "success_rate": (self.processed_count / max(self.processed_count + self.error_count, 1))
            * 100,
        }

    def validate_api_key(self, provider: APIProvider) -> bool:
        """Validate API key is available"""
        try:
            config = self.get_api_config(provider)
            if not config.api_key:
                logger.error(
                    f"API key not found for {provider.value}. Set {config.api_key_env_var} environment variable."
                )
                return False
            return True
        except Exception as e:
            logger.error(f"Error validating API key for {provider.value}: {e}")
            return False

    @abstractmethod
    def ingest(self, **kwargs) -> Dict[str, Any]:
        """Main ingestion method - must be implemented by subclasses"""
        pass

    def cleanup(self):
        """Cleanup resources"""
        try:
            if self.monitor and hasattr(self.monitor, "stop"):
                self.monitor.stop()
        except Exception as e:
            logger.warning(f"Error during cleanup: {e}")


class CongressIngestor(BaseIngestor):
    """Base class for Congress.gov ingestion"""

    def __init__(self, batch_size: int = 50):
        super().__init__("congress.gov", batch_size)

    def validate_congress_api_key(self) -> bool:
        """Validate Congress.gov API key"""
        return self.validate_api_key(APIProvider.CONGRESS_GOV)


class GovInfoIngestor(BaseIngestor):
    """Base class for GovInfo.gov ingestion"""

    def __init__(self, batch_size: int = 50):
        super().__init__("govinfo.gov", batch_size)

    def validate_govinfo_api_key(self) -> bool:
        """Validate GovInfo.gov API key"""
        return self.validate_api_key(APIProvider.GOVINFO)


class OpenStatesIngestor(BaseIngestor):
    """Base class for OpenStates.org ingestion"""

    def __init__(self, batch_size: int = 50):
        super().__init__("openstates.org", batch_size)

    def validate_openstates_api_key(self) -> bool:
        """Validate OpenStates.org API key"""
        return self.validate_api_key(APIProvider.OPENSTATES)


# Utility functions for backward compatibility
def create_ingestion_context(data_source: str, **kwargs) -> Dict[str, Any]:
    """Create standardized ingestion context"""
    return {
        "data_source": data_source,
        "start_time": datetime.utcnow().isoformat(),
        "batch_size": kwargs.get("batch_size", 50),
        "congress": kwargs.get("congress"),
        "session": kwargs.get("session"),
        "chamber": kwargs.get("chamber"),
        **kwargs,
    }


def validate_ingestion_prerequisites(data_sources: List[str]) -> Dict[str, bool]:
    """Validate prerequisites for multiple data sources"""
    results = {}

    # Check database connection
    try:
        db_manager = DatabaseManager()
        test_result = db_manager.test_connection()
        results["database"] = test_result["status"] == "success"
    except Exception as e:
        logger.error(f"Database validation failed: {e}")
        results["database"] = False

    # Check API keys
    api_manager = APIManager()
    api_configs = api_manager.validate_all_configs()

    for source in data_sources:
        if source == "congress.gov":
            results["congress_api"] = api_configs.get("congress.gov", {}).get("status") == "ok"
        elif source == "govinfo.gov":
            results["govinfo_api"] = api_configs.get("govinfo.gov", {}).get("status") == "ok"
        elif source == "openstates.org":
            results["openstates_api"] = api_configs.get("openstates.org", {}).get("status") == "ok"

    return results


if __name__ == "__main__":
    # Test base functionality
    print("Testing Base Ingestor...")

    # Test database connection
    db_test = validate_ingestion_prerequisites(["database"])
    print(f"Database: {'✅' if db_test['database'] else '❌'}")

    # Test API configurations
    api_test = validate_ingestion_prerequisites(["congress.gov", "govinfo.gov", "openstates.org"])
    print(f"Congress API: {'✅' if api_test.get('congress_api') else '❌'}")
    print(f"GovInfo API: {'✅' if api_test.get('govinfo_api') else '❌'}")
    print(f"OpenStates API: {'✅' if api_test.get('openstates_api') else '❌'}")
