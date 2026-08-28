"""Text Chunking Module for Student Study Material (Phase 5)."""

import logging
from typing import List, Optional, Tuple

from src.academic_rag.config import STUDENT_CHUNK_OVERLAP, STUDENT_CHUNK_SIZE
from src.academic_rag.models.study_material import DocumentChunk

logger = logging.getLogger(__name__)


def split_text_into_chunks(
    text: str,
    chunk_size: int = STUDENT_CHUNK_SIZE,
    chunk_overlap: int = STUDENT_CHUNK_OVERLAP,
) -> List[str]:
    """
    Splits a body of text into overlapping chunks, prioritizing paragraph and sentence boundaries.
    """
    clean = text.strip()
    if not clean:
        return []

    if len(clean) <= chunk_size:
        return [clean]

    chunks: List[str] = []
    start = 0
    total_len = len(clean)

    while start < total_len:
        end = min(start + chunk_size, total_len)

        if end < total_len:
            # Look for suitable split point: paragraph boundary (\n\n), then newline (\n), then sentence (. ), then space
            split_found = False
            lookback_limit = max(start + (chunk_size // 2), start)

            for delimiter in ["\n\n", "\n", ". ", "? ", "! ", " "]:
                idx = clean.rfind(delimiter, lookback_limit, end)
                if idx != -1:
                    end = idx + len(delimiter)
                    split_found = True
                    break

            if not split_found:
                # If no split delimiter found in window, hard-cut at end
                pass

        chunk_content = clean[start:end].strip()
        if chunk_content:
            chunks.append(chunk_content)

        if end >= total_len:
            break

        # Advance start with overlap
        start = max(start + 1, end - chunk_overlap)

    return chunks


def chunk_document_pages(
    pages: List[Tuple[int, str]],
    document_id: str,
    student_id: str,
    filename: str,
    material_name: str,
    class_level: int,
    subject: str = "Science",
    chapter: Optional[str] = None,
    chunk_size: int = STUDENT_CHUNK_SIZE,
    chunk_overlap: int = STUDENT_CHUNK_OVERLAP,
) -> List[DocumentChunk]:
    """
    Chunks extracted PDF pages into structured DocumentChunk objects with preserved page numbers and source metadata.
    """
    document_chunks: List[DocumentChunk] = []
    global_chunk_idx = 0

    for page_num, page_text in pages:
        page_chunks = split_text_into_chunks(
            page_text, chunk_size=chunk_size, chunk_overlap=chunk_overlap
        )
        for sub_idx, chunk_text in enumerate(page_chunks):
            chunk_id = f"{document_id}_p{page_num}_c{sub_idx}"
            chunk_obj = DocumentChunk(
                chunk_id=chunk_id,
                document_id=document_id,
                student_id=student_id,
                text=chunk_text,
                page=page_num,
                chunk_index=global_chunk_idx,
                filename=filename,
                material_name=material_name,
                class_level=class_level,
                subject=subject,
                chapter=chapter,
                source_type="user_upload",
            )
            document_chunks.append(chunk_obj)
            global_chunk_idx += 1

    return document_chunks
