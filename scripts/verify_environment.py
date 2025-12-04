#!/usr/bin/env python3
"""
================================================================================
File: verify_environment.py
Author: OpenDiscourse Contributors
Created: 2025-12-04
Last Modified: 2025-12-04
Version: 1.0.0

Description:
    Comprehensive environment verification script. Checks all system
    dependencies, database connections, API keys, and configuration.

Checks:
    - Python version and environment managers (pyenv, uv)
    - Required packages (psycopg2, python-dotenv, etc.)
    - Environment variables and .env file
    - Database connection (PostgreSQL)
    - API key validity (Congress, OpenStates, GovInfo)
    - Directory structure and permissions

Usage:
    python3 scripts/verify_environment.py
    python3 scripts/verify_environment.py --fix  # Auto-fix issues
    python3 scripts/verify_environment.py --verbose  # Detailed output

Changelog:
    2025-12-04: Initial creation

================================================================================
"""

import sys
import os
import subprocess
import importlib
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import argparse


# ============================================================================
# Colors for Terminal Output
# ============================================================================

class Colors:
    """ANSI color codes for terminal output."""
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_status(message: str, status: str):
    """Print status message with color."""
    if status == "OK":
        print(f"{Colors.GREEN}✓{Colors.END} {message}")
    elif status == "WARNING":
        print(f"{Colors.YELLOW}⚠{Colors.END} {message}")
    elif status == "ERROR":
        print(f"{Colors.RED}✗{Colors.END} {message}")
    elif status == "INFO":
        print(f"{Colors.BLUE}ℹ{Colors.END} {message}")


# ============================================================================
# System Checks
# ============================================================================

def check_python_version() -> Tuple[bool, str]:
    """Check if Python version is compatible."""
    version = sys.version_info
    required = (3, 9)

    if version >= required:
        return True, f"Python {version.major}.{version.minor}.{version.micro}"
    else:
        return False, f"Python {version.major}.{version.minor} (requires 3.9+)"


def check_command_exists(command: str) -> Tuple[bool, str]:
    """Check if a command exists in PATH."""
    try:
        result = subprocess.run(
            [command, "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        return True, result.stdout.split('\n')[0]
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False, "Not found"


def check_pyenv() -> Tuple[bool, str]:
    """Check pyenv installation."""
    return check_command_exists("pyenv")


def check_uv() -> Tuple[bool, str]:
    """Check uv installation."""
    return check_command_exists("uv")


def check_pip() -> Tuple[bool, str]:
    """Check pip installation."""
    return check_command_exists("pip")


# ============================================================================
# Package Checks
# ============================================================================

def check_package(package_name: str, import_name: Optional[str] = None) -> Tuple[bool, str]:
    """Check if a Python package is installed."""
    if import_name is None:
        import_name = package_name.replace("-", "_")

    try:
        module = importlib.import_module(import_name)
        version = getattr(module, "__version__", "unknown")
        return True, f"{package_name}=={version}"
    except ImportError:
        return False, f"{package_name} not installed"


def check_required_packages() -> Dict[str, Tuple[bool, str]]:
    """Check all required packages."""
    packages = {
        "psycopg2": ("psycopg2", "psycopg2"),
        "python-dotenv": ("dotenv", "dotenv"),
        "pydantic": ("pydantic", "pydantic"),
        "click": ("click", "click"),
        "requests": ("requests", "requests"),
        "rich": ("rich", "rich"),
    }

    results = {}
    for display_name, (install_name, import_name) in packages.items():
        results[display_name] = check_package(install_name, import_name)

    return results


# ============================================================================
# Environment Variable Checks
# ============================================================================

def check_env_file() -> Tuple[bool, str]:
    """Check if .env file exists."""
    env_path = Path(".env")
    if env_path.exists():
        return True, f".env found ({env_path.stat().st_size} bytes)"
    else:
        return False, ".env file not found"


def check_env_variables() -> Dict[str, Tuple[bool, str]]:
    """Check required environment variables."""
    required_vars = [
        "CONGRESS_API_KEY",
        "OPENSTATES_API_KEY",
        "GOVINFO_API_KEY",
        "DB_HOST",
        "DB_NAME",
        "DB_USER",
    ]

    # Load from .env if exists
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    results = {}
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Mask API keys for security
            if "KEY" in var:
                masked = value[:8] + "..." + value[-4:] if len(value) > 12 else "***"
                results[var] = (True, f"Set ({masked})")
            else:
                results[var] = (True, f"Set ({value})")
        else:
            results[var] = (False, "Not set")

    return results


# ============================================================================
# Database Checks
# ============================================================================

def check_database_connection() -> Tuple[bool, str]:
    """Check PostgreSQL database connection."""
    try:
        import psycopg2
        from dotenv import load_dotenv
        load_dotenv()

        # Get connection parameters
        conn_params = {
            "host": os.getenv("DB_HOST", "localhost"),
            "port": int(os.getenv("DB_PORT", "5432")),
            "database": os.getenv("DB_NAME", "opendiscourse"),
            "user": os.getenv("DB_USER", "postgres"),
        }

        # Add password if set
        password = os.getenv("DB_PASSWORD")
        if password:
            conn_params["password"] = password

        # Try to connect
        conn = psycopg2.connect(**conn_params, connect_timeout=5)

        # Check database
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]

        cursor.close()
        conn.close()

        return True, f"Connected ({conn_params['database']}@{conn_params['host']})"

    except ImportError:
        return False, "psycopg2 not installed"
    except Exception as e:
        return False, f"Connection failed: {str(e)[:50]}"


def check_database_tables() -> Tuple[bool, str]:
    """Check if required tables exist."""
    try:
        import psycopg2
        from dotenv import load_dotenv
        load_dotenv()

        conn_params = {
            "host": os.getenv("DB_HOST", "localhost"),
            "port": int(os.getenv("DB_PORT", "5432")),
            "database": os.getenv("DB_NAME", "opendiscourse"),
            "user": os.getenv("DB_USER", "postgres"),
        }

        password = os.getenv("DB_PASSWORD")
        if password:
            conn_params["password"] = password

        conn = psycopg2.connect(**conn_params, connect_timeout=5)
        cursor = conn.cursor()

        # Check for key tables
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'congress'
            LIMIT 5
        """)

        tables = cursor.fetchall()
        cursor.close()
        conn.close()

        if tables:
            return True, f"Found {len(tables)} congress tables"
        else:
            return False, "No congress tables found (run migrations)"

    except Exception as e:
        return False, f"Check failed: {str(e)[:50]}"


# ============================================================================
# API Key Validation
# ============================================================================

def validate_api_key(api_name: str, url: str, headers: Dict[str, str]) -> Tuple[bool, str]:
    """Validate API key by making a test request."""
    try:
        import requests

        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            return True, "Valid (200 OK)"
        elif response.status_code == 401:
            return False, "Invalid key (401 Unauthorized)"
        elif response.status_code == 403:
            return False, "Access denied (403 Forbidden)"
        else:
            return False, f"Error ({response.status_code})"

    except ImportError:
        return False, "requests not installed"
    except Exception as e:
        return False, f"Check failed: {str(e)[:30]}"


def check_congress_api_key() -> Tuple[bool, str]:
    """Check Congress API key validity."""
    api_key = os.getenv("CONGRESS_API_KEY")
    if not api_key:
        return False, "API key not set"

    return validate_api_key(
        "Congress",
        f"https://api.congress.gov/v3/bill?api_key={api_key}&limit=1",
        {}
    )


def check_openstates_api_key() -> Tuple[bool, str]:
    """Check OpenStates API key validity."""
    api_key = os.getenv("OPENSTATES_API_KEY")
    if not api_key:
        return False, "API key not set"

    return validate_api_key(
        "OpenStates",
        "https://v3.openstates.org/jurisdictions",
        {"X-API-KEY": api_key}
    )


def check_govinfo_api_key() -> Tuple[bool, str]:
    """Check GovInfo API key validity."""
    api_key = os.getenv("GOVINFO_API_KEY")
    if not api_key:
        return False, "API key not set"

    return validate_api_key(
        "GovInfo",
        "https://api.govinfo.gov/collections",
        {"X-Api-Key": api_key}
    )


# ============================================================================
# Directory Structure Checks
# ============================================================================

def check_directory_structure() -> Dict[str, Tuple[bool, str]]:
    """Check if required directories exist."""
    directories = [
        "scripts/",
        "scripts/ingestion/",
        "scripts/core/",
        "scripts/api/",
        "migrations/",
        "tests/",
        "logs/",
        "data/",
    ]

    results = {}
    for directory in directories:
        path = Path(directory)
        if path.exists() and path.is_dir():
            results[directory] = (True, "Exists")
        else:
            results[directory] = (False, "Missing")

    return results


# ============================================================================
# Main Verification
# ============================================================================

def main():
    """Run all verification checks."""
    parser = argparse.ArgumentParser(description="Verify OpenDiscourse environment")
    parser.add_argument("--fix", action="store_true", help="Auto-fix issues")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    args = parser.parse_args()

    print(f"\n{Colors.BOLD}OpenDiscourse Environment Verification{Colors.END}\n")
    print("=" * 70)

    # Track overall status
    all_checks_passed = True

    # Python version
    print(f"\n{Colors.BOLD}System:{ Colors.END}")
    success, msg = check_python_version()
    print_status(f"Python version: {msg}", "OK" if success else "ERROR")
    all_checks_passed &= success

    # Commands
    success, msg = check_pyenv()
    print_status(f"pyenv: {msg}", "OK" if success else "WARNING")

    success, msg = check_uv()
    print_status(f"uv: {msg}", "OK" if success else "WARNING")

    success, msg = check_pip()
    print_status(f"pip: {msg}", "OK" if success else "ERROR")
    all_checks_passed &= success

    # Packages
    print(f"\n{Colors.BOLD}Python Packages:{Colors.END}")
    packages = check_required_packages()
    for pkg, (success, msg) in packages.items():
        print_status(f"{pkg}: {msg}", "OK" if success else "ERROR")
        all_checks_passed &= success

    # Environment
    print(f"\n{Colors.BOLD}Environment:{Colors.END}")
    success, msg = check_env_file()
    print_status(f".env file: {msg}", "OK" if success else "WARNING")

    env_vars = check_env_variables()
    for var, (success, msg) in env_vars.items():
        print_status(f"{var}: {msg}", "OK" if success else "WARNING")

    # Database
    print(f"\n{Colors.BOLD}Database:{Colors.END}")
    success, msg = check_database_connection()
    print_status(f"PostgreSQL connection: {msg}", "OK" if success else "ERROR")
    if success:
        success2, msg2 = check_database_tables()
        print_status(f"Database tables: {msg2}", "OK" if success2 else "WARNING")

    # API Keys
    print(f"\n{Colors.BOLD}API Keys:{Colors.END}")
    success, msg = check_congress_api_key()
    print_status(f"Congress API: {msg}", "OK" if success else "ERROR")

    success, msg = check_openstates_api_key()
    print_status(f"OpenStates API: {msg}", "OK" if success else "ERROR")

    success, msg = check_govinfo_api_key()
    print_status(f"GovInfo API: {msg}", "OK" if success else "ERROR")

    # Directories
    print(f"\n{Colors.BOLD}Directory Structure:{Colors.END}")
    dirs = check_directory_structure()
    missing_dirs = [d for d, (success, _) in dirs.items() if not success]
    if missing_dirs:
        print_status(f"Missing directories: {', '.join(missing_dirs)}", "WARNING")
        if args.fix:
            for d in missing_dirs:
                Path(d).mkdir(parents=True, exist_ok=True)
                print_status(f"Created {d}", "OK")
    else:
        print_status("All directories exist", "OK")

    # Summary
    print("\n" + "=" * 70)
    if all_checks_passed:
        print(f"{Colors.GREEN}{Colors.BOLD}✓ Environment verification PASSED{Colors.END}\n")
        return 0
    else:
        print(f"{Colors.YELLOW}{Colors.BOLD}⚠ Environment verification completed with warnings{Colors.END}\n")
        print("Run with --fix to auto-fix some issues")
        return 1


if __name__ == "__main__":
    sys.exit(main())
