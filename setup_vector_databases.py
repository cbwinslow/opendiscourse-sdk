#!/usr/bin/env python3
"""
Vector Database Setup Assistant

This script helps you choose and configure your preferred method for
installing and running pgvector and Qdrant vector databases.
"""

import json
import os
import subprocess
import sys


def print_header():
    """Print setup assistant header."""
    print("=" * 60)
    print("🚀 Vector Database Setup Assistant")
    print("=" * 60)
    print("This script will help you set up pgvector and Qdrant")
    print("Choose your preferred installation method:\n")

def choose_installation_method():
    """Choose installation method for vector databases."""
    print("Available Installation Methods:")
    print("1. 🐳 Docker Compose (Recommended)")
    print("2. 🖥️  Local Installation")
    print("3. ☁️  Cloud Services")
    print("4. 📋 Manual Setup (Advanced)")
    print("5. 🔍 Test Only (Verify existing setup)")
    print()

    while True:
        choice = input("Select option (1-5): ").strip()
        if choice in ['1', '2', '3', '4', '5']:
            return int(choice)
        else:
            print("Please select a valid option (1-5)")

def setup_docker_method():
    """Setup using Docker Compose."""
    print("\n🐳 Docker Compose Setup")
    print("-" * 30)

    # Check Docker availability
    try:
        subprocess.run(['docker', '--version'], check=True, capture_output=True)
        subprocess.run(['docker-compose', '--version'], check=True, capture_output=True)
        print("✓ Docker and Docker Compose are available")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Docker or Docker Compose not found")
        print("\nTo install Docker:")
        print("- Visit: https://docs.docker.com/get-docker/")
        print("- Or use your package manager:")
        print("  Ubuntu: sudo apt install docker.io docker-compose")
        print("  macOS: brew install docker docker-compose")
        return False

    # Start services
    print("\nStarting vector database services...")
    try:
        result = subprocess.run([
            'docker-compose', '-f', 'docker-compose.infrastructure.yml', 'up', '-d'
        ], check=True, capture_output=True, text=True)
        print("✓ Services started successfully")
        print("\nServices are now running:")
        print("- PostgreSQL with pgvector: localhost:5432")
        print("- Qdrant: localhost:6333 (HTTP), localhost:6334 (gRPC)")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start services: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure Docker daemon is running")
        print("2. Check if ports 5432, 6333, 6334 are available")
        print("3. Run 'docker-compose logs' to see detailed logs")
        return False

def setup_local_method():
    """Setup using local installation."""
    print("\n🖥️ Local Installation Setup")
    print("-" * 30)

    print("This method installs vector databases directly on your system.")
    print("\nSupported platforms:")
    print("- Ubuntu/Debian Linux")
    print("- macOS (with Homebrew)")
    print("- Windows (installers available)")

    # PostgreSQL setup
    print("\n📊 PostgreSQL with pgvector:")
    print("1. Ubuntu/Debian: sudo apt install postgresql-15-pgvector")
    print("2. macOS: brew install postgresql@15 pgvector")
    print("3. Windows: Download from postgresql.org (check pgvector option)")

    # Qdrant setup
    print("\n🎯 Qdrant:")
    print("1. Linux: Download from github.com/qdrant/qdrant")
    print("2. macOS: brew install qdrant")
    print("3. Windows: Use Docker or compile from source")

    print("\nAfter installation, update credential files in:")
    print("- config/vector_store/credentials/postgres.json")
    print("- config/vector_store/credentials/qdrant.json")

    return False  # User needs to manually install

def setup_cloud_method():
    """Setup using cloud services."""
    print("\n☁️ Cloud Services Setup")
    print("-" * 30)

    print("Using managed cloud services for vector databases:\n")

    # PostgreSQL cloud options
    print("📊 PostgreSQL Options:")
    print("1. AWS RDS - Enable pgvector extension")
    print("2. Supabase - Built-in pgvector support")
    print("3. Neon - Modern PostgreSQL with pgvector")
    print("4. Google Cloud SQL - Enable pgvector extension")
    print("5. Azure Database - Enable pgvector extension")

    # Qdrant cloud options
    print("\n🎯 Qdrant Options:")
    print("1. Qdrant Cloud - Official managed service")
    print("2. Self-hosted on cloud VM")
    print("3. Kubernetes on cloud provider")

    print("\n💡 Recommended combination:")
    print("- PostgreSQL: Supabase or Neon")
    print("- Qdrant: Qdrant Cloud")

    print("\nAfter setting up cloud services:")
    print("1. Update credential files with connection details")
    print("2. Test connections using test scripts")

    return False  # User needs to set up cloud services

def setup_manual_method():
    """Manual advanced setup."""
    print("\n📋 Manual Setup (Advanced)")
    print("-" * 30)

    print("This option provides advanced configuration for experienced users.\n")

    print("Steps:")
    print("1. Choose PostgreSQL source (local/cloud/custom)")
    print("2. Choose Qdrant source (local/cloud/custom)")
    print("3. Configure connection credentials")
    print("4. Set up security and access controls")
    print("5. Configure monitoring and logging")
    print("6. Set up backup and recovery")

    print("\n📚 See EXTERNAL_INSTALLATION_GUIDE.md for detailed instructions")
    print("📚 See VECTOR_DATABASE_README.md for API integration")

    return False

def test_existing_setup():
    """Test existing vector database setup."""
    print("\n🔍 Testing Existing Setup")
    print("-" * 30)

    # Test PostgreSQL/pgvector
    print("Testing PostgreSQL/pgvector connection...")
    try:
        from api.vector_stores.pgvector_client import create_pgvector_client
        client = create_pgvector_client("config/vector_store/credentials/postgres.json")
        if client.health_check():
            print("✓ PostgreSQL/pgvector is accessible")

            # Get stats
            stats = client.get_collection_stats()
            if stats:
                print(f"  Database stats: {stats}")
        else:
            print("✗ PostgreSQL/pgvector health check failed")
        client.close()
    except Exception as e:
        print(f"✗ PostgreSQL/pgvector connection failed: {e}")

    # Test Qdrant
    print("\nTesting Qdrant connection...")
    try:
        from api.vector_stores.qdrant_client import create_qdrant_client
        client = create_qdrant_client("config/vector_store/credentials/qdrant.json")
        if client.health_check():
            print("✓ Qdrant is accessible")

            # List collections
            collections = client.list_collections()
            if collections:
                print(f"  Collections: {collections}")
        else:
            print("✗ Qdrant health check failed")
        client.close()
    except Exception as e:
        print(f"✗ Qdrant connection failed: {e}")

    print("\n🔧 To fix connection issues:")
    print("1. Check credential files in config/vector_store/credentials/")
    print("2. Verify database services are running")
    print("3. Check network connectivity and firewall settings")

def update_credentials_cloud(cloud_type):
    """Update credentials for cloud services."""
    print(f"\nUpdating credentials for {cloud_type}...")

    if cloud_type.lower() == "supabase":
        print("Enter your Supabase connection details:")
        supabase_url = input("Supabase URL: ").strip()
        anon_key = input("Supabase Anon Key: ").strip()

        # Update PostgreSQL credentials
        pg_config = {
            "host": supabase_url.replace("https://", "").replace("http://", ""),
            "port": 5432,
            "database": "postgres",
            "user": "postgres",
            "password": anon_key,
            "connection_pool_size": 10,
            "connection_timeout": 30,
            "ssl_mode": "require",
            "options": "-c search_path=public"
        }

        with open("config/vector_store/credentials/postgres.json", "w") as f:
            json.dump(pg_config, f, indent=2)

        print("✓ Supabase credentials updated")

    elif cloud_type.lower() == "qdrant cloud":
        print("Enter your Qdrant Cloud connection details:")
        host = input("Qdrant Cloud URL: ").strip()
        api_key = input("Qdrant Cloud API Key: ").strip()

        qdrant_config = {
            "host": host.replace("https://", "").replace("http://", ""),
            "port": 443,
            "grpc_port": 443,
            "api_key": api_key,
            "prefer_grpc": True,
            "https": True
        }

        with open("config/vector_store/credentials/qdrant.json", "w") as f:
            json.dump(qdrant_config, f, indent=2)

        print("✓ Qdrant Cloud credentials updated")

def run_final_tests():
    """Run comprehensive tests after setup."""
    print("\n🧪 Running Final Tests")
    print("-" * 30)

    # Create test data
    print("Creating test script...")
    test_script = '''#!/usr/bin/env python3
import sys
sys.path.append(".")
import numpy as np
from api.vector_stores.pgvector_client import create_pgvector_client
from api.vector_stores.qdrant_client import create_qdrant_client

def comprehensive_test():
    print("🧪 Comprehensive Vector Database Test")
    print("=" * 50)

    # Generate test data
    test_vectors = [np.random.rand(768).tolist() for _ in range(5)]
    test_metadatas = [
        {"document_hash": f"doc-{i}", "chunk_index": 0, "content": f"Test document {i}"}
        for i in range(5)
    ]

    # Test pgvector
    print("\\n📊 Testing PostgreSQL/pgvector...")
    try:
        pg_client = create_pgvector_client("config/vector_store/credentials/postgres.json")
        if pg_client.health_check():
            print("✓ pgvector health check passed")

            # Create collection
            if pg_client.create_collection("test_vectors", 768):
                print("✓ Created test collection")

            # Insert vectors
            if pg_client.insert_vectors(test_vectors[:3], test_metadatas[:3]):
                print("✓ Inserted vectors into pgvector")

                # Search
                results = pg_client.search_similar(test_vectors[0], top_k=2)
                if results:
                    print(f"✓ Found {len(results)} similar vectors")

            print("✓ PostgreSQL/pgvector test completed")
        else:
            print("✗ pgvector health check failed")
        pg_client.close()
    except Exception as e:
        print(f"✗ PostgreSQL/pgvector test failed: {e}")

    # Test Qdrant
    print("\\n🎯 Testing Qdrant...")
    try:
        qdrant_client = create_qdrant_client("config/vector_store/credentials/qdrant.json")
        if qdrant_client.health_check():
            print("✓ Qdrant health check passed")

            # Create collection
            if qdrant_client.create_collection("test_vectors", 768):
                print("✓ Created test collection")

            # Insert vectors
            if qdrant_client.insert_vectors(test_vectors[:3], test_metadatas[:3]):
                print("✓ Inserted vectors into Qdrant")

                # Search
                results = qdrant_client.search_similar(test_vectors[0], top_k=2)
                if results:
                    print(f"✓ Found {len(results)} similar vectors")

            print("✓ Qdrant test completed")
        else:
            print("✗ Qdrant health check failed")
        qdrant_client.close()
    except Exception as e:
        print(f"✗ Qdrant test failed: {e}")

    print("\\n🎉 Vector database setup complete!")

if __name__ == "__main__":
    comprehensive_test()
'''

    with open("comprehensive_test.py", "w") as f:
        f.write(test_script)
    os.chmod("comprehensive_test.py", 0o755)

    print("✓ Test script created: comprehensive_test.py")

    # Ask if user wants to run tests
    run_tests = input("\nRun comprehensive tests now? (y/N): ").strip().lower()
    if run_tests == 'y':
        try:
            subprocess.run([sys.executable, "comprehensive_test.py"])
        except Exception as e:
            print(f"Test execution failed: {e}")

def main():
    """Main setup assistant function."""
    print_header()

    choice = choose_installation_method()

    success = False
    if choice == 1:
        success = setup_docker_method()
    elif choice == 2:
        setup_local_method()
    elif choice == 3:
        cloud_service = input("Which cloud service? (supabase/qdrant cloud/both): ").strip().lower()
        if cloud_service in ["supabase", "both"]:
            update_credentials_cloud("supabase")
        if cloud_service in ["qdrant cloud", "both"]:
            update_credentials_cloud("qdrant cloud")
        success = True
    elif choice == 4:
        setup_manual_method()
    elif choice == 5:
        test_existing_setup()
        success = True

    if choice != 5:
        print("\n" + "=" * 60)
        if success:
            print("✅ Setup completed successfully!")
            run_final_tests()
        else:
            print("⚠️ Setup requires manual intervention")
            print("\nNext steps:")
            print("1. Check the installation guides:")
            print("   - VECTOR_DATABASE_README.md")
            print("   - EXTERNAL_INSTALLATION_GUIDE.md")
            print("2. Run: python comprehensive_test.py")
        print("=" * 60)

if __name__ == "__main__":
    main()
