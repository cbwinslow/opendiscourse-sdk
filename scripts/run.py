#!/usr/bin/env python3
"""Run the OpenDiscourse application.

This script starts the OpenDiscourse application with the specified settings.
"""

import logging
import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

import uvicorn
from fastapi import FastAPI

from opendiscourse.core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="OpenDiscourse API",
    version="0.1.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint."""
    return {
        "message": "Welcome to OpenDiscourse API",
        "version": "0.1.0",
        "docs": "/docs",
    }


def main() -> None:
    """Run the application."""
    logger.info("Starting OpenDiscourse API...")

    uvicorn.run(
        "scripts.run:app",  # Updated to match this file's location
        port=8080,  # Changed port to 8080 to avoid conflicts
        reload=getattr(settings, "DEBUG", False),  # Safer attribute access
        log_level="info" if not getattr(settings, "DEBUG", False) else "debug",
    )


if __name__ == "__main__":
    main()
