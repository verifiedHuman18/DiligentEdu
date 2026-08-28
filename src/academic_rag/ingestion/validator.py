"""File Validation Service for Student Uploaded Materials (Phases 1-3)."""

import io
import logging
import os
import re
from typing import Optional, Union

import fitz  # PyMuPDF

from src.academic_rag.config import (
    MAX_UPLOAD_SIZE_BYTES,
    config,
)
from src.academic_rag.models.study_material import DocumentValidationResult

logger = logging.getLogger(__name__)


def sanitize_filename(filename: str) -> str:
    """Sanitizes user-provided filename to prevent path traversal or unsafe characters."""
    clean = os.path.basename(filename).strip()
    clean = re.sub(r"[^\w\s\.\(\)-]", "_", clean)
    clean = re.sub(r"\s+", " ", clean)
    return clean or "uploaded_material.pdf"


def validate_pdf_file(
    file_data: Union[bytes, io.BytesIO],
    filename: str,
    max_size_bytes: int = MAX_UPLOAD_SIZE_BYTES,
    min_chars_per_page: int = 20,
) -> DocumentValidationResult:
    """
    Validates an uploaded PDF file:
    1. File extension must be strictly .pdf.
    2. File size must not exceed max_size_bytes.
    3. File must be a valid, readable PDF (not corrupted).
    4. Detects scanned / image-only PDFs with insufficient text layer.
    """
    clean_name = sanitize_filename(filename)
    if not clean_name.lower().endswith(".pdf"):
        return DocumentValidationResult(
            is_valid=False,
            error_message="Unsupported file type. Only PDF (.pdf) documents are supported.",
        )

    # Resolve raw bytes
    if isinstance(file_data, io.BytesIO):
        raw_bytes = file_data.getvalue()
    elif isinstance(file_data, bytes):
        raw_bytes = file_data
    else:
        try:
            raw_bytes = file_data.read()
        except Exception as e:
            return DocumentValidationResult(
                is_valid=False,
                error_message=f"Failed to read upload data: {e}",
            )

    size_bytes = len(raw_bytes)
    if size_bytes == 0:
        return DocumentValidationResult(
            is_valid=False,
            error_message="Uploaded file is empty (0 bytes).",
            file_size_bytes=0,
        )

    if size_bytes > max_size_bytes:
        max_mb = max_size_bytes / (1024 * 1024)
        actual_mb = size_bytes / (1024 * 1024)
        return DocumentValidationResult(
            is_valid=False,
            error_message=f"File exceeds maximum allowed size ({actual_mb:.1f} MB > {max_mb:.1f} MB).",
            file_size_bytes=size_bytes,
        )

    # Verify PDF structure and readability via PyMuPDF
    try:
        doc = fitz.open(stream=raw_bytes, filetype="pdf")
    except Exception as e:
        logger.warning(f"Failed to open PDF {clean_name}: {e}")
        return DocumentValidationResult(
            is_valid=False,
            error_message="Invalid or corrupted PDF file. Could not parse document structure.",
            file_size_bytes=size_bytes,
        )

    try:
        page_count = len(doc)
        if page_count == 0:
            doc.close()
            return DocumentValidationResult(
                is_valid=False,
                error_message="PDF contains no pages.",
                file_size_bytes=size_bytes,
                detected_pages=0,
            )

        # Inspect extracted text volume to detect scanned/image-only PDFs
        total_text_chars = 0
        for page_idx in range(page_count):
            page = doc[page_idx]
            page_text = page.get_text("text").strip()
            total_text_chars += len(page_text)

        doc.close()

        avg_chars_per_page = total_text_chars / page_count if page_count > 0 else 0
        if avg_chars_per_page < min_chars_per_page or total_text_chars < 50:
            return DocumentValidationResult(
                is_valid=False,
                error_message=(
                    "OCR required: The uploaded PDF appears to be scanned or image-only with little/no readable text. "
                    "Please upload a standard text PDF."
                ),
                file_size_bytes=size_bytes,
                detected_pages=page_count,
                is_scanned_pdf=True,
            )

        return DocumentValidationResult(
            is_valid=True,
            error_message=None,
            file_size_bytes=size_bytes,
            detected_pages=page_count,
            is_scanned_pdf=False,
        )

    except Exception as e:
        logger.error(f"Error inspecting PDF content {clean_name}: {e}")
        return DocumentValidationResult(
            is_valid=False,
            error_message=f"Error analyzing PDF content: {e}",
            file_size_bytes=size_bytes,
        )
