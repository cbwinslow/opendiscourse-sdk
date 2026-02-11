#!/usr/bin/env python3
"""
Vector Database Test Script

This script demonstrates how to use both pgvector and Qdrant
vector databases.
"""

import sys

sys.path.append(".")


import numpy as np

from api.vector_stores.pgvector_client import create_pgvector_client
from api.vector_stores.qdrant_client import create_qdrant_client


def test_pgvector():
    """Test pgvector functionality."""
    print("\n=== Testing pgvector ===")

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
    print("\n=== Testing Qdrant ===")

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

    print("\n" + "=" * 50)
    print("Test Results:")
    print(f"pgvector: {'✓ PASS' if pgvector_success else '✗ FAIL'}")
    print(f"Qdrant: {'✓ PASS' if qdrant_success else '✗ FAIL'}")

    if pgvector_success and qdrant_success:
        print("\n🎉 All tests passed! Vector databases are working correctly.")
    else:
        print("\n⚠ Some tests failed. Check the logs for details.")

if __name__ == "__main__":
    main()
