#!/usr/bin/env python3
"""
NCERT Quiz Performance Storage Engine (Backward Compatibility Module).
Delegates directly to src.academic_rag.storage, src.academic_rag.quiz, and src.academic_rag.analytics.
"""

import os
import sys
from typing import Any, Dict, List, Optional

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.academic_rag.config import DEFAULT_DB_PATH, STORAGE_DIR
from src.academic_rag.quiz.evaluator import submit_and_grade_quiz
from src.academic_rag.storage.database import init_database
from src.academic_rag.storage.repository import QuizRepository, quiz_repository


def init_db(db_path: str = DEFAULT_DB_PATH) -> None:
    """Initialize the SQLite database with required tables and indexes."""
    init_database(db_path)


def record_quiz_attempt(
    student_id: str,
    quiz_data: Dict[str, Any],
    user_answers: Dict[str, str],
    quiz_id: Optional[str] = None,
    db_path: str = DEFAULT_DB_PATH,
) -> Dict[str, Any]:
    """Records a completed quiz attempt and its individual question responses."""
    repo = quiz_repository if db_path == DEFAULT_DB_PATH else QuizRepository(db_path=db_path)
    return repo.record_attempt(
        student_id=student_id,
        quiz_data=quiz_data,
        user_answers=user_answers,
        quiz_id=quiz_id,
    )


def get_student_history(
    student_id: str,
    class_level: Optional[int] = None,
    include_questions: bool = False,
    db_path: str = DEFAULT_DB_PATH,
) -> List[Dict[str, Any]]:
    """Retrieves the complete chronological quiz history for a student, optionally filtered by class_level."""
    repo = quiz_repository if db_path == DEFAULT_DB_PATH else QuizRepository(db_path=db_path)
    return repo.get_student_history(
        student_id=student_id, class_level=class_level, include_questions=include_questions
    )


def get_student_class_history(
    student_id: str,
    class_level: int,
    include_questions: bool = False,
    db_path: str = DEFAULT_DB_PATH,
) -> List[Dict[str, Any]]:
    """Retrieves chronological quiz history for a student strictly isolated to a specific class."""
    repo = quiz_repository if db_path == DEFAULT_DB_PATH else QuizRepository(db_path=db_path)
    return repo.get_student_class_history(
        student_id=student_id, class_level=class_level, include_questions=include_questions
    )


def get_student_chapter_summary(
    student_id: str,
    class_level: Optional[int] = None,
    db_path: str = DEFAULT_DB_PATH,
) -> Dict[str, List[Dict[str, Any]]]:
    """Groups a student's quiz history by chapter to show progression over time."""
    history = get_student_history(
        student_id, class_level=class_level, include_questions=False, db_path=db_path
    )
    summary: Dict[str, List[Dict[str, Any]]] = {}

    for attempt in history:
        ch = attempt["chapter"]
        if ch not in summary:
            summary[ch] = []

        quiz_idx = len(summary[ch]) + 1
        summary[ch].append(
            {
                "quiz_num": quiz_idx,
                "quiz_id": attempt["quiz_id"],
                "class_level": attempt["class_level"],
                "difficulty": attempt["difficulty"],
                "score": attempt["score"],
                "total_questions": attempt["total_questions"],
                "percentage": attempt["percentage"],
                "timestamp": attempt["timestamp"],
            }
        )

    return summary


def get_student_swat_metrics(
    student_id: str,
    class_level: Optional[int] = None,
    db_path: str = DEFAULT_DB_PATH,
) -> Dict[str, Any]:
    """Calculates aggregated SWAT metrics for a student across all quiz attempts (or for a specific class)."""
    history = get_student_history(
        student_id, class_level=class_level, include_questions=True, db_path=db_path
    )
    if not history:
        return {"total_quizzes": 0, "overall_accuracy": 0.0, "chapters": {}}

    total_attempts = len(history)
    total_q_answered = 0
    total_q_correct = 0
    chapter_stats: Dict[str, Dict[str, Any]] = {}

    for attempt in history:
        ch = attempt["chapter"]
        if ch not in chapter_stats:
            chapter_stats[ch] = {
                "attempts": 0,
                "total_questions": 0,
                "total_correct": 0,
                "latest_percentage": 0.0,
                "percentages": [],
                "difficulties_tested": set(),
            }

        c_stat = chapter_stats[ch]
        c_stat["attempts"] += 1
        c_stat["total_questions"] += attempt["total_questions"]
        c_stat["total_correct"] += attempt["score"]
        c_stat["latest_percentage"] = attempt["percentage"]
        c_stat["percentages"].append(attempt["percentage"])
        c_stat["difficulties_tested"].add(attempt["difficulty"])

        total_q_answered += attempt["total_questions"]
        total_q_correct += attempt["score"]

    for ch, stat in chapter_stats.items():
        stat["accuracy"] = (
            round((stat["total_correct"] / stat["total_questions"] * 100.0), 1)
            if stat["total_questions"] > 0
            else 0.0
        )
        stat["difficulties_tested"] = sorted(list(stat["difficulties_tested"]))

    overall_acc = (
        round((total_q_correct / total_q_answered * 100.0), 1) if total_q_answered > 0 else 0.0
    )

    strengths = [ch for ch, st in chapter_stats.items() if st["accuracy"] >= 75.0]
    weaknesses = [ch for ch, st in chapter_stats.items() if st["accuracy"] < 50.0]
    in_progress = [ch for ch, st in chapter_stats.items() if 50.0 <= st["accuracy"] < 75.0]

    return {
        "student_id": student_id,
        "class_level": class_level,
        "total_quizzes_taken": total_attempts,
        "total_questions_answered": total_q_answered,
        "overall_accuracy": overall_acc,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "in_progress": in_progress,
        "chapters": chapter_stats,
    }


def clear_student_history(student_id: str, db_path: str = DEFAULT_DB_PATH) -> None:
    """Clear all records for a given student."""
    repo = quiz_repository if db_path == DEFAULT_DB_PATH else QuizRepository(db_path=db_path)
    repo.clear_student_data(student_id)


__all__ = [
    "init_db",
    "record_quiz_attempt",
    "get_student_history",
    "get_student_class_history",
    "get_student_chapter_summary",
    "get_student_swat_metrics",
    "clear_student_history",
    "submit_and_grade_quiz",
    "DEFAULT_DB_PATH",
    "STORAGE_DIR",
]

