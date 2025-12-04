# OpenDiscourse Makefile
# Comprehensive installation and management

.PHONY: help install install-dev install-db install-mcp test clean docker

# Default target
help:
	@echo "OpenDiscourse - Legislative Data Ingestion System"
	@echo ""
	@echo "Available targets:"
	@echo "  install         - Full installation (Python packages, database, config)"
	@echo "  install-dev     - Development installation with testing tools"
	@echo "  install-db      - Initialize PostgreSQL database and migrations"
	@echo "  install-mcp     - Install MCP server for AI agent integration"
	@echo "  test            - Run all tests"
	@echo "  test-unit       - Run unit tests only"
	@echo "  test-integration - Run integration tests"
	@echo "  lint            - Run linting and type checking"
	@echo "  format          - Format code with black and isort"
	@echo "  docker          - Build and start Docker containers"
	@echo "  docker-up       - Start Docker services"
	@echo "  docker-down     - Stop Docker services"
	@echo "  clean           - Remove build artifacts and caches"
	@echo "  verify          - Verify environment and dependencies"
	@echo ""

# Installation
install:
	@echo "Installing OpenDiscourse..."
	./scripts/install.sh

install-dev:
	@echo "Installing OpenDiscourse (development mode)..."
	./scripts/install.sh --dev

install-db:
	@echo "Initializing database..."
	python3 -m scripts.core.database bootstrap
	@echo "Running migrations..."
	./scripts/run_migrations.sh

install-mcp:
	@echo "Installing MCP server..."
	./scripts/install_mcp_server.sh

# Testing
test: test-unit test-integration

test-unit:
	@echo "Running unit tests..."
	pytest tests/unit/ -v --cov=scripts --cov-report=term-missing

test-integration:
	@echo "Running integration tests..."
	pytest tests/integration/ -v

# Code quality
lint:
	@echo "Running linters..."
	ruff check scripts/
	mypy scripts/

format:
	@echo "Formatting code..."
	black scripts/ tests/
	isort scripts/ tests/

# Docker
docker: docker-build docker-up

docker-build:
	@echo "Building Docker images..."
	docker-compose build

docker-up:
	@echo "Starting Docker services..."
	docker-compose up -d

docker-down:
	@echo "Stopping Docker services..."
	docker-compose down

# Cleanup
clean:
	@echo "Cleaning build artifacts..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/ dist/ .pytest_cache/ .coverage htmlcov/

# Verification
verify:
	@echo "Verifying environment..."
	python3 scripts/verify_environment.py

# Quick start helpers
congress:
	@echo "Starting Congress CLI..."
	python3 scripts/ingestion/congress_cli.py

openstates:
	@echo "Starting OpenStates CLI..."
	python3 scripts/ingestion/openstates_cli.py

govinfo:
	@echo "Starting GovInfo CLI..."
	python3 scripts/ingestion/govinfo_cli.py
