#!/usr/bin/env python3
"""
High-Performance Bulk Ingestion Orchestrator
Uses async I/O, connection pooling, and parallel processing for maximum speed
"""

import asyncio
import aiohttp
import os
import sys
import yaml
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import asyncpg
from tqdm.asyncio import tqdm

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/bulk_ingestion.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class RateLimiter:
    """Async rate limiter using token bucket algorithm"""
    def __init__(self, rate: int, per: float = 60.0):
        self.rate = rate
        self.per = per
        self.allowance = rate
        self.last_check = asyncio.get_event_loop().time()
        self._lock = asyncio.Lock()

    async def acquire(self):
        async with self._lock:
            current = asyncio.get_event_loop().time()
            time_passed = current - self.last_check
            self.last_check = current
            self.allowance += time_passed * (self.rate / self.per)

            if self.allowance > self.rate:
                self.allowance = self.rate

            if self.allowance < 1.0:
                sleep_time = (1.0 - self.allowance) * (self.per / self.rate)
                await asyncio.sleep(sleep_time)
                self.allowance = 0.0
            else:
                self.allowance -= 1.0


class AsyncIngestionManager:
    """Async version of IngestionManager with connection pooling"""

    def __init__(self, config: Dict):
        self.config = config
        self.db_pool = None
        self.job_id = None

    async def connect(self):
        """Create async connection pool"""
        db_config = self.config['database']

        # Build connection string
        conn_kwargs = {
            'database': db_config['name'],
            'user': db_config.get('user', 'cbwinslow'),
            'min_size': db_config.get('min_pool_size', 5),
            'max_size': db_config.get('max_pool_size', 20)
        }

        # Add host/port if provided (otherwise use Unix socket)
        if db_config.get('host'):
            conn_kwargs['host'] = db_config['host']
        if db_config.get('port') and str(db_config['port']).strip():
            try:
                conn_kwargs['port'] = int(db_config['port'])
            except (ValueError, TypeError):
                pass  # Skip invalid port, use default
        if db_config.get('password'):
            conn_kwargs['password'] = db_config['password']

        try:
            self.db_pool = await asyncpg.create_pool(**conn_kwargs)
            logger.info(f"✅ Connected to database with pool size {conn_kwargs['max_size']}")
            return True
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            return False

    async def close(self):
        """Close connection pool"""
        if self.db_pool:
            await self.db_pool.close()

    async def start_job(self, job_name: str, data_source: str, record_type: str, total_estimated: int = None) -> int:
        """Start a new ingestion job"""
        async with self.db_pool.acquire() as conn:
            self.job_id = await conn.fetchval("""
                INSERT INTO ingestion.ingestion_jobs
                (job_name, data_source, record_type, total_estimated, status)
                VALUES ($1, $2, $3, $4, 'running')
                RETURNING id
            """, job_name, data_source, record_type, total_estimated)

            logger.info(f"🚀 Started job #{self.job_id}: {job_name}")
            return self.job_id

    async def update_progress(self, processed: int, failed: int = 0, current_id: str = None):
        """Update job progress"""
        if not self.job_id:
            return

        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                UPDATE ingestion.ingestion_jobs
                SET processed_records = processed_records + $1,
                    failed_records = failed_records + $2,
                    current_record_id = $3,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = $4
            """, processed, failed, current_id, self.job_id)

    async def complete_job(self, status: str = 'completed', metadata: Dict = None):
        """Complete the current job"""
        if not self.job_id:
            return

        import json
        metadata_json = json.dumps(metadata or {})

        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                UPDATE ingestion.ingestion_jobs
                SET status = $1,
                    completed_at = CURRENT_TIMESTAMP,
                    metadata = COALESCE(metadata, '{}'::jsonb) || $2::jsonb
                WHERE id = $3
            """, status, metadata_json, self.job_id)

            logger.info(f"🏁 Job #{self.job_id} finished with status: {status}")

    async def get_checkpoint(self, data_source: str, data_type: str, category: str) -> Optional[Dict]:
        """Get checkpoint for resuming ingestion"""
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT last_offset, last_page, last_id, is_completed
                FROM incremental.ingestion_checkpoints
                WHERE data_source = $1 AND data_type = $2 AND category = $3
            """, data_source, data_type, category)

            if row:
                return dict(row)
            return None

    async def save_checkpoint(self, data_source: str, data_type: str, category: str,
                             last_offset: int = None, last_page: int = None,
                             last_id: str = None, records_processed: int = 0,
                             is_completed: bool = False):
        """Save checkpoint"""
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO incremental.ingestion_checkpoints
                (data_source, data_type, category, last_offset, last_page, last_id,
                 total_processed, is_completed, last_ingestion_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, CURRENT_TIMESTAMP)
                ON CONFLICT (data_source, data_type, category)
                DO UPDATE SET
                    last_offset = COALESCE($4, incremental.ingestion_checkpoints.last_offset),
                    last_page = COALESCE($5, incremental.ingestion_checkpoints.last_page),
                    last_id = COALESCE($6, incremental.ingestion_checkpoints.last_id),
                    total_processed = incremental.ingestion_checkpoints.total_processed + $7,
                    is_completed = $8,
                    last_ingestion_at = CURRENT_TIMESTAMP
            """, data_source, data_type, category, last_offset, last_page, last_id,
                records_processed, is_completed)


class BulkIngestionOrchestrator:
    """Main orchestrator for parallel bulk ingestion"""

    def __init__(self, config_path: str):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        # Expand environment variables
        self._expand_env_vars(self.config)

        self.manager = AsyncIngestionManager(self.config)
        self.session = None
        self.rate_limiters = {}

    def _expand_env_vars(self, config):
        """Recursively expand ${VAR} or ${VAR:-default} in config"""
        if isinstance(config, dict):
            for key, value in config.items():
                if isinstance(value, str) and value.startswith('${') and value.endswith('}'):
                    # Parse ${VAR:-default} or ${VAR}
                    inner = value[2:-1]  # Remove ${ and }
                    if ':-' in inner:
                        var_name, default = inner.split(':-', 1)
                    else:
                        var_name = inner
                        default = ''
                    config[key] = os.getenv(var_name, default)
                elif isinstance(value, (dict, list)):
                    self._expand_env_vars(value)
        elif isinstance(config, list):
            for item in config:
                self._expand_env_vars(item)

    async def setup(self):
        """Initialize connections and rate limiters"""
        # Connect to database
        if not await self.manager.connect():
            raise Exception("Failed to connect to database")

        # Create HTTP session
        self.session = aiohttp.ClientSession()

        # Initialize rate limiters for each source
        if self.config['openstates']['enabled']:
            self.rate_limiters['openstates'] = RateLimiter(
                self.config['openstates']['rate_limit']
            )

        if self.config['congress']['enabled']:
            self.rate_limiters['congress'] = RateLimiter(
                self.config['congress']['rate_limit']
            )

        if self.config['govinfo']['enabled']:
            self.rate_limiters['govinfo'] = RateLimiter(
                self.config['govinfo']['rate_limit']
            )

        logger.info("✅ Setup complete - ready to begin ingestion")

    async def cleanup(self):
        """Close all connections"""
        if self.session:
            await self.session.close()
        await self.manager.close()

    async def ingest_openstates(self):
        """Ingest all OpenStates data"""
        if not self.config['openstates']['enabled']:
            return

        logger.info("🚀 Starting OpenStates bulk ingestion")
        jurisdictions = self.config['openstates']['jurisdictions']

        # Process jurisdictions in parallel batches
        parallel_jobs = self.config['performance']['parallel_jobs']

        for i in range(0, len(jurisdictions), parallel_jobs):
            batch = jurisdictions[i:i+parallel_jobs]
            tasks = [self._ingest_openstates_jurisdiction(j) for j in batch]
            await asyncio.gather(*tasks)

    async def _ingest_openstates_jurisdiction(self, jurisdiction: str):
        """Ingest all data for a single jurisdiction"""
        logger.info(f"📍 Processing jurisdiction: {jurisdiction}")

        # Call existing openstates_cli for each data type
        # For now, we'll use subprocess to call the CLI
        # TODO: Refactor openstates_cli to be async-native

        import subprocess
        for data_type in self.config['openstates']['data_types']:
            cmd = [
                '.venv/bin/python',
                'scripts/ingestion/openstates_cli.py',
                f'ingest-{data_type}',
                jurisdiction
            ]

            if data_type == 'jurisdictions':
                cmd = cmd[:-1]  # Remove jurisdiction arg

            try:
                logger.info(f"  Ingesting {data_type} for {jurisdiction}")
                result = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd='/home/cbwinslow/Videos/opendiscourse'
                )
                stdout, stderr = await result.communicate()

                if result.returncode == 0:
                    logger.info(f"  ✅ {data_type} complete")
                else:
                    logger.error(f"  ❌ {data_type} failed: {stderr.decode()}")

            except Exception as e:
                logger.error(f"  ❌ Error ingesting {data_type}: {e}")

    async def run(self):
        """Run the complete bulk ingestion"""
        try:
            await self.setup()

            # Start overall job
            await self.manager.start_job(
                "bulk_ingestion_all_sources",
                "multi",
                "all",
                None
            )

            # Run ingestion for each source
            tasks = []

            if self.config['openstates']['enabled']:
                tasks.append(self.ingest_openstates())

            # TODO: Add congress and govinfo ingestion
            # if self.config['congress']['enabled']:
            #     tasks.append(self.ingest_congress())
            #
            # if self.config['govinfo']['enabled']:
            #     tasks.append(self.ingest_govinfo())

            # Run all in parallel
            await asyncio.gather(*tasks)

            # Complete job
            await self.manager.complete_job('completed')

            logger.info("🎉 Bulk ingestion complete!")

        except Exception as e:
            logger.error(f"❌ Bulk ingestion failed: {e}")
            await self.manager.complete_job('failed', {'error': str(e)})
            raise

        finally:
            await self.cleanup()


async def main():
    import argparse
    parser = argparse.ArgumentParser(description='Bulk Data Ingestion Orchestrator')
    parser.add_argument('--config', default='config/ingestion_config.yaml',
                       help='Path to configuration file')
    parser.add_argument('--sources', nargs='+',
                       choices=['openstates', 'congress', 'govinfo', 'all'],
                       default=['all'], help='Data sources to ingest')

    args = parser.parse_args()

    orchestrator = BulkIngestionOrchestrator(args.config)
    await orchestrator.run()


if __name__ == '__main__':
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)

    # Run async main
    asyncio.run(main())
