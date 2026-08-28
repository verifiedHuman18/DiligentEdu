"""Curriculum package."""

from backend.curriculum.concepts import (
    CHAPTER_CONCEPTS_REGISTRY,
    get_all_registered_chapters,
    get_chapter_concept_metadata,
)
from backend.curriculum.service import (
    CurriculumService,
    curriculum_service,
)

__all__ = [
    "CurriculumService",
    "curriculum_service",
    "CHAPTER_CONCEPTS_REGISTRY",
    "get_chapter_concept_metadata",
    "get_all_registered_chapters",
]
