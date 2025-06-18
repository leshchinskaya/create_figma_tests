#!/usr/bin/env python3
"""Convert a PDF requirements document to Markdown and update req.md.

Usage:
    python3 convert_pdf_to_req.py path/to/requirements.pdf
"""

from pathlib import Path
import sys

from pdfminer.high_level import extract_text

REQ_PATH = Path("create_final_tests") / "artifacts" / "req.md"


def pdf_to_markdown(pdf_path: Path) -> str:
    """Extract text from PDF and return it as Markdown-formatted string."""
    text = extract_text(str(pdf_path))
    text = text.replace("\r\n", "\n").strip()
    return text + "\n"


def main():
    if len(sys.argv) != 2:
        print("Usage: python3 convert_pdf_to_req.py path/to/requirements.pdf")
        sys.exit(1)

    pdf_file = Path(sys.argv[1])
    if not pdf_file.is_file():
        print(f"File not found: {pdf_file}")
        sys.exit(1)

    md_content = pdf_to_markdown(pdf_file)
    REQ_PATH.parent.mkdir(parents=True, exist_ok=True)
    REQ_PATH.write_text(md_content, encoding="utf-8")
    print(f"Converted {pdf_file} to Markdown and saved to {REQ_PATH}")


if __name__ == "__main__":
    main()
