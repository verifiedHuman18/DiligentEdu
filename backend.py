#!/usr/bin/env python3
"""
NCERT Academic Assistant — Unified Backend / Data Layer (Phase 15)
Single source of truth facade for all UI and client interactions.
Completely abstracts internal SQLite databases, Pinecone vector stores, and Gemini LLM calls.
"""

import os
import sys
import logging
from typing import Dict, Any, List, Optional, Union

# Reconfigure stdout for UTF-8
sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Internal engine imports
from swat_analyzer import (
    get_student_swat as _internal_get_student_swat,
    format_swat_report,
    STRONG_THRESHOLD,
    AVERAGE_THRESHOLD,
)
from quiz_generator import (
    get_available_chapters as _internal_get_available_chapters,
    create_student_quiz as _internal_create_student_quiz,
    resolve_chapter,
    load_ncert_mapping,
)
from quiz_storage import (
    submit_and_grade_quiz as _internal_submit_and_grade_quiz,
    get_student_history as _internal_get_student_history,
    clear_student_history as _internal_clear_student_history,
    get_student_chapter_summary as _internal_get_student_chapter_summary,
    DEFAULT_DB_PATH,
)
from teacher_engine import (
    get_teacher_student_overview as _internal_get_student_overview,
    get_teacher_chapter_statistics as _internal_get_student_chapter_stats,
    get_teacher_quiz_history as _internal_get_teacher_quiz_history,
    get_student_status as _internal_get_student_status,
    get_teacher_student_profile as _internal_get_teacher_student_profile,
)

logger = logging.getLogger(__name__)


# =====================================================================
# 🎓 STUDENT SIDE BACKEND API
# =====================================================================

def get_student_swat(student_id: str, db_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Retrieves the complete, descriptive SWAT performance profile for a student.

    Args:
        student_id: Unique student ID (e.g. "student_001")

    Returns:
        Structured Dict with overall KPIs, strengths (≥70%), average_topics (50-69%),
        weak_topics (<50%), and chronological performance trend.
    """
    if not student_id or not str(student_id).strip():
        raise ValueError("student_id cannot be empty.")
    return _internal_get_student_swat(str(student_id).strip(), db_path=db_path)


def get_available_chapters(
    class_level: int,
    student_id: Optional[str] = None,
    db_path: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Retrieves the list of NCERT chapters for the given grade, annotated with student's current SWAT status.

    Args:
        class_level: Grade level (9 or 10)
        student_id: Optional student ID to overlay SWAT status

    Returns:
        List of chapter objects with chapter_number, chapter, status, score, attempts.
    """
    return _internal_get_available_chapters(class_level=class_level, student_id=student_id, db_path=db_path)


def generate_student_quiz(
    student_id: str,
    class_level: int,
    chapter: Union[str, int],
    difficulty: str = "medium",
    num_questions: int = 5,
    api_key: Optional[str] = None,
    model: str = "gemini-3.5-flash-lite",
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
        Structured Quiz dictionary with questions, 4 options, correct answer key, and NCERT page citations.
    """
    return _internal_create_student_quiz(
        student_id=student_id,
        class_level=class_level,
        chapter=chapter,
        difficulty=difficulty,
        num_questions=num_questions,
        api_key=api_key,
        model=model,
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

    return _internal_submit_and_grade_quiz(
        student_id=student_id,
        quiz_data=quiz_data,
        user_answers=answers,
        quiz_id=quiz_id,
        db_path=db_path or DEFAULT_DB_PATH,
    )


def get_student_quiz_history(
    student_id: str,
    include_questions: bool = True,
    db_path: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Retrieves chronological attempt history for a student.

    Args:
        student_id: Student ID
        include_questions: Whether to include individual question records

    Returns:
        List of chronological quiz attempt dictionaries.
    """
    if not student_id or not str(student_id).strip():
        raise ValueError("student_id cannot be empty.")
    return _internal_get_student_history(
        student_id=str(student_id).strip(),
        include_questions=include_questions,
        db_path=db_path or DEFAULT_DB_PATH,
    )


# =====================================================================
# 👨‍🏫 TEACHER SIDE BACKEND API
# =====================================================================

def get_student_overview(
    student_id: str,
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    13.1 Overall Student Statistics for Teacher View.
    Returns high-level lifetime performance KPIs.
    """
    if not student_id or not str(student_id).strip():
        raise ValueError("student_id cannot be empty.")
    return _internal_get_student_overview(str(student_id).strip(), db_path=db_path)


def get_student_chapter_stats(
    student_id: str,
    db_path: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    13.2 Chapter Statistics for Teacher View.
    Returns per-chapter metrics (average score, attempts, questions attempted, accuracy, SWAT status).
    """
    if not student_id or not str(student_id).strip():
        raise ValueError("student_id cannot be empty.")
    return _internal_get_student_chapter_stats(str(student_id).strip(), db_path=db_path)


def get_student_status(
    student_id: str,
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    14.1–14.4 Early-Warning Status Engine for Teacher View.
    Evaluates transparent pedagogical rules to diagnose student standing:
    - Overall Standing (Performing Well 🟢, Monitor 🟡, Needs Attention 🔴)
    - Weak-Topic Alerts (< 50%)
    - Trend Diagnosis (Declining warning vs. Improving recognition)
    """
    if not student_id or not str(student_id).strip():
        raise ValueError("student_id cannot be empty.")
    return _internal_get_student_status(str(student_id).strip(), db_path=db_path)


def get_teacher_student_profile(
    student_id: str,
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Unified Teacher Master Profile.
    Combines overview, chapter statistics, chronological history, SWAT summary, and early warnings.
    """
    if not student_id or not str(student_id).strip():
        raise ValueError("student_id cannot be empty.")
    return _internal_get_teacher_student_profile(str(student_id).strip(), db_path=db_path)


def clear_student_data(
    student_id: str,
    db_path: Optional[str] = None,
) -> None:
    """
    Clears all quiz records and question responses for a given student ID.
    """
    if not student_id or not str(student_id).strip():
        raise ValueError("student_id cannot be empty.")
    _internal_clear_student_history(str(student_id).strip(), db_path=db_path or DEFAULT_DB_PATH)


# Exported Public API
__all__ = [
    # Student Side
    "get_student_swat",
    "get_available_chapters",
    "generate_student_quiz",
    "submit_quiz",
    "get_student_quiz_history",
    # Teacher Side
    "get_student_overview",
    "get_student_chapter_stats",
    "get_student_status",
    "get_teacher_student_profile",
    # Utilities
    "clear_student_data",
    "format_swat_report",
]
