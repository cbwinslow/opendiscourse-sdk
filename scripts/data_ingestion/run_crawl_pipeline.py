"""Entry point for crawl4ai + OpenRouter ingestion with persistence."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Any

from cassandra.cluster import Cluster
from crawl4ai import AsyncCrawler
from crawl4ai_openrouter import (
    Crawl4AIOpenRouterPipeline,
    PipelineSettings,
    build_default_targets,
)
from neo4j import GraphDatabase
from openrouter import OpenRouter
from persistence import StorageClients, upsert_record
from psycopg import AsyncConnectionPool
from pymongo import MongoClient
from source_ingestion_tasks import DEFAULT_PROCESSORS


async def build_storage_clients() -> StorageClients:
    postgres_pool = await AsyncConnectionPool.connect(
        "postgresql+psycopg://opendiscourse:password@localhost:5432/opendiscourse"
    )

    mongo_client = MongoClient("mongodb://localhost:27017")
    cassandra_cluster = Cluster(["localhost"])
    neo4j_driver = GraphDatabase.async_driver("bolt://localhost:7687", auth=("neo4j", "password"))

    return StorageClients(
        postgres=postgres_pool,
        mongo=mongo_client,
        cassandra=cassandra_cluster,
        neo4j=neo4j_driver,
    )


async def run_pipeline() -> None:
    storage_clients = await build_storage_clients()

    async def _upsert(record: dict[str, Any]) -> None:
        await upsert_record(record, storage_clients)

    targets = build_default_targets()
    for target in targets:
        processor = DEFAULT_PROCESSORS.get(target.name)
        if processor:
            target.post_processors = (*target.post_processors, processor)

    crawler = AsyncCrawler()
    router_client = OpenRouter.from_env()
    settings = PipelineSettings(output_dir=Path("data/crawl4ai"))

    pipeline = Crawl4AIOpenRouterPipeline(
        crawler=crawler,
        router_client=router_client,
        targets=targets,
        settings=settings,
        upsert_callback=_upsert,
    )

    await pipeline.run()


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_pipeline())


if __name__ == "__main__":
    main()
