"""Teacher Analytics & Early-Warning Diagnostic Engine (Zero LLM calls)."""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from src.academic_rag.analytics.swat import get_student_swat
from src.academic_rag.config import config
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
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    """13.1 Overall Student Lifetime Statistics."""
    repo = quiz_repository if db_path is None else type(quiz_repository)(db_path=db_path)
    history = repo.get_student_history(student_id, include_questions=False)

    if not history:
        return {
            "student_id": student_id,
            "has_data": False,
            "class": 10,
            "overall_average": 0,
            "total_quizzes": 0,
            "questions_attempted": 0,
            "questions_correct": 0,
            "accuracy": 0,
        }

    class_level = history[-1].get("class_level", 10)
    total_quizzes = len(history)
    total_questions = sum(att["total_questions"] for att in history)
    total_correct = sum(att["score"] for att in history)

    overall_avg = int(round(sum(att["percentage"] for att in history) / total_quizzes)) if total_quizzes > 0 else 0
    accuracy = int(round((float(total_correct) / float(total_questions)) * 100.0)) if total_questions > 0 else 0

    return {
        "student_id": student_id,
        "has_data": True,
        "class": class_level,
        "overall_average": overall_avg,
        "total_quizzes": total_quizzes,
        "questions_attempted": total_questions,
        "questions_correct": total_correct,
        "accuracy": accuracy,
    }


def get_teacher_chapter_statistics(
    student_id: str,
    db_path: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """13.2 Chapter Statistics for Teacher View."""
    swat = get_student_swat(student_id, db_path=db_path)
    if not swat.get("has_data"):
        return []

    breakdown = swat.get("chapter_breakdown", {})
    chapter_stats = []

    for ch_name, data in breakdown.items():
        chapter_stats.append({
            "chapter": ch_name,
            "average": data["score"],
            "attempts": data["attempts"],
            "questions_attempted": data["questions"],
            "questions_correct": data["correct"],
            "accuracy": int(round(data["accuracy"])),
            "status": data["category"],
        })

    chapter_stats.sort(key=lambda x: x["average"], reverse=True)
    return chapter_stats


def get_teacher_quiz_history(
    student_id: str,
    db_path: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """13.3 Chronological Quiz History formatted for tables and plots."""
    repo = quiz_repository if db_path is None else type(quiz_repository)(db_path=db_path)
    history = repo.get_student_history(student_id, include_questions=False)
    if not history:
        return []

    formatted = []
    for att in history:
        formatted.append({
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
        })

    return formatted


def get_teacher_swat_summary(
    student_id: str,
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    """13.4 Categorized SWAT Summary for Teacher View."""
    swat = get_student_swat(student_id, db_path=db_path)
    return {
        "student_id": student_id,
        "has_data": swat.get("has_data", False),
        "strengths": swat.get("strengths", []),
        "average_topics": swat.get("average_topics", []),
        "weak_topics": swat.get("weak_topics", []),
    }


def get_student_status(
    student_id: str,
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Early-Warning Status Engine.
    Evaluates transparent pedagogical rules to diagnose student standing:
    - Overall Standing (Performing Well 🟢, Monitor 🟡, Needs Attention 🔴)
    - Weak-Topic Alerts (< 50%)
    - Trend Diagnosis (Declining alert vs. Improving recognition)
    """
    repo = quiz_repository if db_path is None else type(quiz_repository)(db_path=db_path)
    history = repo.get_student_history(student_id, include_questions=False)
    swat = get_student_swat(student_id, db_path=db_path)

    if not history or not swat.get("has_data"):
        return {
            "student_id": student_id,
            "has_data": False,
            "overall_status": "No Data",
            "status_code": "no_data",
            "status_icon": "⚪",
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
        status_icon = "🟢"
    elif overall_avg >= 50:
        overall_status = "Monitor"
        status_code = "monitor"
        status_icon = "🟡"
    else:
        overall_status = "Needs Attention"
        status_code = "needs_attention"
        status_icon = "🔴"

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
            trend_reason = f"Performance is steadily improving over recent quizzes ({earlier_avg}% ➔ {recent_avg}%)."
        elif diff <= -4.0:
            trend_direction = "declining"
            trend_alert = True
            trend_reason = f"Recent quiz performance is declining ({earlier_avg}% ➔ {recent_avg}%)."
        else:
            trend_direction = "stable"
            trend_reason = f"Performance has remained steady around {recent_avg}%."

    alerts = []
    weak_topic_names = []
    for wt in swat.get("weak_topics", []):
        ch_name = wt["chapter"]
        ch_score = wt["score"]
        weak_topic_names.append(ch_name)
        alerts.append({
            "type": "weak_topic",
            "chapter": ch_name,
            "score": ch_score,
            "message": f"⚠ Weak performance in {ch_name} ({ch_score}%)",
        })

    if trend_alert:
        alerts.append({
            "type": "declining_trend",
            "message": f"⚠ {trend_reason}",
        })

    positive_notes = []
    if trend_direction == "improving":
        positive_notes.append(f"📈 {trend_reason}")
        if status_code != "performing_well":
            overall_status = "Improving"
            status_code = "improving"
            status_icon = "📈"

    return {
        "student_id": student_id,
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
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Unified Master Profile for Teacher View."""
    overview = get_teacher_student_overview(student_id, db_path=db_path)
    chapters = get_teacher_chapter_statistics(student_id, db_path=db_path)
    history = get_teacher_quiz_history(student_id, db_path=db_path)
    swat = get_teacher_swat_summary(student_id, db_path=db_path)
    status = get_student_status(student_id, db_path=db_path)

    return {
        "student_id": student_id,
        "has_data": overview["has_data"],
        "overview": overview,
        "chapter_statistics": chapters,
        "quiz_history": history,
        "swat_summary": swat,
        "status": status,
    }
