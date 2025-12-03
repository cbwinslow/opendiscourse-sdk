"""Configuration settings for OpenDiscourse.

This module handles the loading and validation of application settings
from environment variables and configuration files.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseSettings


class Settings(BaseSettings):
    """Application settings.

    Loads settings from environment variables with the prefix 'OPENDISCOURSE_'.
    """
        case_sensitive=True,
        env_file='.env',
        env_file_encoding='utf-8'
    )

    # Application
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    SECRET_KEY: str = "change-me-in-production"
    API_V1_STR: str = "/api/v1"

    # Backend
    BACKEND_CORS_ORIGINS: List[Union[str, AnyHttpUrl]] = [
        "http://localhost",
        "http://localhost:3000",  # Frontend default port
    ]

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        """Parse CORS origins."""
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # Database
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "opendiscourse"
    DATABASE_URI: Optional[PostgresDsn] = None

    @validator("DATABASE_URI", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        """Assemble the database connection string."""
        if isinstance(v, str):
            return v
        # Compose the connection string manually for Pydantic v2+
        user = values.get("POSTGRES_USER")
        password = values.get("POSTGRES_PASSWORD")
        host = values.get("POSTGRES_SERVER")
        db = values.get("POSTGRES_DB")
        return f"postgresql://{user}:{password}@{host}/{db}"

    # API
    API_PREFIX: str = "/api"
    PROJECT_NAME: str = "OpenDiscourse"

    # Security
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    SECURITY_ALGORITHM: str = "HS256"


# Global settings instance
settings = Settings()
