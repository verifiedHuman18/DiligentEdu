#!/usr/bin/env python3
"""
NCERT Science Quiz Generation Engine (Backward Compatibility Module).
Delegates directly to src.academic_rag.quiz and src.academic_rag.curriculum.
"""

import os
import sys
from typing import Dict, Any, List, Optional, Union, Tuple

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.academic_rag.config import (
    MAPPING_FILE,
    INDEX_NAME,
    EMBEDDING_MODEL_NAME,
    DEFAULT_MODEL,
)
from src.academic_rag.curriculum.service import curriculum_service
from src.academic_rag.rag.retriever import get_embeddings, get_pinecone_index
from src.academic_rag.quiz.generator import (
    generate_quiz,
    create_student_quiz,
    retrieve_chapter_context_for_quiz,
)
from src.academic_rag.analytics.swat import get_available_chapters


def load_ncert_mapping() -> Dict[str, Any]:
    """Load NCERT chapter mapping file."""
    return curriculum_service.get_mapping()


def resolve_chapter(class_level: int, chapter_identifier: Union[str, int]) -> Tuple[int, str]:
    """Resolves chapter identifier into (chapter_number, canonical_chapter_title)."""
    return curriculum_service.resolve_chapter(class_level, chapter_identifier)


__all__ = [
    "load_ncert_mapping",
    "get_embeddings",
    "get_pinecone_index",
    "resolve_chapter",
    "retrieve_chapter_context_for_quiz",
    "generate_quiz",
    "create_student_quiz",
    "get_available_chapters",
    "MAPPING_FILE",
    "INDEX_NAME",
    "EMBEDDING_MODEL_NAME",
    "DEFAULT_MODEL",
]

if __name__ == "__main__":
    print("Testing Student Chapter Selection & Quiz Configuration...")
    chapters = get_available_chapters(class_level=10, student_id="student_001")
    print(f"Available Class 10 chapters ({len(chapters)}):")
    for ch in chapters[:4]:
        print(f"  Ch {ch['chapter_number']}: {ch['chapter']} -> Status: {ch['status']} (Score: {ch['score']})")
