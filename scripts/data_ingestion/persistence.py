"""Persistence utilities for ingestion outputs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from cassandra.cluster import Cluster
from neo4j import GraphDatabase
from psycopg import AsyncConnection
from pymongo import MongoClient


class UpsertProtocol(Protocol):
    async def __call__(self, record: dict[str, Any]) -> None:  # pragma: no cover - protocol definition
        ...


@dataclass(slots=True)
class StorageClients:
    postgres: AsyncConnection[Any]
    mongo: MongoClient
    cassandra: Cluster
    neo4j: GraphDatabase


async def upsert_record(record: dict[str, Any], clients: StorageClients) -> None:
    """Fan out data into relational, document, and graph stores."""

    await _upsert_postgres(record, clients.postgres)
    # run blocking sync I/O in threads so the async event loop isn't blocked
    import asyncio
    await asyncio.gather(
        asyncio.to_thread(_upsert_mongo, record, clients.mongo),
        asyncio.to_thread(_upsert_cassandra, record, clients.cassandra),
    )
    await _upsert_neo4j(record, clients.neo4j)


async def _upsert_postgres(record: dict[str, Any], conn: AsyncConnection[Any]) -> None:
    async with conn.cursor() as cur:
        await cur.execute(
            """
            INSERT INTO raw_ingest (source, url, retrieved_at, payload)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (url) DO UPDATE
            SET retrieved_at = EXCLUDED.retrieved_at,
                payload = EXCLUDED.payload
            """,
            (
                record.get("metadata", {}).get("source"),
                record.get("url"),
                record.get("retrieved_at"),
                record,
            ),
        )


def _upsert_mongo(record: dict[str, Any], client: MongoClient) -> None:
    client["opendiscourse"]["raw_ingest"].update_one(
        {"url": record.get("url")},
        {"$set": record},
        upsert=True,
    )


def _upsert_cassandra(record: dict[str, Any], cluster: Cluster) -> None:
    session = cluster.connect()
    try:
        session.execute(
            """
            INSERT INTO opendiscourse.raw_ingest (url, retrieved_at, payload)
            VALUES (%s, %s, %s)
            """,
            (
                record.get("url"),
                record.get("retrieved_at"),
                record,
            ),
        )
    finally:


async def _upsert_neo4j(record: dict[str, Any], driver: GraphDatabase) -> None:
    async with driver.session() as session:  # type: ignore[attr-defined]
        await session.execute_write(_merge_graph_entities, record)


async def _merge_graph_entities(tx, record: dict[str, Any]) -> None:  # type: ignore[no-untyped-def]
    await tx.run(
        """
        MERGE (s:Source {name: $source})
        MERGE (d:Document {url: $url})
        SET d.summary = $summary,
            d.embedding = $embedding,
            d.retrieved_at = $retrieved_at
        MERGE (s)-[:PUBLISHED]->(d)
        """,
        {
            "source": record.get("metadata", {}).get("source"),
            "url": record.get("url"),
            "summary": record.get("summary"),
            "embedding": record.get("embedding"),
            "retrieved_at": record.get("retrieved_at"),
        },
    )
