"""Academic RAG Assistant package."""

__version__ = "0.1.0"

from src.academic_rag.analytics.swat import (
    format_swat_report,
    get_available_chapters,
    get_student_swat,
)
from src.academic_rag.analytics.teacher import (
    get_student_status,
    get_teacher_chapter_statistics,
    get_teacher_quiz_history,
    get_teacher_student_overview,
    get_teacher_student_profile,
)
from src.academic_rag.config import config
from src.academic_rag.curriculum.service import curriculum_service
from src.academic_rag.quiz.adaptive import get_next_quiz_config
from src.academic_rag.quiz.evaluator import submit_and_grade_quiz
from src.academic_rag.quiz.generator import (
    create_student_quiz,
    generate_quiz,
)
from src.academic_rag.rag.engine import stream_ncert_rag_response
from src.academic_rag.rag.retriever import retrieve_ncert_context
from src.academic_rag.storage.repository import quiz_repository

__all__ = [
    "config",
    "curriculum_service",
    "quiz_repository",
    "retrieve_ncert_context",
    "stream_ncert_rag_response",
    "generate_quiz",
    "create_student_quiz",
    "submit_and_grade_quiz",
    "get_next_quiz_config",
    "get_student_swat",
    "get_available_chapters",
    "format_swat_report",
    "get_teacher_student_overview",
    "get_teacher_chapter_statistics",
    "get_teacher_quiz_history",
    "get_student_status",
    "get_teacher_student_profile",
]
