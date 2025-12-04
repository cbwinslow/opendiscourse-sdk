"""
Database Bootstrap and Management.

Provides functionality to create, migrate, and manage PostgreSQL databases.
"""

import subprocess
import sys
from pathlib import Path
from typing import Optional, List
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOL ATION_LEVEL_AUTOCOMMIT

from scripts.core.config import Settings, get_settings


class DatabaseBootstrap:
    """Database bootstrap and migration manager."""

    def __init__(self, settings: Optional[Settings] = None):
        """
        Initialize database bootstrap.

        Args:
            settings: Application settings (uses global if not provided)
        """
        self.settings = settings or get_settings()
        self.db_config = self.settings.database
        self.migrations_dir = self.settings.migrations_dir

    def database_exists(self) -> bool:
        """
        Check if database exists.

        Returns:
            True if database exists
        """
        try:
            # Connect to postgres database to check if our database exists
            conn = psycopg2.connect(
                host=self.db_config.host,
                port=self.db_config.port,
                user=self.db_config.user,
                password=self.db_config.password.get_secret_value() if self.db_config.password else None,
                dbname='postgres'
            )
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

            cursor = conn.cursor()
            cursor.execute(
                "SELECT 1 FROM pg_database WHERE datname = %s",
                (self.db_config.name,)
            )
            exists = cursor.fetchone() is not None

            cursor.close()
            conn.close()

            return exists

        except psycopg2.Error as e:
            print(f"❌ Error checking database existence: {e}")
            return False

    def create_database(self) -> bool:
        """
        Create database if it doesn't exist.

        Returns:
            True if created successfully
        """
        if self.database_exists():
            print(f"✓ Database '{self.db_config.name}' already exists")
            return True

        try:
            print(f"📊 Creating database '{self.db_config.name}'...")

            # Connect to postgres database
            conn = psycopg2.connect(
                host=self.db_config.host,
                port=self.db_config.port,
                user=self.db_config.user,
                password=self.db_config.password.get_secret_value() if self.db_config.password else None,
                dbname='postgres'
            )
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

            cursor = conn.cursor()
            cursor.execute(
                sql.SQL("CREATE DATABASE {}").format(
                    sql.Identifier(self.db_config.name)
                )
            )

            cursor.close()
            conn.close()

            print(f"✅ Database '{self.db_config.name}' created successfully")
            return True

        except psycopg2.Error as e:
            print(f"❌ Error creating database: {e}")
            return False

    def get_applied_migrations(self) -> List[str]:
        """
        Get list of applied migrations.

        Returns:
            List of applied migration filenames
        """
        try:
            conn = psycopg2.connect(self.db_config.dsn)
            cursor = conn.cursor()

            # Create migrations table if it doesn't exist
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    id SERIAL PRIMARY KEY,
                    migration VARCHAR(255) UNIQUE NOT NULL,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

            # Get applied migrations
            cursor.execute("SELECT migration FROM schema_migrations ORDER BY id")
            migrations = [row[0] for row in cursor.fetchall()]

            cursor.close()
            conn.close()

            return migrations

        except psycopg2.Error as e:
            print(f"❌ Error getting applied migrations: {e}")
            return []

    def get_pending_migrations(self) -> List[Path]:
        """
        Get list of pending migration files.

        Returns:
            List of migration file paths
        """
        if not self.migrations_dir.exists():
            print(f"⚠️  Migrations directory not found: {self.migrations_dir}")
            return []

        # Get all migration files
        migration_files = sorted(self.migrations_dir.glob("*.sql"))

        # Get applied migrations
        applied = set(self.get_applied_migrations())

        # Filter to pending only
        pending = [f for f in migration_files if f.name not in applied]

        return pending

    def apply_migration(self, migration_file: Path) -> bool:
        """
        Apply a single migration file.

        Args:
            migration_file: Path to migration SQL file

        Returns:
            True if successful
        """
        try:
            print(f"📝 Applying migration: {migration_file.name}")

            conn = psycopg2.connect(self.db_config.dsn)
            cursor = conn.cursor()

            # Read and execute migration
            with open(migration_file, 'r') as f:
                migration_sql = f.read()

            cursor.execute(migration_sql)

            # Record migration
            cursor.execute(
                "INSERT INTO schema_migrations (migration) VALUES (%s)",
                (migration_file.name,)
            )

            conn.commit()
            cursor.close()
            conn.close()

            print(f"✅ Migration applied: {migration_file.name}")
            return True

        except psycopg2.Error as e:
            print(f"❌ Error applying migration {migration_file.name}: {e}")
            if conn:
                conn.rollback()
                conn.close()
            return False

    def migrate(self) -> bool:
        """
        Apply all pending migrations.

        Returns:
            True if all migrations successful
        """
        pending = self.get_pending_migrations()

        if not pending:
            print("✓ No pending migrations")
            return True

        print(f"📦 Found {len(pending)} pending migration(s)")

        success = True
        for migration_file in pending:
            if not self.apply_migration(migration_file):
                success = False
                break

        return success

    def bootstrap(self, create_db: bool = True) -> bool:
        """
        Bootstrap database (create + migrate).

        Args:
            create_db: Whether to create database if it doesn't exist

        Returns:
            True if successful
        """
        print("🚀 Bootstrapping database...")

        # Create database if requested
        if create_db:
            if not self.create_database():
                return False

        # Apply migrations
        if not self.migrate():
            print("❌ Migration failed")
            return False

        print("✅ Database bootstrap complete")
        return True

    def test_connection(self) -> bool:
        """
        Test database connection.

        Returns:
            True if connection successful
        """
        try:
            print(f"🔌 Testing connection to {self.db_config.host}:{self.db_config.port}/{self.db_config.name}...")

            conn = psycopg2.connect(self.db_config.dsn)
            cursor = conn.cursor()
            cursor.execute("SELECT version()")
            version = cursor.fetchone()[0]

            cursor.close()
            conn.close()

            print(f"✅ Connection successful")
            print(f"   PostgreSQL version: {version}")
            return True

        except psycopg2.Error as e:
            print(f"❌ Connection failed: {e}")
            return False


def bootstrap_interactive() -> bool:
    """
    Interactive database bootstrap.

    Returns:
        True if successful
    """
    print("=" * 60)
    print("OpenDiscourse Database Bootstrap")
    print("=" * 60)
    print()

    settings = get_settings()
    bootstrap = DatabaseBootstrap(settings)

    # Test connection to PostgreSQL server
    print("Step 1: Testing PostgreSQL connection...")
    try:
        conn = psycopg2.connect(
            host=settings.database.host,
            port=settings.database.port,
            user=settings.database.user,
            password=settings.database.password.get_secret_value() if settings.database.password else None,
            dbname='postgres'
        )
        conn.close()
        print("✅ PostgreSQL server connection successful")
    except psycopg2.Error as e:
        print(f"❌ Cannot connect to PostgreSQL server: {e}")
        print("\nPlease check your database configuration in .env file:")
        print(f"  DB_HOST={settings.database.host}")
        print(f"  DB_PORT={settings.database.port}")
        print(f"  DB_USER={settings.database.user}")
        return False

    print()

    # Check if database exists
    print("Step 2: Checking database status...")
    db_exists = bootstrap.database_exists()

    if db_exists:
        print(f"✓ Database '{settings.database.name}' exists")
        create = False
    else:
        print(f"⚠️  Database '{settings.database.name}' does not exist")

        response = input(f"\nCreate database '{settings.database.name}'? [Y/n]: ").strip().lower()
        create = response in ['', 'y', 'yes']

        if not create:
            print("❌ Database creation cancelled")
            return False

    print()

    # Bootstrap
    print("Step 3: Running bootstrap...")
    success = bootstrap.bootstrap(create_db=create)

    if success:
        print()
        print("=" * 60)
        print("✅ Bootstrap Complete!")
        print("=" * 60)
        print()
        print("Your database is ready. You can now use the CLI tools:")
        print("  opendiscourse-congress ingest-bills 118")
        print("  opendiscourse-states ingest-bills ca")
        print("  opendiscourse-govinfo ingest-collections")
        print()

    return success
