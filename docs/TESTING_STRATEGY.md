t # OpenDiscourse Testing Strategy and Best Practices

## Overview

This document outlines the comprehensive testing strategy for the OpenDiscourse project, covering unit tests, integration tests, performance tests, and end-to-end testing across Python (backend) and JavaScript/TypeScript (frontend) components.

## Table of Contents

1. [Testing Philosophy](#testing-philosophy)
2. [Test Structure](#test-structure)
3. [Testing Frameworks](#testing-frameworks)
4. [Test Categories](#test-categories)
5. [Running Tests](#running-tests)
6. [Best Practices](#best-practices)
7. [CI/CD Integration](#cicd-integration)
8. [Coverage Goals](#coverage-goals)

## Testing Philosophy

Our testing approach follows the "Testing Pyramid" principle:

- **70% Unit Tests**: Fast, isolated tests for individual components
- **20% Integration Tests**: Tests for component interactions
- **10% End-to-End Tests**: Full workflow validation

### Core Principles

1. **Test Early, Test Often**: Tests are written alongside code development
2. **Fast Feedback**: Unit tests run in milliseconds, integration tests in seconds
3. **Reliable and Deterministic**: Tests produce consistent results
4. **Maintainable**: Tests are readable and easy to maintain
5. **Comprehensive Coverage**: Critical paths are thoroughly tested

## Test Structure

### Directory Organization

```
tests/
├── unit/                    # Unit tests for individual components
│   ├── test_database_adapter.py
│   ├── test_api_client.py
│   └── test_utils.py
├── integration/            # Integration tests
│   ├── test_ingestion.py
│   ├── test_api_endpoints.py
│   └── test_database.py
├── e2e/                    # End-to-end tests
│   ├── test_ingestion_workflow.py
│   └── test_search_functionality.py
├── performance/            # Performance and load tests
│   ├── test_performance.py
│   ├── test_load.py
│   └── test_benchmarks.py
├── bulk_ingestion/         # Specialized bulk ingestion tests
│   ├── test_data_transformation.py
│   ├── test_error_handling.py
│   └── test_performance.py
└── utils/                  # Test utilities and helpers
    ├── test_helpers.py
    └── mock_data.py
```

### Test File Naming Convention

- **Unit Tests**: `test_<component>.py`
- **Integration Tests**: `test_<feature>_integration.py`
- **Performance Tests**: `test_<component>_performance.py`
- **E2E Tests**: `test_<workflow>_e2e.py`

## Testing Frameworks

### Python Stack

| Framework | Purpose | Usage |
|-----------|---------|-------|
| **pytest** | Main testing framework | `pytest tests/unit/` |
| **unittest** | Standard library testing | Legacy compatibility |
| **pytest-cov** | Coverage reporting | `--cov=scripts` |
| **pytest-asyncio** | Async testing support | `@pytest.mark.asyncio` |
| **pytest-mock** | Mocking utilities | `pytest-mock` |
| **factory-boy** | Test data generation | Factories |

### JavaScript/TypeScript Stack

| Framework | Purpose | Usage |
|-----------|---------|-------|
| **Jest** | Main testing framework | `npm test` |
| **React Testing Library** | Component testing | `@testing-library/react` |
| **Jest DOM** | DOM matchers | `@testing-library/jest-dom` |
| **MSW** | API mocking | Mock Service Worker |
| **Playwright** | E2E testing | `npx playwright test` |

## Test Categories

### 1. Unit Tests

**Purpose**: Test individual components in isolation

**Characteristics**:
- Fast execution (< 100ms per test)
- No external dependencies
- Mock all external calls
- Test one thing at a time

**Example Structure**:
```python
@pytest.mark.unit
class TestDatabaseAdapter:
    def test_connection_creation(self, sqlite_adapter):
        """Test database connection creation."""
        assert sqlite_adapter._connection is None
        sqlite_adapter.connect()
        assert sqlite_adapter._connection is not None

    @patch('psycopg2.connect')
    def test_connection_error_handling(self, mock_connect):
        """Test connection error handling."""
        mock_connect.side_effect = ConnectionError("Database unavailable")

        with pytest.raises(ConnectionError):
            adapter.connect()
```

### 2. Integration Tests

**Purpose**: Test component interactions and data flow

**Characteristics**:
- Use real databases (with test isolation)
- Test API endpoints with real HTTP calls
- Verify data persistence and retrieval
- Longer execution time (1-5 seconds)

**Example Structure**:
```python
@pytest.mark.integration
@pytest.mark.database
class TestCongressDataIngestion:
    def test_full_ingestion_workflow(self, clean_database, mock_congress_api):
        """Test complete data ingestion workflow."""
        # Setup test data
        session_data = test_data_factory.create_session_data()

        # Execute ingestion
        ingester = CongressDataIngester()
        result = ingester.ingest_congress_data(
            congress_start=118,
            congress_end=118,
            session=clean_database
        )

        # Verify results
        assert result.records_processed > 0
        assert result.records_succeeded > 0

        # Verify data in database
        cursor = clean_database.cursor()
        cursor.execute("SELECT COUNT(*) FROM congress.bills")
        count = cursor.fetchone()[0]
        assert count > 0
```

### 3. Performance Tests

**Purpose**: Ensure system performance meets requirements

**Characteristics**:
- Measure execution time and memory usage
- Test under various load conditions
- Establish performance baselines
- Long execution time (10+ seconds)

**Example Structure**:
```python
@pytest.mark.performance
@pytest.mark.slow
class TestIngestionPerformance:
    def test_large_dataset_insert_performance(self, benchmark, large_dataset):
        """Test insertion performance with large dataset."""
        def insert_data():
            # Insert 10,000 records
            for bill in large_dataset:
                adapter.execute(
                    "INSERT INTO bills (bill_id, title) VALUES (?, ?)",
                    (bill['bill_id'], bill['title'])
                )
            adapter.commit()

        result = benchmark.measure_function(insert_data)

        # Performance assertions
        assert result['execution_time'] < 30.0  # Must complete in 30s
        assert result['memory_delta'] < 100 * 1024 * 1024  # < 100MB
```

### 4. End-to-End Tests

**Purpose**: Validate complete user workflows

**Characteristics**:
- Test full user journeys
- Use real browser automation
- Verify UI interactions
- Longest execution time (1+ minutes)

**Example Structure**:
```python
@pytest.mark.e2e
class TestSearchWorkflow:
    def test_complete_search_workflow(self, browser, authenticated_user):
        """Test complete search workflow from UI."""
        # Navigate to application
        browser.goto('/search')

        # Perform search
        search_input = browser.get_by_placeholder('Search legislation')
        search_input.fill('healthcare reform')
        search_button = browser.get_by_role('button', name='Search')
        search_button.click()

        # Verify results
        results = browser.get_by_role('region', name='Search results')
        expect(results).to_contain_text('Healthcare Reform Act')
        expect(results).to_contain_text('Results: 42 found')
```

### 5. Load Tests

**Purpose**: Test system behavior under high load

**Characteristics**:
- Simulate concurrent users
- Test system limits and breaking points
- Monitor resource consumption
- Long execution time (5+ minutes)

## Running Tests

### Python Tests

```bash
# Run all tests
pytest

# Run specific test categories
pytest -m unit                    # Unit tests only
pytest -m integration            # Integration tests only
pytest -m performance            # Performance tests only
pytest -m "not slow"             # Skip slow tests

# Run with coverage
pytest --cov=scripts --cov-report=html

# Run specific test file
pytest tests/unit/test_database_adapter.py

# Run with markers
pytest -m "unit and database"

# Run in parallel (requires pytest-xdist)
pytest -n auto
```

### JavaScript Tests

```bash
# Run all tests
npm test

# Run with coverage
npm run test:coverage

# Run in watch mode
npm run test:watch

# Run specific test file
npm test -- SearchInterface.test.tsx

# Run E2E tests (requires Playwright)
npm run test:e2e
```

### Custom Test Commands

```bash
# Run performance benchmarks only
pytest tests/performance/ --benchmark-only

# Run tests with specific database
pytest tests/integration/ -m database --db-url="postgresql://..."

# Run tests with environment variables
SKIP_NETWORK_TESTS=true pytest tests/ -m network
```

## Best Practices

### 1. Test Naming and Organization

**Good Test Names**:
- `test_should_create_database_connection_when_valid_config_provided()`
- `test_handles_api_rate_limiting_gracefully()`
- `test_search_returns_results_within_two_seconds()`

**Test Structure (AAA Pattern)**:
```python
def test_feature_behavior(self):
    # Arrange
    setup_test_data()
    mock_external_dependencies()

    # Act
    result = function_under_test()

    # Assert
    assert result.expected_property == "value"
    assert another_verification()
```

### 2. Data Management

**Use Factories for Test Data**:
```python
class TestDataFactory:
    @staticmethod
    def create_bill_data(**overrides):
        defaults = {
            'bill_id': 'hr123-118',
            'title': 'Test Bill',
            'congress': 118
        }
        defaults.update(overrides)
        return defaults
```

**Database Test Isolation**:
```python
@pytest.fixture
def clean_database():
    """Provide clean database for each test."""
    db = create_test_database()
    yield db
    db.cleanup()
```

### 3. Mocking and Stubbing

**Mock External Dependencies**:
```python
@pytest.fixture
def mock_congress_api():
    with patch('requests.get') as mock_get:
        mock_get.return_value = APITestHelper.mock_congress_api_response()
        yield mock_get
```

**Use Appropriate Mock Levels**:
- **Unit Tests**: Mock all external calls
- **Integration Tests**: Mock only external services
- **E2E Tests**: Use real services where possible

### 4. Assertions and Validation

**Specific Assertions**:
```python
# Good
assert response.status_code == 200
assert 'congress' in response.json()
assert len(results) == 42

# Avoid
assert response.ok  # Too vague
assert results  # Doesn't check count
```

**Use Custom Matchers**:
```python
expect(response).to_have_status(200)
expect(results).to_have_length(42)
expect(bill).to_have_congress(118)
```

### 5. Performance Testing

**Set Performance Benchmarks**:
```python
# Establish baselines
MAX_INSERT_TIME = 30.0  # seconds
MAX_SEARCH_TIME = 2.0   # seconds
MAX_MEMORY_USAGE = 100 * 1024 * 1024  # 100MB
```

**Monitor Resource Usage**:
```python
def test_performance(self, benchmark):
    result = benchmark.measure_function(slow_operation)

    assert result['execution_time'] < 5.0
    assert result['memory_delta'] < 50 * 1024 * 1024
```

### 6. Test Data and Fixtures

**Reusable Fixtures**:
```python
@pytest.fixture
def sample_bill_data():
    """Provide consistent test bill data."""
    return DatabaseTestHelper._generate_bill_data(1)[0]

@pytest.fixture
def authenticated_client():
    """Provide authenticated API client."""
    client = APIClient()
    client.authenticate(test_user)
    return client
```

**Parameterize Tests**:
```python
@pytest.mark.parametrize("bill_type,expected_count", [
    ('HR', 150),
    ('S', 75),
    ('HJ', 25),
])
def test_bill_type_filtering(self, bill_type, expected_count):
    results = search_bills(type=bill_type)
    assert len(results) >= expected_count
```

## CI/CD Integration

### GitHub Actions Workflow

The project uses a comprehensive CI pipeline:

1. **Python Unit Tests** (Multiple Python versions)
2. **Python Integration Tests** (With PostgreSQL)
3. **JavaScript/TypeScript Tests**
4. **End-to-End Tests**
5. **Performance Tests**
6. **Security Scans**
7. **Code Quality Checks**

### Test Execution in CI

```yaml
# Run tests with proper environment
- name: Run Python tests
  env:
    DB_HOST: localhost
    DB_PORT: 5432
    TEST_DATABASE_AVAILABLE: true
  run: |
    pytest tests/unit/ --cov=scripts --cov-fail-under=80

- name: Run JavaScript tests
  run: |
    cd web && npm test -- --coverage --watchAll=false
```

### Coverage Reporting

- **HTML Reports**: Generated locally in `htmlcov/`
- **XML Reports**: Used by CI for Codecov integration
- **JSON Reports**: Used for performance tracking

## Coverage Goals

### Coverage Targets

| Component Type | Target Coverage | Minimum Coverage |
|----------------|----------------|------------------|
| Core Logic | 90% | 80% |
| API Endpoints | 85% | 75% |
| Database Layer | 80% | 70% |
| Ingestion Scripts | 85% | 75% |
| Utilities | 95% | 85% |
| Frontend Components | 80% | 70% |

### Critical Path Coverage

Must achieve 100% coverage on:
- Data validation functions
- Error handling paths
- Authentication/authorization
- Payment processing
- Critical business logic

### Coverage Exclusions

The following are intentionally excluded from coverage:
- `__main__` blocks
- Debug/development code
- Third-party library wrappers
- Database migrations
- Configuration loading

## Test Maintenance

### Regular Maintenance Tasks

1. **Update Test Data**: Keep mock data realistic and current
2. **Review Performance Benchmarks**: Adjust thresholds based on system improvements
3. **Clean Up Obsolete Tests**: Remove tests for deprecated features
4. **Update Fixtures**: Ensure test fixtures match production data structure
5. **Monitor Test Execution Time**: Keep unit tests fast (< 100ms average)

### Test Review Process

1. **Code Review**: All tests must be reviewed with code changes
2. **Performance Review**: New tests must not significantly impact build time
3. **Coverage Analysis**: Monitor coverage trends and address gaps
4. **Flaky Test Detection**: Identify and fix unreliable tests

## Debugging Tests

### Common Issues and Solutions

**Tests Timing Out**:
```python
# Increase timeout for slow operations
@pytest.mark.slow
@pytest.mark.timeout(60)
def test_slow_operation(self):
    pass
```

**Flaky Database Tests**:
```python
# Use transactions for isolation
@pytest.fixture
def transaction(db):
    db.begin()
    yield db
    db.rollback()
```

**Mock Configuration Issues**:
```python
# Ensure mocks are reset between tests
@pytest.fixture(autouse=True)
def reset_mocks():
    yield
    jest.clearAllMocks()  # JavaScript
    # OR
    patch.stopall()  # Python
```

### Debug Commands

```bash
# Run single test with full output
pytest tests/unit/test_specific.py::test_function -v -s

# Run with debugger
pytest tests/unit/test_specific.py::test_function --pdb

# Run with profiling
pytest tests/unit/test_specific.py --profile

# Run specific test with custom markers
pytest tests/ -m "unit and not slow" -v
```

## Conclusion

This testing strategy ensures comprehensive coverage, reliable test execution, and maintainable test suites. Regular review and updates of this strategy will help maintain test quality as the project evolves.

For questions about testing practices or to report issues with the test suite, please create an issue in the project repository.
