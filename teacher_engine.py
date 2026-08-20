#!/usr/bin/env python3
"""
NCERT Teacher Analytics & Early-Warning Engine (Backward Compatibility Module).
Delegates directly to src.academic_rag.analytics.teacher.
"""

import os
import sys
from typing import Dict, Any, List, Optional

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.academic_rag.config import STRONG_THRESHOLD, AVERAGE_THRESHOLD, DEFAULT_DB_PATH
from src.academic_rag.analytics.teacher import (
    get_teacher_student_overview,
    get_teacher_chapter_statistics,
    get_teacher_quiz_history,
    get_teacher_swat_summary,
    get_student_status,
    get_teacher_student_profile,
)

__all__ = [
    "get_teacher_student_overview",
    "get_teacher_chapter_statistics",
    "get_teacher_quiz_history",
    "get_teacher_swat_summary",
    "get_student_status",
    "get_teacher_student_profile",
    "STRONG_THRESHOLD",
    "AVERAGE_THRESHOLD",
    "DEFAULT_DB_PATH",
]

if __name__ == "__main__":
    print("Testing Teacher Analytics Engine...")
    import json
    profile = get_teacher_student_profile("student_001")
    print(json.dumps(profile, indent=2))
