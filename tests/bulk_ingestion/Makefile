# Makefile for bulk ingestion test suite

.PHONY: help test test-unit test-integration test-performance test-all clean install coverage reports debug

# Default target
help:
	@echo "Bulk Ingestion Test Suite - Available Commands:"
	@echo ""
	@echo "Setup:"
	@echo "  install       Install test dependencies"
	@echo "  clean         Clean test artifacts and reports"
	@echo ""
	@echo "Testing:"
	@echo "  test          Run all tests"
	@echo "  test-unit     Run unit tests only (fast)"
	@echo "  test-integration Run integration tests (requires database)"
	@echo "  test-performance Run performance tests"
	@echo "  test-troubleshooting Run troubleshooting tests"
	@echo "  test-specific FILE=path Run specific test file"
	@echo ""
	@echo "Coverage:"
	@echo "  coverage      Generate coverage report"
	@echo "  coverage-html Generate HTML coverage report"
	@echo ""
	@echo "Reports:"
	@echo "  reports       Generate all test reports"
	@echo "  report-html   Generate HTML test report"
	@echo "  report-junit  Generate JUnit XML report"
	@echo ""
	@echo "Debugging:"
	@echo "  debug         Run with verbose output and debugging"
	@echo "  debug-db      Debug database connectivity"
	@echo "  debug-api     Debug API connectivity"
	@echo ""
	@echo "CI/CD:"
	@echo "  ci-unit       Run unit tests for CI"
	@echo "  ci-integration Run integration tests for CI"

# Installation
install:
	@echo "Installing test dependencies..."
	pip install -r requirements-test.txt
	@echo "Installing project dependencies..."
	pip install -r ../../requirements.txt

# Cleaning
clean:
	@echo "Cleaning test artifacts..."
	rm -rf reports/
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -f test_results.xml
	rm -f coverage.xml
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete

# Unit tests (fast, no external dependencies)
test-unit:
	@echo "Running unit tests..."
	pytest -m "unit and not slow" --tb=short -v

# Integration tests (require database and APIs)
test-integration:
	@echo "Running integration tests..."
	pytest -m "integration and not slow" --tb=short -v

# Performance tests
test-performance:
	@echo "Running performance tests..."
	pytest -m "performance" --tb=short -v --durations=0

# Troubleshooting tests
test-troubleshooting:
	@echo "Running troubleshooting tests..."
	pytest -m "troubleshooting" --tb=short -v

# Specific test file
test-specific:
ifdef FILE
	@echo "Running specific test file: $(FILE)"
	pytest $(FILE) -v
else
	@echo "Error: Please specify FILE=path/to/test_file.py"
endif

# All tests
test-all:
	@echo "Running all tests..."
	pytest --tb=short -v

# Coverage
coverage:
	@echo "Running tests with coverage..."
	pytest --cov=scripts --cov-report=term-missing --cov-report=html:reports/coverage

coverage-html:
	@echo "Generating HTML coverage report..."
	pytest --cov=scripts --cov-report=html:reports/coverage
	@echo "Coverage report generated: reports/coverage/index.html"

# Reports
reports:
	@echo "Generating all test reports..."
	mkdir -p reports
	pytest --html=reports/test_report.html --self-contained-html --junit-xml=reports/junit.xml

report-html:
	@echo "Generating HTML test report..."
	mkdir -p reports
	pytest --html=reports/test_report.html --self-contained-html

report-junit:
	@echo "Generating JUnit XML report..."
	mkdir -p reports
	pytest --junit-xml=reports/junit.xml

# Debugging
debug:
	@echo "Running tests with verbose debugging..."
	pytest -v -s --tb=long --log-cli-level=DEBUG

debug-db:
	@echo "Debugging database connectivity..."
	pytest tests/bulk_ingestion/test_database.py::TestDatabaseConnectivity::test_database_connection_basic -v -s

debug-api:
	@echo "Debugging API connectivity..."
	pytest tests/bulk_ingestion/test_api_integration.py::TestAPIConnectivity::test_congress_api_connectivity -v -s

# CI/CD targets
ci-unit:
	@echo "Running CI unit tests..."
	pytest -m "unit and not slow" --tb=short --junit-xml=reports/junit-ci.xml --cov=scripts --cov-report=xml:reports/coverage-ci.xml

ci-integration:
	@echo "Running CI integration tests..."
	pytest -m "integration and not slow" --tb=short --junit-xml=reports/junit-integration.xml

# Quick smoke test
smoke-test:
	@echo "Running smoke test..."
	pytest tests/bulk_ingestion/test_database.py::TestDatabaseConnectivity::test_database_connection_mock -v

# Test with specific markers
test-markers:
	@echo "Available test markers:"
	@pytest --markers | grep -E "^\s+[a-z]"

# Install development dependencies
install-dev:
	@echo "Installing development dependencies..."
	pip install -r requirements-test.txt
	pip install black flake8 mypy

# Code quality
lint:
	@echo "Running code quality checks..."
	flake8 tests/bulk_ingestion/
	mypy tests/bulk_ingestion/

format:
	@echo "Formatting code..."
	black tests/bulk_ingestion/

# Performance profiling
profile:
	@echo "Running performance profiling..."
	python -m cProfile -o profiling_output.prof -m pytest tests/bulk_ingestion/test_performance.py -v

# Load testing simulation
load-test:
	@echo "Running load test simulation..."
	python -c "
import sys
sys.path.append('.')
from tests.bulk_ingestion.conftest import generate_test_bills
from tests.bulk_ingestion.utils.database_utils import get_database_helper
from tests.bulk_ingestion.utils.api_utils import get_api_helper
import time

print('Load test simulation...')
helper = get_database_helper(use_test_db=False)
api_helper = get_api_helper()

# Simulate load
start_time = time.time()
for i in range(100):
    bill_data = {'billId': f'load-test-{i}', 'title': f'Load Test {i}'}
    # Simulate processing
    time.sleep(0.001)

end_time = time.time()
print(f'Load test completed: 100 operations in {end_time - start_time:.2f}s')
"

# Health check
health-check:
	@echo "Running health check..."
	@echo "1. Checking Python environment..."
	python --version
	@echo "2. Checking required packages..."
	python -c "import pytest; print('✓ pytest available')"
	python -c "import psycopg2; print('✓ psycopg2 available')"
	python -c "import requests; print('✓ requests available')"
	python -c "import psutil; print('✓ psutil available')"
	@echo "3. Checking test structure..."
	@ls tests/bulk_ingestion/test_*.py | wc -l | xargs echo "Test files found:"
	@echo "4. Running quick health check..."
	pytest tests/bulk_ingestion/test_troubleshooting.py::TestSystemDiagnostics::test_system_resources_diagnostic -v -s
