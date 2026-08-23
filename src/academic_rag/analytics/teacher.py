"""Teacher Analytics & Early-Warning Diagnostic Engine (Zero LLM calls)."""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.academic_rag.analytics.swat import get_student_swat
from src.academic_rag.curriculum.service import curriculum_service
from src.academic_rag.storage.repository import quiz_repository

logger = logging.getLogger(__name__)


def _format_date(iso_timestamp: str) -> str:
    """Formats ISO timestamp into short date like 'Aug 19'."""
    try:
        dt = datetime.fromisoformat(iso_timestamp.replace("Z", "+00:00"))
        return dt.strftime("%b %d")
    except Exception:
        return iso_timestamp[:10] if iso_timestamp else "N/A"


def get_teacher_student_overview(
    student_id: str,
    class_level: Optional[int] = None,
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    """13.1 Overall Student Statistics (Class-Isolated)."""
    repo = quiz_repository if db_path is None else type(quiz_repository)(db_path=db_path)
    history = repo.get_student_history(student_id, class_level=class_level, include_questions=False)

    resolved_class = (
        int(class_level)
        if class_level is not None
        else (history[-1].get("class_level", 10) if history else 10)
    )
    total_chapters_count = (
        len(curriculum_service.get_chapters_for_grade(resolved_class))
        if resolved_class in [9, 10]
        else 13
    )

    if not history:
        return {
            "student_id": student_id,
            "has_data": False,
            "class": resolved_class,
            "class_level": resolved_class,
            "overall_average": 0,
            "total_quizzes": 0,
            "questions_attempted": 0,
            "questions_correct": 0,
            "accuracy": 0,
            "attempted_chapters": 0,
            "total_chapters": total_chapters_count,
        }

    total_quizzes = len(history)
    total_questions = sum(att["total_questions"] for att in history)
    total_correct = sum(att["score"] for att in history)
    attempted_chapters_count = len(set(att["chapter"] for att in history))

    overall_avg = (
        int(round(sum(att["percentage"] for att in history) / total_quizzes))
        if total_quizzes > 0
        else 0
    )
    accuracy = (
        int(round((float(total_correct) / float(total_questions)) * 100.0))
        if total_questions > 0
        else 0
    )

    return {
        "student_id": student_id,
        "has_data": True,
        "class": resolved_class,
        "class_level": resolved_class,
        "overall_average": overall_avg,
        "total_quizzes": total_quizzes,
        "questions_attempted": total_questions,
        "questions_correct": total_correct,
        "accuracy": accuracy,
        "attempted_chapters": attempted_chapters_count,
        "total_chapters": total_chapters_count,
    }


def get_teacher_chapter_statistics(
    student_id: str,
    class_level: Optional[int] = None,
    db_path: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """13.2 Chapter Statistics for Teacher View (Class-Isolated)."""
    swat = get_student_swat(student_id, class_level=class_level, db_path=db_path)
    if not swat.get("has_data"):
        return []

    breakdown = swat.get("chapter_breakdown", {})
    chapter_stats = []

    for ch_name, data in breakdown.items():
        if data.get("category") == "unattempted" or data.get("attempts", 0) == 0:
            continue
        acc_val = int(round(data["accuracy"])) if data.get("accuracy") is not None else 0
        chapter_stats.append(
            {
                "chapter": ch_name,
                "average": data["score"],
                "attempts": data["attempts"],
                "questions_attempted": data["questions"],
                "questions_correct": data["correct"],
                "accuracy": acc_val,
                "status": data["category"],
            }
        )

    chapter_stats.sort(key=lambda x: (x["average"] is not None, x["average"]), reverse=True)
    return chapter_stats


def get_teacher_quiz_history(
    student_id: str,
    class_level: Optional[int] = None,
    db_path: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """13.3 Chronological Quiz History formatted for tables and plots (Class-Isolated)."""
    repo = quiz_repository if db_path is None else type(quiz_repository)(db_path=db_path)
    history = repo.get_student_history(student_id, class_level=class_level, include_questions=False)
    if not history:
        return []

    formatted = []
    for att in history:
        formatted.append(
            {
                "quiz_id": att["quiz_id"],
                "date": _format_date(att["timestamp"]),
                "timestamp": att["timestamp"],
                "class_level": att["class_level"],
                "chapter": att["chapter"],
                "difficulty": att["difficulty"].capitalize(),
                "score": att["score"],
                "total_questions": att["total_questions"],
                "percentage": int(round(att["percentage"])),
                "score_display": f"{int(round(att['percentage']))}%",
            }
        )

    return formatted


def get_teacher_swat_summary(
    student_id: str,
    class_level: Optional[int] = None,
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    """13.4 Categorized SWAT Summary for Teacher View (Class-Isolated)."""
    swat = get_student_swat(student_id, class_level=class_level, db_path=db_path)
    return {
        "student_id": student_id,
        "class_level": class_level,
        "has_data": swat.get("has_data", False),
        "strengths": swat.get("strengths", []),
        "average_topics": swat.get("average_topics", []),
        "weak_topics": swat.get("weak_topics", []),
        "unattempted_topics": swat.get("unattempted_topics", []),
        "unattempted": swat.get("unattempted_topics", []),
    }


def get_student_status(
    student_id: str,
    class_level: Optional[int] = None,
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Early-Warning Status Engine (Class-Isolated).
    Evaluates transparent pedagogical rules to diagnose student standing:
    - Overall Standing (Performing Well 🟢, Monitor 🟡, Needs Attention 🔴)
    - Weak-Topic Alerts (< 50%)
    - Trend Diagnosis (Declining alert vs. Improving recognition)
    """
    repo = quiz_repository if db_path is None else type(quiz_repository)(db_path=db_path)
    history = repo.get_student_history(student_id, class_level=class_level, include_questions=False)
    swat = get_student_swat(student_id, class_level=class_level, db_path=db_path)

    if not history or not swat.get("has_data"):
        return {
            "student_id": student_id,
            "class_level": class_level,
            "has_data": False,
            "overall_status": "No Data",
            "status_code": "no_data",
            "status_icon": "no_data",
            "overall_average": 0,
            "trend": {
                "direction": "no_data",
                "alert": False,
                "reason": "No quiz history recorded yet.",
            },
            "alerts": [],
            "weak_topics": [],
            "positive_notes": [],
        }

    overall_avg = swat["overall"]["average"]
    total_quizzes = len(history)
    quiz_percentages = [att["percentage"] for att in history]

    if overall_avg >= 70:
        overall_status = "Performing Well"
        status_code = "performing_well"
        status_icon = "performing_well"
    elif overall_avg >= 50:
        overall_status = "Monitor"
        status_code = "monitor"
        status_icon = "monitor"
    else:
        overall_status = "Needs Attention"
        status_code = "needs_attention"
        status_icon = "needs_attention"

    trend_alert = False
    trend_reason = ""
    trend_direction = "stable"
    earlier_avg = 0
    recent_avg = 0

    if total_quizzes == 1:
        trend_direction = "stable"
        earlier_avg = int(round(quiz_percentages[0]))
        recent_avg = int(round(quiz_percentages[0]))
        trend_reason = f"Initial baseline quiz score: {recent_avg}%."
    else:
        mid = max(1, total_quizzes // 2)
        earlier_scores = quiz_percentages[:mid]
        recent_scores = quiz_percentages[mid:]

        earlier_mean = sum(earlier_scores) / len(earlier_scores)
        recent_mean = sum(recent_scores) / len(recent_scores)
        diff = recent_mean - earlier_mean

        earlier_avg = int(round(earlier_mean))
        recent_avg = int(round(recent_mean))

        if diff >= 4.0:
            trend_direction = "improving"
            trend_reason = f"Performance is steadily improving over recent quizzes ({earlier_avg}% -> {recent_avg}%)."
        elif diff <= -4.0:
            trend_direction = "declining"
            trend_alert = True
            trend_reason = (
                f"Recent quiz performance is declining ({earlier_avg}% -> {recent_avg}%)."
            )
        else:
            trend_direction = "stable"
            trend_reason = f"Performance has remained steady around {recent_avg}%."

    alerts = []
    weak_topic_names = []
    for wt in swat.get("weak_topics", []):
        ch_name = wt["chapter"]
        ch_score = wt["score"]
        weak_topic_names.append(ch_name)
        alerts.append(
            {
                "type": "weak_topic",
                "chapter": ch_name,
                "score": ch_score,
                "message": f"Weak performance in {ch_name} ({ch_score}%)",
            }
        )

    if trend_alert:
        alerts.append(
            {
                "type": "declining_trend",
                "message": f"{trend_reason}",
            }
        )

    positive_notes = []
    if trend_direction == "improving":
        positive_notes.append(trend_reason)
        if status_code != "performing_well":
            overall_status = "Improving"
            status_code = "improving"
            status_icon = "improving"

    return {
        "student_id": student_id,
        "class_level": class_level,
        "has_data": True,
        "overall_status": overall_status,
        "status_code": status_code,
        "status_icon": status_icon,
        "overall_average": overall_avg,
        "total_quizzes": total_quizzes,
        "trend": {
            "direction": trend_direction,
            "alert": trend_alert,
            "reason": trend_reason,
            "earlier_average": earlier_avg,
            "recent_average": recent_avg,
        },
        "alerts": alerts,
        "weak_topics": weak_topic_names,
        "positive_notes": positive_notes,
    }


def get_teacher_student_profile(
    student_id: str,
    class_level: Optional[int] = None,
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Unified Master Profile for Teacher View (Class-Isolated)."""
    from src.academic_rag.analytics.action_plan import generate_action_plan

    overview = get_teacher_student_overview(student_id, class_level=class_level, db_path=db_path)
    chapters = get_teacher_chapter_statistics(student_id, class_level=class_level, db_path=db_path)
    history = get_teacher_quiz_history(student_id, class_level=class_level, db_path=db_path)
    swat = get_teacher_swat_summary(student_id, class_level=class_level, db_path=db_path)
    status = get_student_status(student_id, class_level=class_level, db_path=db_path)
    action_plan = generate_action_plan(student_id, class_level=class_level, db_path=db_path)

    return {
        "student_id": student_id,
        "class_level": class_level,
        "has_data": overview["has_data"],
        "overview": overview,
        "chapter_statistics": chapters,
        "quiz_history": history,
        "swat_summary": swat,
        "status": status,
        "action_plan": action_plan,
    }
