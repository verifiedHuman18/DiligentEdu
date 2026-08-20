#!/usr/bin/env python3
"""
NCERT Student SWAT Analysis Engine (Backward Compatibility Module).
Delegates directly to src.academic_rag.analytics.swat.
"""

import os
import sys
from typing import Dict, Any, Optional

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.academic_rag.config import STRONG_THRESHOLD, AVERAGE_THRESHOLD, DEFAULT_DB_PATH
from src.academic_rag.analytics.swat import (
    get_student_swat,
    calculate_student_swat,
    format_swat_report,
)

__all__ = [
    "get_student_swat",
    "calculate_student_swat",
    "format_swat_report",
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
