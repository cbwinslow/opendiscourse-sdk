"""crawl4ai + OpenRouter ingestion pipelines for political intelligence."""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Awaitable, Callable, Sequence

from crawl4ai import AsyncCrawler, CrawlRequest, CrawlResponse
from openrouter import OpenRouter

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class CrawlTarget:
    """Configuration for a single crawl job."""

    name: str
    url: str
    frequency: str
    content_selector: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    post_processors: Sequence[Callable[[CrawlResponse], Awaitable[dict[str, Any]]]] = ()


@dataclass(slots=True)
class PipelineSettings:
    """Runtime configuration for the ingestion pipeline."""

    output_dir: Path
    summary_model: str = "anthropic/claude-3.5-sonnet"
    embedding_model: str = "openai/text-embedding-3-large"
    max_concurrency: int = 4


class Crawl4AIOpenRouterPipeline:
    """Coordinates crawl4ai fetches with OpenRouter-powered enrichment."""

    def __init__(
        self,
        crawler: AsyncCrawler,
        router_client: OpenRouter,
        targets: Sequence[CrawlTarget],
        settings: PipelineSettings,
        upsert_callback: Callable[[dict[str, Any]], Awaitable[None]],
    ) -> None:
        """Initialize the pipeline with dependencies.

        Args:
            crawler: Configured AsyncCrawler instance.
            router_client: OpenRouter client for LLM/embedding calls.
            targets: Sequence of crawl targets to process.
            settings: Runtime configuration.
            upsert_callback: Async function to persist enriched records.
        """
        self._crawler = crawler
        self._router = router_client
        self._targets = targets
        self._settings = settings
        self._upsert = upsert_callback

    async def run(self) -> None:
        """Execute all crawl targets respecting concurrency limits."""

        semaphore = asyncio.Semaphore(self._settings.max_concurrency)

        async def _run_target(target: CrawlTarget) -> None:
            async with semaphore:
                await self._process_target(target)

        await asyncio.gather(*(_run_target(target) for target in self._targets))

    async def _process_target(self, target: CrawlTarget) -> None:
        logger.info("Crawling %s", target.url)
        request = CrawlRequest(url=target.url, selector=target.content_selector)
        response = await self._crawler.crawl(request)

        if response.error:
            logger.error("Crawl failed for %s: %s", target.url, response.error)
            return

        enriched = await self._enrich_response(target, response)
        await self._persist_output(target, enriched)
        await self._upsert(enriched)

    async def _enrich_response(self, target: CrawlTarget, response: CrawlResponse) -> dict[str, Any]:
        """Generate summaries, embeddings, and metadata for downstream storage."""

        content = response.content or ""
        summary_prompt = (
            "You are an analyst tracking political activity. Summarize the content with"
            " bill references, participants, and notable claims."
        )
        summary = await self._router.responses.create(
            model=self._settings.summary_model,
            messages=[{"role": "system", "content": summary_prompt}, {"role": "user", "content": content}],
        )

        embedding = await self._router.embeddings.create(
            model=self._settings.embedding_model,
            input=content,
        )

        summary_text = getattr(summary, "output_text", getattr(summary, "text", summary))
        emb_value: Any = None
        # handle object-like responses with .data and list payloads
        if hasattr(embedding, "data") and getattr(embedding, "data"):
            first = embedding.data[0]
            emb_value = getattr(first, "embedding", None)
        # handle dict-like responses commonly returned by some clients
        elif isinstance(embedding, dict):
            data = embedding.get("data")
            if isinstance(data, list) and data:
                first = data[0]
                if isinstance(first, dict):
                    emb_value = first.get("embedding")
            else:
                emb_value = embedding.get("embedding")
        else:
            # fallback to the raw embedding object
            emb_value = embedding
        enriched: dict[str, Any] = {
            "target": target.name,
            "url": target.url,
            "frequency": target.frequency,
            "retrieved_at": datetime.utcnow().isoformat(),
            "raw_content": content,
            "summary": summary_text,
            "embedding": emb_value,
            "metadata": target.metadata,
        }

        for processor in target.post_processors:
            processed = await processor(response)
            enriched.update(processed)

        return enriched

    async def _persist_output(self, target: CrawlTarget, enriched: dict[str, Any]) -> None:
        self._settings.output_dir.mkdir(parents=True, exist_ok=True)
        output_path = self._settings.output_dir / f"{target.name}.jsonl"
        with output_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(enriched, ensure_ascii=False) + "\n")


async def default_upsert(record: dict[str, Any]) -> None:
    """Placeholder upsert: logs the record identifier for monitoring."""

    logger.debug("Upserting record for %s", record.get("url"))


def build_default_targets() -> list[CrawlTarget]:
    """Factory for standard legislative and social targets."""

    return [
        CrawlTarget(
            name="congress_bills",
            url="https://www.congress.gov/search?q=%7B%22source%22:%22legislation%22%7D",
            frequency="daily",
            content_selector=".basic-search-results-lists",  # narrow scrape to list entries
            metadata={"source": "congress.gov", "entity_type": "bill"},
        ),
        CrawlTarget(
            name="govinfo_hearings",
            url="https://www.govinfo.gov/app/collection/chrg",
            frequency="weekly",
            metadata={"source": "govinfo.gov", "entity_type": "hearing"},
        ),
        CrawlTarget(
            name="openstates_recent",
            url="https://api.openstates.org/v1/bills/?sort=updated_at",
            frequency="hourly",
            metadata={"source": "openstates", "entity_type": "bill"},
        ),
        CrawlTarget(
            name="openlegislation_updates",
            url="https://legislation.nysenate.gov/api/3/bills/advanced_search?term=*&sort=lastUpdate",
            frequency="daily",
            metadata={"source": "openlegislation", "entity_type": "bill"},
        ),
        CrawlTarget(
            name="politician_social_media",
            url="https://api.twitter.com/2/users/:id/tweets",
            frequency="hourly",
            metadata={"source": "twitter", "entity_type": "social_post"},
        ),
    ]


def configure_pipeline(
    targets: Sequence[CrawlTarget] | None = None,
    settings: PipelineSettings | None = None,
    upsert_callback: Callable[[dict[str, Any]], Awaitable[None]] = default_upsert,
) -> Crawl4AIOpenRouterPipeline:
    """Build a pipeline instance with shared crawler/router clients."""

    resolved_targets = list(targets or build_default_targets())
    resolved_settings = settings or PipelineSettings(output_dir=Path("data/crawl4ai"))

    crawler = AsyncCrawler()
    router_client = OpenRouter.from_env()

    return Crawl4AIOpenRouterPipeline(
        crawler=crawler,
        router_client=router_client,
        targets=resolved_targets,
        settings=resolved_settings,
        upsert_callback=upsert_callback,
    )


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    pipeline = configure_pipeline()
    asyncio.run(pipeline.run())


if __name__ == "__main__":
    main()
