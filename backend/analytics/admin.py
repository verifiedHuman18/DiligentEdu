"""Admin Analytics Engine (Class-wide Aggregation)."""

from typing import Any, Dict, List

from backend.analytics.teacher import get_all_students_from_db
from backend.curriculum.service import curriculum_service
from backend.storage.repository import quiz_repository


def get_class_students(class_level: int) -> List[Dict[str, Any]]:
    """Fetches all students belonging to the specific class level."""
    all_students = get_all_students_from_db()
    return [s for s in all_students if s.get("class_level") == class_level]


def get_class_overview(class_level: int) -> Dict[str, Any]:
    """Calculates aggregate metrics across an entire class level efficiently."""
    students = get_class_students(class_level)
    student_ids = {str(s["id"]).strip() for s in students if "id" in s}
    total_students = len(students)

    history = quiz_repository.get_class_history(class_level=class_level, include_questions=False)

    # Filter attempts that belong to students in this class if student roster exists
    if student_ids:
        class_attempts = [att for att in history if str(att.get("student_id", "")).strip() in student_ids]
    else:
        class_attempts = history

    total_quizzes = len(class_attempts)
    total_questions_attempted = sum(att.get("total_questions", 0) for att in class_attempts)
    total_questions_correct = sum(att.get("score", 0) for att in class_attempts)
    sum_percentages = sum(float(att.get("percentage", 0.0)) for att in class_attempts)

    active_student_ids = {str(att.get("student_id", "")).strip() for att in class_attempts if att.get("student_id")}
    active_students = len(active_student_ids.intersection(student_ids)) if student_ids else len(active_student_ids)

    class_average = int(round(sum_percentages / total_quizzes)) if total_quizzes > 0 else 0
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
    """Calculates class-wide performance grouped by chapter in a single efficient query."""
    history = quiz_repository.get_class_history(class_level=class_level, include_questions=False)
    chapters = curriculum_service.get_chapters_for_grade(class_level)

    ch_stats: Dict[str, Dict[str, Any]] = {
        ch.chapter_title: {
            "attempts": 0,
            "correct": 0,
            "total": 0,
            "sum_scores": 0.0,
            "quiz_count": 0,
        }
        for ch in chapters
    }

    for att in history:
        ch = att.get("chapter")
        if not ch:
            continue
        if ch not in ch_stats:
            ch_stats[ch] = {
                "attempts": 0,
                "correct": 0,
                "total": 0,
                "sum_scores": 0.0,
                "quiz_count": 0,
            }

        ch_stats[ch]["attempts"] += 1
        ch_stats[ch]["correct"] += att.get("score", 0)
        ch_stats[ch]["total"] += att.get("total_questions", 0)
        ch_stats[ch]["sum_scores"] += float(att.get("percentage", 0.0))
        ch_stats[ch]["quiz_count"] += 1

    result = []
    for ch_name, stats in ch_stats.items():
        if stats["quiz_count"] > 0:
            avg_score = int(round(stats["sum_scores"] / stats["quiz_count"]))
            accuracy = (
                int(round((stats["correct"] / stats["total"]) * 100))
                if stats["total"] > 0
                else 0
            )
            result.append(
                {
                    "chapter": ch_name,
                    "average": avg_score,
                    "accuracy": accuracy,
                    "quizzes_taken": stats["quiz_count"],
                    "total_questions": stats["total"],
                    "correct": stats["correct"],
                }
            )

    result.sort(key=lambda x: x["average"], reverse=True)
    return result
