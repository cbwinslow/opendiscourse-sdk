# OpenDiscourse Bulk Ingestion Test Suite

## 🎯 **OVERVIEW**
Comprehensive test suite for bulk data ingestion process covering all aspects from API connectivity to end-to-end integration testing.

## 📁 **TEST STRUCTURE**

```
tests/bulk_ingestion/
├── README.md                          # This file
├── conftest.py                        # Pytest configuration and fixtures
├── test_config.py                     # Configuration and environment tests
├── test_database.py                   # Database connectivity and schema tests
├── test_api_integration.py            # API connectivity and rate limiting tests
├── test_data_transformation.py        # Data normalization and transformation tests
├── test_error_handling.py             # Error handling and recovery tests
├── test_performance.py                # Performance and benchmarking tests
├── test_incremental_processing.py     # Checkpoint and incremental tests
├── test_end_to_end.py                 # Full integration tests
├── test_troubleshooting.py            # Diagnostic utilities
├── utils/
│   ├── __init__.py
│   ├── database_utils.py              # Database test utilities
│   ├── api_utils.py                   # API test utilities
│   ├── data_fixtures.py               # Test data fixtures
│   └── mock_responses.py              # Mock API responses
└── reports/                           # Test reports and outputs
    └── .gitkeep
```

## 🚀 **QUICK START**

### **Run All Tests**
```bash
# Run complete test suite
pytest tests/bulk_ingestion/ -v --tb=short

# Run with coverage
pytest tests/bulk_ingestion/ --cov=scripts --cov-report=html
```

### **Run Specific Test Categories**
```bash
# Database tests only
pytest tests/bulk_ingestion/test_database.py -v

# API integration tests
pytest tests/bulk_ingestion/test_api_integration.py -v

# End-to-end tests
pytest tests/bulk_ingestion/test_end_to_end.py -v

# Performance tests
pytest tests/bulk_ingestion/test_performance.py -v
```

### **Run with Troubleshooting**
```bash
# Detailed output for debugging
pytest tests/bulk_ingestion/ -v -s --tb=long

# Stop on first failure
pytest tests/bulk_ingestion/ -x

# Run specific test
pytest tests/bulk_ingestion/test_api_integration.py::test_congress_api_connectivity -v
```

## 📋 **TEST CATEGORIES**

### **1. Configuration Tests** (`test_config.py`)
- Environment variable validation
- API key verification
- Database connection configuration
- Configuration loading and parsing

### **2. Database Tests** (`test_database.py`)
- Database connectivity
- Schema validation
- Table existence and structure
- Foreign key constraints
- Incremental tables functionality

### **3. API Integration Tests** (`test_api_integration.py`)
- API connectivity testing
- Rate limiting functionality
- Error handling and recovery
- Response parsing and validation
- Authentication verification

### **4. Data Transformation Tests** (`test_data_transformation.py`)
- Data normalization functions
- Field mapping and transformation
- Date parsing and formatting
- Data validation and sanitization
- Bill data processing

### **5. Error Handling Tests** (`test_error_handling.py`)
- Network failure scenarios
- API error responses
- Database connection failures
- Data corruption handling
- Recovery mechanisms

### **6. Performance Tests** (`test_performance.py`)
- Batch processing performance
- Rate limiting effectiveness
- Memory usage monitoring
- Database insertion performance
- Large dataset handling

### **7. Incremental Processing Tests** (`test_incremental_processing.py`)
- Checkpoint functionality
- Resume from interruption
- Duplicate detection
- Session management
- Progress tracking

### **8. End-to-End Tests** (`test_end_to_end.py`)
- Full ingestion workflow
- Multi-congress processing
- Data integrity verification
- Performance benchmarking
- Error recovery scenarios

### **9. Troubleshooting Tests** (`test_troubleshooting.py`)
- Diagnostic utilities
- System health checks
- Resource monitoring
- Log analysis
- Performance profiling

## 🛠️ **UTILITIES**

### **Database Utils** (`utils/database_utils.py`)
- Test database setup and teardown
- Sample data generation
- Database state verification
- Schema validation helpers

### **API Utils** (`utils/api_utils.py`)
- Mock API responses
- API testing helpers
- Rate limiting verification
- Error simulation

### **Data Fixtures** (`utils/data_fixtures.py`)
- Sample bill data
- Mock API responses
- Test data generators
- Reference datasets

## 📊 **TEST EXECUTION REPORTS**

### **HTML Reports**
```bash
# Generate HTML coverage report
pytest tests/bulk_ingestion/ --cov=scripts --cov-report=html:tests/bulk_ingestion/reports/coverage

# Generate JUnit XML for CI/CD
pytest tests/bulk_ingestion/ --junit-xml=tests/bulk_ingestion/reports/junit.xml
```

### **Performance Reports**
```bash
# Generate performance benchmark report
pytest tests/bulk_ingestion/test_performance.py --benchmark-only --benchmark-json=reports/benchmark.json
```

## 🔧 **TESTING BEST PRACTICES**

### **Test Isolation**
- Each test is independent and can run separately
- Database state is reset after each test
- Mock external dependencies when possible
- Use fixtures for common setup

### **Data Management**
- Use in-memory SQLite for unit tests
- Use PostgreSQL for integration tests
- Generate synthetic test data
- Clean up test data after execution

### **Performance Testing**
- Measure actual API call rates
- Monitor memory usage
- Track database performance
- Set performance thresholds

### **Error Simulation**
- Simulate network failures
- Test with invalid responses
- Verify graceful degradation
- Test recovery mechanisms

## 🎯 **SUCCESS CRITERIA**

### **All Tests Must Pass**
- ✅ 100% of unit tests pass
- ✅ 95%+ of integration tests pass
- ✅ No database constraint violations
- ✅ All API connectivity tests succeed
- ✅ Performance benchmarks met

### **Performance Thresholds**
- **Congress API**: < 2 requests/second sustained
- **Database Insertion**: > 50 records/second
- **Memory Usage**: < 500MB for 10K record batches
- **Error Recovery**: < 30 seconds for failure recovery

## 🔍 **TROUBLESHOOTING**

### **Common Issues**
1. **Database Connection**: Check PostgreSQL service and credentials
2. **API Keys**: Verify environment variables are set
3. **Rate Limiting**: Monitor API response headers
4. **Memory Issues**: Adjust batch sizes
5. **Network Timeouts**: Increase timeout values

### **Debug Commands**
```bash
# Check environment
python -c "from env_config import validate_api_keys; print(validate_api_keys())"

# Test database connection
python -c "import psycopg2; conn = psycopg2.connect(database='opendiscourse', user='cbwinslow'); print('Connected')"

# Test API connectivity
python -c "import requests; r = requests.get('https://api.congress.gov/v3/member/congress/118?limit=1', headers={'X-API-Key': 'DEMO_KEY'}); print(f'Status: {r.status_code}')"
```

---

*Last Updated: 2025-12-03*
*Test Suite Version: 1.0*
*Coverage Target: 90%+*
