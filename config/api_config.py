"""
Centralized API Configuration for OpenDiscourse Ingestion System
Single source of truth for all API keys and endpoint configurations
"""

import os
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class APIProvider(Enum):
    CONGRESS_GOV = "congress.gov"
    GOVINFO = "govinfo.gov"
    OPENSTATES = "openstates.org"
    SUPABASE = "supabase"


@dataclass
class APIConfig:
    """API configuration data class"""

    provider: APIProvider
    base_url: str
    api_key: Optional[str] = None
    api_key_env_var: Optional[str] = None
    rate_limit: int = 100  # requests per minute
    timeout: int = 30  # seconds
    retry_attempts: int = 3
    retry_backoff: float = 1.5
    headers: Optional[Dict[str, str]] = None

    def __post_init__(self):
        if self.headers is None:
            self.headers = {}

        # Load API key from environment if not provided
        if not self.api_key and self.api_key_env_var:
            self.api_key = os.getenv(self.api_key_env_var)

        # Set default headers based on provider
        if self.provider == APIProvider.CONGRESS_GOV:
            self.headers.update({"Accept": "application/json", "X-API-Key": self.api_key or ""})
        elif self.provider == APIProvider.GOVINFO:
            self.headers.update({"Accept": "application/json"})
        elif self.provider == APIProvider.OPENSTATES:
            self.headers.update({"Accept": "application/json", "X-API-Key": self.api_key or ""})


class APIManager:
    """Centralized API configuration manager"""

    _instance: Optional["APIManager"] = None
    _configs: Dict[APIProvider, APIConfig] = {}

    def __new__(cls) -> "APIManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "_initialized"):
            self._load_configs()
            self._initialized = True

    def _load_configs(self) -> None:
        """Load API configurations from environment"""

        # Congress.gov API
        self._configs[APIProvider.CONGRESS_GOV] = APIConfig(
            provider=APIProvider.CONGRESS_GOV,
            base_url="https://api.congress.gov/v3",
            api_key_env_var="CONGRESS_API_KEY",
            rate_limit=100,
            timeout=30,
        )

        # GovInfo.gov API
        self._configs[APIProvider.GOVINFO] = APIConfig(
            provider=APIProvider.GOVINFO,
            base_url="https://api.govinfo.gov",
            api_key_env_var="GOVINFO_API_KEY",
            rate_limit=100,
            timeout=30,
        )

        # OpenStates.org API
        self._configs[APIProvider.OPENSTATES] = APIConfig(
            provider=APIProvider.OPENSTATES,
            base_url="https://v3.openstates.org",
            api_key_env_var="OPENSTATES_API_KEY",
            rate_limit=100,
            timeout=30,
        )

        # Supabase API
        supabase_url = os.getenv("SUPABASE_URL")
        if supabase_url:
            self._configs[APIProvider.SUPABASE] = APIConfig(
                provider=APIProvider.SUPABASE,
                base_url=supabase_url,
                api_key_env_var="SUPABASE_SERVICE_ROLE_KEY",
                rate_limit=1000,
                timeout=60,
            )

    def get_config(self, provider: APIProvider) -> APIConfig:
        """Get API configuration for a provider"""
        if provider not in self._configs:
            raise ValueError(f"No configuration found for provider: {provider}")

        config = self._configs[provider]

        # Validate API key for providers that require it
        if provider in [APIProvider.CONGRESS_GOV, APIProvider.GOVINFO, APIProvider.OPENSTATES]:
            if not config.api_key:
                logger.warning(
                    f"API key not found for {provider.value}. Set {config.api_key_env_var} environment variable."
                )
            else:
                logger.info(f"API key loaded for {provider.value}")

        return config

    def validate_all_configs(self) -> Dict[str, Any]:
        """Validate all API configurations"""
        results = {}

        for provider, config in self._configs.items():
            provider_name = provider.value
            result = {
                "provider": provider_name,
                "base_url": config.base_url,
                "api_key_set": bool(config.api_key),
                "api_key_env_var": config.api_key_env_var,
                "rate_limit": config.rate_limit,
                "timeout": config.timeout,
            }

            # Check if API key is required but missing
            if provider in [APIProvider.CONGRESS_GOV, APIProvider.GOVINFO, APIProvider.OPENSTATES]:
                if not config.api_key:
                    result["status"] = "error"
                    result["error"] = (
                        f"API key required but not found. Set {config.api_key_env_var} environment variable."
                    )
                else:
                    result["status"] = "ok"
            else:
                result["status"] = "ok"

            results[provider_name] = result

        return results

    def get_headers(self, provider: APIProvider) -> Dict[str, str]:
        """Get headers for API request"""
        config = self.get_config(provider)
        return config.headers.copy() if config.headers else {}

    def get_base_url(self, provider: APIProvider) -> str:
        """Get base URL for API"""
        config = self.get_config(provider)
        return config.base_url

    def get_api_key(self, provider: APIProvider) -> Optional[str]:
        """Get API key for provider"""
        config = self.get_config(provider)
        return config.api_key


# Global instance
api_manager = APIManager()


# Convenience functions
def get_api_config(provider: APIProvider) -> APIConfig:
    """Get API configuration for a provider"""
    return api_manager.get_config(provider)


def get_api_headers(provider: APIProvider) -> Dict[str, str]:
    """Get headers for API request"""
    return api_manager.get_headers(provider)


def get_api_base_url(provider: APIProvider) -> str:
    """Get base URL for API"""
    return api_manager.get_base_url(provider)


def get_api_key(provider: APIProvider) -> Optional[str]:
    """Get API key for provider"""
    return api_manager.get_api_key(provider)


def validate_api_configs() -> Dict[str, Any]:
    """Validate all API configurations"""
    return api_manager.validate_all_configs()


# Provider-specific convenience functions
def get_congress_config() -> APIConfig:
    """Get Congress.gov API configuration"""
    return get_api_config(APIProvider.CONGRESS_GOV)


def get_govinfo_config() -> APIConfig:
    """Get GovInfo.gov API configuration"""
    return get_api_config(APIProvider.GOVINFO)


def get_openstates_config() -> APIConfig:
    """Get OpenStates.org API configuration"""
    return get_api_config(APIProvider.OPENSTATES)


def get_supabase_config() -> APIConfig:
    """Get Supabase API configuration"""
    return get_api_config(APIProvider.SUPABASE)


# Legacy compatibility variables and functions
GOVINFO_API_KEY = get_api_key(APIProvider.GOVINFO) or "YOUR_API_KEY_HERE"
GOVINFO_BASE_URL = get_api_base_url(APIProvider.GOVINFO)
GOVINFO_HEADERS = get_api_headers(APIProvider.GOVINFO)

# Legacy aliases for backward compatibility
BASE_URL = GOVINFO_BASE_URL
HEADERS = GOVINFO_HEADERS
COLLECTIONS_URL = f"{GOVINFO_BASE_URL}/collections"

# Congress.gov API Configuration (legacy)
CONGRESS_API_KEY = get_api_key(APIProvider.CONGRESS_GOV) or ""
CONGRESS_BASE_URL = get_api_base_url(APIProvider.CONGRESS_GOV)
CONGRESS_HEADERS = get_api_headers(APIProvider.CONGRESS_GOV)

# OpenStates API Configuration (legacy)
OPENSTATES_API_KEY = get_api_key(APIProvider.OPENSTATES) or ""
OPENSTATES_BASE_URL = get_api_base_url(APIProvider.OPENSTATES)
OPENSTATES_HEADERS = get_api_headers(APIProvider.OPENSTATES)

# Bulk Data Configuration
BULK_DATA_CONFIG = {
    "rate_limit_delay": 0.5,  # seconds between requests
    "timeout": 30,
    "retry_attempts": 3,
    "data_dir": "data/bulk_ingestion",
}

# Ollama Configuration
OLLAMA_CONFIG = {
    "base_url": "http://localhost:11434",
    "default_model": "llama2",
    "timeout": 300,
    "max_retries": 3,
}

# MCP Server Configuration
MCP_SERVER = "http://localhost:8080"


# Legacy compatibility functions
def get_congress_api_key() -> Optional[str]:
    """Get Congress.gov API key (legacy compatibility)"""
    return get_api_key(APIProvider.CONGRESS_GOV)


def get_govinfo_api_key() -> Optional[str]:
    """Get GovInfo.gov API key (legacy compatibility)"""
    return get_api_key(APIProvider.GOVINFO)


def get_openstates_api_key() -> Optional[str]:
    """Get OpenStates.org API key (legacy compatibility)"""
    return get_api_key(APIProvider.OPENSTATES)


if __name__ == "__main__":
    # Test API configuration
    logging.basicConfig(level=logging.INFO)

    print("Testing API configuration...")
    results = validate_api_configs()

    for provider, result in results.items():
        if result["status"] == "ok":
            print(f"✅ {provider}: Configuration valid")
            print(f"   URL: {result['base_url']}")
            print(f"   API Key: {'Set' if result['api_key_set'] else 'Not set'}")
        else:
            print(f"❌ {provider}: {result['error']}")
            print(f"   Environment variable: {result['api_key_env_var']}")
        print()
