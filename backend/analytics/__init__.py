"""Analytics package."""

from backend.analytics.action_plan import generate_action_plan
from backend.analytics.swat import (
    calculate_student_swat,
    format_swat_report,
    get_attempted_chapters,
    get_available_chapters,
    get_student_swat,
    get_unattempted_chapters,
)
from backend.analytics.teacher import (
    get_student_status,
    get_teacher_chapter_statistics,
    get_teacher_quiz_history,
    get_teacher_student_overview,
    get_teacher_student_profile,
    get_teacher_swat_summary,
)

__all__ = [
    "get_student_swat",
    "get_available_chapters",
    "get_attempted_chapters",
    "get_unattempted_chapters",
    "generate_action_plan",
    "format_swat_report",
    "calculate_student_swat",
    "get_teacher_student_overview",
    "get_teacher_chapter_statistics",
    "get_teacher_quiz_history",
    "get_teacher_swat_summary",
    "get_student_status",
    "get_teacher_student_profile",
]
