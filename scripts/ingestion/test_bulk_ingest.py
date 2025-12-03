#!/usr/bin/env python3
"""
Test script for bulk ingestion
Runs a small test with 2 states to validate the system
"""

import asyncio
import yaml
import sys
from pathlib import Path

# Modify path
sys.path.append(str(Path(__file__).parent))

async def test_run():
    """Run a small test ingestion"""
    print("🧪 Starting test ingestion run")
    print("=" * 60)

    # Create a test config
    test_config = {
        'openstates': {
            'enabled': True,
            'api_key': '',  # Will be loaded from env
            'jurisdictions': ['ca', 'ny'],  # Just 2 states for testing
            'data_types': ['jurisdictions', 'people', 'organizations', 'sessions'],
            'rate_limit': 100,
            'concurrent_requests': 5
        },
        'congress': {'enabled': False},
        'govinfo': {'enabled': False},
        'database': {
            'name': 'opendiscourse',
            'user': 'cbwinslow',
            'password': '',
            'host': '',
            'port': '',
            'min_pool_size': 2,
            'max_pool_size': 5,
            'batch_size': 50
        },
        'performance': {
            'async_mode': True,
            'parallel_jobs': 2,
            'worker_threads': 2,
            'connection_pooling': True
        },
        'checkpointing': {
            'enabled': True,
            'save_interval': 50,
            'resume_on_startup': True
        },
        'error_handling': {
            'max_retries': 3,
            'retry_delay': 1,
            'exponential_backoff': True,
            'continue_on_error': True
        },
        'logging': {
            'level': 'INFO',
            'file': 'logs/test_ingestion.log',
            'console': True
        },
        'reporting': {
            'console_updates': True,
            'update_interval': 10,
            'progress_bar': True,
            'final_summary': True
        }
    }

    # Save test config
    import os
    os.makedirs('config', exist_ok=True)
    with open('config/test_ingestion_config.yaml', 'w') as f:
        yaml.dump(test_config, f)

    print("✅ Created test configuration")
    print(f"   - States: {test_config['openstates']['jurisdictions']}")
    print(f"   - Data types: {test_config['openstates']['data_types']}")
    print(f"   - Parallel jobs: {test_config['performance']['parallel_jobs']}")
    print()

    # Import and run orchestrator
    from bulk_ingest import BulkIngestionOrchestrator

    orchestrator = BulkIngestionOrchestrator('config/test_ingestion_config.yaml')

    print("🚀 Starting test ingestion...")
    print()

    await orchestrator.run()

    print()
    print("=" * 60)
    print("🎉 Test ingestion complete!")
    print()
    print("Check the database with:")
    print("  psql -d opendiscourse -c \"SELECT * FROM ingestion.ingestion_jobs ORDER BY started_at DESC LIMIT 5;\"")
    print("  psql -d opendiscourse -c \"SELECT COUNT(*) FROM openstates.people;\"")


if __name__ == '__main__':
    asyncio.run(test_run())
