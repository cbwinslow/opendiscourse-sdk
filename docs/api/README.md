# API Documentation

This directory contains API documentation for OpenDiscourse.

## Contents

- **OpenAPI Schema**: Automatically generated API documentation (see [openapi.json](openapi.json))
- **Endpoints**: Detailed documentation for each API endpoint
- **Authentication**: API authentication and authorization guide
- **Examples**: Usage examples and sample requests/responses

## Accessing API Documentation

When running the development server, API documentation is available at:
- Interactive docs: `/docs`
- ReDoc: `/redoc`
- OpenAPI JSON: `/openapi.json`

To regenerate the schema file locally, run:
```bash
PYTHONPATH=. python scripts/generate_openapi.py
```