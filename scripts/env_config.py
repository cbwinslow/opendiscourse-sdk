#!/usr/bin/env python3
"""
Environment configuration loader for OpenDiscourse project
Automatically loads .env file and provides configuration utilities
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any

def load_env_file(env_file_path: str = ".env") -> Dict[str, str]:
    """
    Load environment variables from .env file

    Args:
        env_file_path: Path to .env file relative to project root

    Returns:
        Dictionary of loaded environment variables
    """
    env_vars = {}

    # Find .env file (check current directory and parent directories)
    project_root = Path(__file__).parent.parent
    env_file = project_root / env_file_path

    if not env_file.exists():
        # Try current directory
        env_file = Path(env_file_path)

    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()

                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue

                # Parse key=value pairs
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()

                    # Remove quotes if present
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]

                    env_vars[key] = value
                    os.environ[key] = value

    return env_vars

def get_required_env_var(key: str) -> str:
    """
    Get required environment variable, raise error if missing

    Args:
        key: Environment variable name

    Returns:
        Environment variable value

    Raises:
        ValueError: If environment variable is not set
    """
    value = os.getenv(key)
    if not value:
        raise ValueError(f"Required environment variable {key} is not set")
    return value

def get_optional_env_var(key: str, default: Optional[str] = None) -> Optional[str]:
    """
    Get optional environment variable with default value

    Args:
        key: Environment variable name
        default: Default value if not set

    Returns:
        Environment variable value or default
    """
    return os.getenv(key, default)

def validate_api_keys() -> Dict[str, bool]:
    """
    Validate that required API keys are present

    Returns:
        Dictionary mapping API names to availability status
    """
    api_keys = {
        'congress.gov': bool(get_optional_env_var('CONGRESS_API_KEY')),
        'openstates.org': bool(get_optional_env_var('OPENSTATES_API_KEY')),
        'govinfo.gov': bool(get_optional_env_var('GOVINFO_API_KEY'))
    }

    return api_keys

def get_database_config() -> Dict[str, str]:
    """
    Get database configuration from environment variables

    Returns:
        Database configuration dictionary
    """
    return {
        'database': get_optional_env_var('DB_NAME', 'cbwinslow'),
        'user': get_optional_env_var('DB_USER', 'cbwinslow'),
        'password': get_optional_env_var('DB_PASSWORD', ''),
        'host': get_optional_env_var('DB_HOST', ''),
        'port': get_optional_env_var('DB_PORT', '5432')
    }

# Auto-load environment variables when module is imported
_env_vars = load_env_file()

# Export validation functions
__all__ = [
    'load_env_file',
    'get_required_env_var',
    'get_optional_env_var',
    'validate_api_keys',
    'get_database_config'
]
