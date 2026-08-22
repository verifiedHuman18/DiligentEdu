#!/usr/bin/env python3
"""
NCERT Academic Assistant — Unified Backend / Data Layer Facade.
Single source of truth facade for all UI, client, and test interactions.
Completely abstracts internal SQLite databases, Pinecone vector stores, and Gemini LLM calls.
"""

import logging
import os
import sys
from typing import Any, Dict, List, Optional, Union

# Reconfigure stdout for UTF-8
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.academic_rag.analytics.action_plan import (
    generate_action_plan as _internal_generate_action_plan,
)
from src.academic_rag.analytics.swat import (
    format_swat_report,
)
from src.academic_rag.analytics.swat import (
    get_attempted_chapters as _internal_get_attempted_chapters,
)
from src.academic_rag.analytics.swat import (
    get_available_chapters as _internal_get_available_chapters,
)
from src.academic_rag.analytics.swat import (
    get_student_swat as _internal_get_student_swat,
)
from src.academic_rag.analytics.swat import (
    get_unattempted_chapters as _internal_get_unattempted_chapters,
)
from src.academic_rag.analytics.teacher import (
    get_student_status as _internal_get_student_status,
)
from src.academic_rag.analytics.teacher import (
    get_teacher_chapter_statistics as _internal_get_student_chapter_stats,
)
from src.academic_rag.analytics.teacher import (
    get_teacher_quiz_history as _internal_get_teacher_quiz_history,
)
from src.academic_rag.analytics.teacher import (
    get_teacher_student_overview as _internal_get_student_overview,
)
from src.academic_rag.analytics.teacher import (
    get_teacher_student_profile as _internal_get_teacher_student_profile,
)
from src.academic_rag.config import DEFAULT_DB_PATH
from src.academic_rag.curriculum.service import (
    curriculum_service,
    get_chapter_pdf,
    get_ncert_curriculum,
)
from src.academic_rag.quiz.evaluator import submit_and_grade_quiz
from src.academic_rag.quiz.generator import create_student_quiz
from src.academic_rag.storage.repository import quiz_repository

logger = logging.getLogger(__name__)


# =====================================================================
# 🎓 STUDENT SIDE BACKEND API CONTRACTS (Phase 21)
# =====================================================================


def get_student_swat(
    student_id: str,
    class_level: Optional[int] = None,
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Retrieves the complete, descriptive SWAT performance profile for a student.

    Args:
        student_id: Unique student ID (e.g. "student_001")
        class_level: Optional grade level (9 or 10) to isolate metrics
        db_path: Optional custom DB path

    Returns:
        Structured Dict with overall KPIs, strong (≥70%), average (50-69%),
        weak (<50%), unattempted chapters, and chronological performance trend.
    """
    if not student_id or not str(student_id).strip():
        raise ValueError("student_id cannot be empty.")
    return _internal_get_student_swat(
        str(student_id).strip(), class_level=class_level, db_path=db_path
    )


def get_student_action_plan(
    student_id: str,
    class_level: Optional[int] = None,
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Generates a prioritized, explainable, and actionable study recommendation plan for a student.

    Args:
        student_id: Unique student ID
        class_level: Optional grade level (9 or 10)
        db_path: Optional custom DB path

    Returns:
        Dict with overall urgency priority and ordered actionable recommendations.
    """
    if not student_id or not str(student_id).strip():
        raise ValueError("student_id cannot be empty.")
    return _internal_generate_action_plan(
        str(student_id).strip(), class_level=class_level, db_path=db_path
    )


def get_chapters_with_status(
    student_id: Optional[Union[str, int]] = None,
    class_level: Optional[Union[str, int]] = None,
    db_path: Optional[str] = None,
    **kwargs: Any,
) -> List[Dict[str, Any]]:
    """
    Retrieves the complete list of NCERT chapters for a grade, annotated with student mastery status.

    Accepts either:
      - (student_id: str, class_level: int)
      - (class_level: int, student_id: Optional[str])
      - Keyword args: get_chapters_with_status(student_id="...", class_level=10)

    Returns:
        List of chapter dicts with chapter_number, chapter, status, score, attempts.
    """
    if isinstance(student_id, int) and (class_level is None or isinstance(class_level, str)):
        cls = student_id
        sid = str(class_level) if isinstance(class_level, str) else kwargs.get("student_id")
    else:
        sid = str(student_id) if student_id is not None else kwargs.get("student_id")
        cls = int(class_level) if class_level is not None else kwargs.get("class_level", 10)

    return _internal_get_available_chapters(class_level=cls, student_id=sid, db_path=db_path)


def generate_quiz(
    student_id: str,
    class_level: int,
    chapter: Union[str, int],
    difficulty: str = "medium",
    num_questions: int = 5,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    model_name: Optional[str] = None,
    **kwargs: Any,
) -> Dict[str, Any]:
    """
    Generates a structured, curriculum-grounded MCQ practice quiz in ONE single Gemini API request.

    Args:
        student_id: Student ID requesting the quiz
        class_level: Grade level (9 or 10)
        chapter: Canonical chapter name string or chapter number int
        difficulty: 'easy', 'medium', or 'hard'
        num_questions: Number of questions to generate (default: 5)
        api_key: Optional Gemini API key
        model: Model identifier (default: "gemini-3.5-flash-lite")

    Returns:
        Structured Quiz dictionary with questions, 4 options, answer key, and NCERT citations.
    """
    return create_student_quiz(
        student_id=student_id,
        class_level=class_level,
        chapter=chapter,
        difficulty=difficulty,
        num_questions=num_questions,
        api_key=api_key,
        model=model or model_name,
        **kwargs,
    )


def submit_quiz(
    student_id: str,
    quiz_id: Optional[str] = None,
    answers: Optional[Dict[str, str]] = None,
    quiz_data: Optional[Dict[str, Any]] = None,
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Processes a completed quiz attempt:
    1. Evaluates answers locally with 0 LLM calls.
    2. Persists attempt and question responses in SQLite.
    3. Automatically re-computes the student's SWAT profile.
    4. Returns score, percentage, previous chapter average, new chapter average, and SWAT status delta.

    Args:
        student_id: Student ID submitting the quiz
        quiz_id: Unique quiz attempt ID
        answers: Dict of student choices (e.g. {"q_choice_1": "B", ...})
        quiz_data: The quiz dictionary that was generated
        db_path: Optional custom DB path

    Returns:
        Structured evaluation result with score, feedback, and SWAT transition diff.
    """
    if not quiz_data:
        raise ValueError("quiz_data is required for grading and recording the quiz attempt.")
    if answers is None:
        answers = {}

    return submit_and_grade_quiz(
        student_id=student_id,
        quiz_data=quiz_data,
        user_answers=answers,
        quiz_id=quiz_id,
        db_path=db_path or DEFAULT_DB_PATH,
    )


def get_student_quiz_history(
    student_id: str,
    class_level: Optional[int] = None,
    include_questions: bool = True,
    db_path: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Retrieves chronological attempt history for a student, optionally isolated by class level.
    """
    if not student_id or not str(student_id).strip():
        raise ValueError("student_id cannot be empty.")
    repo = quiz_repository if db_path is None else type(quiz_repository)(db_path=db_path)
    return repo.get_student_history(
        student_id=str(student_id).strip(),
        class_level=class_level,
        include_questions=include_questions,
    )


def get_student_class_history(
    student_id: str,
    class_level: int,
    include_questions: bool = False,
    db_path: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Retrieves chronological attempt history for a student strictly isolated to a specific class.
    """
    if not student_id or not str(student_id).strip():
        raise ValueError("student_id cannot be empty.")
    repo = quiz_repository if db_path is None else type(quiz_repository)(db_path=db_path)
    return repo.get_student_class_history(
        student_id=str(student_id).strip(),
        class_level=class_level,
        include_questions=include_questions,
    )


def get_attempted_chapters(
    student_id: str,
    class_level: int,
    db_path: Optional[str] = None,
) -> List[str]:
    """Retrieves list of attempted chapter names for a student in a specific class."""
    if not student_id or not str(student_id).strip():
        raise ValueError("student_id cannot be empty.")
    return _internal_get_attempted_chapters(
        str(student_id).strip(), class_level=class_level, db_path=db_path
    )


def get_unattempted_chapters(
    student_id: str,
    class_level: int,
    db_path: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Retrieves list of unattempted chapter dicts with score=None for a student in a specific class."""
    if not student_id or not str(student_id).strip():
        raise ValueError("student_id cannot be empty.")
    return _internal_get_unattempted_chapters(
        str(student_id).strip(), class_level=class_level, db_path=db_path
    )


# =====================================================================
# 👨‍🏫 TEACHER SIDE BACKEND API CONTRACTS (Phase 21)
# =====================================================================


def get_teacher_student_overview(
    student_id: str,
    class_level: Optional[int] = None,
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Retrieves overall student statistics and KPIs for Teacher View."""
    if not student_id or not str(student_id).strip():
        raise ValueError("student_id cannot be empty.")
    return _internal_get_student_overview(
        str(student_id).strip(), class_level=class_level, db_path=db_path
    )


def get_teacher_swat(
    student_id: str,
    class_level: Optional[int] = None,
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Retrieves SWAT summary for Teacher View powered by the SAME shared SWAT engine
    without duplicating calculations.
    """
    if not student_id or not str(student_id).strip():
        raise ValueError("student_id cannot be empty.")
    return _internal_get_student_swat(
        str(student_id).strip(), class_level=class_level, db_path=db_path
    )


def get_teacher_action_plan(
    student_id: str,
    class_level: Optional[int] = None,
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Retrieves prioritized action plan with supporting diagnostic statistics for Teacher View.
    """
    if not student_id or not str(student_id).strip():
        raise ValueError("student_id cannot be empty.")
    return _internal_generate_action_plan(
        str(student_id).strip(), class_level=class_level, db_path=db_path
    )


def get_teacher_quiz_history(
    student_id: str,
    class_level: Optional[int] = None,
    db_path: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Retrieves class-scoped chronological quiz history for Teacher View."""
    if not student_id or not str(student_id).strip():
        raise ValueError("student_id cannot be empty.")
    return _internal_get_teacher_quiz_history(
        str(student_id).strip(), class_level=class_level, db_path=db_path
    )


def get_student_chapter_stats(
    student_id: str,
    class_level: Optional[int] = None,
    db_path: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Chapter Statistics for Teacher View."""
    if not student_id or not str(student_id).strip():
        raise ValueError("student_id cannot be empty.")
    return _internal_get_student_chapter_stats(
        str(student_id).strip(), class_level=class_level, db_path=db_path
    )


def get_student_status(
    student_id: str,
    class_level: Optional[int] = None,
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Early-Warning Status Engine for Teacher View."""
    if not student_id or not str(student_id).strip():
        raise ValueError("student_id cannot be empty.")
    return _internal_get_student_status(
        str(student_id).strip(), class_level=class_level, db_path=db_path
    )


def get_teacher_student_profile(
    student_id: str,
    class_level: Optional[int] = None,
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Unified Teacher Master Profile."""
    if not student_id or not str(student_id).strip():
        raise ValueError("student_id cannot be empty.")
    return _internal_get_teacher_student_profile(
        str(student_id).strip(), class_level=class_level, db_path=db_path
    )


def clear_student_data(
    student_id: str,
    db_path: Optional[str] = None,
) -> None:
    """Clears all quiz records and question responses for a given student ID."""
    if not student_id or not str(student_id).strip():
        raise ValueError("student_id cannot be empty.")
    repo = quiz_repository if db_path is None else type(quiz_repository)(db_path=db_path)
    repo.clear_student_data(str(student_id).strip())


# Backward compatibility aliases
generate_student_quiz = generate_quiz
generate_action_plan = get_student_action_plan
get_available_chapters = get_chapters_with_status
get_student_overview = get_teacher_student_overview

# Exported Public API
__all__ = [
    # Phase 21 Student Contracts
    "get_student_swat",
    "get_student_action_plan",
    "get_chapters_with_status",
    "generate_quiz",
    "submit_quiz",
    # Phase 21 Teacher Contracts
    "get_teacher_student_overview",
    "get_teacher_swat",
    "get_teacher_action_plan",
    "get_teacher_quiz_history",
    # Additional Facades & Helpers
    "get_student_quiz_history",
    "get_student_class_history",
    "get_attempted_chapters",
    "get_unattempted_chapters",
    "get_student_chapter_stats",
    "get_student_status",
    "get_teacher_student_profile",
    "generate_student_quiz",
    "generate_action_plan",
    "get_available_chapters",
    "get_student_overview",
    "clear_student_data",
    "format_swat_report",
    "curriculum_service",
    "get_ncert_curriculum",
    "get_chapter_pdf",
]
