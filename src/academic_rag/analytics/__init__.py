"""Analytics package."""

from src.academic_rag.analytics.swat import (
    get_student_swat,
    get_available_chapters,
    format_swat_report,
    calculate_student_swat,
)
from src.academic_rag.analytics.teacher import (
    get_teacher_student_overview,
    get_teacher_chapter_statistics,
    get_teacher_quiz_history,
    get_teacher_swat_summary,
    get_student_status,
    get_teacher_student_profile,
)

__all__ = [
    "get_student_swat",
    "get_available_chapters",
    "format_swat_report",
    "calculate_student_swat",
    "get_teacher_student_overview",
    "get_teacher_chapter_statistics",
    "get_teacher_quiz_history",
    "get_teacher_swat_summary",
    "get_student_status",
    "get_teacher_student_profile",
]
