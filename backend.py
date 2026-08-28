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

from src.academic_rag.ai import (
    get_active_api_mode,
    get_api_status,
    get_primary_api_key,
    get_user_fallback_api_key,
    has_primary_api_key,
    has_user_fallback_api_key,
    remove_user_fallback_api_key,
    set_user_fallback_api_key,
    test_gemini_api_key,
)
from src.academic_rag.analytics.action_plan import (
    generate_action_plan as _internal_generate_action_plan,
)
from src.academic_rag.analytics.action_plan import (
    reset_teacher_action_plan as _internal_reset_teacher_action_plan,
)
from src.academic_rag.analytics.action_plan import (
    save_teacher_action_plan as _internal_save_teacher_action_plan,
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
# STUDENT SIDE BACKEND API CONTRACTS (Phase 21)
# =====================================================================


def get_student_swat(
    student_id: str,
    class_level: Optional[int] = None,
    subject: str = "Science",
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Retrieves the complete, descriptive SWAT performance profile for a student in a specific subject.

    Args:
        student_id: Unique student ID (e.g. "student_001")
        class_level: Optional grade level (9 or 10) to isolate metrics
        subject: Subject name ("Science" or "Mathematics")
        db_path: Optional custom DB path

    Returns:
        Structured Dict with overall KPIs, strong (≥70%), average (50-69%),
        weak (<50%), unattempted chapters, and chronological performance trend.
    """
    if not student_id or not str(student_id).strip():
        raise ValueError("student_id cannot be empty.")
    return _internal_get_student_swat(
        str(student_id).strip(), class_level=class_level, subject=subject, db_path=db_path
    )


def get_student_action_plan(
    student_id: str,
    class_level: Optional[int] = None,
    subject: str = "Science",
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Generates a prioritized, explainable, and actionable study recommendation plan for a student in a specific subject.

    Args:
        student_id: Unique student ID
        class_level: Optional grade level (9 or 10)
        subject: Subject name ("Science" or "Mathematics")
        db_path: Optional custom DB path

    Returns:
        Dict with overall urgency priority and ordered actionable recommendations.
    """
    if not student_id or not str(student_id).strip():
        raise ValueError("student_id cannot be empty.")
    return _internal_generate_action_plan(
        str(student_id).strip(), class_level=class_level, subject=subject, db_path=db_path
    )


def get_chapters_with_status(
    student_id: Optional[Union[str, int]] = None,
    class_level: Optional[Union[str, int]] = None,
    subject: str = "Science",
    db_path: Optional[str] = None,
    **kwargs: Any,
) -> List[Dict[str, Any]]:
    """
    Retrieves the complete list of NCERT chapters for a grade and subject, annotated with student mastery status.

    Accepts either:
      - (student_id: str, class_level: int)
      - (class_level: int, student_id: Optional[str])
      - Keyword args: get_chapters_with_status(student_id="...", class_level=10, subject="Mathematics")

    Returns:
        List of chapter dicts with chapter_number, chapter, status, score, attempts.
    """
    if isinstance(student_id, int) and (class_level is None or isinstance(class_level, str)):
        cls = student_id
        sid = str(class_level) if isinstance(class_level, str) else kwargs.get("student_id")
    else:
        sid = str(student_id) if student_id is not None else kwargs.get("student_id")
        cls = int(class_level) if class_level is not None else kwargs.get("class_level", 10)

    target_subj = kwargs.get("subject", subject)
    return _internal_get_available_chapters(class_level=cls, student_id=sid, subject=target_subj, db_path=db_path)


def generate_quiz(
    student_id: str,
    class_level: int,
    chapter: Union[str, int],
    difficulty: str = "medium",
    num_questions: int = 5,
    subject: str = "Science",
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
        subject: 'Science' or 'Mathematics'
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
        subject=subject,
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
    subject: Optional[str] = None,
    include_questions: bool = True,
    db_path: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Retrieves chronological attempt history for a student, optionally isolated by class level and subject.
    """
    if not student_id or not str(student_id).strip():
        raise ValueError("student_id cannot be empty.")
    repo = quiz_repository if db_path is None else type(quiz_repository)(db_path=db_path)
    return repo.get_student_history(
        student_id=str(student_id).strip(),
        class_level=class_level,
        subject=subject,
        include_questions=include_questions,
    )


def get_student_class_history(
    student_id: str,
    class_level: int,
    subject: Optional[str] = None,
    include_questions: bool = False,
    db_path: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Retrieves chronological attempt history for a student strictly isolated to a specific class and subject.
    """
    if not student_id or not str(student_id).strip():
        raise ValueError("student_id cannot be empty.")
    repo = quiz_repository if db_path is None else type(quiz_repository)(db_path=db_path)
    return repo.get_student_class_history(
        student_id=str(student_id).strip(),
        class_level=class_level,
        subject=subject,
        include_questions=include_questions,
    )


def get_attempted_chapters(
    student_id: str,
    class_level: int,
    subject: str = "Science",
    db_path: Optional[str] = None,
) -> List[str]:
    """Retrieves list of attempted chapter names for a student in a specific class and subject."""
    if not student_id or not str(student_id).strip():
        raise ValueError("student_id cannot be empty.")
    return _internal_get_attempted_chapters(
        str(student_id).strip(), class_level=class_level, subject=subject, db_path=db_path
    )


def get_unattempted_chapters(
    student_id: str,
    class_level: int,
    subject: str = "Science",
    db_path: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Retrieves list of unattempted chapter dicts with score=None for a student in a specific class and subject."""
    if not student_id or not str(student_id).strip():
        raise ValueError("student_id cannot be empty.")
    return _internal_get_unattempted_chapters(
        str(student_id).strip(), class_level=class_level, subject=subject, db_path=db_path
    )


# =====================================================================
# TEACHER SIDE BACKEND API CONTRACTS (Phase 21)
# =====================================================================


def get_teacher_student_overview(
    student_id: str,
    class_level: Optional[int] = None,
    subject: str = "Science",
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Retrieves overall student statistics and KPIs for Teacher View."""
    if not student_id or not str(student_id).strip():
        raise ValueError("student_id cannot be empty.")
    return _internal_get_student_overview(
        str(student_id).strip(), class_level=class_level, subject=subject, db_path=db_path
    )


def get_teacher_swat(
    student_id: str,
    class_level: Optional[int] = None,
    subject: str = "Science",
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Retrieves SWAT summary for Teacher View powered by the SAME shared SWAT engine
    without duplicating calculations.
    """
    if not student_id or not str(student_id).strip():
        raise ValueError("student_id cannot be empty.")
    return _internal_get_student_swat(
        str(student_id).strip(), class_level=class_level, subject=subject, db_path=db_path
    )


def get_teacher_action_plan(
    student_id: str,
    class_level: Optional[int] = None,
    subject: str = "Science",
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Retrieves prioritized action plan with supporting diagnostic statistics for Teacher View.
    """
    if not student_id or not str(student_id).strip():
        raise ValueError("student_id cannot be empty.")
    return _internal_generate_action_plan(
        str(student_id).strip(), class_level=class_level, subject=subject, db_path=db_path
    )


def save_teacher_action_plan(
    student_id: str,
    class_level: int,
    actions: List[Dict[str, Any]],
    teacher_notes: Optional[str] = None,
    subject: str = "Science",
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Saves or updates customized action plan for a student assigned by a teacher.
    """
    if not student_id or not str(student_id).strip():
        raise ValueError("student_id cannot be empty.")
    return _internal_save_teacher_action_plan(
        str(student_id).strip(),
        class_level=class_level,
        actions=actions,
        teacher_notes=teacher_notes,
        subject=subject,
        db_path=db_path,
    )


def reset_teacher_action_plan(
    student_id: str,
    class_level: int,
    subject: str = "Science",
    db_path: Optional[str] = None,
) -> bool:
    """
    Resets a student's action plan back to standard algorithmic SWAT recommendations.
    """
    if not student_id or not str(student_id).strip():
        raise ValueError("student_id cannot be empty.")
    return _internal_reset_teacher_action_plan(
        str(student_id).strip(), class_level=class_level, subject=subject, db_path=db_path
    )


def get_teacher_quiz_history(
    student_id: str,
    class_level: Optional[int] = None,
    subject: str = "Science",
    limit: int = 10,
    db_path: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Retrieves class-scoped chronological quiz history for Teacher View."""
    if not student_id or not str(student_id).strip():
        raise ValueError("student_id cannot be empty.")
    return _internal_get_teacher_quiz_history(
        str(student_id).strip(), class_level=class_level, subject=subject, limit=limit, db_path=db_path
    )


def get_student_chapter_stats(
    student_id: str,
    class_level: Optional[int] = None,
    subject: str = "Science",
    db_path: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Chapter Statistics for Teacher View."""
    if not student_id or not str(student_id).strip():
        raise ValueError("student_id cannot be empty.")
    return _internal_get_student_chapter_stats(
        str(student_id).strip(), class_level=class_level, subject=subject, db_path=db_path
    )


def get_student_status(
    student_id: str,
    class_level: Optional[int] = None,
    subject: str = "Science",
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Early-Warning Status Engine for Teacher View."""
    if not student_id or not str(student_id).strip():
        raise ValueError("student_id cannot be empty.")
    return _internal_get_student_status(
        str(student_id).strip(), class_level=class_level, subject=subject, db_path=db_path
    )


def get_teacher_student_profile(
    student_id: str,
    class_level: Optional[int] = None,
    subject: str = "Science",
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Unified Teacher Master Profile."""
    if not student_id or not str(student_id).strip():
        raise ValueError("student_id cannot be empty.")
    return _internal_get_teacher_student_profile(
        str(student_id).strip(), class_level=class_level, subject=subject, db_path=db_path
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


# =====================================================================
# STUDENT STUDY MATERIAL CONTRACTS (Phases 1-23)
# =====================================================================


def upload_study_material(
    student_id: str,
    file_data: Any,
    filename: str,
    material_name: Optional[str] = None,
    class_level: int = 10,
    subject: str = "Science",
    chapter: Optional[str] = None,
    pinecone_api_key: Optional[str] = None,
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Ingests and registers an uploaded PDF study material for a student.
    Validates, extracts text, generates 384-dim local MiniLM embeddings (0 Gemini calls),
    and indexes into student-isolated vector storage.
    """
    from src.academic_rag.ingestion.pdf_ingester import ingest_study_material_pdf

    return ingest_study_material_pdf(
        student_id=student_id,
        file_data=file_data,
        filename=filename,
        material_name=material_name,
        class_level=class_level,
        subject=subject,
        chapter=chapter,
        pinecone_api_key=pinecone_api_key,
        db_path=db_path,
    )


def get_student_study_materials(
    student_id: str,
    class_level: Optional[int] = None,
    chapter: Optional[str] = None,
    subject: Optional[str] = None,
    db_path: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Retrieves the list of uploaded study materials for a student.
    """
    from src.academic_rag.storage.repository import study_material_repository

    repo = study_material_repository if db_path is None else type(study_material_repository)(db_path=db_path)
    return repo.get_student_documents(
        student_id=student_id, class_level=class_level, chapter=chapter, subject=subject
    )


def delete_study_material(
    document_id: str,
    student_id: Optional[str] = None,
    api_key: Optional[str] = None,
    db_path: Optional[str] = None,
) -> bool:
    """
    Completely deletes an uploaded study material:
    Removes SQLite database metadata record + deletes Pinecone vector embeddings.
    """
    from src.academic_rag.rag.retriever import delete_student_material_vectors
    from src.academic_rag.storage.repository import study_material_repository

    repo = study_material_repository if db_path is None else type(study_material_repository)(db_path=db_path)
    # 1. Delete vectors from Pinecone
    delete_student_material_vectors(document_id=document_id, student_id=student_id, api_key=api_key)
    # 2. Delete database record
    return repo.delete_document_record(document_id=document_id, student_id=student_id)


def validate_study_material_file(
    file_data: Any,
    filename: str,
) -> Dict[str, Any]:
    """
    Validates PDF file type, size, readability, and scanned PDF detection.
    """
    from src.academic_rag.ingestion.validator import validate_pdf_file

    res = validate_pdf_file(file_data=file_data, filename=filename)
    return {
        "is_valid": res.is_valid,
        "error_message": res.error_message,
        "file_size_bytes": res.file_size_bytes,
        "detected_pages": res.detected_pages,
        "is_scanned_pdf": res.is_scanned_pdf,
    }


# =============================================================================
# Knowledge Graph / Knowledge Map Contracts (Phases 1-31)
# =============================================================================


def get_chapter_knowledge_graph(
    student_id: str,
    class_level: int,
    chapter: str,
    subject: str = "Science",
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Constructs the concept-level knowledge graph for a chapter, subject, and student,
    incorporating mastery calculations, unattempted concept safety, and linked study resources.
    """
    from src.academic_rag.analytics.knowledge_graph import (
        get_chapter_knowledge_graph as _internal_get_chapter_knowledge_graph,
    )

    return _internal_get_chapter_knowledge_graph(
        student_id=student_id,
        class_level=class_level,
        chapter_name=chapter,
        subject=subject,
        db_path=db_path,
    )


def get_available_knowledge_map_chapters(
    class_level: int,
    subject: str = "Science",
) -> List[Dict[str, Any]]:
    """Returns chapters available for concept knowledge mapping in the given class and subject."""
    from src.academic_rag.analytics.knowledge_graph import (
        get_available_knowledge_map_chapters as _internal_get_avail_km_chapters,
    )

    return _internal_get_avail_km_chapters(class_level=class_level, subject=subject)


def calculate_student_concept_telemetry(
    student_id: str,
    class_level: int,
    chapter: Optional[str] = None,
    subject: str = "Science",
    db_path: Optional[str] = None,
) -> Dict[str, Dict[str, Any]]:
    """Calculates granular concept-level performance telemetry for a student in a specific subject."""
    from src.academic_rag.analytics.knowledge_graph import (
        calculate_student_concept_telemetry as _internal_calc_concept_telemetry,
    )

    return _internal_calc_concept_telemetry(
        student_id=student_id,
        class_level=class_level,
        chapter_name=chapter,
        subject=subject,
        db_path=db_path,
    )


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
    # Study Material Contracts (Phases 1-23)
    "upload_study_material",
    "get_student_study_materials",
    "delete_study_material",
    "validate_study_material_file",
    # Phase 21 Teacher Contracts
    "get_teacher_student_overview",
    "get_teacher_swat",
    "get_teacher_action_plan",
    "save_teacher_action_plan",
    "reset_teacher_action_plan",
    "get_teacher_quiz_history",
    # AI Resolution & API Configuration (Phases 2-20)
    "get_primary_api_key",
    "get_user_fallback_api_key",
    "has_primary_api_key",
    "has_user_fallback_api_key",
    "get_active_api_mode",
    "get_api_status",
    "set_user_fallback_api_key",
    "remove_user_fallback_api_key",
    "test_gemini_api_key",
    # Knowledge Graph / Knowledge Map Contracts (Phases 1-31)
    "get_chapter_knowledge_graph",
    "get_available_knowledge_map_chapters",
    "calculate_student_concept_telemetry",
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
