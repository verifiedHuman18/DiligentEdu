"""PDF Page Extraction and Text Normalization Processor (Phase 4)."""

import io
import logging
import re
from typing import List, Tuple, Union

import fitz  # PyMuPDF

logger = logging.getLogger(__name__)


def clean_extracted_text(text: str) -> str:
    """Normalizes whitespace, linebreaks, and non-printable characters while preserving paragraph semantics."""
    if not text:
        return ""
    # Normalize unicode spaces
    cleaned = text.replace("\u00a0", " ").replace("\u200b", "")
    # Normalize multiple newlines/tabs
    cleaned = re.sub(r"\r\n|\r", "\n", cleaned)
    # Remove control characters except tab and newline
    cleaned = "".join(
        ch for ch in cleaned if ch == "\n" or ch == "\t" or (ord(ch) >= 32 and ord(ch) != 127)
    )
    # Normalize multiple consecutive blank lines
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    # Normalize repeated inline horizontal spaces
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    return cleaned.strip()


def extract_pages_from_pdf(
    file_data: Union[bytes, io.BytesIO, str],
) -> List[Tuple[int, str]]:
    """
    Extracts text page-by-page from a PDF file.

    Args:
        file_data: PDF bytes, BytesIO stream, or filepath.

    Returns:
        List of (1-indexed page_number, cleaned_page_text) tuples for pages that contain text.
    """
    if isinstance(file_data, io.BytesIO):
        doc = fitz.open(stream=file_data.getvalue(), filetype="pdf")
    elif isinstance(file_data, bytes):
        doc = fitz.open(stream=file_data, filetype="pdf")
    elif isinstance(file_data, str):
        doc = fitz.open(file_data)
    else:
        raise ValueError(f"Unsupported file_data type: {type(file_data)}")

    page_results: List[Tuple[int, str]] = []
    try:
        for page_idx in range(len(doc)):
            page_num = page_idx + 1  # 1-indexed
            page = doc[page_idx]
            raw_text = page.get_text("text")
            cleaned = clean_extracted_text(raw_text)
            if cleaned:
                page_results.append((page_num, cleaned))
    finally:
        doc.close()

    return page_results
