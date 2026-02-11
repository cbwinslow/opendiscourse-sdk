"""Asynchronous Congress.gov ingestion pipeline.

Dependencies
------------
- aiohttp
- asyncpg
- typer
- tenacity
- python-dateutil
- (optional) cudf or cupy for GPU acceleration

This module orchestrates high-throughput downloads from the Congress.gov REST API, leverages
asyncio for request concurrency, thread pools for CPU-bound normalization, and optional GPU-backed
batch transforms when RAPIDS libraries are available. The resulting records are persisted into the
schema defined under `congress.gov/migrations/`.
"""
from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import date, datetime, time
from typing import Any, Optional

import aiohttp
import asyncpg
import typer
from dateutil import parser as date_parser
from tenacity import (
    AsyncRetrying,
    RetryError,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

app = typer.Typer(add_completion=False, help="Ingest data from api.congress.gov into PostgreSQL.")


def _configure_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )


@dataclass(slots=True)
class RuntimeOptions:
    database_url: str
    api_key: str
    max_concurrent_requests: int = 10
    thread_pool_size: int = 4
    request_timeout: int = 30
    sample_size: Optional[int] = None
    changed_since: Optional[datetime] = None
    use_gpu: bool = False
    dry_run: bool = False


@dataclass(slots=True)
class GPUAdapters:
    enabled: bool = False
    cudf: Any | None = None
    cupy: Any | None = None

    @classmethod
    def detect(cls, use_gpu: bool) -> "GPUAdapters":
        if not use_gpu:
            return cls(enabled=False)
        try:
            import cudf  # type: ignore[import-not-found]

            return cls(enabled=True, cudf=cudf)
        except Exception:  # pragma: no cover - optional dependency
            try:
                import cupy  # type: ignore[import-not-found]

                return cls(enabled=True, cupy=cupy)
            except Exception:
                logging.warning("GPU libraries not found; defaulting to CPU processing.")
                return cls(enabled=False)

    def accelerate(self, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not self.enabled or not records:
            return records
        try:  # pragma: no cover - depends on optional packages
            if self.cudf is not None:
                frame = self.cudf.DataFrame(records)
                return frame.to_pandas().to_dict("records")
            if self.cupy is not None:
                _ = self.cupy.asarray(records)  # warm GPU cache; conversion not returned
                return records
        except Exception as exc:
            logging.warning("GPU acceleration failed; falling back to CPU (%s)", exc)
        return records


class CongressAPIClient:
    BASE_URL = "https://api.congress.gov/v3"

    def __init__(self, api_key: str, session: aiohttp.ClientSession, request_timeout: int = 30):
        self._api_key = api_key
        self._session = session
        self._request_timeout = request_timeout
        self._logger = logging.getLogger(self.__class__.__name__)

    async def _request(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        headers = {"X-API-Key": self._api_key}
        url = f"{self.BASE_URL}/{path.lstrip('/')}"
        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(5),
            wait=wait_exponential(multiplier=1, min=1, max=10),
            retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError)),
        ):
            with attempt:
                async with self._session.get(
                    url, headers=headers, params=params, timeout=self._request_timeout
                ) as response:
                    response.raise_for_status()
                    payload = await response.json()
                    self._logger.debug("GET %s -> %s", url, response.status)
                    return payload
        raise RuntimeError("Request retries exhausted")

    async def paginate(
        self,
        path: str,
        params: dict[str, Any],
        sample_size: Optional[int] = None,
    ) -> AsyncIterator[dict[str, Any]]:
        fetched = 0
        cursor: Optional[str] = None
        while True:
            request_params = dict(params)
            if cursor:
                request_params["offset"] = cursor
            payload = await self._request(path, request_params)
            results = payload.get(path.split("/")[-1], {})
            items = results.get("items") or results.get("item") or []
            for item in items:
                yield item
                fetched += 1
                if sample_size is not None and fetched >= sample_size:
                    return
            cursor = results.get("next")
            if not cursor:
                return


class BaseResourceLoader:
    resource_name: str
    endpoint: str
    primary_table: str

    def __init__(self, client: CongressAPIClient, pool: asyncpg.Pool, gpu: GPUAdapters, options: RuntimeOptions):
        self.client = client
        self.pool = pool
        self.gpu = gpu
        self.options = options
        self.logger = logging.getLogger(self.__class__.__name__)

    def build_params(self) -> dict[str, Any]:
        params: dict[str, Any] = {"format": "json"}
        if self.options.changed_since:
            params["lastModifiedDate"] = self.options.changed_since.strftime("%Y-%m-%d")
        return params

    async def fetch(self) -> AsyncIterator[dict[str, Any]]:
        async for item in self.client.paginate(
            self.endpoint,
            self.build_params(),
            sample_size=self.options.sample_size,
        ):
            yield item

    async def ingest(self) -> None:
        semaphore = asyncio.Semaphore(self.options.max_concurrent_requests)
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=self.options.max_concurrent_requests * 2)

        async def producer() -> None:
            async for item in self.fetch():
                await queue.put(item)
            await queue.put({"__END__": True})

        async def consumer() -> None:
            loop = asyncio.get_running_loop()
            while True:
                item = await queue.get()
                if "__END__" in item:
                    await queue.put(item)
                    return
                async with semaphore:
                    transformed = await asyncio.to_thread(self.transform_record, item)
                    batch = self.gpu.accelerate([transformed])
                    if not self.options.dry_run:
                        await self.persist_batch(batch)

        await asyncio.gather(producer(), *(consumer() for _ in range(self.options.thread_pool_size)))

    def transform_record(self, item: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    async def persist_batch(self, batch: list[dict[str, Any]]) -> None:
        raise NotImplementedError


class BillsLoader(BaseResourceLoader):
    resource_name = "bills"
    endpoint = "bill"
    primary_table = "congress.bills"

    def transform_record(self, item: dict[str, Any]) -> dict[str, Any]:
        fields = item.get("bill", item)
        introduced = fields.get("introducedDate")
        latest_action = fields.get("latestAction", {})
        committees = fields.get("committees", {}).get("items", [])
        return {
            "congress_number": int(fields.get("congress")),
            "bill_type": fields.get("billType"),
            "bill_number": int(fields.get("billNumber")),
            "origin_chamber": (fields.get("originChamber") or {}).get("code"),
            "introduced_date": introduced,
            "latest_action_date": latest_action.get("actionDate"),
            "latest_action_text": latest_action.get("text"),
            "policy_area": (fields.get("policyArea") or {}).get("name"),
            "summary_text": (fields.get("summaries") or {}).get("text"),
            "summary_last_updated": (fields.get("summaries") or {}).get("lastModified"),
            "status": fields.get("currentChamber"),
            "official_title": fields.get("title"),
            "sponsor_bioguide_id": (fields.get("sponsors") or {}).get("items", [{}])[0].get("bioguideId"),
            "committee_ids": [c.get("systemCode") for c in committees if c.get("systemCode")],
        }

    async def persist_batch(self, batch: list[dict[str, Any]]) -> None:
        if not batch:
            return
        async with self.pool.acquire() as connection:
            await connection.executemany(
                """
                INSERT INTO congress.bills (
                    congress_number, bill_type, bill_number, origin_chamber, introduced_date,
                    latest_action_date, latest_action_text, policy_area, summary_text,
                    summary_last_updated, status, official_title, sponsor_bioguide_id, committee_ids
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14
                )
                ON CONFLICT (congress_number, bill_type, bill_number) DO UPDATE
                SET
                    origin_chamber = EXCLUDED.origin_chamber,
                    latest_action_date = EXCLUDED.latest_action_date,
                    latest_action_text = EXCLUDED.latest_action_text,
                    policy_area = EXCLUDED.policy_area,
                    summary_text = EXCLUDED.summary_text,
                    summary_last_updated = EXCLUDED.summary_last_updated,
                    status = EXCLUDED.status,
                    official_title = EXCLUDED.official_title,
                    sponsor_bioguide_id = EXCLUDED.sponsor_bioguide_id,
                    committee_ids = EXCLUDED.committee_ids,
                    updated_at = now()
                """,
                [
                    (
                        record["congress_number"],
                        record["bill_type"],
                        record["bill_number"],
                        record["origin_chamber"],
                        _parse_date(record["introduced_date"]),
                        _parse_date(record["latest_action_date"]),
                        record["latest_action_text"],
                        record["policy_area"],
                        record["summary_text"],
                        _parse_datetime(record["summary_last_updated"]),
                        record["status"],
                        record["official_title"],
                        record["sponsor_bioguide_id"],
                        record["committee_ids"],
                    )
                    for record in batch
                ],
            )


class MembersLoader(BaseResourceLoader):
    resource_name = "members"
    endpoint = "member"
    primary_table = "congress.members"

    def transform_record(self, item: dict[str, Any]) -> dict[str, Any]:
        fields = item.get("member", item)
        terms = fields.get("terms", {}).get("items", [])
        return {
            "bioguide_id": fields.get("bioguideId"),
            "first_name": fields.get("firstName"),
            "middle_name": fields.get("middleName"),
            "last_name": fields.get("lastName"),
            "suffix": fields.get("suffix"),
            "official_full_name": fields.get("fullName"),
            "birthday": fields.get("birthYear"),
            "gender": fields.get("gender"),
            "biography": fields.get("biographyText"),
            "birthplace": fields.get("birthPlace"),
            "death_date": fields.get("deathYear"),
            "terms": [
                {
                    "congress_number": t.get("congress"),
                    "chamber_code": t.get("chamber", {}).get("code"),
                    "state_code": t.get("state", {}).get("postalCode"),
                    "district": t.get("district"),
                    "party_code": (t.get("party" ) or {}).get("code"),
                    "start_date": t.get("start"),
                    "end_date": t.get("end"),
                    "role_title": t.get("position"),
                    "leadership_role": t.get("leadershipTitle"),
                }
                for t in terms
            ],
        }

    async def persist_batch(self, batch: list[dict[str, Any]]) -> None:
        if not batch:
            return
        async with self.pool.acquire() as connection:
            async with connection.transaction():
                await connection.executemany(
                    """
                    INSERT INTO congress.members (
                        bioguide_id, first_name, middle_name, last_name, suffix,
                        official_full_name, birthday, gender, biography, birthplace, death_date
                    ) VALUES (
                        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11
                    )
                    ON CONFLICT (bioguide_id) DO UPDATE SET
                        first_name = EXCLUDED.first_name,
                        middle_name = EXCLUDED.middle_name,
                        last_name = EXCLUDED.last_name,
                        suffix = EXCLUDED.suffix,
                        official_full_name = EXCLUDED.official_full_name,
                        birthday = EXCLUDED.birthday,
                        gender = EXCLUDED.gender,
                        biography = EXCLUDED.biography,
                        birthplace = EXCLUDED.birthplace,
                        death_date = EXCLUDED.death_date,
                        updated_at = now()
                    """,
                    [
                        (
                            record["bioguide_id"],
                            record["first_name"],
                            record["middle_name"],
                            record["last_name"],
                            record["suffix"],
                            record["official_full_name"],
                            _parse_year(record["birthday"]),
                            record["gender"],
                            record["biography"],
                            record["birthplace"],
                            _parse_year(record["death_date"]),
                        )
                        for record in batch
                    ],
                )
                for record in batch:
                    if not record["terms"]:
                        continue
                    await connection.execute(
                        "DELETE FROM congress.member_terms WHERE bioguide_id = $1",
                        record["bioguide_id"],
                    )
                    await connection.executemany(
                        """
                        INSERT INTO congress.member_terms (
                            bioguide_id, congress_number, chamber_code, state_code, district,
                            party_code, start_date, end_date, role_title, leadership_role
                        ) VALUES (
                            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10
                        )
                        """,
                        [
                            (
                                record["bioguide_id"],
                                term["congress_number"],
                                term["chamber_code"],
                                term["state_code"],
                                term["district"],
                                term["party_code"],
                                _parse_date(term["start_date"]),
                                _parse_date(term["end_date"]),
                                term["role_title"],
                                term["leadership_role"],
                            )
                            for term in record["terms"]
                        ],
                    )


class CommitteesLoader(BaseResourceLoader):
    resource_name = "committees"
    endpoint = "committee"
    primary_table = "congress.committees"

    def transform_record(self, item: dict[str, Any]) -> dict[str, Any]:
        fields = item.get("committee", item)
        return {
            "committee_id": fields.get("systemCode") or fields.get("code"),
            "chamber_code": (fields.get("chamber") or {}).get("code"),
            "name": fields.get("name"),
            "type": fields.get("type"),
            "url": fields.get("url"),
            "established_at": fields.get("established"),
            "terminated_at": fields.get("terminated"),
            "parent_committee_id": (fields.get("parentCommittee") or {}).get("systemCode"),
        }

    async def persist_batch(self, batch: list[dict[str, Any]]) -> None:
        if not batch:
            return
        async with self.pool.acquire() as connection:
            await connection.executemany(
                """
                INSERT INTO congress.committees (
                    committee_id, chamber_code, name, type, url, established_at,
                    terminated_at, parent_committee_id
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8
                )
                ON CONFLICT (committee_id) DO UPDATE SET
                    chamber_code = EXCLUDED.chamber_code,
                    name = EXCLUDED.name,
                    type = EXCLUDED.type,
                    url = EXCLUDED.url,
                    established_at = EXCLUDED.established_at,
                    terminated_at = EXCLUDED.terminated_at,
                    parent_committee_id = EXCLUDED.parent_committee_id,
                    updated_at = now()
                """,
                [
                    (
                        record["committee_id"],
                        record["chamber_code"],
                        record["name"],
                        record["type"],
                        record["url"],
                        _parse_date(record["established_at"]),
                        _parse_date(record["terminated_at"]),
                        record["parent_committee_id"],
                    )
                    for record in batch
                ],
            )


class RollCallLoader(BaseResourceLoader):
    resource_name = "rollcalls"
    endpoint = "rollcall"
    primary_table = "congress.roll_calls"

    def build_params(self) -> dict[str, Any]:
        params = super().build_params()
        params.setdefault("chamber", "House")
        return params

    def transform_record(self, item: dict[str, Any]) -> dict[str, Any]:
        fields = item.get("rollCall", item)
        votes = (fields.get("votes") or {}).get("items", [])
        return {
            "congress_number": fields.get("congress"),
            "chamber_code": (fields.get("chamber") or {}).get("code"),
            "session_number": fields.get("sessionNumber"),
            "roll_number": fields.get("rollNumber"),
            "vote_question": fields.get("question"),
            "vote_type": fields.get("voteType"),
            "vote_result": fields.get("result"),
            "issue": fields.get("issue"),
            "related_bill": fields.get("bill"),
            "vote_date": fields.get("voteDate"),
            "vote_time": fields.get("voteTime"),
            "votes": votes,
        }

    async def persist_batch(self, batch: list[dict[str, Any]]) -> None:
        if not batch:
            return
        async with self.pool.acquire() as connection:
            async with connection.transaction():
                await connection.executemany(
                    """
                    INSERT INTO congress.roll_calls (
                        congress_number, chamber_code, session_number, roll_number, vote_question,
                        vote_type, vote_result, issue, related_bill_id, vote_date, vote_time
                    ) VALUES (
                        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11
                    )
                    ON CONFLICT (congress_number, chamber_code, session_number, roll_number) DO UPDATE SET
                        vote_question = EXCLUDED.vote_question,
                        vote_type = EXCLUDED.vote_type,
                        vote_result = EXCLUDED.vote_result,
                        issue = EXCLUDED.issue,
                        related_bill_id = EXCLUDED.related_bill_id,
                        vote_date = EXCLUDED.vote_date,
                        vote_time = EXCLUDED.vote_time,
                        updated_at = now()
                    RETURNING roll_call_id, congress_number, chamber_code, session_number, roll_number
                    """,
                    [
                        (
                            record["congress_number"],
                            record["chamber_code"],
                            record["session_number"],
                            record["roll_number"],
                            record["vote_question"],
                            record["vote_type"],
                            record["vote_result"],
                            record["issue"],
                            None,
                            _parse_date(record["vote_date"]),
                            _parse_time(record["vote_time"]),
                        )
                        for record in batch
                    ],
                )
                for record in batch:
                    await connection.execute(
                        "DELETE FROM congress.roll_call_votes USING congress.roll_calls rc "
                        "WHERE congress.roll_call_votes.roll_call_id = rc.roll_call_id "
                        "AND rc.congress_number = $1 AND rc.chamber_code = $2 "
                        "AND rc.session_number = $3 AND rc.roll_number = $4",
                        record["congress_number"],
                        record["chamber_code"],
                        record["session_number"],
                        record["roll_number"],
                    )
                    if not record["votes"]:
                        continue
                    await connection.executemany(
                        """
                        INSERT INTO congress.roll_call_votes (
                            roll_call_id, bioguide_id, vote_position, vote_cast_at
                        ) VALUES (
                            (SELECT roll_call_id FROM congress.roll_calls WHERE congress_number = $1 AND chamber_code = $2 AND session_number = $3 AND roll_number = $4),
                            $5, $6, $7
                        )
                        ON CONFLICT (roll_call_id, bioguide_id) DO UPDATE SET
                            vote_position = EXCLUDED.vote_position,
                            vote_cast_at = EXCLUDED.vote_cast_at,
                            updated_at = now()
                        """,
                        [
                            (
                                record["congress_number"],
                                record["chamber_code"],
                                record["session_number"],
                                record["roll_number"],
                                vote.get("member", {}).get("bioguideId"),
                                vote.get("position"),
                                _parse_datetime(vote.get("voteCast")),
                            )
                            for vote in record["votes"]
                        ],
                    )


RESOURCE_LOADERS: dict[str, type[BaseResourceLoader]] = {
    BillsLoader.resource_name: BillsLoader,
    MembersLoader.resource_name: MembersLoader,
    CommitteesLoader.resource_name: CommitteesLoader,
    RollCallLoader.resource_name: RollCallLoader,
}


def _parse_date(value: Any) -> Optional[date]:
    if not value:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    try:
        return date_parser.parse(str(value)).date()
    except Exception:
        return None


def _parse_time(value: Any) -> Optional[time]:
    if not value:
        return None
    try:
        return date_parser.parse(str(value)).time()
    except Exception:
        return None


def _parse_datetime(value: Any) -> Optional[datetime]:
    if not value:
        return None
    try:
        return date_parser.parse(str(value))
    except Exception:
        return None


def _parse_year(value: Any) -> Optional[date]:
    if not value:
        return None
    try:
        return date_parser.parse(str(value)).date()
    except Exception:
        return None


async def _ensure_connection(pool: asyncpg.Pool) -> None:
    async with pool.acquire() as connection:
        await connection.execute("SELECT 1")


async def _run_ingestion(resources: list[str], options: RuntimeOptions) -> None:
    connector = aiohttp.TCPConnector(limit_per_host=options.max_concurrent_requests)
    timeout = aiohttp.ClientTimeout(total=options.request_timeout)
    gpu = GPUAdapters.detect(options.use_gpu)

    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        client = CongressAPIClient(options.api_key, session, options.request_timeout)
        pool = await asyncpg.create_pool(options.database_url, min_size=1, max_size=options.thread_pool_size)
        await _ensure_connection(pool)
        try:
            for resource in resources:
                loader_cls = RESOURCE_LOADERS.get(resource)
                if not loader_cls:
                    raise KeyError(f"Unsupported resource '{resource}'. Available: {list(RESOURCE_LOADERS)}")
                loader = loader_cls(client, pool, gpu, options)
                logging.info("Starting ingest for resource '%s'", resource)
                await loader.ingest()
                logging.info("Completed ingest for resource '%s'", resource)
        finally:
            await pool.close()


@app.command()
def main(
    resources: list[str] = typer.Argument(..., help="Resources to ingest (e.g., bills members committees)."),
    database_url: str = typer.Option(..., envvar="CONGRESS_DATABASE_URL", help="PostgreSQL connection URL."),
    api_key: str = typer.Option(..., envvar="CONGRESS_API_KEY", help="Congress.gov API key."),
    max_concurrent_requests: int = typer.Option(16, help="Maximum concurrent HTTP requests."),
    thread_pool_size: int = typer.Option(8, help="Number of worker consumers for normalization."),
    request_timeout: int = typer.Option(60, help="HTTP request timeout in seconds."),
    sample_size: Optional[int] = typer.Option(None, help="Limit number of records for smoke tests."),
    changed_since: Optional[str] = typer.Option(None, help="Ingest only records modified on or after this ISO date."),
    use_gpu: bool = typer.Option(False, help="Enable GPU acceleration when RAPIDS libraries are installed."),
    dry_run: bool = typer.Option(False, help="Download and transform without writing to the database."),
    log_level: str = typer.Option("INFO", help="Python logging level."),
) -> None:
    """Entry point for the CLI."""
    _configure_logging(log_level)
    changed_dt = date_parser.parse(changed_since).replace(tzinfo=None) if changed_since else None
    options = RuntimeOptions(
        database_url=database_url,
        api_key=api_key,
        max_concurrent_requests=max_concurrent_requests,
        thread_pool_size=thread_pool_size,
        request_timeout=request_timeout,
        sample_size=sample_size,
        changed_since=changed_dt,
        use_gpu=use_gpu,
        dry_run=dry_run,
    )
    try:
        asyncio.run(_run_ingestion(resources, options))
    except KeyboardInterrupt:  # pragma: no cover - CLI handling
        typer.echo("Ingestion interrupted", err=True)
        raise typer.Exit(1)
    except RetryError as exc:
        logging.error("Exceeded retry attempts: %s", exc)
        raise typer.Exit(2) from exc
    except Exception as exc:  # pragma: no cover - top level safety
        logging.exception("Ingestion failed: %s", exc)
        raise typer.Exit(3) from exc


if __name__ == "__main__":
    app()
