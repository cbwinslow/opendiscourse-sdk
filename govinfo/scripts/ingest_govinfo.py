"""Asynchronous ingestion pipeline for govinfo bulk data and API content."""
from __future__ import annotations

import argparse
import asyncio
import concurrent.futures
import contextlib
import dataclasses
import hashlib
import importlib
import importlib.util
import json
import logging
import math
import os
from collections.abc import AsyncIterator, Iterable, Sequence
from dataclasses import dataclass, field
from datetime import date, datetime
from datetime import time as time_type
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urljoin

import aiofiles
import aiohttp
import asyncpg

GPU_MODULE_SPEC = importlib.util.find_spec("cupy")
GPU_MODULE = importlib.import_module("cupy") if GPU_MODULE_SPEC else None


def _gpu_copy(data: bytes) -> bytes:
    """Copy bytes through GPU memory when available for acceleration."""
    if not data or GPU_MODULE is None:
        return data
    try:
        gpu_array = GPU_MODULE.asarray(memoryview(data), dtype=GPU_MODULE.uint8)
        GPU_MODULE.cuda.Stream.null.synchronize()
        return bytes(GPU_MODULE.asnumpy(gpu_array))
    except Exception:  # noqa: BLE001 - GPU acceleration is best effort
        return data


@dataclass(slots=True)
class IngestionConfig:
    api_key: str
    collections: Sequence[str]
    bulk_collections: Sequence[str]
    start: Optional[str]
    end: Optional[str]
    page_size: int
    max_packages: Optional[int]
    bulk_sample: Optional[int]
    output_dir: Path
    pg_dsn: Optional[str]
    max_concurrency: int = 12
    bulk_concurrency: int = 6
    request_timeout: int = 120
    connect_timeout: int = 30
    retry_attempts: int = 4
    retry_backoff: float = 1.75
    enable_api: bool = True
    enable_bulk: bool = True
    dry_run: bool = False


class GovInfoHTMLLinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:  # noqa: D401
        if tag.lower() != "a":
            return
        href = next((value for key, value in attrs if key == "href"), None)
        if href:
            self.links.append(href)


class GovInfoAPIClient:
    BASE_URL = "https://api.govinfo.gov/"

    def __init__(self, session: aiohttp.ClientSession, config: IngestionConfig) -> None:
        self._session = session
        self._config = config
        self._sem = asyncio.Semaphore(config.max_concurrency)

    async def _request_json(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        params = dict(params or {})
        params.setdefault("api_key", self._config.api_key)
        url = urljoin(self.BASE_URL, path)
        timeout = aiohttp.ClientTimeout(total=self._config.request_timeout)
        for attempt in range(1, self._config.retry_attempts + 1):
            async with self._sem:
                try:
                    async with self._session.get(url, params=params, timeout=timeout) as resp:
                        resp.raise_for_status()
                        return await resp.json(loads=json.loads)
                except Exception as exc:  # noqa: BLE001
                    if attempt >= self._config.retry_attempts:
                        raise
                    await asyncio.sleep(self._config.retry_backoff ** attempt)
                    logging.warning("API request failed (%s) attempt %s/%s", exc, attempt, self._config.retry_attempts)
        raise RuntimeError(f"Failed to call {url}")

    async def fetch_binary(self, url: str) -> bytes:
        timeout = aiohttp.ClientTimeout(total=self._config.request_timeout)
        async with self._sem:
            async with self._session.get(url, timeout=timeout) as resp:
                resp.raise_for_status()
                return _gpu_copy(await resp.read())

    async def iter_collection_packages(self, collection: str) -> AsyncIterator[dict[str, Any]]:
        if not self._config.enable_api:
            return
        params: dict[str, Any] = {"pageSize": self._config.page_size, "offsetMark": "*"}
        if self._config.start:
            params["lastModifiedStartDate"] = self._config.start
        if self._config.end:
            params["lastModifiedEndDate"] = self._config.end
        total = 0
        while True:
            payload = await self._request_json(f"collections/{collection}", params=params)
            packages = payload.get("packages", [])
            for package in packages:
                yield package
                total += 1
                if self._config.max_packages and total >= self._config.max_packages:
                    logging.info("Reached package cap for %s", collection)
                    return
            next_page = payload.get("nextPage")
            if not next_page:
                return
            params["offsetMark"] = next_page

    async def fetch_package_summary(self, package_id: str) -> dict[str, Any]:
        return await self._request_json(f"packages/{package_id}", params={"summary": "true"})


class GovInfoBulkDownloader:
    BULK_BASE = "https://www.govinfo.gov/bulkdata/"

    def __init__(self, session: aiohttp.ClientSession, config: IngestionConfig) -> None:
        self._session = session
        self._config = config
        self._sem = asyncio.Semaphore(config.bulk_concurrency)
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=os.cpu_count() or 4)

    async def close(self) -> None:
        self._executor.shutdown(wait=False, cancel_futures=True)

    async def iter_collection_links(self, collection: str) -> AsyncIterator[str]:
        if not self._config.enable_bulk:
            return
        base_url = urljoin(self.BULK_BASE, f"{collection}/")
        async for link in self._walk_links(base_url):
            yield link

    async def _walk_links(self, url: str) -> AsyncIterator[str]:
        timeout = aiohttp.ClientTimeout(total=self._config.request_timeout)
        async with self._sem:
            async with self._session.get(url, timeout=timeout) as resp:
                resp.raise_for_status()
                text = await resp.text()
        parser = GovInfoHTMLLinkParser()
        parser.feed(text)
        count = 0
        for href in parser.links:
            if not href or href.startswith("../"):
                continue
            full_url = urljoin(url, href)
            if full_url.endswith("/"):
                async for nested in self._walk_links(full_url):
                    yield nested
            else:
                yield full_url
                count += 1
                if self._config.bulk_sample and count >= self._config.bulk_sample:
                    return

    async def download(self, url: str, destination: Path) -> Path:
        timeout = aiohttp.ClientTimeout(total=self._config.request_timeout)
        destination.parent.mkdir(parents=True, exist_ok=True)
        async with self._sem:
            async with self._session.get(url, timeout=timeout) as resp:
                resp.raise_for_status()
                data = _gpu_copy(await resp.read())
        async with aiofiles.open(destination, "wb") as fh:
            await fh.write(data)
        return destination

    async def extract_zip(self, path: Path, target_dir: Path) -> list[Path]:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(self._executor, self._sync_extract, path, target_dir)

    @staticmethod
    def _sync_extract(path: Path, target_dir: Path) -> list[Path]:
        import zipfile

        extracted: list[Path] = []
        with zipfile.ZipFile(path) as archive:
            for member in archive.infolist():
                target_dir.mkdir(parents=True, exist_ok=True)
                archive.extract(member, path=target_dir)
                extracted.append(target_dir / member.filename)
        return extracted


@dataclass(slots=True)
class PackageIngestionResult:
    packages: list[dict[str, Any]] = field(default_factory=list)
    bills: list[dict[str, Any]] = field(default_factory=list)
    bill_actions: list[dict[str, Any]] = field(default_factory=list)
    bill_summaries: list[dict[str, Any]] = field(default_factory=list)
    bill_versions: list[dict[str, Any]] = field(default_factory=list)
    bill_committees: list[dict[str, Any]] = field(default_factory=list)
    bill_cosponsors: list[dict[str, Any]] = field(default_factory=list)
    bill_subjects: list[dict[str, Any]] = field(default_factory=list)
    votes: list[dict[str, Any]] = field(default_factory=list)
    vote_totals: list[dict[str, Any]] = field(default_factory=list)
    vote_actions: list[dict[str, Any]] = field(default_factory=list)
    vote_ballots: list[dict[str, Any]] = field(default_factory=list)
    members: list[dict[str, Any]] = field(default_factory=list)
    memberships: list[dict[str, Any]] = field(default_factory=list)
    member_terms: list[dict[str, Any]] = field(default_factory=list)
    member_votes: list[dict[str, Any]] = field(default_factory=list)
    member_attendance: list[dict[str, Any]] = field(default_factory=list)


class PackageTransformer:
    @staticmethod
    def normalize_package(package_summary: dict[str, Any]) -> dict[str, Any]:
        downloads = package_summary.get("download", {})
        metadata = package_summary.get("metadata", {})
        related = package_summary.get("relatedPackages") or package_summary.get("related") or []
        metadata_payload = dict(metadata) if isinstance(metadata, dict) else {}
        if related:
            metadata_payload["relatedPackages"] = related
        return {
            "package_id": package_summary.get("packageId"),
            "collection_code": package_summary.get("collectionCode"),
            "title": package_summary.get("title"),
            "congress_number": PackageTransformer._to_int(package_summary.get("congress")),
            "chamber_code": package_summary.get("chamber"),
            "bill_type": metadata.get("billType") if isinstance(metadata, dict) else None,
            "bill_number": metadata.get("billNumber") if isinstance(metadata, dict) else None,
            "document_class": metadata.get("docClass") if isinstance(metadata, dict) else None,
            "doc_number": metadata.get("documentNumber") if isinstance(metadata, dict) else None,
            "granule_count": package_summary.get("granuleCount"),
            "date_issued": PackageTransformer._parse_date(metadata.get("dateIssued")) if isinstance(metadata, dict) else None,
            "last_modified": PackageTransformer._parse_datetime(package_summary.get("lastModified")),
            "summary": metadata.get("title") if isinstance(metadata, dict) else None,
            "origin": metadata.get("originatingOffice") if isinstance(metadata, dict) else None,
            "urls": downloads,
            "metadata": metadata_payload,
            "retrieved_at": datetime.utcnow(),
        }

    @staticmethod
    def parse_billstatus_xml(xml_bytes: bytes, package_id: str) -> PackageIngestionResult:
        import xml.etree.ElementTree as ET

        result = PackageIngestionResult()
        xml_bytes = _gpu_copy(xml_bytes)
        root = ET.fromstring(xml_bytes)
        bill_data = root.find("bill") or root
        bill_id = bill_data.findtext("billNumber") or package_id
        congress = PackageTransformer._to_int(bill_data.findtext("congress"))
        bill_type = bill_data.findtext("billType")
        latest_action = bill_data.find("latestAction")
        subjects = bill_data.findall("subjects/subject")
        committees = bill_data.findall("committees/committee")
        cosponsors = bill_data.findall("cosponsors/item")
        summaries = bill_data.findall("summaries/item")
        actions = bill_data.findall("actions/item")
        versions = bill_data.findall("textVersions/item")
        sponsors = bill_data.findall("sponsors/item")
        votes = bill_data.findall("votes/item")

        result.bills.append(
            {
                "bill_id": bill_id,
                "package_id": package_id,
                "bill_type": bill_type,
                "bill_number": bill_data.findtext("billNumber"),
                "congress_number": congress,
                "chamber_code": bill_data.findtext("originChamber"),
                "origin_chamber": bill_data.findtext("originChamber"),
                "introduced_date": PackageTransformer._parse_date(bill_data.findtext("introducedDate")),
                "latest_action_date": PackageTransformer._parse_date(latest_action.findtext("actionDate") if latest_action is not None else None),
                "latest_action_text": latest_action.findtext("text") if latest_action is not None else None,
                "status": bill_data.findtext("currentChamber"),
                "subjects_primary": bill_data.findtext("policyArea/name"),
                "subjects_secondary": [sub.findtext("name") for sub in subjects],
                "committees": [committee.findtext("systemCode") for committee in committees],
                "sponsors": [PackageTransformer._parse_member(sponsor) for sponsor in sponsors],
                "cosponsors": [PackageTransformer._parse_member(cosp) for cosp in cosponsors],
                "summaries": [PackageTransformer._parse_summary(summary) for summary in summaries],
                "text_versions": [PackageTransformer._parse_version(version) for version in versions],
                "related_packages": [rel.text for rel in bill_data.findall("relatedBills/item/packageId")],
                "last_updated_at": datetime.utcnow(),
            }
        )

        for summary in summaries:
            result.bill_summaries.append(
                {
                    "bill_id": bill_id,
                    "summary_date": PackageTransformer._parse_date(summary.findtext("date")),
                    "summary_text": summary.findtext("text"),
                    "source": summary.findtext("source"),
                    "is_official": PackageTransformer._parse_bool(summary.findtext("official")),
                    "metadata": PackageTransformer._element_to_dict(summary),
                }
            )

        for version in versions:
            result.bill_versions.append(
                {
                    "bill_id": bill_id,
                    "version_code": version.findtext("code"),
                    "version_name": version.findtext("name"),
                    "issued_date": PackageTransformer._parse_date(version.findtext("date")),
                    "urls": PackageTransformer._element_to_dict(version.find("urls")),
                    "is_latest": PackageTransformer._parse_bool(version.findtext("isLatest")),
                    "metadata": PackageTransformer._element_to_dict(version),
                }
            )

        for committee in committees:
            result.bill_committees.append(
                {
                    "bill_id": bill_id,
                    "committee_code": committee.findtext("systemCode"),
                    "role": committee.findtext("activity"),
                    "referral_date": PackageTransformer._parse_date(committee.findtext("activityDate")),
                    "report_number": committee.findtext("reportNumber"),
                }
            )

        for cosponsor in cosponsors:
            member = PackageTransformer._parse_member(cosponsor)
            member_id = member.get("member_id") or member.get("bioguide_id")
            result.bill_cosponsors.append(
                {
                    "bill_id": bill_id,
                    "member_id": member_id,
                    "cosponsor_type": cosponsor.findtext("sponsorshipType"),
                    "cosponsored_date": PackageTransformer._parse_date(cosponsor.findtext("since")),
                    "withdrew_date": PackageTransformer._parse_date(cosponsor.findtext("withdrawn")),
                }
            )
            if member_id:
                result.members.append(member)

        for subject in subjects:
            result.bill_subjects.append(
                {
                    "bill_id": bill_id,
                    "subject_term": subject.findtext("name"),
                    "subject_type": subject.findtext("type"),
                    "is_primary": PackageTransformer._parse_bool(subject.findtext("isPrimary")) or False,
                }
            )

        for action in actions:
            result.bill_actions.append(
                {
                    "bill_id": bill_id,
                    "action_date": PackageTransformer._parse_date(action.findtext("actionDate")),
                    "action_time": PackageTransformer._parse_time(action.findtext("actionTime")),
                    "action_text": action.findtext("text"),
                    "chamber_code": action.findtext("chamber"),
                    "action_type": action.findtext("type"),
                    "committees": [c.text for c in action.findall("committeeSystemCode")],
                    "roll_call_number": action.findtext("rollNumber"),
                    "recorded_vote_id": action.findtext("recordedVote"),
                }
            )

        for vote in votes:
            vote_id = vote.findtext("rollNumber") or f"{bill_id}-{vote.findtext('voteDate')}"
            session_id = vote.findtext("session")
            chamber = vote.findtext("chamber")
            vote_date = PackageTransformer._parse_date(vote.findtext("voteDate"))
            result.votes.append(
                {
                    "vote_id": vote_id,
                    "package_id": package_id,
                    "congress_number": congress,
                    "session_id": session_id,
                    "chamber_code": chamber,
                    "vote_number": PackageTransformer._to_int(vote.findtext("rollNumber")),
                    "vote_question": vote.findtext("question"),
                    "vote_type": vote.findtext("type"),
                    "vote_result": vote.findtext("result"),
                    "vote_date": vote_date,
                    "vote_time": PackageTransformer._parse_time(vote.findtext("voteTime")),
                    "vote_title": vote.findtext("question"),
                    "bill_id": bill_id,
                    "related_amendment": vote.findtext("amendmentNumber"),
                    "related_matter": vote.findtext("voteDocument"),
                    "metadata": PackageTransformer._element_to_dict(vote),
                }
            )
            totals = vote.find("totals")
            if totals is not None:
                result.vote_totals.append(
                    {
                        "vote_id": vote_id,
                        "total_yes": PackageTransformer._to_int(totals.findtext("yeaVotes")),
                        "total_no": PackageTransformer._to_int(totals.findtext("nayVotes")),
                        "total_present": PackageTransformer._to_int(totals.findtext("presentVotes")),
                        "total_not_voting": PackageTransformer._to_int(totals.findtext("notVoting")),
                        "majority_requirement": totals.findtext("majorityRequired"),
                        "result_text": vote.findtext("result"),
                        "metadata": PackageTransformer._element_to_dict(totals),
                    }
                )
            members = vote.findall("members/item")
            for member in members:
                member_data = PackageTransformer._parse_member(member)
                member_id = member_data.get("member_id") or member_data.get("bioguide_id")
                ballot_value = member.findtext("vote")
                attendance_status = ballot_value or ""
                result.vote_ballots.append(
                    {
                        "vote_id": vote_id,
                        "member_id": member_id,
                        "vote_cast": ballot_value,
                        "vote_pair": member.findtext("pairVote"),
                        "vote_group": member.findtext("party"),
                        "vote_note": member.findtext("note"),
                        "is_vote_changed": PackageTransformer._parse_bool(member.findtext("voteChanged")),
                        "changed_at": PackageTransformer._parse_datetime(member.findtext("voteChangedDate")),
                    }
                )
                result.member_votes.append(
                    {
                        "member_id": member_id,
                        "vote_id": vote_id,
                        "vote_cast": ballot_value,
                        "vote_pair": member.findtext("pairVote"),
                        "vote_note": member.findtext("note"),
                        "was_present": attendance_status not in {"Not Voting", "Absent"},
                        "voted_at": PackageTransformer._combine_datetime(vote_date, PackageTransformer._parse_time(vote.findtext("voteTime"))),
                        "source": "billstatus",
                    }
                )
                result.member_attendance.append(
                    {
                        "member_id": member_id,
                        "session_id": session_id,
                        "congress_number": congress,
                        "chamber_code": chamber,
                        "attended_votes": 1 if attendance_status not in {"Not Voting", "Absent"} else 0,
                        "missed_votes": 1 if attendance_status in {"Not Voting", "Absent"} else 0,
                        "present_votes": 1 if attendance_status == "Present" else 0,
                        "leave_votes": 1 if attendance_status == "Leave" else 0,
                        "attendance_rate": 1.0 if attendance_status not in {"Not Voting", "Absent"} else 0.0,
                        "report_date": vote_date,
                        "source": "billstatus",
                    }
                )
                if member_id:
                    result.members.append(member_data)
        return result

    @staticmethod
    def _parse_member(element: Any) -> dict[str, Any]:
        if element is None:
            return {}
        payload = {
            "member_id": element.findtext("memberId"),
            "bioguide_id": element.findtext("bioguideId"),
            "first_name": element.findtext("firstName"),
            "middle_name": element.findtext("middleName"),
            "last_name": element.findtext("lastName"),
            "suffix": element.findtext("suffix"),
            "full_name": element.findtext("fullName"),
            "preferred_name": element.findtext("preferredName"),
            "party_code": element.findtext("party"),
            "state": element.findtext("state"),
            "district": element.findtext("district"),
            "chamber_code": element.findtext("chamber"),
        }
        if not payload["member_id"] and payload["bioguide_id"]:
            payload["member_id"] = payload["bioguide_id"]
        return payload

    @staticmethod
    def _parse_summary(element: Any) -> dict[str, Any]:
        return {
            "date": element.findtext("date") if element is not None else None,
            "text": element.findtext("text") if element is not None else None,
            "source": element.findtext("source") if element is not None else None,
            "official": element.findtext("official") if element is not None else None,
        }

    @staticmethod
    def _parse_version(element: Any) -> dict[str, Any]:
        return {
            "code": element.findtext("code") if element is not None else None,
            "name": element.findtext("name") if element is not None else None,
            "date": element.findtext("date") if element is not None else None,
            "urls": PackageTransformer._element_to_dict(element.find("urls")) if element is not None else {},
            "isLatest": element.findtext("isLatest") if element is not None else None,
        }

    @staticmethod
    def _element_to_dict(element: Any) -> dict[str, Any]:
        if element is None:
            return {}
        payload: dict[str, Any] = {}
        for child in element:
            payload.setdefault(child.tag, child.text)
        return payload

    @staticmethod
    def _parse_bool(value: Optional[str]) -> Optional[bool]:
        if value is None:
            return None
        return value.lower() in {"y", "yes", "true", "1"}

    @staticmethod
    def _parse_time(value: Optional[str]) -> Optional[time_type]:
        if not value:
            return None
        for fmt in ("%H:%M:%S", "%H:%M"):
            with contextlib.suppress(ValueError):
                return datetime.strptime(value, fmt).time()
        return None

    @staticmethod
    def _parse_date(value: Optional[str]) -> Optional[date]:
        if not value:
            return None
        for fmt in ("%Y-%m-%d", "%Y%m%d", "%m/%d/%Y"):
            with contextlib.suppress(ValueError):
                return datetime.strptime(value, fmt).date()
        return None

    @staticmethod
    def _parse_datetime(value: Optional[str]) -> Optional[datetime]:
        if not value:
            return None
        for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
            with contextlib.suppress(ValueError):
                return datetime.strptime(value, fmt)
        return None

    @staticmethod
    def _combine_datetime(date_value: Optional[date], time_value: Optional[time_type]) -> Optional[datetime]:
        if date_value is None:
            return None
        if time_value is None:
            return datetime.combine(date_value, datetime.min.time())
        return datetime.combine(date_value, time_value)

    @staticmethod
    def _to_int(value: Any) -> Optional[int]:
        if value in (None, ""):
            return None
        with contextlib.suppress(ValueError, TypeError):
            return int(value)
        return None


class PostgresIngestor:
    def __init__(self, pool: asyncpg.pool.Pool) -> None:
        self._pool = pool

    @classmethod
    async def create(cls, dsn: str | None) -> "PostgresIngestor | None":
        if not dsn:
            return None
        pool = await asyncpg.create_pool(dsn=dsn, min_size=1, max_size=10)
        return cls(pool)

    async def close(self) -> None:
        await self._pool.close()

    async def insert_batch(self, table: str, rows: Iterable[dict[str, Any]], conflict_target: Sequence[str] | str | None) -> None:
        buffered = list(rows)
        if not buffered:
            return
        if isinstance(conflict_target, str):
            conflict_cols = [conflict_target]
        else:
            conflict_cols = list(conflict_target or [])
        if conflict_cols:
            buffered = [row for row in buffered if all(row.get(col) is not None for col in conflict_cols)]
        if not buffered:
            return
        columns = list(buffered[0].keys())
        value_template = ", ".join(f"${idx + 1}" for idx in range(len(columns)))
        column_list = ", ".join(columns)
        if conflict_cols:
            conflict_clause = ", ".join(conflict_cols)
            update_list = ", ".join(f"{col}=EXCLUDED.{col}" for col in columns if col not in conflict_cols)
            query = f"INSERT INTO {table} ({column_list}) VALUES ({value_template}) ON CONFLICT ({conflict_clause}) DO UPDATE SET {update_list}"
        else:
            query = f"INSERT INTO {table} ({column_list}) VALUES ({value_template}) ON CONFLICT DO NOTHING"
        values = [tuple(row[col] for col in columns) for row in buffered]
        async with self._pool.acquire() as conn:
            await conn.executemany(query, values)


async def process_collection(api_client: GovInfoAPIClient, transformer: PackageTransformer, collection: str, pg: PostgresIngestor | None, config: IngestionConfig, output_dir: Path) -> None:
    logging.info("Processing API collection %s", collection)
    result = PackageIngestionResult()
    async for package in api_client.iter_collection_packages(collection):
        package_id = package.get("packageId")
        if not package_id:
            continue
        summary = await api_client.fetch_package_summary(package_id)
        normalized = transformer.normalize_package(summary)
        result.packages.append(normalized)
        xml_url = summary.get("download", {}).get("xml")
        if xml_url:
            xml_bytes = await api_client.fetch_binary(xml_url)
            package_result = transformer.parse_billstatus_xml(xml_bytes, package_id)
            merge_ingestion_results(result, package_result)
        if config.max_packages and len(result.packages) >= config.max_packages:
            break
    await persist_results(pg, result)
    await write_results(output_dir / f"{collection.lower()}_packages.jsonl", result.packages)


def merge_ingestion_results(base: PackageIngestionResult, new: PackageIngestionResult) -> None:
    for field in dataclasses.fields(PackageIngestionResult):
        base_list = getattr(base, field.name)
        new_list = getattr(new, field.name)
        if isinstance(base_list, list) and isinstance(new_list, list):
            base_list.extend(new_list)


async def persist_results(pg: PostgresIngestor | None, result: PackageIngestionResult) -> None:
    if pg is None:
        return
    await pg.insert_batch("govinfo.packages", result.packages, "package_id")
    await pg.insert_batch("govinfo.bills", result.bills, "bill_id")
    await pg.insert_batch("govinfo.bill_actions", result.bill_actions, ["bill_id", "action_date", "action_time", "action_text"])
    await pg.insert_batch("govinfo.bill_summaries", result.bill_summaries, ["bill_id", "summary_date", "source"])
    await pg.insert_batch("govinfo.bill_versions", result.bill_versions, ["bill_id", "version_code"])
    await pg.insert_batch("govinfo.bill_committees", result.bill_committees, ["bill_id", "committee_code", "referral_date"])
    await pg.insert_batch("govinfo.bill_cosponsors", result.bill_cosponsors, ["bill_id", "member_id"])
    await pg.insert_batch("govinfo.bill_subjects", result.bill_subjects, ["bill_id", "subject_term", "subject_type"])
    await pg.insert_batch("govinfo.votes", result.votes, "vote_id")
    await pg.insert_batch("govinfo.vote_totals", result.vote_totals, "vote_id")
    await pg.insert_batch("govinfo.vote_actions", result.vote_actions, ["vote_id", "action_sequence"])
    await pg.insert_batch("govinfo.vote_ballots", result.vote_ballots, ["vote_id", "member_id"])
    await pg.insert_batch("govinfo.member_votes", result.member_votes, ["member_id", "vote_id"])
    await pg.insert_batch("govinfo.member_attendance", result.member_attendance, ["member_id", "session_id", "congress_number", "chamber_code"])
    await pg.insert_batch("govinfo.members", result.members, "member_id")


async def write_results(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    async with aiofiles.open(path, "w") as fh:
        for row in rows:
            await fh.write(json.dumps(row, default=str) + "\n")


async def ingest_bulk(downloader: GovInfoBulkDownloader, collections: Sequence[str], output_dir: Path, config: IngestionConfig) -> None:
    for collection in collections:
        logging.info("Downloading bulk collection %s", collection)
        count = 0
        async for link in downloader.iter_collection_links(collection):
            filename = link.rstrip("/").split("/")[-1]
            hashed = hashlib.sha256(link.encode()).hexdigest()[:16]
            download_path = output_dir / "downloads" / collection / f"{hashed}-{filename}"
            downloaded = await downloader.download(link, download_path)
            manifest_entry = {"source_url": link, "local_path": str(downloaded), "size_bytes": downloaded.stat().st_size}
            if downloaded.suffix.lower() == ".zip":
                extracted_files = await downloader.extract_zip(downloaded, output_dir / "extracted" / collection / hashed)
                manifest_entry["extracted"] = [str(path) for path in extracted_files]
            await write_results(output_dir / "manifests" / f"{collection.lower()}_{hashed}.jsonl", [manifest_entry])
            count += 1
            if config.bulk_sample and count >= config.bulk_sample:
                logging.info("Bulk sample limit reached for %s", collection)
                break


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="GovInfo bulk/API ingestion orchestrator")
    parser.add_argument("--api-key", dest="api_key", default=os.environ.get("GOVINFO_API_KEY"))
    parser.add_argument("--collections", default="BILLS,BILLSTATUS,BILLSTATUSXML", help="Comma-separated API collections")
    parser.add_argument("--bulk-collections", default="BILLS,BILLSTATUS,VOTES", help="Comma-separated bulk collections to download")
    parser.add_argument("--start")
    parser.add_argument("--end")
    parser.add_argument("--page-size", type=int, default=200)
    parser.add_argument("--max-packages", type=int)
    parser.add_argument("--bulk-sample", type=int)
    parser.add_argument("--output-dir", default="govinfo_output")
    parser.add_argument("--pg-dsn", default=os.environ.get("GOVINFO_PG_DSN"))
    parser.add_argument("--max-concurrency", type=int, default=12)
    parser.add_argument("--bulk-concurrency", type=int, default=6)
    parser.add_argument("--disable-api", action="store_true")
    parser.add_argument("--disable-bulk", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--log-level", default="INFO")
    return parser.parse_args(argv)


async def run(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO), format="%(asctime)s %(levelname)s %(message)s")
    if not args.api_key and not args.disable_api:
        raise SystemExit("An API key is required unless --disable-api is set")
    config = IngestionConfig(
        api_key=args.api_key or "",
        collections=[c.strip().upper() for c in args.collections.split(",") if c.strip()],
        bulk_collections=[c.strip().upper() for c in args.bulk_collections.split(",") if c.strip()],
        start=args.start,
        end=args.end,
        page_size=args.page_size,
        max_packages=args.max_packages,
        bulk_sample=args.bulk_sample,
        output_dir=Path(args.output_dir),
        pg_dsn=args.pg_dsn,
        max_concurrency=args.max_concurrency,
        bulk_concurrency=args.bulk_concurrency,
        enable_api=not args.disable_api,
        enable_bulk=not args.disable_bulk,
        dry_run=args.dry_run,
    )
    config.output_dir.mkdir(parents=True, exist_ok=True)
    timeout = aiohttp.ClientTimeout(total=config.request_timeout, connect=config.connect_timeout)
    connector = aiohttp.TCPConnector(limit=math.ceil(config.max_concurrency * 1.5))
    async with aiohttp.ClientSession(timeout=timeout, connector=connector, headers={"User-Agent": "govinfo-ingest/1.0"}) as session:
        api_client = GovInfoAPIClient(session, config)
        downloader = GovInfoBulkDownloader(session, config)
        transformer = PackageTransformer()
        pg = await PostgresIngestor.create(config.pg_dsn) if not config.dry_run else None
        try:
            tasks = []
            if config.enable_api:
                for collection in config.collections:
                    tasks.append(process_collection(api_client, transformer, collection, pg, config, config.output_dir))
            if tasks:
                await asyncio.gather(*tasks)
            if config.enable_bulk:
                await ingest_bulk(downloader, config.bulk_collections, config.output_dir, config)
        finally:
            if pg is not None:
                await pg.close()
            await downloader.close()


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
