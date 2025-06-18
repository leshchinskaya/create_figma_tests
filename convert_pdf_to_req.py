#!/usr/bin/env python3
"""Convert a PDF requirements document to Markdown and update req.md.

Usage:
    python3 convert_pdf_to_req.py <path_or_url_to_pdf>

The script accepts either a local file path or an HTTPS URL (for example from
Confluence)."""

from pathlib import Path
from urllib.parse import urlparse
import sys
import tempfile
import requests

from pdfminer.high_level import extract_text

REQ_PATH = Path("create_final_tests") / "artifacts" / "req.md"


def pdf_to_markdown(pdf_path: Path) -> str:
    """Extract text from PDF and return it as Markdown-formatted string."""
    text = extract_text(str(pdf_path))
    text = text.replace("\r\n", "\n").strip()
    return text + "\n"


def is_url(path_or_url: str) -> bool:
    """Return True if the argument looks like an HTTP(S) URL."""
    parsed = urlparse(path_or_url)
    return parsed.scheme in {"http", "https"}


def download_pdf(url: str) -> Path:
    """Download PDF from URL and return the local temporary path."""
    response = requests.get(url)
    response.raise_for_status()
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(response.content)
        return Path(tmp.name)


def main():
    if len(sys.argv) != 2:
        print("Usage: python3 convert_pdf_to_req.py <path_or_url_to_pdf>")
        sys.exit(1)

    source = sys.argv[1]

    downloaded_temp: Path | None = None

    if is_url(source):
        try:
            downloaded_temp = download_pdf(source)
            pdf_path = downloaded_temp
        except requests.exceptions.RequestException as e:
            print(f"Failed to download PDF: {e}")
            sys.exit(1)
    else:
        pdf_path = Path(source)
        if not pdf_path.is_file():
            print(f"File not found: {pdf_path}")
            sys.exit(1)

    md_content = pdf_to_markdown(pdf_path)
    REQ_PATH.parent.mkdir(parents=True, exist_ok=True)
    REQ_PATH.write_text(md_content, encoding="utf-8")
    print(f"Converted {source} to Markdown and saved to {REQ_PATH}")

    if downloaded_temp:
        downloaded_temp.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
