# OpenDiscourse AGENT.md

## Build/Lint/Test Commands
- **Test all**: `pytest tests/`
- **Test single file**: `pytest tests/test_filename.py`
- **Test with coverage**: `pytest --cov=opendiscourse tests/`
- **Lint**: `ruff check .` and `black --check .`
- **Format**: `black opendiscourse/ tests/` and `ruff format .`
- **Type check**: `mypy opendiscourse/`
- **Frontend build**: `npm run build` (in web/ dir)
- **Frontend test**: `npm test` (in web/ dir)

## Architecture
- **FastAPI backend** with PostgreSQL + pgvector for vector search
- **React frontend** (TypeScript) with testing via Jest
- **Key modules**: api/ (FastAPI routes), opendiscourse/ (core Python), web/ (React)
- **Databases**: PostgreSQL with pgvector, Redis, Weaviate/ChromaDB for vectors
- **Core services**: document processing, RAG, semantic search, government data ingestion

## Code Style (from .windsurfrules)
- **Python**: PEP 8, Python 3.10+ type hints, Google-style docstrings
- **Types**: Use `list[Type]`, `X | Y` unions, `Optional[Type]` or `Type | None`
- **Errors**: Custom exception classes, never bare except, structured logging
- **Testing**: pytest, 80%+ coverage, parameterized tests, mock externals
- **Line length**: 88 chars (black config)
- **Imports**: Use ruff/isort, known-first-party = ["opendiscourse"]
