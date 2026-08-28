"""Admin Analytics Engine (Class-wide Aggregation)."""

from typing import Any, Dict, List

from backend.analytics.teacher import get_all_students_from_db, get_teacher_student_overview
from backend.curriculum.service import curriculum_service
from backend.storage.repository import quiz_repository


def get_class_students(class_level: int) -> List[Dict[str, Any]]:
    """Fetches all students belonging to the specific class level."""
    all_students = get_all_students_from_db()
    return [s for s in all_students if s["class_level"] == class_level]


def get_class_overview(class_level: int) -> Dict[str, Any]:
    """Calculates aggregate metrics across an entire class level."""
    students = get_class_students(class_level)

    total_students = len(students)
    active_students = 0
    total_quizzes = 0
    total_questions_attempted = 0
    total_questions_correct = 0
    sum_averages = 0

    for student in students:
        overview = get_teacher_student_overview(student["id"], class_level=class_level)
        if overview.get("has_data"):
            active_students += 1
            total_quizzes += overview["total_quizzes"]
            total_questions_attempted += overview["questions_attempted"]
            total_questions_correct += overview["questions_correct"]
            sum_averages += overview["overall_average"]

    class_average = int(round(sum_averages / active_students)) if active_students > 0 else 0
    class_accuracy = (
        int(round((total_questions_correct / total_questions_attempted) * 100))
        if total_questions_attempted > 0
        else 0
    )

    return {
        "class_level": class_level,
        "total_students": total_students,
        "active_students": active_students,
        "class_average": class_average,
        "class_accuracy": class_accuracy,
        "total_quizzes": total_quizzes,
        "total_questions_attempted": total_questions_attempted,
        "total_questions_correct": total_questions_correct,
    }


def get_class_chapter_performance(class_level: int) -> List[Dict[str, Any]]:
    """Calculates class-wide performance grouped by chapter."""
    students = get_class_students(class_level)
    chapters = curriculum_service.get_chapters_for_grade(class_level)

    ch_stats = {
        ch.chapter_title: {
            "attempts": 0,
            "correct": 0,
            "total": 0,
            "sum_scores": 0,
            "quiz_count": 0,
        }
        for ch in chapters
    }

    for student in students:
        history = quiz_repository.get_student_history(
            student["id"], class_level=class_level, include_questions=False
        )
        for att in history:
            ch = att["chapter"]
            if ch in ch_stats:
                ch_stats[ch]["attempts"] += 1
                ch_stats[ch]["correct"] += att["score"]
                ch_stats[ch]["total"] += att["total_questions"]
                ch_stats[ch]["sum_scores"] += att["percentage"]
                ch_stats[ch]["quiz_count"] += 1

    result = []
    for ch_name, stats in ch_stats.items():
        if stats["quiz_count"] > 0:
            avg_score = int(round(stats["sum_scores"] / stats["quiz_count"]))
            accuracy = int(round((stats["correct"] / stats["total"]) * 100))
            result.append(
                {
                    "chapter": ch_name,
                    "average": avg_score,
                    "accuracy": accuracy,
                    "quizzes_taken": stats["quiz_count"],
                }
            )

    result.sort(key=lambda x: x["average"], reverse=True)
    return result
