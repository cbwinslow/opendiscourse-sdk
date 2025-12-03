#!/usr/bin/env python3
"""
Debug script to test the bulk_ingest configuration and connection
"""
import asyncio
import yaml
import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

async def test_bulk_ingest_connection():
    """Test the exact same connection logic as bulk_ingest"""

    # Load config
    with open('config/ingestion_config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    # Expand env vars (same as bulk_ingest FIXED version)
    def expand_env_vars(cfg):
        if isinstance(cfg, dict):
            for key, value in cfg.items():
                if isinstance(value, str) and value.startswith('${') and value.endswith('}'):
                    # Parse ${VAR:-default} or ${VAR}
                    inner = value[2:-1]  # Remove ${ and }
                    if ':-' in inner:
                        var_name, default = inner.split(':-', 1)
                    else:
                        var_name = inner
                        default = ''
                    cfg[key] = os.getenv(var_name, default)
                elif isinstance(value, (dict, list)):
                    expand_env_vars(value)
        elif isinstance(cfg, list):
            for item in cfg:
                expand_env_vars(item)

    expand_env_vars(config)

    db_config = config['database']
    print("Database configuration after env expansion:")
    for k, v in db_config.items():
        print(f"  {k}: {repr(v)}")
    print()

    # Build connection kwargs (same as AsyncIngestionManager)
    conn_kwargs = {
        'database': db_config['name'],
        'user': db_config.get('user', 'cbwinslow'),
        'min_size': db_config.get('min_pool_size', 5),
        'max_size': db_config.get('max_pool_size', 20)
    }

    # Add host/port if provided
    if db_config.get('host'):
        conn_kwargs['host'] = db_config['host']
        print(f"  Setting host: {db_config['host']}")

    if db_config.get('port') and str(db_config['port']).strip():
        try:
            conn_kwargs['port'] = int(db_config['port'])
            print(f"  Setting port: {conn_kwargs['port']}")
        except (ValueError, TypeError) as e:
            print(f"  ⚠️  Port parse error: {e}")

    if db_config.get('password'):
        conn_kwargs['password'] = db_config['password']
        print(f"  Setting password: {'***' if db_config['password'] else '(empty)'}")

    print(f"\nConnection kwargs:")
    for k, v in conn_kwargs.items():
        if k == 'password':
            print(f"  {k}: ***")
        else:
            print(f"  {k}: {v}")
    print()

    # Try to connect
    try:
        import asyncpg
        pool = await asyncpg.create_pool(**conn_kwargs)
        print("✅ Connection pool created successfully!")

        # Test a query
        async with pool.acquire() as conn:
            result = await conn.fetchval("SELECT COUNT(*) FROM openstates.people")
            print(f"✅ Query successful: {result} people in database")

        await pool.close()
        return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = asyncio.run(test_bulk_ingest_connection())
    sys.exit(0 if success else 1)
