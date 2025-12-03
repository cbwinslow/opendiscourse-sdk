# Development Setup Guide - OpenDiscourse

## Overview

This guide provides step-by-step instructions for setting up a complete development environment for OpenDiscourse. Follow these instructions to get a local development environment running quickly.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Database Configuration](#database-configuration)
4. [Application Setup](#application-setup)
5. [Development Tools](#development-tools)
6. [Running the Application](#running-the-application)
7. [Testing Setup](#testing-setup)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements

- **OS**: Linux (Ubuntu 22.04+ recommended), macOS 12+, or Windows 11 with WSL2
- **RAM**: Minimum 8GB, recommended 16GB+
- **Storage**: 20GB free space for development environment
- **Network**: Stable internet connection for downloading dependencies

### Required Software

#### 1. Python 3.13+

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install python3.13 python3.13-venv python3.13-dev python3.13-pip
```

**macOS (using Homebrew):**
```bash
brew install python@3.13
```

**Verify Installation:**
```bash
python3.13 --version
# Should output: Python 3.13.x
```

#### 2. PostgreSQL 14+

**Ubuntu/Debian:**
```bash
sudo apt install postgresql postgresql-contrib postgresql-client
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

**macOS:**
```bash
brew install postgresql@14
brew services start postgresql@14
```

**Verify Installation:**
```bash
psql --version
# Should output: psql (PostgreSQL) 14.x
```

#### 3. Node.js 18+ (for frontend development)

**Using Node Version Manager (recommended):**
```bash
# Install nvm
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
source ~/.bashrc

# Install and use Node.js 18
nvm install 18
nvm use 18
nvm alias default 18
```

**Verify Installation:**
```bash
node --version  # Should output: v18.x.x
npm --version   # Should output: 9.x.x
```

#### 4. Docker (optional, for containerized development)

**Ubuntu:**
```bash
sudo apt install docker.io docker-compose
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER
```

**macOS:**
```bash
brew install --cask docker
```

#### 5. Git

**Ubuntu:**
```bash
sudo apt install git
```

**macOS:**
```bash
brew install git
```

**Configure Git:**
```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

---

## Environment Setup

### 1. Clone the Repository

```bash
git clone https://github.com/cbwinslow/opendiscourse.git
cd opendiscourse
```

### 2. Create Python Virtual Environment

```bash
# Create virtual environment
python3.13 -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # Linux/macOS
# OR
.venv\Scripts\activate     # Windows

# Verify activation (should show (.venv) in prompt)
which python  # Should point to .venv/bin/python
```

### 3. Install Python Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install development dependencies
pip install -r requirements-dev.txt

# Install the package in development mode
pip install -e .
```

### 4. Environment Variables

```bash
# Copy environment template
cp config/environments/.env.example config/environments/.env

# Edit the environment file
nano config/environments/.env
```

**Required Environment Variables:**
```bash
# Database Configuration
DATABASE_URL=postgresql://opendiscourse:password@localhost:5432/opendiscourse_dev

# API Keys (get from respective services)
OPENAI_API_KEY=your_openai_api_key_here
NVIDIA_NIM_API_KEY=your_nvidia_nim_key_here

# Application Settings
DEBUG=true
LOG_LEVEL=DEBUG
SECRET_KEY=your_secret_key_here

# Government Data APIs
GOVINFO_API_KEY=your_govinfo_key_here

# Vector Database
CHROMA_PERSIST_DIRECTORY=./data/chroma
CHROMA_HOST=localhost
CHROMA_PORT=8000

# Redis (optional, for caching)
REDIS_URL=redis://localhost:6379/0
```

---

## Database Configuration

### 1. Create PostgreSQL Database and User

```bash
# Switch to postgres user
sudo -u postgres psql

# Create database and user
CREATE DATABASE opendiscourse_dev;
CREATE USER opendiscourse WITH PASSWORD 'password';
GRANT ALL PRIVILEGES ON DATABASE opendiscourse_dev TO opendiscourse;

# Enable pgvector extension
\c opendiscourse_dev
CREATE EXTENSION IF NOT EXISTS vector;

# Exit psql
\q
```

### 2. Test Database Connection

```bash
# Test connection
psql -h localhost -U opendiscourse -d opendiscourse_dev -c "SELECT version();"
```

### 3. Initialize Database Schema

```bash
# Run database migrations
python scripts/setup/init_db.py

# Verify tables were created
psql -h localhost -U opendiscourse -d opendiscourse_dev -c "\dt"
```

---

## Application Setup

### 1. Install Additional Dependencies

#### Vector Database (ChromaDB)
```bash
# ChromaDB is included in requirements, but you can run it separately
docker run -p 8000:8000 ghcr.io/chroma-core/chroma:latest
```

#### Redis (for caching)
```bash
# Ubuntu
sudo apt install redis-server
sudo systemctl start redis
sudo systemctl enable redis

# macOS
brew install redis
brew services start redis
```

### 2. Download AI Models (optional)

```bash
# Download sentence transformer models
python -c "
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')
print('Model downloaded successfully')
"
```

### 3. Create Required Directories

```bash
# Create data directories
mkdir -p data/{raw,processed,uploads,exports}
mkdir -p logs
mkdir -p temp

# Set permissions
chmod 755 data logs temp
```

---

## Development Tools

### 1. Code Quality Tools

```bash
# Install pre-commit hooks
pre-commit install

# Run code formatting
black opendiscourse/ tests/
isort opendiscourse/ tests/

# Type checking
mypy opendiscourse/

# Linting
flake8 opendiscourse/ tests/
```

### 2. IDE Configuration

#### VS Code Extensions (recommended)
```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.black-formatter",
    "ms-python.mypy-type-checker",
    "charliermarsh.ruff",
    "ms-vscode.vscode-json",
    "bradlc.vscode-tailwindcss"
  ]
}
```

#### PyCharm Configuration
1. Open project in PyCharm
2. Configure Python interpreter to use `.venv/bin/python`
3. Install Python plugin for PostgreSQL
4. Configure database connection

### 3. Database Tools

#### pgAdmin (GUI tool)
```bash
# Ubuntu
sudo apt install pgadmin4

# macOS
brew install --cask pgadmin4
```

#### DBeaver (Cross-platform)
```bash
# Download from https://dbeaver.io/download/
```

---

## Running the Application

### 1. Start Required Services

```bash
# Start PostgreSQL (if not running)
sudo systemctl start postgresql

# Start Redis (if using)
sudo systemctl start redis

# Start ChromaDB (if running separately)
docker run -d -p 8000:8000 ghcr.io/chroma-core/chroma:latest
```

### 2. Run Database Migrations

```bash
# Ensure database is up to date
python scripts/setup/init_db.py
```

### 3. Start the Development Server

```bash
# Activate virtual environment
source .venv/bin/activate

# Start the main application
python -m opendiscourse

# Or use uvicorn directly
uvicorn opendiscourse.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Start Frontend Development Server (optional)

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### 5. Verify Installation

```bash
# Check API health
curl http://localhost:8000/api/v1/health

# Check database connection
python -c "
from opendiscourse.db.session import get_db
from opendiscourse.core.config import settings
print('Database connection successful!')
"
```

---

## Testing Setup

### 1. Test Database Setup

```bash
# Create test database
sudo -u postgres psql -c "CREATE DATABASE opendiscourse_test;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE opendiscourse_test TO opendiscourse;"

# Enable pgvector extension
sudo -u postgres psql -d opendiscourse_test -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

### 2. Set Test Environment Variables

```bash
# Add to your .env file or set temporarily
export TEST_DATABASE_URL=postgresql://opendiscourse:password@localhost:5432/opendiscourse_test
```

### 3. Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=opendiscourse --cov-report=html

# Run specific test categories
pytest tests/unit/          # Unit tests
pytest tests/integration/   # Integration tests
pytest tests/api/          # API tests

# Run tests with verbose output
pytest -v -s
```

### 4. Generate Test Reports

```bash
# Coverage report
pytest --cov=opendiscourse --cov-report=html
open htmlcov/index.html  # View coverage report

# Performance tests
pytest tests/performance/ --benchmark-json=benchmark.json
```

---

## Development Workflow

### 1. Daily Development

```bash
# Activate environment
source .venv/bin/activate

# Pull latest changes
git pull origin main

# Update dependencies (if needed)
pip install -r requirements-dev.txt

# Run quality checks
./scripts/quality-check.sh

# Start development server
python -m opendiscourse
```

### 2. Code Quality Workflow

```bash
# Before committing
black opendiscourse/ tests/    # Format code
isort opendiscourse/ tests/    # Sort imports
mypy opendiscourse/           # Type checking
flake8 opendiscourse/ tests/  # Linting
pytest tests/                 # Run tests

# Or use the combined script
./scripts/quality-check.sh
```

### 3. Database Development

```bash
# Create new migration
python scripts/database/create_migration.py "add_new_field"

# Apply migrations
python scripts/database/migrate.py

# Reset database (development only)
python scripts/database/reset_db.py
```

---

## Troubleshooting

### Common Issues

#### 1. Python Virtual Environment Issues

**Problem**: `command not found: python3.13`
```bash
# Solution: Install Python 3.13
sudo apt install python3.13 python3.13-venv
```

**Problem**: Virtual environment not activating
```bash
# Solution: Recreate virtual environment
rm -rf .venv
python3.13 -m venv .venv
source .venv/bin/activate
```

#### 2. Database Connection Issues

**Problem**: `connection refused` error
```bash
# Check if PostgreSQL is running
sudo systemctl status postgresql

# Start PostgreSQL if not running
sudo systemctl start postgresql

# Check if user exists
sudo -u postgres psql -c "\du"
```

**Problem**: `role does not exist`
```bash
# Create the user
sudo -u postgres createuser -s opendiscourse
sudo -u postgres psql -c "ALTER USER opendiscourse PASSWORD 'password';"
```

#### 3. Permission Issues

**Problem**: Permission denied errors
```bash
# Fix file permissions
chmod +x scripts/*.sh
chmod 755 data/ logs/ temp/

# Fix ownership (if needed)
sudo chown -R $USER:$USER .
```

#### 4. Dependency Issues

**Problem**: `ModuleNotFoundError`
```bash
# Reinstall dependencies
pip install --force-reinstall -r requirements-dev.txt

# Install in development mode
pip install -e .
```

**Problem**: Conflicting package versions
```bash
# Clean install
pip freeze > temp_requirements.txt
pip uninstall -r temp_requirements.txt -y
pip install -r requirements-dev.txt
```

#### 5. Port Conflicts

**Problem**: Port already in use
```bash
# Find process using port
lsof -i :8000

# Kill process (replace PID)
kill -9 <PID>

# Use different port
uvicorn opendiscourse.main:app --port 8001
```

### Performance Issues

#### 1. Slow Database Queries

```bash
# Enable query logging in PostgreSQL
sudo nano /etc/postgresql/14/main/postgresql.conf

# Add/modify these lines:
log_statement = 'all'
log_min_duration_statement = 1000
```

#### 2. Memory Issues

```bash
# Monitor memory usage
htop

# Adjust PostgreSQL settings
sudo nano /etc/postgresql/14/main/postgresql.conf

# Modify these settings based on available RAM:
shared_buffers = 256MB
effective_cache_size = 1GB
```

### Getting Help

1. **Check Logs**:
   ```bash
   tail -f logs/application.log
   tail -f logs/error.log
   ```

2. **Database Logs**:
   ```bash
   sudo tail -f /var/log/postgresql/postgresql-14-main.log
   ```

3. **System Resources**:
   ```bash
   htop          # Monitor CPU and memory
   df -h         # Check disk space
   netstat -tlnp # Check ports in use
   ```

4. **Documentation**:
   - [Project Documentation](../README.md)
   - [API Reference](../api/API_REFERENCE.md)
   - [Troubleshooting Guide](TROUBLESHOOTING.md)

5. **Community Support**:
   - GitHub Issues: [Report bugs](https://github.com/cbwinslow/opendiscourse/issues)
   - Discussions: [Community help](https://github.com/cbwinslow/opendiscourse/discussions)

---

## Next Steps

After completing the setup:

1. **Explore the codebase**: Familiarize yourself with the project structure
2. **Run examples**: Try the example scripts in `examples/`
3. **Read documentation**: Review API documentation and guides
4. **Contribute**: Check out open issues and contribution guidelines
5. **Join community**: Participate in discussions and get help

---

**Setup Guide Version**: 1.0  
**Last Updated**: June 26, 2025  
**Compatible with**: OpenDiscourse v1.0.1+

