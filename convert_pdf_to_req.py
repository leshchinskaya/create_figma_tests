#!/usr/bin/env python3
"""Convert requirement documents to Markdown and update req.md.

Usage:
    python3 convert_pdf_to_req.py <path_or_url_or_confluence_page>

The script accepts:
 - a local PDF file path
 - a direct URL to a PDF file
 - a Confluence page URL (its child pages will be downloaded as well).
Confluence credentials must be configured in `config.py`."""

from pathlib import Path
from urllib.parse import urlparse, parse_qs
import sys
import tempfile
import requests
import config

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


def is_confluence_page(url: str) -> bool:
    """Check if the URL points to a Confluence page with a pageId query."""
    base = urlparse(config.CONFLUENCE_BASE_URL).netloc
    parsed = urlparse(url)
    return parsed.netloc == base and "pageId" in parse_qs(parsed.query)


def parse_page_id(value: str) -> str | None:
    """Extract pageId from a URL or return the value if it looks like an ID."""
    if value.isdigit():
        return value
    parsed = urlparse(value)
    qs = parse_qs(parsed.query)
    if "pageId" in qs:
        return qs["pageId"][0]
    return None


def fetch_descendants(page_id: str, session: requests.Session) -> list[str]:
    """Return a list of page IDs including the given page and all descendants."""
    ids = [page_id]
    api_url = f"{config.CONFLUENCE_BASE_URL}/rest/api/content/{page_id}/child/page?limit=100"
    resp = session.get(api_url)
    resp.raise_for_status()
    data = resp.json()
    for child in data.get("results", []):
        child_id = child.get("id")
        if child_id:
            ids.extend(fetch_descendants(child_id, session))
    return ids


def download_pdf(url: str, session: requests.Session | None = None) -> Path:
    """Download PDF from URL using an optional session and return the local temporary path."""
    sess = session or requests.Session()
    response = sess.get(url)
    response.raise_for_status()
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(response.content)
        return Path(tmp.name)


def main():
    if len(sys.argv) != 2:
        print("Usage: python3 convert_pdf_to_req.py <path_or_url_or_confluence_page>")
        sys.exit(1)

    source = sys.argv[1]

    downloaded_files: list[Path] = []
    session = requests.Session()
    session.auth = (config.CONFLUENCE_USERNAME, config.CONFLUENCE_PASSWORD)

    if (page_id := parse_page_id(source)) and is_confluence_page(source):
        page_ids = fetch_descendants(page_id, session)
        md_parts = []
        for pid in page_ids:
            try:
                pdf_path = download_pdf(
                    f"{config.CONFLUENCE_BASE_URL}/spaces/flyingpdf/pdfpageexport.action?pageId={pid}",
                    session=session,
                )
                downloaded_files.append(pdf_path)
                md_parts.append(pdf_to_markdown(pdf_path))
            except requests.exceptions.RequestException as e:
                print(f"Failed to download page {pid}: {e}")
                sys.exit(1)
        md_content = "\n\n".join(md_parts)
    else:
        downloaded_temp: Path | None = None
        if is_url(source):
            try:
                sess = session if source.startswith(config.CONFLUENCE_BASE_URL) else None
                downloaded_temp = download_pdf(source, session=sess)
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
        if downloaded_temp:
            downloaded_files.append(downloaded_temp)

    REQ_PATH.parent.mkdir(parents=True, exist_ok=True)
    REQ_PATH.write_text(md_content, encoding="utf-8")
    print(f"Converted {source} to Markdown and saved to {REQ_PATH}")

    for f in downloaded_files:
        f.unlink(missing_ok=True)


if __name__ == "__main__":
    main()

