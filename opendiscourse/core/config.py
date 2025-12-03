"""Simplified configuration settings for OpenDiscourse."""

import os
from typing import List


class Settings:
    """Application settings."""

    # Application
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-me-in-production")
    API_V1_STR: str = "/api/v1"

    # Backend
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost",
        "http://localhost:3000",
    ]

    # Database
    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "localhost")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "postgres")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "opendiscourse")

    @property
    def DATABASE_URI(self) -> str:
        """Get database connection string."""
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}/{self.POSTGRES_DB}"
        )

    # API
    API_PREFIX: str = "/api"
    PROJECT_NAME: str = "OpenDiscourse"

    # Security
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    SECURITY_ALGORITHM: str = "HS256"


# Global settings instance
settings = Settings()
