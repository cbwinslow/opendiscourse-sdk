#!/usr/bin/env python3
"""
Vector Database Installation Script

This script installs and configures vector databases including pgvector and Qdrant
for the Open Discourse project.
"""

import subprocess
import sys
import os
import json
import logging
from pathlib import Path
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_command(command: str, cwd: str = None) -> bool:
    """Run a shell command and return success status.

    Args:
        command: Command to execute
        cwd: Working directory

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        logger.info(f"Running: {command}")
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True
        )
        logger.info(f"Success: {command}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed: {command}")
        logger.error(f"Error: {e.stderr}")
        return False


def install_python_dependencies() -> bool:
    """Install Python dependencies for vector databases.

    Returns:
        bool: True if successful, False otherwise
    """
    logger.info("Installing Python dependencies...")

    dependencies = [
        "psycopg2-binary",  # PostgreSQL adapter
        "pgvector",         # pgvector Python bindings
        "qdrant-client",    # Qdrant client
        "numpy",            # For vector operations
        "pydantic",         # For data validation
    ]

    for dep in dependencies:
        if not run_command(f"{sys.executable} -m pip install {dep}"):
            logger.error(f"Failed to install {dep}")
            return False

    logger.info("Python dependencies installed successfully")
    return True


def check_docker() -> bool:
    """Check if Docker is installed and running.

    Returns:
        bool: True if Docker is available, False otherwise
    """
    logger.info("Checking Docker installation...")

    if not run_command("docker --version"):
        logger.warning("Docker is not installed or not in PATH")
        return False

    if not run_command("docker-compose --version"):
        logger.warning("Docker Compose is not installed or not in PATH")
        return False

    logger.info("Docker and Docker Compose are available")
    return True


def start_vector_databases() -> bool:
    """Start vector database services using Docker Compose.

    Returns:
        bool: True if successful, False otherwise
    """
    logger.info("Starting vector database services...")

    # Start services
    if not run_command("docker-compose -f docker-compose.infrastructure.yml up -d"):
        logger.error("Failed to start vector database services")
        logger.warning("Docker daemon may not be running in this environment")
        logger.info("You can manually start services with: docker-compose -f docker-compose.infrastructure.yml up -d")
        logger.info("Or use external vector database instances by updating credential files")
        return False

    # Wait for services to be ready
    import time
    logger.info("Waiting for services to be ready...")
    time.sleep(10)

    logger.info("Vector database services started successfully")
    return True


def verify_installation() -> bool:
    """Verify that vector databases are working correctly.

    Returns:
        bool: True if verification passes, False otherwise
    """
    logger.info("Verifying vector database installation...")

    # Test PostgreSQL connection
    try:
        import psycopg2

        # Read PostgreSQL config
        with open("config/vector_store/credentials/postgres.json", "r") as f:
            pg_config = json.load(f)

        connection = psycopg2.connect(
            host=pg_config["host"],
            port=pg_config["port"],
            database=pg_config["database"],
            user=pg_config["user"],
            password=pg_config["password"]
        )

        # Check if pgvector extension exists
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM pg_extension WHERE extname = 'vector';")
        result = cursor.fetchone()

        if result:
            logger.info("✓ pgvector extension is installed and working")
        else:
            logger.warning("⚠ pgvector extension not found")

        cursor.close()
        connection.close()

    except Exception as e:
        logger.error(f"PostgreSQL verification failed: {e}")
        return False

    # Test Qdrant connection
    try:
        from qdrant_client import QdrantClient

        with open("config/vector_store/credentials/qdrant.json", "r") as f:
            qdrant_config = json.load(f)

        client = QdrantClient(
            host=qdrant_config["host"],
            port=qdrant_config["port"]
        )

        # Try to get collections
        collections = client.get_collections()
        logger.info("✓ Qdrant is running and accessible")

    except Exception as e:
        logger.error(f"Qdrant verification failed: {e}")
        return False

    logger.info("Vector database verification completed successfully")
    return True


def create_test_script() -> bool:
    """Create a test script to demonstrate vector database usage.

    Returns:
        bool: True if successful, False otherwise
    """
    logger.info("Creating test script...")

    test_script = '''#!/usr/bin/env python3
"""
Vector Database Test Script

This script demonstrates how to use both pgvector and Qdrant
vector databases.
"""

import sys
import os
sys.path.append(".")

from api.vector_stores.pgvector_client import create_pgvector_client
from api.vector_stores.qdrant_client import create_qdrant_client
import numpy as np
import json

def test_pgvector():
    """Test pgvector functionality."""
    print("\\n=== Testing pgvector ===")

    try:
        # Create client
        client = create_pgvector_client("config/vector_store/credentials/postgres.json")

        # Test health check
        if client.health_check():
            print("✓ pgvector is healthy")
        else:
            print("✗ pgvector health check failed")
            return False

        # Create test data
        vectors = [
            np.random.rand(768).tolist(),
            np.random.rand(768).tolist(),
            np.random.rand(768).tolist()
        ]

        metadatas = [
            {"document_hash": "test-doc-1", "chunk_index": 0, "content": "Test document 1"},
            {"document_hash": "test-doc-1", "chunk_index": 1, "content": "Test document 1 chunk 2"},
            {"document_hash": "test-doc-2", "chunk_index": 0, "content": "Test document 2"}
        ]

        # Insert vectors
        if client.insert_vectors(vectors, metadatas):
            print("✓ Successfully inserted vectors into pgvector")
        else:
            print("✗ Failed to insert vectors")
            return False

        # Search similar
        query_vector = vectors[0]
        results = client.search_similar(query_vector, top_k=2)

        if results:
            print(f"✓ Found {len(results)} similar vectors")
            for result in results:
                print(f"  - Similarity: {result['similarity']:.3f}")
        else:
            print("⚠ No similar vectors found")

        # Get stats
        stats = client.get_collection_stats()
        if stats:
            print(f"✓ Collection stats: {stats}")

        client.close()
        return True

    except Exception as e:
        print(f"✗ pgvector test failed: {e}")
        return False

def test_qdrant():
    """Test Qdrant functionality."""
    print("\\n=== Testing Qdrant ===")

    try:
        # Create client
        client = create_qdrant_client("config/vector_store/credentials/qdrant.json")

        # Test health check
        if client.health_check():
            print("✓ Qdrant is healthy")
        else:
            print("✗ Qdrant health check failed")
            return False

        # Create collection
        if client.create_collection("test_collection", 768):
            print("✓ Successfully created collection in Qdrant")
        else:
            print("⚠ Collection creation failed (may already exist)")

        # Create test data
        vectors = [
            np.random.rand(768).tolist(),
            np.random.rand(768).tolist(),
            np.random.rand(768).tolist()
        ]

        metadatas = [
            {"document_hash": "test-doc-1", "chunk_index": 0, "content": "Test document 1"},
            {"document_hash": "test-doc-1", "chunk_index": 1, "content": "Test document 1 chunk 2"},
            {"document_hash": "test-doc-2", "chunk_index": 0, "content": "Test document 2"}
        ]

        # Insert vectors
        if client.insert_vectors(vectors, metadatas, collection_name="test_collection"):
            print("✓ Successfully inserted vectors into Qdrant")
        else:
            print("✗ Failed to insert vectors")
            return False

        # Search similar
        query_vector = vectors[0]
        results = client.search_similar(query_vector, top_k=2, collection_name="test_collection")

        if results:
            print(f"✓ Found {len(results)} similar vectors")
            for result in results:
                print(f"  - Similarity: {result['similarity']:.3f}")
        else:
            print("⚠ No similar vectors found")

        # Get stats
        stats = client.get_collection_stats("test_collection")
        if stats:
            print(f"✓ Collection stats: {stats}")

        client.close()
        return True

    except Exception as e:
        print(f"✗ Qdrant test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("Vector Database Test Suite")
    print("=" * 50)

    pgvector_success = test_pgvector()
    qdrant_success = test_qdrant()

    print("\\n" + "=" * 50)
    print("Test Results:")
    print(f"pgvector: {'✓ PASS' if pgvector_success else '✗ FAIL'}")
    print(f"Qdrant: {'✓ PASS' if qdrant_success else '✗ FAIL'}")

    if pgvector_success and qdrant_success:
        print("\\n🎉 All tests passed! Vector databases are working correctly.")
    else:
        print("\\n⚠ Some tests failed. Check the logs for details.")

if __name__ == "__main__":
    main()
'''

    try:
        with open("test_vector_databases.py", "w") as f:
            f.write(test_script)
        os.chmod("test_vector_databases.py", 0o755)
        logger.info("Test script created successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to create test script: {e}")
        return False


def main():
    """Main installation function."""
    logger.info("Starting vector database installation...")

    # Check if we're in the right directory
    if not os.path.exists("docker-compose.infrastructure.yml"):
        logger.error("Please run this script from the project root directory")
        sys.exit(1)

    # Install Python dependencies
    if not install_python_dependencies():
        logger.error("Failed to install Python dependencies")
        sys.exit(1)

    # Check Docker (non-fatal)
    docker_available = check_docker()

    if docker_available:
        # Start databases if Docker is available
        if not start_vector_databases():
            logger.warning("Failed to start Docker services. Continuing without service verification...")
            logger.info("You can start services manually with: docker-compose -f docker-compose.infrastructure.yml up -d")
    else:
        logger.warning("Docker not available. Skipping automatic service startup...")
        logger.info("To use the vector databases, either:")
        logger.info("1. Install and start Docker, then run: docker-compose -f docker-compose.infrastructure.yml up -d")
        logger.info("2. Update credential files to point to external vector database instances")

    # Verify installation (attempt connection test)
    verification_success = verify_installation()

    if not verification_success:
        logger.warning("Database verification failed. This is expected if databases are not running.")
        logger.info("You can test the setup once databases are running with: python test_vector_databases.py")

    # Create test script (always do this)
    if not create_test_script():
        logger.error("Failed to create test script")
        sys.exit(1)

    logger.info("🎉 Vector database installation completed!")
    logger.info("")
    logger.info("Files created:")
    logger.info("- api/vector_stores/pgvector_client.py - pgvector client library")
    logger.info("- api/vector_stores/qdrant_client.py - Qdrant client library")
    logger.info("- config/vector_store/credentials/postgres.json - PostgreSQL credentials")
    logger.info("- config/vector_store/credentials/qdrant.json - Qdrant credentials")
    logger.info("- test_vector_databases.py - Test script")
    logger.info("")
    logger.info("Configuration updated:")
    logger.info("- docker-compose.infrastructure.yml - Added pgvector and Qdrant services")
    logger.info("- config/vector_store/config.json - Added vector database configurations")
    logger.info("")
    if docker_available:
        logger.info("Next steps:")
        logger.info("1. Run the test script: python test_vector_databases.py")
        logger.info("2. Start services if not running: docker-compose -f docker-compose.infrastructure.yml up -d")
        logger.info("3. Use the clients from api/vector_stores/ in your application")
    else:
        logger.info("Next steps:")
        logger.info("1. Install and start Docker if you want to use the included services")
        logger.info("2. Or update credential files to point to external vector database instances")
        logger.info("3. Run the test script: python test_vector_databases.py")
    logger.info("")
    logger.info("Database endpoints (when running):")
    logger.info("- PostgreSQL (pgvector): localhost:5432")
    logger.info("- Qdrant: localhost:6333 (HTTP), localhost:6334 (gRPC)")


if __name__ == "__main__":
    main()
