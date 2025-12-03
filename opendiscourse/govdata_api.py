"""Wrapper for the https://www.govdata.gov API endpoints."""

from __future__ import annotations

import logging
from pathlib import Path

import requests

from .integration_constants import REQUEST_TIMEOUT
from .utils.decorators import retry

logger = logging.getLogger(__name__)


class GovDataAPI:
    """Client for the govdata.gov API and bulk data services."""

    BASE_URL = "https://www.govdata.gov"

    def __init__(self, session: requests.Session | None = None) -> None:
        self.session = session or requests.Session()

    @retry()
    def list_datasets(self) -> list[dict[str, object]]:
        """Return a list of available datasets."""
        url = f"{self.BASE_URL}/api/1/api"
        resp = self.session.get(url, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        return data.get("datasets", [])

    @retry()
    def get_dataset_metadata(self, dataset_id: str) -> dict[str, object]:
        """Retrieve metadata for a specific dataset."""
        url = f"{self.BASE_URL}/api/1/datasets/{dataset_id}"
        resp = self.session.get(url, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        return resp.json()

    @retry()
    def download_bulk_data(self, dataset_id: str, target_dir: str | Path) -> Path:
        """Download a bulk dataset to ``target_dir``."""
        target_path = Path(target_dir)
        target_path.mkdir(parents=True, exist_ok=True)
        url = f"{self.BASE_URL}/bulkdata/{dataset_id}"
        resp = self.session.get(url, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        file_path = target_path / f"{dataset_id}.zip"
        with open(file_path, "wb") as f:
            f.write(resp.content)
        logger.info("Downloaded bulk data %s to %s", dataset_id, file_path)
        return file_path
