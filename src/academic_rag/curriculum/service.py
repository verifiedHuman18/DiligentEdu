"""Authoritative NCERT Curriculum Service."""

import json
import logging
import os
from typing import Any, Dict, List, Optional, Tuple, Union

from src.academic_rag.config import config
from src.academic_rag.exceptions import ChapterNotFoundError, CurriculumError
from src.academic_rag.models.curriculum import ChapterInfo

logger = logging.getLogger(__name__)


DEFAULT_CURRICULUM_MAPPING = {
    "class9": {
        "iesc101.pdf": {
            "chapter_number": 1,
            "chapter": "Exploration: Entering the World of Secondary Science",
        },
        "iesc102.pdf": {"chapter_number": 2, "chapter": "Cell: The Building Block of Life"},
        "iesc103.pdf": {"chapter_number": 3, "chapter": "Tissues in Action"},
        "iesc104.pdf": {"chapter_number": 4, "chapter": "Describing Motion Around Us"},
        "iesc105.pdf": {"chapter_number": 5, "chapter": "Exploring Mixtures and their Separation"},
        "iesc106.pdf": {"chapter_number": 6, "chapter": "How Forces Affect Motion"},
        "iesc107.pdf": {"chapter_number": 7, "chapter": "Work, Energy, and Simple Machines"},
        "iesc108.pdf": {"chapter_number": 8, "chapter": "Journey Inside the Atom"},
        "iesc109.pdf": {"chapter_number": 9, "chapter": "Atomic Foundations of Matter"},
        "iesc110.pdf": {
            "chapter_number": 10,
            "chapter": "Sound Waves: Characteristics and Applications",
        },
        "iesc111.pdf": {"chapter_number": 11, "chapter": "Reproduction: How Life Continues"},
        "iesc112.pdf": {
            "chapter_number": 12,
            "chapter": "Patterns in Life: Diversity and Classification",
        },
        "iesc113.pdf": {
            "chapter_number": 13,
            "chapter": "Earth as a System: Energy, Matter, and Life",
        },
    },
    "class10": {
        "jesc101.pdf": {"chapter_number": 1, "chapter": "Chemical Reactions and Equations"},
        "jesc102.pdf": {"chapter_number": 2, "chapter": "Acids, Bases and Salts"},
        "jesc103.pdf": {"chapter_number": 3, "chapter": "Metals and Non-metals"},
        "jesc104.pdf": {"chapter_number": 4, "chapter": "Carbon and its Compounds"},
        "jesc105.pdf": {"chapter_number": 5, "chapter": "Life Processes"},
        "jesc106.pdf": {"chapter_number": 6, "chapter": "Control and Coordination"},
        "jesc107.pdf": {"chapter_number": 7, "chapter": "How do Organisms Reproduce?"},
        "jesc108.pdf": {"chapter_number": 8, "chapter": "Heredity"},
        "jesc109.pdf": {"chapter_number": 9, "chapter": "Light – Reflection and Refraction"},
        "jesc110.pdf": {"chapter_number": 10, "chapter": "The Human Eye and the Colourful World"},
        "jesc111.pdf": {"chapter_number": 11, "chapter": "Electricity"},
        "jesc112.pdf": {"chapter_number": 12, "chapter": "Magnetic Effects of Electric Current"},
        "jesc113.pdf": {"chapter_number": 13, "chapter": "Our Environment"},
    },
}


class CurriculumService:
    """Provides access to NCERT textbook syllabus, chapters, and resolver utilities."""

    def __init__(self, mapping_path: Optional[str] = None):
        self.mapping_path = mapping_path or str(config.mapping_file_path)
        self._cached_mapping: Optional[Dict[str, Any]] = None

    def get_mapping(self) -> Dict[str, Any]:
        """Loads and caches the raw JSON curriculum mapping."""
        if self._cached_mapping is not None:
            return self._cached_mapping

        if os.path.exists(self.mapping_path):
            try:
                with open(self.mapping_path, "r", encoding="utf-8") as f:
                    self._cached_mapping = json.load(f)
                    return self._cached_mapping
            except Exception as e:
                logger.error(f"Error loading {self.mapping_path}: {e}")

        # Fallback to built-in curriculum mapping
        self._cached_mapping = DEFAULT_CURRICULUM_MAPPING
        return self._cached_mapping

    def get_chapters_for_grade(self, class_level: int) -> List[ChapterInfo]:
        """Returns sorted list of all chapters in a grade (Class 9 or 10)."""
        mapping = self.get_mapping()
        class_key = f"class{int(class_level)}"
        class_map = mapping.get(class_key, {})

        chapters = []
        for fname, info in class_map.items():
            chapters.append(
                ChapterInfo(
                    chapter_number=int(info.get("chapter_number", 0)),
                    chapter_title=str(info.get("chapter", "")),
                    filename=fname,
                    class_level=int(class_level),
                )
            )

        chapters.sort(key=lambda x: x.chapter_number)
        return chapters

    def resolve_chapter(
        self, class_level: int, chapter_identifier: Union[str, int]
    ) -> Tuple[int, str]:
        """
        Resolves chapter identifier (int, digit str, or title substring) into
        (chapter_number, canonical_title).
        """
        try:
            class_int = int(class_level)
        except (ValueError, TypeError):
            raise CurriculumError(f"Invalid class level: {class_level}. Must be 9 or 10.")

        if class_int not in (9, 10):
            raise CurriculumError(
                f"Invalid class level: {class_int}. Supported class levels are 9 and 10."
            )

        mapping = self.get_mapping()
        class_key = f"class{class_int}"
        class_map = mapping.get(class_key, {})

        if not class_map:
            raise CurriculumError(f"No curriculum mapping data found for Class {class_int}")

        # Case 1: Integer or numeric string
        if isinstance(chapter_identifier, int) or (
            isinstance(chapter_identifier, str) and chapter_identifier.strip().isdigit()
        ):
            target_num = int(chapter_identifier)
            for fname, info in class_map.items():
                if int(info.get("chapter_number", 0)) == target_num:
                    return target_num, str(info.get("chapter", ""))
            raise ChapterNotFoundError(
                f"Chapter number {target_num} not found in Class {class_int} NCERT Science."
            )

        # Case 2: String matching
        clean_query = str(chapter_identifier).strip().lower()
        if ":" in clean_query:
            clean_query = clean_query.split(":", 1)[1].strip()
        elif "-" in clean_query:
            clean_query = clean_query.split("-", 1)[1].strip()

        # Exact / Substring search
        for fname, info in class_map.items():
            ch_title = str(info.get("chapter", ""))
            ch_title_lower = ch_title.lower()
            if (
                clean_query == ch_title_lower
                or clean_query in ch_title_lower
                or ch_title_lower in clean_query
            ):
                return int(info.get("chapter_number", 0)), ch_title

        # Keyword match
        words = [w for w in clean_query.split() if len(w) > 3]
        for fname, info in class_map.items():
            ch_title = str(info.get("chapter", ""))
            if any(w in ch_title.lower() for w in words):
                return int(info.get("chapter_number", 0)), ch_title

        raise ChapterNotFoundError(
            f"Could not resolve chapter '{chapter_identifier}' for Class {class_int}."
        )

    def get_next_chapter(self, class_level: int, current_chapter_num: int) -> Tuple[int, str, bool]:
        """
        Finds the next sequential chapter in the NCERT curriculum.
        Returns: (next_chapter_number, next_chapter_title, has_more_chapters)
        """
        chapters = self.get_chapters_for_grade(class_level)
        if not chapters:
            return current_chapter_num, "General Science", False

        for idx, ch in enumerate(chapters):
            if ch.chapter_number == current_chapter_num:
                if idx + 1 < len(chapters):
                    next_ch = chapters[idx + 1]
                    return next_ch.chapter_number, next_ch.chapter_title, True
                else:
                    return ch.chapter_number, ch.chapter_title, False

        return chapters[0].chapter_number, chapters[0].chapter_title, True


# Singleton instance
curriculum_service = CurriculumService()
