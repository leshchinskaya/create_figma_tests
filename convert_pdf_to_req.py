#!/usr/bin/env python3
"""Convert documents to a structured folder format with page-specific content.

Usage:
    python3 convert_pdf_to_req.py <path_or_url_or_confluence_page>

The script accepts:
 - a local PDF file path: Text is extracted page by page.
 - a direct URL to a PDF file: Text is extracted page by page.
 - a Confluence page URL: Content is fetched and converted to Markdown.
   (Child pages will be processed similarly if it's a parent Confluence page).

Confluence credentials must be configured in `config.py`.
The output will be saved in page-specific folders under:
./create_final_tests/folder_structure/confluence/
Each Confluence page or PDF page becomes a 'page_N/content.md' file.
"""

import sys
import tempfile
import re
import os
from pathlib import Path
from urllib.parse import urlparse, parse_qs, unquote

import requests
import config

try:
    from pdfminer.high_level import extract_pages
    from pdfminer.layout import LTTextContainer
except ImportError:
    print("pdfminer.six is not installed. Please install it by running: pip install pdfminer.six")
    sys.exit(1)

try:
    import markdownify
except ImportError:
    print("markdownify is not installed. Please install it by running: pip install markdownify")
    sys.exit(1)

BASE_OUTPUT_DIR = Path("./create_final_tests/folder_structure/confluence")


def extract_text_per_page(pdf_path: Path) -> list[str]:
    """Extract text from each page of a PDF and return a list of strings."""
    page_texts = []
    for page_layout in extract_pages(pdf_path):
        page_text = ""
        for element in page_layout:
            if isinstance(element, LTTextContainer):
                page_text += element.get_text()
        page_texts.append(page_text.strip())
    return page_texts


def generate_document_id(source_path_or_url: str, is_confluence: bool = False, confluence_pid: str | None = None) -> str:
    """Generate a sanitized document ID for folder naming."""
    if is_confluence and confluence_pid:
        name = f"confluence_{confluence_pid}"
    elif is_url(source_path_or_url):
        parsed_url = urlparse(source_path_or_url)
        path_part = unquote(parsed_url.path.strip('/'))
        if path_part:
            name = Path(path_part).stem
        else:
            name = parsed_url.netloc + "_" + parsed_url.path.replace('/', '_')
        if not name:
            name = "downloaded_pdf"
    else:
        name = Path(source_path_or_url).stem
    
    name = re.sub(r'[^a-zA-Z0-9_\-]', '_', name)
    name = re.sub(r'_+', '_', name)
    name = name.strip('_')
    return name if name else "default_document_id"


def process_pdf_to_page_folders(pdf_path: Path, document_id: str, base_output_dir: Path):
    """Extract text per PDF page and save to base_output_dir/document_id/page_N/content.md."""
    try:
        page_texts = extract_text_per_page(pdf_path)
    except Exception as e:
        print(f"Error extracting text from {pdf_path.name}: {e}")
        return

    doc_output_dir = base_output_dir / document_id
    
    if not page_texts:
        print(f"No text extracted from {pdf_path.name} (document: {document_id}). Skipping.")
        return

    for i, page_text in enumerate(page_texts):
        page_num = i + 1
        page_dir = doc_output_dir / f"page_{page_num}"
        page_dir.mkdir(parents=True, exist_ok=True)
        output_file = page_dir / "content.md"
        try:
            output_file.write_text(page_text, encoding="utf-8")
        except Exception as e:
            print(f"Error writing page {page_num} for {document_id} to {output_file}: {e}")
            continue
    print(f"Successfully processed PDF {pdf_path.name} into {doc_output_dir} ({len(page_texts)} pages)")


def fetch_and_convert_confluence_to_markdown(page_id: str, session: requests.Session, document_id: str, base_output_dir: Path) -> str | None:
    """Fetch Confluence page content as HTML and convert it to Markdown."""
    if not hasattr(config, 'CONFLUENCE_BASE_URL') or not config.CONFLUENCE_BASE_URL:
        print(f"Error: CONFLUENCE_BASE_URL not configured. Cannot fetch page {page_id}.")
        return None

    api_url = f"{config.CONFLUENCE_BASE_URL}/rest/api/content/{page_id}?expand=body.view"
    try:
        print(f"Fetching content for Confluence page ID {page_id} from {api_url}...")
        resp = session.get(api_url)
        resp.raise_for_status()
        data = resp.json()
        html_content = data.get('body', {}).get('view', {}).get('value')
        if not html_content:
            print(f"No HTML content found for Confluence page ID {page_id}.")
            return None
        
        md_content = markdownify.markdownify(html_content, heading_style=markdownify.ATX)
        if md_content is None:
            print(f"Markdown conversion failed for page ID {page_id}.")
            return None

        # --- Attachment Handling ---
        page_1_dir = base_output_dir / document_id / "page_1"
        attachments_dir = page_1_dir / "attachments"

        # Regex to find /download/attachments/... paths not followed by ')' and within parentheses
        attachment_url_pattern = re.compile(r'/download/attachments/[^)]+(?=\))')
        found_attachment_paths = sorted(list(set(attachment_url_pattern.findall(md_content))), key=len, reverse=True)

        if found_attachment_paths:
            attachments_dir.mkdir(parents=True, exist_ok=True)
            print(f"Found {len(found_attachment_paths)} unique attachment paths to process for {document_id}.")

            for original_path in found_attachment_paths:
                try:
                    if not original_path.startswith("http"):
                        full_download_url = f"{config.CONFLUENCE_BASE_URL.rstrip('/')}{original_path}"
                    else:
                        full_download_url = original_path # Should ideally not happen for /download/attachments

                    parsed_original_url = urlparse(original_path)
                    filename = unquote(Path(parsed_original_url.path).name)
                    if not filename:
                        print(f"Warning: Could not determine filename for attachment {original_path} in {document_id}. Skipping.")
                        continue
                    
                    local_save_path = attachments_dir / filename
                    # Ensure relative path uses forward slashes for Markdown
                    relative_markdown_path = (Path("attachments") / filename).as_posix()

                    print(f"Downloading attachment: {full_download_url} to {local_save_path} for {document_id}")
                    dl_resp = session.get(full_download_url, stream=True)
                    dl_resp.raise_for_status()

                    with open(local_save_path, 'wb') as f:
                        for chunk in dl_resp.iter_content(chunk_size=8192):
                            f.write(chunk)
                    
                    print(f"Successfully downloaded {filename}. Updating Markdown link.")
                    md_content = md_content.replace(original_path, relative_markdown_path)

                except requests.exceptions.RequestException as e_dl:
                    print(f"Error downloading attachment {original_path} for {document_id}: {e_dl}. Original link will be kept.")
                except IOError as e_io:
                    print(f"Error saving attachment {filename} for {document_id}: {e_io}. Original link will be kept.")
                except Exception as e_gen:
                    print(f"An unexpected error occurred while processing attachment {original_path} for {document_id}: {e_gen}. Original link will be kept.")
        # --- End Attachment Handling ---

        print(f"Successfully converted Confluence page ID {page_id} to Markdown (attachments processed).")
        return md_content
    except requests.exceptions.RequestException as e:
        print(f"Error fetching Confluence page ID {page_id}: {e}")
        return None
    except Exception as e:
        print(f"Error converting HTML to Markdown for page ID {page_id}: {e}")
        return None


def save_markdown_content(markdown_text: str, document_id: str, base_output_dir: Path):
    """Save the given markdown text to base_output_dir/document_id/page_1/content.md."""
    doc_output_dir = base_output_dir / document_id
    page_dir = doc_output_dir / "page_1" 
    page_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = page_dir / "content.md"
    try:
        output_file.write_text(markdown_text, encoding="utf-8")
        print(f"Successfully saved Markdown for {document_id} to {output_file}")
    except Exception as e:
        print(f"Error writing Markdown for {document_id} to {output_file}: {e}")


def is_url(path_or_url: str) -> bool:
    parsed = urlparse(path_or_url)
    return parsed.scheme in {"http", "https"}


def is_confluence_page(url: str) -> bool:
    if not hasattr(config, 'CONFLUENCE_BASE_URL') or not config.CONFLUENCE_BASE_URL:
        return False
    base = urlparse(config.CONFLUENCE_BASE_URL).netloc
    parsed = urlparse(url)
    return parsed.netloc == base and "pageId" in parse_qs(parsed.query)


def parse_page_id(value: str) -> str | None:
    if value.isdigit():
        return value
    parsed = urlparse(value)
    qs = parse_qs(parsed.query)
    if "pageId" in qs:
        page_id_list = qs["pageId"]
        if page_id_list:
            return page_id_list[0]
    return None


def fetch_descendants(page_id: str, session: requests.Session) -> list[str]:
    ids = [page_id]
    if not hasattr(config, 'CONFLUENCE_BASE_URL') or not config.CONFLUENCE_BASE_URL:
        print("Error: CONFLUENCE_BASE_URL not configured. Cannot fetch descendants.")
        return ids

    api_url = f"{config.CONFLUENCE_BASE_URL}/rest/api/content/{page_id}/child/page?limit=100"
    try:
        resp = session.get(api_url)
        resp.raise_for_status()
        data = resp.json()
        for child in data.get("results", []):
            child_id = child.get("id")
            if child_id:
                ids.extend(fetch_descendants(child_id, session))
    except requests.exceptions.RequestException as e:
        print(f"Error fetching descendants for page {page_id}: {e}")
    return ids


def download_pdf(url: str, session: requests.Session | None = None) -> Path | None:
    effective_session = session or requests.Session()
    try:
        response = effective_session.get(url)
        response.raise_for_status()
        if 'application/pdf' not in response.headers.get('Content-Type', '').lower():
            print(f"Warning: Content at {url} does not appear to be a PDF. Content-Type: {response.headers.get('Content-Type')}")
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(response.content)
            return Path(tmp.name)
    except requests.exceptions.RequestException as e:
        print(f"Failed to download PDF from {url}: {e}")
        return None


def main():
    if len(sys.argv) != 2:
        print("Usage: python3 convert_pdf_to_req.py <path_or_url_or_confluence_page>")
        sys.exit(1)

    source = sys.argv[1].strip()
    BASE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    downloaded_files_to_clean: list[Path] = []
    session = requests.Session()
    if hasattr(config, 'CONFLUENCE_USERNAME') and hasattr(config, 'CONFLUENCE_PASSWORD'):
        if config.CONFLUENCE_USERNAME and config.CONFLUENCE_PASSWORD:
            session.auth = (config.CONFLUENCE_USERNAME, config.CONFLUENCE_PASSWORD)
        else:
            print("Warning: Confluence username or password missing. Confluence operations might fail.")
    else:
        print("Warning: CONFLUENCE_USERNAME or CONFLUENCE_PASSWORD not in config.py. Confluence operations might fail.")

    parsed_source_page_id = parse_page_id(source)
    is_conf_page_check = is_confluence_page(source)

    if parsed_source_page_id and is_conf_page_check:
        print(f"Processing Confluence source: {source} (Page ID: {parsed_source_page_id})")
        if not hasattr(config, 'CONFLUENCE_BASE_URL') or not config.CONFLUENCE_BASE_URL:
            print("Error: CONFLUENCE_BASE_URL not configured. Cannot process Confluence pages.")
            sys.exit(1)

        page_ids_to_process = fetch_descendants(parsed_source_page_id, session)
        print(f"Found {len(page_ids_to_process)} Confluence pages to process (including descendants).")

        for pid_to_process in page_ids_to_process:
            doc_id = generate_document_id(source_path_or_url="", is_confluence=True, confluence_pid=pid_to_process) # Moved doc_id generation up
            markdown_content = fetch_and_convert_confluence_to_markdown(pid_to_process, session, doc_id, BASE_OUTPUT_DIR)
            if markdown_content is not None:
                save_markdown_content(markdown_content, doc_id, BASE_OUTPUT_DIR)
            else:
                print(f"Skipping Confluence page ID {pid_to_process} due to fetch/conversion failure.")
    
    elif is_url(source):
        print(f"Processing URL source (expected PDF): {source}")
        temp_pdf_path = download_pdf(source, session=session)
        if temp_pdf_path:
            downloaded_files_to_clean.append(temp_pdf_path)
            doc_id = generate_document_id(source_path_or_url=source)
            process_pdf_to_page_folders(temp_pdf_path, doc_id, BASE_OUTPUT_DIR)
        else:
            print(f"Failed to process URL {source} as PDF due to download failure or non-PDF content.")

    else:
        print(f"Processing local file source (expected PDF): {source}")
        local_pdf_path = Path(source)
        if local_pdf_path.is_file() and local_pdf_path.suffix.lower() == '.pdf':
            doc_id = generate_document_id(source_path_or_url=str(local_pdf_path))
            process_pdf_to_page_folders(local_pdf_path, doc_id, BASE_OUTPUT_DIR)
        elif not local_pdf_path.is_file():
            print(f"Error: File not found at {local_pdf_path}")
        else:
            print(f"Error: File {local_pdf_path} is not a PDF.")

    if downloaded_files_to_clean:
        print(f"Cleaning up {len(downloaded_files_to_clean)} temporary downloaded PDF files...")
        for f_path in downloaded_files_to_clean:
            try:
                f_path.unlink(missing_ok=True)
            except Exception as e:
                print(f"Warning: Could not delete temporary file {f_path}: {e}")
    print("Processing complete.")

if __name__ == "__main__":
    main()
