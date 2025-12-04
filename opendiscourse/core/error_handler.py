#!/usr/bin/env python3
"""
Global Error Handler for OpenDiscourse
Automatically handles common database connection issues and other project-wide errors
"""

import os
import sys
import traceback
import logging
import subprocess
import psycopg2
from typing import Optional, Dict, Any, Callable
from pathlib import Path
from functools import wraps
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/cbwinslow/Videos/opendiscourse/logs/error_handler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DatabaseTroubleshooter:
    """Automatic database connection issue resolver"""

    def __init__(self):
        self.connection_templates = {
            'unix_socket': {
                'database': 'opendiscourse',
                'user': 'cbwinslow',
                'host': '/var/run/postgresql',
                'port': None,
                'password': None
            },
            'tcp_connection': {
                'database': 'opendiscourse',
                'user': 'cbwinslow',
                'host': 'localhost',
                'port': 5432,
                'password': None
            },
            'tcp_with_password': {
                'database': 'opendiscourse',
                'user': 'cbwinslow',
                'host': 'localhost',
                'port': 5432,
                'password': os.getenv('DB_PASSWORD', '')
            }
        }

    def diagnose_connection_issue(self, error: Exception) -> Optional[Dict[str, Any]]:
        """Diagnose database connection issues and return fix"""
        error_str = str(error).lower()

        if 'peer authentication failed' in error_str:
            logger.info("Peer authentication failed - trying TCP connection")
            return self.connection_templates['tcp_connection']

        elif 'connection refused' in error_str:
            logger.info("Connection refused - checking if PostgreSQL is running")
            self._start_postgresql_if_needed()
            return self.connection_templates['tcp_connection']

        elif 'database' in error_str and 'does not exist' in error_str:
            logger.info("Database does not exist - creating database")
            self._create_database_if_needed()
            return self.connection_templates['unix_socket']

        elif 'role' in error_str and 'does not exist' in error_str:
            logger.info("User does not exist - creating user")
            self._create_user_if_needed()
            return self.connection_templates['unix_socket']

        elif 'socket' in error_str and ('failed' in error_str or 'no such file' in error_str):
            logger.info("Unix socket issue - trying TCP connection")
            return self.connection_templates['tcp_connection']

        return None

    def _start_postgresql_if_needed(self):
        """Check if PostgreSQL is running (no automatic restart for security)"""
        try:
            result = subprocess.run(['systemctl', 'status', 'postgresql'],
                                  capture_output=True, text=True, timeout=10)
            if 'inactive' in result.stdout or 'dead' in result.stdout:
                logger.warning("PostgreSQL service is not running. Please start it manually:")
                logger.warning("  sudo systemctl start postgresql")
                logger.warning("  sudo systemctl enable postgresql")
                return False
            return True
        except Exception as e:
            logger.error(f"Failed to check PostgreSQL status: {e}")
            return False

    def _create_database_if_needed(self):
        """Check if database exists (no automatic creation for security)"""
        try:
            conn = psycopg2.connect(
                database='postgres',
                user='cbwinslow',
                host='localhost',
                connect_timeout=5
            )
            conn.autocommit = True
            cursor = conn.cursor()
            cursor.execute('SELECT 1 FROM pg_database WHERE datname = %s', ('opendiscourse',))
            exists = cursor.fetchone()

            if not exists:
                logger.warning("Database 'opendiscourse' does not exist. Please create it manually:")
                logger.warning("  sudo -u postgres createdb opendiscourse")
                logger.warning("  or: psql -U postgres -c 'CREATE DATABASE opendiscourse;'")
                cursor.close()
                conn.close()
                return False

            cursor.close()
            conn.close()
            logger.info("Database 'opendiscourse' exists")
            return True

        except Exception as e:
            logger.error(f"Failed to check database existence: {e}")
            logger.warning("Please ensure PostgreSQL is running and database exists:")
            logger.warning("  sudo systemctl status postgresql")
            logger.warning("  sudo -u postgres createdb opendiscourse")
            return False

    def _create_user_if_needed(self):
        """Check if user exists (no automatic creation for security)"""
        try:
            conn = psycopg2.connect(
                database='postgres',
                user='postgres',
                host='localhost',
                connect_timeout=5
            )
            conn.autocommit = True
            cursor = conn.cursor()
            cursor.execute('SELECT 1 FROM pg_roles WHERE rolname = %s', ('cbwinslow',))
            exists = cursor.fetchone()

            if not exists:
                logger.warning("User 'cbwinslow' does not exist. Please create it manually:")
                logger.warning("  sudo -u postgres createuser cbwinslow")
                logger.warning("  or: psql -U postgres -c \"CREATE USER cbwinslow;\"")
                logger.warning("  Then grant privileges: psql -U postgres -c \"GRANT ALL PRIVILEGES ON DATABASE opendiscourse TO cbwinslow;\"")
                cursor.close()
                conn.close()
                return False

            cursor.close()
            conn.close()
            logger.info("User 'cbwinslow' exists")
            return True

        except Exception as e:
            logger.error(f"Failed to check user existence: {e}")
            logger.warning("Please ensure user exists and has proper privileges:")
            logger.warning("  sudo -u postgres createuser cbwinslow")
            logger.warning("  psql -U postgres -c \"GRANT ALL PRIVILEGES ON DATABASE opendiscourse TO cbwinslow;\"")
            return False

    def get_working_connection(self) -> psycopg2.extensions.connection:
        """Get a working database connection with auto-fix"""
        last_error = None

        for template_name, template in self.connection_templates.items():
            try:
                logger.info(f"Trying connection template: {template_name}")

                # Build connection parameters
                params = {k: v for k, v in template.items() if v is not None}
                conn = psycopg2.connect(**params)
                logger.info(f"Successfully connected using {template_name}")
                return conn

            except Exception as e:
                last_error = e
                logger.warning(f"Template {template_name} failed: {e}")

                # Try to fix the issue
                fix = self.diagnose_connection_issue(e)
                if fix:
                    try:
                        params = {k: v for k, v in fix.items() if v is not None}
                        conn = psycopg2.connect(**params)
                        logger.info(f"Fixed issue and connected using template: {template_name}")
                        return conn
                    except Exception as fix_error:
                        logger.error(f"Fix attempt failed: {fix_error}")

        # If all templates failed, raise the last error
        if last_error:
            raise last_error
        else:
            raise Exception("No connection templates available")

class APIKeyValidator:
    """Validates and manages API keys"""

    def __init__(self):
        self.required_keys = {
            'CONGRESS_API_KEY': 'U71JFZEqNsiSranCdbrj4pZaobtoMtAnl18cIJc2',
            'GOVINFO_API_KEY': 'oiihWFbDARKQhZLDcvnXeToEBjWheKWdMV2LiJmN',
            'OPENSTATES_API_KEY': 'a4cffebb-1787-481f-be4c-762638ed0a7f'
        }

    def validate_all_keys(self) -> Dict[str, bool]:
        """Validate all required API keys"""
        results = {}

        for key_name, expected_value in self.required_keys.items():
            actual_value = os.getenv(key_name)

            if not actual_value:
                results[key_name] = False
                logger.error(f"Missing API key: {key_name}")
                self._fix_missing_key(key_name, expected_value)
            elif actual_value == expected_value:
                results[key_name] = True
                logger.info(f"Valid API key: {key_name}")
            else:
                results[key_name] = False
                logger.warning(f"Invalid API key for {key_name}")
                self._fix_invalid_key(key_name, expected_value)

        return results

    def _fix_missing_key(self, key_name: str, value: str):
        """Add missing API key to environment"""
        env_file = Path('/home/cbwinslow/Videos/opendiscourse/.env')

        try:
            if env_file.exists():
                content = env_file.read_text()
                if key_name not in content:
                    with open(env_file, 'a') as f:
                        f.write(f'\n{key_name}={value}\n')
                    logger.info(f"Added missing {key_name} to .env file")
            else:
                env_file.write_text(f'{key_name}={value}\n')
                logger.info(f"Created .env file with {key_name}")

            # Set environment variable for current session
            os.environ[key_name] = value

        except Exception as e:
            logger.error(f"Failed to fix missing key {key_name}: {e}")

    def _fix_invalid_key(self, key_name: str, correct_value: str):
        """Fix invalid API key"""
        self._fix_missing_key(key_name, correct_value)

class EnvironmentValidator:
    """Validates and fixes environment setup"""

    def __init__(self):
        self.project_root = Path('/home/cbwinslow/Videos/opendiscourse')
        self.required_dirs = ['logs', 'data', 'scripts', 'config']
        self.required_files = ['.env', 'requirements.txt']

    def validate_environment(self) -> Dict[str, bool]:
        """Validate project environment"""
        results = {}

        # Check directories
        for dir_name in self.required_dirs:
            dir_path = self.project_root / dir_name
            if dir_path.exists():
                results[f'dir_{dir_name}'] = True
            else:
                results[f'dir_{dir_name}'] = False
                logger.warning(f"Missing directory: {dir_name}")
                self._create_directory(dir_path)

        # Check files
        for file_name in self.required_files:
            file_path = self.project_root / file_name
            if file_path.exists():
                results[f'file_{file_name}'] = True
            else:
                results[f'file_{file_name}'] = False
                logger.warning(f"Missing file: {file_name}")
                self._create_file(file_path)

        return results

    def _create_directory(self, dir_path: Path):
        """Create missing directory"""
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {dir_path}")
        except PermissionError:
            logger.error(f"Permission denied creating directory {dir_path}")
            logger.warning(f"Please create manually: mkdir -p {dir_path}")
        except Exception as e:
            logger.error(f"Failed to create directory {dir_path}: {e}")

    def _create_file(self, file_path: Path):
        """Create missing file"""
        try:
            if file_path.name == '.env':
                file_path.write_text("""# OpenDiscourse Environment Variables
CONGRESS_API_KEY=U71JFZEqNsiSranCdbrj4pZaobtoMtAnl18cIJc2
GOVINFO_API_KEY=oiihWFbDARKQhZLDcvnXeToEBjWheKWdMV2LiJmN
OPENSTATES_API_KEY=a4cffebb-1787-481f-be4c-762638ed0a7f
DB_NAME=opendiscourse
DB_USER=cbwinslow
""")
            elif file_path.name == 'requirements.txt':
                file_path.write_text("""# OpenDiscourse Dependencies
psycopg2-binary==2.9.7
requests==2.31.0
python-dotenv==1.0.0
""")
            logger.info(f"Created file: {file_path}")
        except PermissionError:
            logger.error(f"Permission denied creating file {file_path}")
            logger.warning(f"Please create manually with appropriate content")
        except Exception as e:
            logger.error(f"Failed to create file {file_path}: {e}")

class GlobalErrorHandler:
    """Main global error handler class"""

    def __init__(self):
        self.db_troubleshooter = DatabaseTroubleshooter()
        self.api_validator = APIKeyValidator()
        self.env_validator = EnvironmentValidator()
        self.error_log = []

    def handle_database_error(self, error: Exception, retry_func: Callable = None):
        """Handle database errors with automatic fixes"""
        self._log_error(error)

        if isinstance(error, psycopg2.OperationalError):
            logger.info("Attempting to fix database connection issue...")
            try:
                conn = self.db_troubleshooter.get_working_connection()
                logger.info("Database connection fixed!")

                if retry_func:
                    return retry_func(conn)
                return conn

            except Exception as fix_error:
                logger.error(f"Failed to fix database connection: {fix_error}")
                raise error

        raise error

    def handle_api_error(self, error: Exception, service: str = None):
        """Handle API errors"""
        self._log_error(error)

        if service:
            logger.error(f"API error for {service}: {error}")

        # Validate API keys
        validation_results = self.api_validator.validate_all_keys()
        if not all(validation_results.values()):
            logger.warning("Some API keys were invalid and have been fixed")

        return error

    def handle_import_error(self, error: Exception):
        """Handle import errors"""
        self._log_error(error)

        error_str = str(error).lower()
        if 'psycopg2' in error_str:
            logger.info("Installing psycopg2-binary...")
            try:
                subprocess.run(['pip', 'install', 'psycopg2-binary'], check=True)
                logger.info("psycopg2-binary installed successfully")
            except Exception as install_error:
                logger.error(f"Failed to install psycopg2-binary: {install_error}")

        elif 'requests' in error_str:
            logger.info("Installing requests...")
            try:
                subprocess.run(['pip', 'install', 'requests'], check=True)
                logger.info("requests installed successfully")
            except Exception as install_error:
                logger.error(f"Failed to install requests: {install_error}")

        return error

    def validate_project_setup(self) -> Dict[str, Any]:
        """Validate entire project setup"""
        logger.info("Validating project setup...")

        results = {
            'database': self._test_database_connection(),
            'api_keys': self.api_validator.validate_all_keys(),
            'environment': self.env_validator.validate_environment(),
            'timestamp': datetime.now().isoformat()
        }

        logger.info(f"Project validation complete: {results}")
        return results

    def _test_database_connection(self) -> bool:
        """Test database connection"""
        try:
            conn = self.db_troubleshooter.get_working_connection()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False

    def _log_error(self, error: Exception):
        """Log error details"""
        error_info = {
            'timestamp': datetime.now().isoformat(),
            'type': type(error).__name__,
            'message': str(error),
            'traceback': traceback.format_exc()
        }

        self.error_log.append(error_info)
        logger.error(f"Error logged: {error_info}")

# Global instance
global_error_handler = GlobalErrorHandler()

def safe_database_connection(func):
    """Decorator for safe database operations with automatic error handling"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except psycopg2.Error as e:
            logger.info(f"Database error in {func.__name__}, attempting recovery...")

            def retry_with_connection(conn):
                # Update function args with working connection if needed
                if 'conn' in kwargs:
                    kwargs['conn'] = conn
                elif args and hasattr(args[0], 'conn'):
                    args[0].conn = conn
                return func(*args, **kwargs)

            return global_error_handler.handle_database_error(e, retry_with_connection)

    return wrapper

def safe_api_call(func):
    """Decorator for safe API calls with automatic error handling"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            service = kwargs.get('service', 'unknown')
            global_error_handler.handle_api_error(e, service)
            raise e

    return wrapper

def validate_environment_before_run(func):
    """Decorator to validate environment before running function"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        validation = global_error_handler.validate_project_setup()

        if not validation['database']:
            raise Exception("Database connection failed - cannot proceed")

        if not all(validation['api_keys'].values()):
            logger.warning("Some API keys are invalid - may affect functionality")

        return func(*args, **kwargs)

    return wrapper

# Auto-fix common issues on import
try:
    global_error_handler.validate_project_setup()
except Exception as e:
    logger.warning(f"Initial validation failed: {e}")

logger.info("Global error handler initialized")
