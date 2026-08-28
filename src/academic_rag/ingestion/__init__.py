"""Study Material Ingestion Package (Phases 1-8, 20-21)."""

from src.academic_rag.ingestion.chunker import chunk_document_pages, split_text_into_chunks
from src.academic_rag.ingestion.document_processor import (
    clean_extracted_text,
    extract_pages_from_pdf,
)
from src.academic_rag.ingestion.pdf_ingester import ingest_study_material_pdf
from src.academic_rag.ingestion.validator import sanitize_filename, validate_pdf_file

__all__ = [
    "validate_pdf_file",
    "sanitize_filename",
    "extract_pages_from_pdf",
    "clean_extracted_text",
    "split_text_into_chunks",
    "chunk_document_pages",
    "ingest_study_material_pdf",
]
