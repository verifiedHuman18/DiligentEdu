#!/usr/bin/env python3
"""
NCERT Science Adaptive Quiz Engine (Backward Compatibility Module).
Delegates directly to src.academic_rag.quiz.adaptive and src.academic_rag.curriculum.
"""

import os
import sys
import json
from typing import Dict, Any, List, Optional, Union, Tuple

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.academic_rag.config import MAPPING_FILE
from src.academic_rag.curriculum.service import curriculum_service
from src.academic_rag.quiz.adaptive import get_next_quiz_config


def load_ncert_mapping() -> Dict[str, Any]:
    """Load NCERT chapter mapping file."""
    return curriculum_service.get_mapping()


def get_chapter_sequence(class_level: int) -> List[Dict[str, Any]]:
    """Returns ordered list of chapters for a given grade level."""
    return [ch.to_dict() for ch in curriculum_service.get_chapters_for_grade(class_level)]


def resolve_chapter_info(class_level: int, chapter_identifier: Union[str, int]) -> Tuple[int, str]:
    """Resolves chapter name or number into (chapter_number, canonical_chapter_title)."""
    return curriculum_service.resolve_chapter(class_level, chapter_identifier)


def get_next_chapter(class_level: int, current_chapter_num: int) -> Tuple[int, str, bool]:
    """Finds the next sequential chapter in the NCERT curriculum."""
    return curriculum_service.get_next_chapter(class_level, current_chapter_num)


__all__ = [
    "load_ncert_mapping",
    "get_chapter_sequence",
    "resolve_chapter_info",
    "get_next_chapter",
    "get_next_quiz_config",
    "MAPPING_FILE",
]

if __name__ == "__main__":
    print("=== Testing Adaptive Quiz Engine (Shim) ===")
    res1 = {"class_level": 10, "chapter": "Electricity", "percentage": 35, "difficulty": "medium"}
    cfg1 = get_next_quiz_config(res1)
    print("\nScenario 1 (35% on Electricity):")
    print(json.dumps(cfg1, indent=2))
