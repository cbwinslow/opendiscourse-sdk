# 🚀 GitHub Project V2 Setup for PyPI CLI Tools

## 📋 **PROJECT CREATION**

### **Main Project: PyPI CLI Tools Development**
```yaml
title: "PyPI CLI Tools Development"
description: "Development of 3 separate CLI tools for bulk data ingestion from Congress.gov, GovInfo.gov, and OpenStates.org"
visibility: "public"
template: "basic"
```

### **Project Columns**
```yaml
columns:
  - name: "Backlog"
    id: "backlog"
  - name: "In Progress"
    id: "in_progress"
  - name: "Review"
    id: "review"
  - name: "Testing"
    id: "testing"
  - name: "Done"
    id: "done"
```

### **Project Labels**
```yaml
labels:
  - name: "priority:critical"
    color: "d73a4a"
    description: "Critical priority issues"
  - name: "priority:high"
    color: "fbca04"
    description: "High priority issues"
  - name: "priority:medium"
    color: "0075ca"
    description: "Medium priority issues"
  - name: "priority:low"
    color: "7057ff"
    description: "Low priority issues"
  - name: "type:feature"
    color: "84b6eb"
    description: "New feature requests"
  - name: "type:bug"
    color: "d73a4a"
    description: "Bug reports"
  - name: "type:enhancement"
    color: "a2eeef"
    description: "Enhancement requests"
  - name: "type:documentation"
    color: "0075ca"
    description: "Documentation issues"
  - name: "component:congress-cli"
    color: "f9d0c4"
    description: "Congress CLI component"
  - name: "component:govinfo-cli"
    color: "c2e0c6"
    description: "GovInfo CLI component"
  - name: "component:openstates-cli"
    color: "bfdadc"
    description: "OpenStates CLI component"
  - name: "status:ready"
    color: "2ea043"
    description: "Ready to work on"
  - name: "status:blocked"
    color: "d73a4a"
    description: "Blocked by dependencies"
```

---

## 🎯 **ISSUES TO CREATE**

### **Phase 1: Foundation Issues**

#### **#1: Create package structure for congress-cli**
```yaml
title: "Create package structure for congress-cli"
body: |
  ## Description
  Create the complete package structure for congress-cli with all necessary directories and files.

  ## Tasks
  - [ ] Create src/congress_cli package directory
  - [ ] Setup pyproject.toml with dependencies
  - [ ] Create __init__.py with package metadata
  - [ ] Setup models/ directory for Pydantic models
  - [ ] Setup api/ directory for API client
  - [ ] Setup database/ directory for migrations
  - [ ] Setup ingestion/ directory for ingestion logic
  - [ ] Setup monitoring/ directory for progress tracking
  - [ ] Setup utils/ directory for utilities
  - [ ] Create CLI entry point
  - [ ] Setup basic tests directory

  ## Requirements
  - Follow Python packaging best practices
  - Include all required dependencies (click, pydantic, requests, psycopg2, etc.)
  - Setup proper package metadata
  - Include development dependencies for testing

  ## Acceptance Criteria
  - Package can be installed with `pip install -e .`
  - Basic CLI interface works
  - All imports work correctly
  - Tests can be run with pytest

  ## Labels
  component:congress-cli, type:feature, priority:high, status:ready
```

#### **#2: Implement Pydantic models for Congress API**
```yaml
title: "Implement Pydantic models for Congress API"
body: |
  ## Description
  Create comprehensive Pydantic models for Congress.gov API responses with validation.

  ## Tasks
  - [ ] Create CongressMember model with validation
  - [ ] Create CongressBill model with validation
  - [ ] Create APIResponse model for pagination
  - [ ] Create MemberResponse and BillResponse models
  - [ ] Create DatabaseConfig, APIConfig, IngestionConfig models
  - [ ] Add proper validators for all fields
  - [ ] Add JSON serialization support
  - [ ] Create type aliases for better readability

  ## Requirements
  - Use Pydantic v1.10+ features
  - Include comprehensive field validation
  - Add proper error messages
  - Support JSON serialization
  - Include enum types for constrained values

  ## Acceptance Criteria
  - All models validate correctly
  - API responses can be parsed without errors
  - Validation errors are descriptive
  - Models can be serialized to JSON
  - Type hints are comprehensive

  ## Labels
  component:congress-cli, type:feature, priority:high, status:ready
```

#### **#3: Create API abstraction layer for Congress.gov**
```yaml
title: "Create API abstraction layer for Congress.gov"
body: |
  ## Description
  Implement a sophisticated API client with rate limiting, retry logic, and error handling.

  ## Tasks
  - [ ] Create CongressAPIClient class
  - [ ] Implement rate limiting with RateLimiter class
  - [ ] Implement retry logic with RetryStrategy class
  - [ ] Add comprehensive error handling
  - [ ] Create methods for all API endpoints
  - [ ] Add request/response logging
  - [ ] Implement batch processing with BatchProcessor
  - [ ] Add API statistics tracking
  - [ ] Add connection testing functionality

  ## Requirements
  - Use requests library with session management
  - Implement exponential backoff for retries
  - Handle rate limiting gracefully
  - Provide comprehensive error messages
  - Support custom retry conditions and callbacks
  - Track API usage statistics

  ## Acceptance Criteria
  - All API endpoints work correctly
  - Rate limiting respects API limits
  - Retry logic handles transient errors
  - Error messages are descriptive
  - Statistics tracking works
  - Connection testing passes

  ## Labels
  component:congress-cli, type:feature, priority:high, status:ready
```

#### **#4: Implement SQL bootstrap for Congress schema**
```yaml
title: "Implement SQL bootstrap for Congress schema"
body: |
  ## Description
  Create database migration system for Congress CLI with comprehensive schema.

  ## Tasks
  - [ ] Create DatabaseBootstrap class
  - [ ] Write SQL migration files for all tables
  - [ ] Create congress.members table
  - [ ] Create congress.bills table
  - [ ] Create relationship tables (bill_cosponsors, bill_committees)
  - [ ] Create incremental tracking tables
  - [ ] Create proper indexes for performance
  - [ ] Add database functions and triggers
  - [ ] Implement migration status tracking
  - [ ] Add database backup functionality

  ## Requirements
  - Use PostgreSQL with psycopg2
  - Support schema creation and updates
  - Include proper foreign key constraints
  - Add comprehensive indexes
  - Support incremental ingestion tracking
  - Include data quality metrics

  ## Acceptance Criteria
  - Database can be bootstrapped successfully
  - All tables are created with proper constraints
  - Indexes improve query performance
  - Migration status can be tracked
  - Backup functionality works
  - Database connections can be tested

  ## Labels
  component:congress-cli, type:feature, priority:high, status:ready
```

#### **#5: Create incremental ingestion engine**
```yaml
title: "Create incremental ingestion engine"
body: |
  ## Description
  Implement sophisticated incremental ingestion with offset tracking and progress monitoring.

  ## Tasks
  - [ ] Create IncrementalIngestor class
  - [ ] Implement offset management with OffsetManager
  - [ ] Add checkpoint tracking and persistence
  - [ ] Create progress tracking with ProgressTracker
  - [ ] Implement batch processing with error handling
  - [ ] Add resume functionality from checkpoints
  - [ ] Create delegate functions for custom processing
  - [ ] Add comprehensive logging and metrics
  - [ ] Implement data transformation pipeline
  - [ ] Add data validation and quality checks

  ## Requirements
  - Support resume from checkpoints
  - Track progress with ETA calculations
  - Handle errors gracefully with retry logic
  - Support custom data processors
  - Provide comprehensive metrics
  - Maintain data quality standards

  ## Acceptance Criteria
  - Ingestion can be resumed from checkpoints
  - Progress tracking is accurate
  - Error handling is robust
  - Custom processors work correctly
  - Metrics are comprehensive
  - Data quality is maintained

  ## Labels
  component:congress-cli, type:feature, priority:high, status:ready
```

#### **#6: Add monitoring and progress tracking**
```yaml
title: "Add monitoring and progress tracking"
body: |
  ## Description
  Implement comprehensive monitoring and progress tracking system.

  ## Tasks
  - [ ] Create ProgressTracker class with metrics
  - [ ] Implement real-time progress callbacks
  - [ ] Add ETA calculations and rate tracking
  - [ ] Create monitoring dashboard components
  - [ ] Add performance metrics collection
  - [ ] Implement alert system for errors
  - [ ] Create log aggregation and analysis
  - [ ] Add database performance monitoring
  - [ ] Create ingestion quality metrics
  - [ ] Add resource usage tracking

  ## Requirements
  - Real-time progress updates
  - Accurate ETA calculations
  - Comprehensive performance metrics
  - Alert system for critical errors
  - Log analysis capabilities
  - Resource usage monitoring

  ## Acceptance Criteria
  - Progress tracking is accurate and real-time
  - ETA calculations are reliable
  - Performance metrics are comprehensive
  - Alerts trigger appropriately
  - Log analysis works correctly
  - Resource monitoring is functional

  ## Labels
  component:congress-cli, type:feature, priority:medium, status:ready
```

#### **#7: Implement CLI interface with Click**
```yaml
title: "Implement CLI interface with Click"
body: |
  ## Description
  Create comprehensive CLI interface using Click framework with rich output.

  ## Tasks
  - [ ] Create main CLI group with Click
  - [ ] Implement bootstrap command
  - [ ] Add ingest-members command with progress
  - [ ] Add ingest-bills command with progress
  - [ ] Create status command for checkpoints
  - [ ] Add info command for system info
  - [ ] Implement report command
  - [ ] Add test-connection command
  - [ ] Create version command
  - [ ] Add rich console output with colors

  ## Requirements
  - Use Click framework for CLI
  - Rich console output with progress bars
  - Comprehensive help documentation
  - Proper error handling and messages
  - Support for configuration files
  - Verbose and quiet modes

  ## Acceptance Criteria
  - All commands work correctly
  - Help documentation is comprehensive
  - Rich output is user-friendly
  - Error messages are helpful
  - Configuration loading works
  - Progress bars are accurate

  ## Labels
  component:congress-cli, type:feature, priority:high, status:ready
```

#### **#8: Add comprehensive testing**
```yaml
title: "Add comprehensive testing"
body: |
  ## Description
  Create comprehensive test suite with high coverage for all components.

  ## Tasks
  - [ ] Create unit tests for Pydantic models
  - [ ] Add tests for API client functionality
  - [ ] Test database migrations and operations
  - [ ] Create tests for ingestion engine
  - [ ] Add integration tests for CLI commands
  - [ ] Create performance tests
  - [ ] Add error handling tests
  - [ ] Create mock API responses for testing
  - [ ] Add end-to-end tests
  - [ ] Setup CI/CD pipeline with testing

  ## Requirements
  - Use pytest framework
  - Achieve >90% test coverage
  - Include unit and integration tests
  - Mock external dependencies
  - Performance benchmarking
  - Automated CI/CD testing

  ## Acceptance Criteria
  - Test coverage >90%
  - All tests pass consistently
  - CI/CD pipeline works
  - Performance tests meet benchmarks
  - Mock testing is comprehensive
  - Error scenarios are tested

  ## Labels
  component:congress-cli, type:feature, priority:medium, status:ready
```

#### **#9: Create documentation and examples**
```yaml
title: "Create documentation and examples"
body: |
  ## Description
  Create comprehensive documentation with examples and tutorials.

  ## Tasks
  - [ ] Create comprehensive README.md
  - [ ] Write installation guide
  - [ ] Create quick start tutorial
  - [ ] Add configuration guide
  - [ ] Create API documentation
  - [ ] Write troubleshooting guide
  - [ ] Add examples and use cases
  - [ ] Create development guide
  - [ ] Add changelog and version notes
  - [ ] Setup documentation website

  ## Requirements
  - Comprehensive README
  - Step-by-step tutorials
  - Configuration examples
  - API reference documentation
  - Troubleshooting guide
  - Development setup guide

  ## Acceptance Criteria
  - Documentation is comprehensive
  - Examples work correctly
  - Installation guide is clear
  - API documentation is complete
  - Troubleshooting covers common issues
  - Development guide is helpful

  ## Labels
  component:congress-cli, type:documentation, priority:medium, status:ready
```

#### **#10: Release to PyPI**
```yaml
title: "Release to PyPI"
body: |
  ## Description
  Prepare and release congress-cli to PyPI with proper packaging and distribution.

  ## Tasks
  - [ ] Finalize package configuration
  - [ ] Create distribution packages
  - [ ] Test package installation
  - [ ] Create PyPI account and setup
  - [ ] Upload to test PyPI first
  - [ ] Validate test installation
  - [ ] Upload to production PyPI
  - [ ] Create GitHub release
  - [ ] Update documentation with installation instructions
  - [ ] Announce release

  ## Requirements
  - Proper package metadata
  - Test PyPI validation
  - Production PyPI upload
  - GitHub release
  - Updated documentation

  ## Acceptance Criteria
  - Package installs correctly from PyPI
  - All CLI commands work
  - Documentation is updated
  - GitHub release is created
  - Installation instructions are clear

  ## Labels
  component:congress-cli, type:feature, priority:high, status:ready
```

---

## 🔄 **SIMILAR ISSUES FOR OTHER CLIs**

### **GovInfo CLI Issues**
- #11-20: Same structure as #1-10 but for govinfo-cli
- Focus on collection-based ingestion and granule processing
- Different API endpoints and data models

### **OpenStates CLI Issues**
- #21-30: Same structure as #1-10 but for openstates-cli
- Focus on state-based processing and people/bills data
- Different API structure and pagination

---

## 📊 **PROJECT AUTOMATION**

### **GitHub Actions Workflow**
```yaml
name: "PyPI CLI Tools CI/CD"
on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, "3.10", "3.11"]
        package: [congress-cli, govinfo-cli, openstates-cli]

    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: |
          cd pypi_packages/${{ matrix.package }}
          pip install -e ".[dev]"

      - name: Run tests
        run: |
          cd pypi_packages/${{ matrix.package }}
          pytest --cov=${{ matrix.package.replace('-', '_') }} --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml

  build:
    needs: test
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'

    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.10"

      - name: Build packages
        run: |
          for package in congress-cli govinfo-cli openstates-cli; do
            cd pypi_packages/$package
            python -m build
          done

      - name: Upload to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1
        with:
          password: ${{ secrets.PYPI_API_TOKEN }}
          packages-dir: pypi_packages/*/dist/
```

---

## 🎯 **MILESTONES**

### **Milestone 1: Congress CLI Foundation (Week 1-2)**
- Issues #1-5 completed
- Basic package structure and models
- API client and database bootstrap
- Incremental ingestion engine

### **Milestone 2: Congress CLI Polish (Week 3-4)**
- Issues #6-10 completed
- Monitoring and CLI interface
- Testing and documentation
- PyPI release

### **Milestone 3: GovInfo CLI (Week 5-6)**
- Issues #11-20 completed
- Complete GovInfo CLI implementation
- Testing and release

### **Milestone 4: OpenStates CLI (Week 7-8)**
- Issues #21-30 completed
- Complete OpenStates CLI implementation
- Testing and release

---

## 📈 **SUCCESS METRICS**

### **Development Metrics**
- ✅ All 30 issues completed
- ✅ 3 CLI packages released to PyPI
- ✅ >90% test coverage
- ✅ Complete documentation
- ✅ CI/CD pipeline working

### **Quality Metrics**
- ✅ Zero critical bugs
- ✅ Performance benchmarks met
- ✅ User feedback positive
- ✅ Installation success rate >95%
- ✅ Regular maintenance updates

---

**🚀 This comprehensive GitHub project setup will ensure organized development of all 3 CLI tools with proper issue tracking, automation, and quality assurance.**
