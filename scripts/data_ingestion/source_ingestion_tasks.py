"""Source-specific enrichment callbacks for crawl4ai pipelines."""

from __future__ import annotations

import json
from typing import Any

from crawl4ai import CrawlResponse


async def parse_congress_listing(response: CrawlResponse) -> dict[str, Any]:
    """Extract bill identifiers from congress.gov search markup."""

    soup = response.soup  # type: ignore[attr-defined]
    bill_ids: list[str] = []
    for link in soup.select("ol.basic-search-results-lists li .result-heading a"):  # type: ignore[union-attr]
        href = getattr(link, "get", lambda _x, default=None: default)("href")
        if not href:
            continue
        bill_ids.append(href.split("/")[-1])

    return {"bill_ids": bill_ids}


async def parse_govinfo_metadata(response: CrawlResponse) -> dict[str, Any]:
    """Extract publication identifiers and download links from govinfo."""

    soup = response.soup  # type: ignore[attr-defined]
    records: list[dict[str, str]] = []
    for item in soup.select("div#collection-data li"):  # type: ignore[union-attr]
        title_node = item.select_one("span.title")
        link_node = item.select_one("a.download")
        records.append(
            {
                "title": title_node.text.strip() if title_node else "",
                "download_url": link_node["href"] if link_node and link_node.has_attr("href") else "",
            }
        )

    return {"documents": records}


async def parse_openstates_payload(response: CrawlResponse) -> dict[str, Any]:
    """Convert OpenStates JSON into normalized bill metadata."""

    payload = json.loads(response.content or "{}")
    bills: list[dict[str, Any]] = []
    for item in payload.get("results", []):
        bills.append(
            {
                "bill_id": item.get("identifier"),
                "jurisdiction": item.get("jurisdiction"),
                "latest_action_date": item.get("latest_action_date"),
                "title": item.get("title"),
                "classification": item.get("classification"),
            }
        )

    return {"bills": bills}


async def parse_openlegislation_payload(response: CrawlResponse) -> dict[str, Any]:
    """Normalize OpenLegislation API results."""

    payload = json.loads(response.content or "{}")
    results = payload.get("result", {})
    return {
        "count": results.get("total"),
        "bills": [
            {
                "print_no": bill.get("printNo"),
                "session": bill.get("session"),
                "status": bill.get("status"),
                "title": bill.get("title"),
            }
            for bill in results.get("items", [])
        ],
    }


async def parse_social_payload(response: CrawlResponse) -> dict[str, Any]:
    """Normalize social media posts for downstream sentiment analysis."""

    payload = json.loads(response.content or "{}")
    posts = []
    for tweet in payload.get("data", []):
        posts.append(
            {
                "post_id": tweet.get("id"),
                "author_id": tweet.get("author_id"),
                "text": tweet.get("text"),
                "created_at": tweet.get("created_at"),
            }
        )

    return {"posts": posts}


DEFAULT_PROCESSORS = {
    "congress_bills": parse_congress_listing,
    "govinfo_hearings": parse_govinfo_metadata,
    "openstates_recent": parse_openstates_payload,
    "openlegislation_updates": parse_openlegislation_payload,
    "politician_social_media": parse_social_payload,
}
