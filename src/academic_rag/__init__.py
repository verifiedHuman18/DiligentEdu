"""Academic RAG Assistant package."""

__version__ = "0.1.0"

from src.academic_rag.analytics.action_plan import generate_action_plan
from src.academic_rag.analytics.swat import (
    format_swat_report,
    get_attempted_chapters,
    get_available_chapters,
    get_student_swat,
    get_unattempted_chapters,
)
from src.academic_rag.analytics.teacher import (
    get_student_status,
    get_teacher_chapter_statistics,
    get_teacher_quiz_history,
    get_teacher_student_overview,
    get_teacher_student_profile,
)
from src.academic_rag.config import config
from src.academic_rag.curriculum.service import (
    curriculum_service,
    get_chapter_pdf,
    get_ncert_curriculum,
)
from src.academic_rag.quiz.adaptive import get_next_quiz_config
from src.academic_rag.quiz.evaluator import submit_and_grade_quiz
from src.academic_rag.quiz.generator import (
    create_student_quiz,
    generate_quiz,
)
from src.academic_rag.rag.engine import stream_ncert_rag_response
from src.academic_rag.rag.retriever import retrieve_ncert_context
from src.academic_rag.storage.repository import (
    get_student_class_history,
    quiz_repository,
)

# Aliases for unified contracts
get_student_action_plan = generate_action_plan
get_chapters_with_status = get_available_chapters

__all__ = [
    "config",
    "curriculum_service",
    "get_ncert_curriculum",
    "get_chapter_pdf",
    "quiz_repository",
    "get_student_class_history",
    "retrieve_ncert_context",
    "stream_ncert_rag_response",
    "generate_quiz",
    "create_student_quiz",
    "submit_and_grade_quiz",
    "get_next_quiz_config",
    "get_student_swat",
    "get_student_action_plan",
    "get_chapters_with_status",
    "get_available_chapters",
    "get_attempted_chapters",
    "get_unattempted_chapters",
    "generate_action_plan",
    "format_swat_report",
    "get_teacher_student_overview",
    "get_teacher_swat",
    "get_teacher_action_plan",
    "get_teacher_chapter_statistics",
    "get_teacher_quiz_history",
    "get_student_status",
    "get_teacher_student_profile",
]



