#!/usr/bin/env python3
"""
NCERT Student SWAT Analysis Engine (Backward Compatibility Module).
Delegates directly to src.academic_rag.analytics.swat.
"""

import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.academic_rag.analytics.swat import (
    calculate_student_swat,
    format_swat_report,
    get_attempted_chapters,
    get_student_swat,
    get_unattempted_chapters,
)
from src.academic_rag.config import AVERAGE_THRESHOLD, DEFAULT_DB_PATH, STRONG_THRESHOLD

__all__ = [
    "get_student_swat",
    "calculate_student_swat",
    "format_swat_report",
    "get_attempted_chapters",
    "get_unattempted_chapters",
    "STRONG_THRESHOLD",
    "AVERAGE_THRESHOLD",
    "DEFAULT_DB_PATH",
]

if __name__ == "__main__":
    print("Testing get_student_swat function...")
    res = get_student_swat("student_001")
    import json

    print(json.dumps(res, indent=2))
    print("\n" + format_swat_report(res))
