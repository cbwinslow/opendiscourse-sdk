# Changelog

All notable changes to the OpenDiscourse project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- Enhanced document processing workflows
- Advanced entity extraction services
- NVIDIA NIM integration for production RAG
- Enhanced React frontend

## [1.0.1] - 2025-06-26

### Added
- **Core Python Package Structure**: Standardized `opendiscourse/` package with proper module organization
- **Enhanced Configuration Management**: Centralized configuration system with environment-specific settings
- **Database Components**: PostgreSQL integration with pgvector extension for vector search capabilities
- **Document Ingestion Pipeline**: Comprehensive document processing and ingestion workflows
- **Government Data API Integration**: GovInfo API integration with automated scraping capabilities
- **RAG Database Implementation**: Vector database implementation for retrieval-augmented generation
- **Enhanced Entity Extraction**: Improved entity extraction services with better accuracy
- **Development Tools**: Added mypy configuration, development requirements, and setup scripts
- **CI/CD Pipeline**: GitHub Actions workflow for data pipeline automation
- **Documentation**: Enhanced project structure documentation and development guides

### Changed
- **Project Structure**: Major reorganization moving from `src/` to `opendiscourse/` package structure
- **Database Models**: Refactored database models with improved relationships and validation
- **API Architecture**: Enhanced API structure with v1 and v2 endpoints
- **Configuration System**: Moved from simple env files to comprehensive TOML-based configuration
- **Document Processing**: Improved document processing with better error handling and validation
- **Search Functionality**: Enhanced semantic search with vector similarity capabilities
- **Code Quality**: Improved type hints, linting, and code organization throughout the project

### Removed
- **Legacy Node.js Components**: Removed outdated JavaScript services in favor of Python implementation
- **Deprecated Scripts**: Cleaned up old setup scripts and replaced with modern alternatives
- **Unused Dependencies**: Removed unused packages and streamlined requirements
- **Legacy Database Schema**: Replaced old SQL schema with modern Drizzle-based approach
- **Outdated API Endpoints**: Removed legacy API implementations

### Fixed
- **Import Issues**: Resolved circular imports and dependency conflicts
- **Database Connections**: Fixed database session management and connection pooling
- **Configuration Loading**: Improved environment variable handling and configuration validation
- **Document Processing**: Fixed edge cases in document parsing and metadata extraction
- **Vector Search**: Resolved performance issues in similarity search operations
- **Error Handling**: Enhanced error reporting and logging throughout the application

### Security
- **Input Validation**: Added comprehensive input sanitization and validation
- **API Security**: Implemented proper authentication and authorization mechanisms
- **Database Security**: Enhanced database connection security and query parameterization
- **File Processing**: Secured file upload and processing workflows

### Performance
- **Database Queries**: Optimized database queries with proper indexing
- **Vector Operations**: Improved vector search performance with better algorithms
- **Memory Usage**: Reduced memory footprint in document processing
- **API Response Times**: Optimized API endpoints for faster response times

### Migration Notes

This release includes significant structural changes. For existing installations:

1. **Database Migration**: Run database migrations to update schema:
   ```bash
   python -m opendiscourse.db.migrate
   ```

2. **Configuration Update**: Update configuration files to new TOML format:
   ```bash
   cp config/environments/.env.example config/environments/.env
   # Edit with your specific configuration
   ```

3. **Dependencies**: Update Python dependencies:
   ```bash
   pip install -r requirements-dev.txt
   ```

4. **Environment Variables**: Update environment variables according to new configuration schema

### Technical Details

#### Database Changes
- Migrated from SQLAlchemy to Drizzle ORM
- Added pgvector extension for vector similarity search
- Implemented proper foreign key relationships
- Added comprehensive indexing for performance

#### API Changes
- Restructured API endpoints with versioning (v1, v2)
- Implemented proper OpenAPI documentation
- Added comprehensive error handling and validation
- Enhanced authentication and authorization

#### Document Processing
- Implemented multi-format document support (PDF, DOC, TXT, etc.)
- Added automated metadata extraction
- Implemented document versioning and history
- Enhanced search and filtering capabilities

#### Vector Search
- Integrated sentence transformers for embeddings
- Implemented similarity search with configurable thresholds
- Added batch processing for large document collections
- Optimized query performance with proper indexing

### Dependencies Updates

#### Added
- `sentence-transformers` for embeddings generation
- `pgvector` for PostgreSQL vector operations
- `toml` for configuration management
- `mypy` for type checking
- `black` for code formatting

#### Updated
- `fastapi` to latest stable version
- `postgresql` to version 14+
- `python` to 3.13+
- `numpy` and `scipy` for numerical operations

#### Removed
- Legacy Node.js dependencies
- Unused Python packages
- Deprecated database drivers

## [1.0.0] - 2025-05-26

### Added
- Initial project structure
- Basic API endpoints
- Document storage capabilities
- Simple search functionality
- PostgreSQL database integration
- Docker containerization
- Basic documentation

### Changed
- N/A (Initial release)

### Removed
- N/A (Initial release)

---

## Version History

- **v1.0.1** (2025-06-26): Major structural improvements, enhanced data pipeline, RAG implementation
- **v1.0.0** (2025-05-26): Initial release with basic functionality

## Contributing

When contributing to this project, please:

1. Update this changelog with your changes
2. Follow the [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) format
3. Group changes by type (Added, Changed, Deprecated, Removed, Fixed, Security)
4. Include migration notes for breaking changes
5. Reference relevant issue numbers where applicable

## Release Process

1. Update version numbers in `pyproject.toml`
2. Update this changelog with release date
3. Create a git tag with the version number
4. Generate release notes from changelog
5. Deploy to staging for testing
6. Deploy to production after validation

---

**Changelog Maintained By**: Development Team  
**Last Updated**: June 26, 2025  
**Format Version**: 1.0.0

