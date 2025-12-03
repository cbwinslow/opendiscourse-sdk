"""Utilities for loading documents from various sources."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

import requests
from bs4 import BeautifulSoup
from pdfminer.high_level import extract_text as extract_pdf_text

from .integration_constants import REQUEST_TIMEOUT
from .utils.decorators import retry


class BaseLoader:
    """Base class for document loaders."""

    def load(self) -> str:  # pragma: no cover - simple interface
        raise NotImplementedError


class HTMLLoader(BaseLoader):
    """Load and extract text from a web page."""

    def __init__(self, url: str) -> None:
        self.url = url

    @retry()
    def load(self) -> str:
        response = requests.get(self.url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        return soup.get_text(separator="\n")


class TextFileLoader(BaseLoader):
    """Load text from a local file."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def load(self) -> str:
        return self.path.read_text(encoding="utf-8")


class PDFLoader(BaseLoader):
    """Load text from a local PDF file."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def load(self) -> str:
        return extract_pdf_text(str(self.path))


class RemotePDFLoader(BaseLoader):
    """Download a remote PDF and extract its text."""

    def __init__(self, url: str) -> None:
        self.url = url

    @retry()
    def load(self) -> str:
        response = requests.get(self.url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        with TemporaryDirectory() as tmpdir:
            pdf_path = Path(tmpdir) / "document.pdf"
            pdf_path.write_bytes(response.content)
            return extract_pdf_text(str(pdf_path))
