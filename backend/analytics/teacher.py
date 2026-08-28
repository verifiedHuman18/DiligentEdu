"""Teacher Diagnostics and Master Analytics Service (Phase 13, 20 & Cross-Subject Support).

Aggregates student performance across class levels and subjects, provides categorized SWAT summaries,
real-time status engines, chapter-level metrics, and full action-plan supporting statistics.
"""

import logging
from typing import Any, Dict, List, Optional

from backend.analytics.swat import get_student_swat
from backend.storage.repository import quiz_repository

logger = logging.getLogger(__name__)


def _format_date(iso_str: Optional[str]) -> str:
    """Formats ISO timestamp (YYYY-MM-DDTHH:MM:SS) into readable date format (DD Mon YYYY)."""
    if not iso_str:
        return "N/A"
    try:
        parts = iso_str.split("T")[0].split("-")
        if len(parts) == 3:
            months = [
                "",
                "Jan",
                "Feb",
                "Mar",
                "Apr",
                "May",
                "Jun",
                "Jul",
                "Aug",
                "Sep",
                "Oct",
                "Nov",
                "Dec",
            ]
            y, m, d = parts[0], int(parts[1]), int(parts[2])
            return f"{d} {months[m]} {y}"
    except Exception:
        pass
    return iso_str[:10] if len(iso_str) >= 10 else iso_str


def get_all_students_from_db() -> List[Dict[str, Any]]:
    """Fetches all students from the Prisma database with their name and class_level."""
    from prisma import Prisma

    db = Prisma()
    db.connect()
    students = db.user.find_many(where={"role": "student"})
    db.disconnect()
    return [
        {"id": s.id, "email": s.email, "name": s.name or s.id, "class_level": s.class_level}
        for s in students
    ]


def promote_student_in_db(student_id: str, new_class_level: int) -> None:
    """Promotes a student to a new class level in the Prisma DB."""
    from prisma import Prisma

    db = Prisma()
    db.connect()
    db.user.update(where={"id": student_id}, data={"class_level": new_class_level})
    db.disconnect()


def get_teacher_student_overview(
    student_id: str,
    class_level: Optional[int] = None,
    subject: str = "Science",
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    """13.1 Master Diagnostic Overview for Teacher View (Class- and Subject-Isolated)."""
    subj_clean = "Mathematics" if "math" in str(subject).lower() else "Science"
    repo = quiz_repository if db_path is None else type(quiz_repository)(db_path=db_path)
    history = repo.get_student_history(
        student_id, class_level=class_level, subject=subj_clean, include_questions=False
    )
    swat = get_student_swat(
        student_id, class_level=class_level, subject=subj_clean, db_path=db_path
    )

    if not history or not swat.get("has_data"):
        return {
            "student_id": student_id,
            "class": class_level,
            "class_level": class_level,
            "subject": subj_clean,
            "has_data": False,
            "overall_average": 0,
            "total_quizzes": 0,
            "total_quizzes_taken": 0,
            "total_questions_attempted": 0,
            "total_questions_correct": 0,
            "accuracy": 0,
            "last_active": None,
            "syllabus_coverage_pct": 0,
            "attempted_chapters_count": 0,
            "total_chapters_count": swat.get("overall", {}).get("total_chapters", 13),
        }

    total_quizzes = len(history)
    total_q = sum(att["total_questions"] for att in history)
    total_corr = sum(att["score"] for att in history)
    overall_acc = int(round((total_corr / total_q * 100))) if total_q > 0 else 0

    sorted_by_time = sorted(history, key=lambda x: x["timestamp"], reverse=True)
    last_ts = sorted_by_time[0]["timestamp"] if sorted_by_time else None

    att_count = swat["overall"].get("attempted_chapters", 0)
    total_chs = swat["overall"].get("total_chapters", 13)
    cov_pct = int(round((att_count / total_chs * 100))) if total_chs > 0 else 0

    return {
        "student_id": student_id,
        "class": class_level,
        "class_level": class_level,
        "subject": subj_clean,
        "has_data": True,
        "overall_average": swat["overall"]["average"],
        "total_quizzes": total_quizzes,
        "total_quizzes_taken": total_quizzes,
        "total_questions_attempted": total_q,
        "total_questions_correct": total_corr,
        "accuracy": overall_acc,
        "last_active": _format_date(last_ts),
        "syllabus_coverage_pct": cov_pct,
        "attempted_chapters_count": att_count,
        "total_chapters_count": total_chs,
    }


def get_teacher_chapter_statistics(
    student_id: str,
    class_level: Optional[int] = None,
    subject: str = "Science",
    db_path: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """13.2 Chapter-Level Diagnostic Statistics for Teacher View (Class- and Subject-Isolated)."""
    subj_clean = "Mathematics" if "math" in str(subject).lower() else "Science"
    swat = get_student_swat(
        student_id, class_level=class_level, subject=subj_clean, db_path=db_path
    )
    breakdown = swat.get("chapter_breakdown", {})

    chapter_stats = []
    for ch_title, data in breakdown.items():
        if data.get("attempts", 0) > 0:
            ch_num = data.get("chapter_number")
            total_q = data.get("total_questions", data.get("questions", 0))
            corr_q = data.get("questions_correct", data.get("correct", 0))
            acc_val = data.get("accuracy")
            score_val = data.get("score")
            attempts_val = data.get("attempts", 0)
            status_val = data.get("category", data.get("status", "average"))

            chapter_stats.append(
                {
                    "chapter_number": ch_num,
                    "chapter": ch_title,
                    "average": score_val,
                    "score": score_val,
                    "attempts": attempts_val,
                    "total_questions": total_q,
                    "questions": total_q,
                    "questions_correct": corr_q,
                    "correct": corr_q,
                    "accuracy": acc_val,
                    "status": status_val,
                }
            )

    chapter_stats.sort(key=lambda x: (x["average"] is not None, x["average"]), reverse=True)
    return chapter_stats


def get_teacher_quiz_history(
    student_id: str,
    class_level: Optional[int] = None,
    subject: str = "Science",
    limit: int = 10,
    db_path: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """13.3 Recent Quiz History for Teacher View (Class- and Subject-Isolated)."""
    subj_clean = "Mathematics" if "math" in str(subject).lower() else "Science"
    repo = quiz_repository if db_path is None else type(quiz_repository)(db_path=db_path)
    history = repo.get_student_history(
        student_id, class_level=class_level, subject=subj_clean, include_questions=False
    )
    if limit and len(history) > limit:
        history = history[-limit:]

    formatted = []
    for att in history:
        formatted.append(
            {
                "quiz_id": att["quiz_id"],
                "date": _format_date(att["timestamp"]),
                "timestamp": att["timestamp"],
                "class_level": att["class_level"],
                "subject": att.get("subject", subj_clean),
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
    subject: str = "Science",
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    """13.4 Categorized SWAT Summary for Teacher View (Class- and Subject-Isolated)."""
    subj_clean = "Mathematics" if "math" in str(subject).lower() else "Science"
    swat = get_student_swat(
        student_id, class_level=class_level, subject=subj_clean, db_path=db_path
    )
    return {
        "student_id": student_id,
        "class_level": class_level,
        "subject": subj_clean,
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
    subject: str = "Science",
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Early-Warning Status Engine (Class- and Subject-Isolated).
    Evaluates transparent pedagogical rules to diagnose student standing:
    - Overall Standing (Performing Well 🟢, Monitor 🟡, Needs Attention 🔴)
    - Weak-Topic Alerts (< 50%)
    - Trend Diagnosis (Declining alert vs. Improving recognition)
    """
    subj_clean = "Mathematics" if "math" in str(subject).lower() else "Science"
    repo = quiz_repository if db_path is None else type(quiz_repository)(db_path=db_path)
    history = repo.get_student_history(
        student_id, class_level=class_level, subject=subj_clean, include_questions=False
    )
    swat = get_student_swat(
        student_id, class_level=class_level, subject=subj_clean, db_path=db_path
    )

    if not history or not swat.get("has_data"):
        return {
            "student_id": student_id,
            "class_level": class_level,
            "subject": subj_clean,
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
        "subject": subj_clean,
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
    subject: str = "Science",
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Unified Master Profile for Teacher View (Class- and Subject-Isolated)."""
    from backend.analytics.action_plan import generate_action_plan

    subj_clean = "Mathematics" if "math" in str(subject).lower() else "Science"
    overview = get_teacher_student_overview(
        student_id, class_level=class_level, subject=subj_clean, db_path=db_path
    )
    chapters = get_teacher_chapter_statistics(
        student_id, class_level=class_level, subject=subj_clean, db_path=db_path
    )
    history = get_teacher_quiz_history(
        student_id, class_level=class_level, subject=subj_clean, db_path=db_path
    )
    swat = get_teacher_swat_summary(
        student_id, class_level=class_level, subject=subj_clean, db_path=db_path
    )
    status = get_student_status(
        student_id, class_level=class_level, subject=subj_clean, db_path=db_path
    )
    action_plan = generate_action_plan(
        student_id, class_level=class_level, subject=subj_clean, db_path=db_path
    )

    return {
        "student_id": student_id,
        "class_level": class_level,
        "subject": subj_clean,
        "has_data": overview["has_data"],
        "overview": overview,
        "chapters": chapters,
        "chapter_statistics": chapters,
        "history": history,
        "quiz_history": history,
        "swat": swat,
        "swat_summary": swat,
        "status": status,
        "action_plan": action_plan,
    }
