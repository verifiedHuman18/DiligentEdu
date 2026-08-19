#!/usr/bin/env python3
"""
NCERT Student SWAT Analysis Engine (Phase 10)
Completely UI-independent backend that transforms stored quiz history into a descriptive SWAT profile.
Calculates strengths, average topics, weak topics, overall statistics, and performance trends with zero LLM calls.
"""

import os
import sys
import json
import logging
from typing import Dict, Any, List, Optional, Union

# Reconfigure stdout for UTF-8
sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from quiz_storage import get_student_history, DEFAULT_DB_PATH

logger = logging.getLogger(__name__)

# ==========================================
# ⚙️ CONFIGURABLE THRESHOLDS
# ==========================================
STRONG_THRESHOLD: float = 70.0    # 70%+   -> STRONG
AVERAGE_THRESHOLD: float = 50.0   # 50–69% -> AVERAGE
                                  # < 50%  -> WEAK


def get_student_swat(
    student_id: str,
    db_path: Optional[str] = None,
    strong_threshold: float = STRONG_THRESHOLD,
    average_threshold: float = AVERAGE_THRESHOLD,
) -> Dict[str, Any]:
    """
    Main backend function for Phase 10 SWAT Engine.
    Reads student quiz history from SQLite and computes a purely descriptive SWAT performance profile.

    Args:
        student_id: Unique student ID (e.g. "student_001")
        db_path: Optional path to SQLite database (defaults to data/storage/quiz_history.db)
        strong_threshold: Score percentage threshold for Strong (default: 70.0)
        average_threshold: Score percentage threshold for Average (default: 50.0)

    Returns:
        Structured Dict:
        {
            "student_id": "student_001",
            "overall": {
                "average": 67,
                "accuracy": 68,
                "quizzes_attempted": 5,
                "total_questions": 25,
                "total_correct": 17
            },
            "strengths": [
                {"chapter": "Chemical Reactions", "score": 84, "attempts": 2, "questions": 10}
            ],
            "average_topics": [
                {"chapter": "Life Processes", "score": 63, "attempts": 1, "questions": 5}
            ],
            "weak_topics": [
                {"chapter": "Electricity", "score": 42, "attempts": 2, "questions": 10}
            ],
            "trend": {
                "direction": "improving",
                "recent_average": 72,
                "earlier_average": 52
            }
        }
    """
    active_db = db_path or DEFAULT_DB_PATH
    history = get_student_history(student_id, include_questions=True, db_path=active_db)

    if not history:
        return {
            "student_id": student_id,
            "has_data": False,
            "overall": {
                "average": 0,
                "accuracy": 0,
                "quizzes_attempted": 0,
                "total_questions": 0,
                "total_correct": 0,
            },
            "strengths": [],
            "average_topics": [],
            "weak_topics": [],
            "chapter_breakdown": {},
            "trend": {
                "direction": "no_data",
                "recent_average": 0,
                "earlier_average": 0,
                "summary": "No quiz attempts recorded yet.",
            },
        }

    # 1. Chapter-wise aggregation
    chapter_map: Dict[str, Dict[str, Any]] = {}
    total_questions = 0
    total_correct = 0
    quiz_percentages: List[float] = []

    for attempt in history:
        ch = attempt["chapter"]
        pct = float(attempt["percentage"])
        quiz_percentages.append(pct)
        total_questions += int(attempt["total_questions"])
        total_correct += int(attempt["score"])

        if ch not in chapter_map:
            chapter_map[ch] = {
                "chapter": ch,
                "class_level": attempt["class_level"],
                "attempts": 0,
                "scores": [],
                "questions_attempted": 0,
                "questions_correct": 0,
            }

        c_data = chapter_map[ch]
        c_data["attempts"] += 1
        c_data["scores"].append(pct)
        c_data["questions_attempted"] += int(attempt["total_questions"])
        c_data["questions_correct"] += int(attempt["score"])

    # 2. Classify chapters into strengths, average_topics, weak_topics
    strengths: List[Dict[str, Any]] = []
    average_topics: List[Dict[str, Any]] = []
    weak_topics: List[Dict[str, Any]] = []
    chapter_breakdown: Dict[str, Dict[str, Any]] = {}

    for ch, data in chapter_map.items():
        avg_score = round(sum(data["scores"]) / len(data["scores"]), 1)
        int_score = int(round(avg_score))
        acc = round(float(data["questions_correct"]) / float(data["questions_attempted"]) * 100.0, 1) if data["questions_attempted"] > 0 else 0.0

        item = {
            "chapter": ch,
            "score": int_score,
            "accuracy": acc,
            "attempts": data["attempts"],
            "questions": data["questions_attempted"],
            "correct": data["questions_correct"],
        }

        if avg_score >= strong_threshold:
            item["category"] = "strong"
            strengths.append(item)
        elif avg_score >= average_threshold:
            item["category"] = "average"
            average_topics.append(item)
        else:
            item["category"] = "weak"
            weak_topics.append(item)

        chapter_breakdown[ch] = item

    # Sort each list by score descending
    strengths.sort(key=lambda x: x["score"], reverse=True)
    average_topics.sort(key=lambda x: x["score"], reverse=True)
    weak_topics.sort(key=lambda x: x["score"], reverse=True)

    # 3. Overall statistics
    total_quizzes = len(history)
    overall_avg = int(round(sum(quiz_percentages) / total_quizzes)) if total_quizzes > 0 else 0
    overall_acc = int(round(float(total_correct) / float(total_questions) * 100.0)) if total_questions > 0 else 0

    # 4. Performance trend calculation (comparing earlier vs recent quizzes)
    if total_quizzes == 1:
        direction = "stable"
        recent_avg = int(round(quiz_percentages[0]))
        earlier_avg = int(round(quiz_percentages[0]))
        trend_summary = f"Single quiz completed with score {recent_avg}%."
    else:
        # Split into earlier half and recent half
        mid = max(1, total_quizzes // 2)
        earlier_scores = quiz_percentages[:mid]
        recent_scores = quiz_percentages[mid:]

        earlier_mean = sum(earlier_scores) / len(earlier_scores)
        recent_mean = sum(recent_scores) / len(recent_scores)
        diff = recent_mean - earlier_mean

        earlier_avg = int(round(earlier_mean))
        recent_avg = int(round(recent_mean))

        if diff >= 4.0:
            direction = "improving"
            trend_summary = f"Performance is improving (earlier average: {earlier_avg}%, recent average: {recent_avg}%)."
        elif diff <= -4.0:
            direction = "declining"
            trend_summary = f"Performance is declining (earlier average: {earlier_avg}%, recent average: {recent_avg}%)."
        else:
            direction = "stable"
            trend_summary = f"Performance is steady (earlier average: {earlier_avg}%, recent average: {recent_avg}%)."

    return {
        "student_id": student_id,
        "has_data": True,
        "overall": {
            "average": overall_avg,
            "accuracy": overall_acc,
            "quizzes_attempted": total_quizzes,
            "total_questions": total_questions,
            "total_correct": total_correct,
        },
        "strengths": strengths,
        "average_topics": average_topics,
        "weak_topics": weak_topics,
        "chapter_breakdown": chapter_breakdown,
        "trend": {
            "direction": direction,
            "recent_average": recent_avg,
            "earlier_average": earlier_avg,
            "summary": trend_summary,
        },
    }


# Backwards compatibility wrapper for calculate_student_swat
def calculate_student_swat(
    student_id: str,
    db_path: str = DEFAULT_DB_PATH,
    strong_threshold: float = STRONG_THRESHOLD,
    average_threshold: float = AVERAGE_THRESHOLD,
) -> Dict[str, Any]:
    """Compatibility wrapper returning legacy format with categories dictionary."""
    swat = get_student_swat(student_id, db_path, strong_threshold, average_threshold)
    if not swat["has_data"]:
        return {
            "student_id": student_id,
            "has_data": False,
            "total_quizzes": 0,
            "questions_attempted": 0,
            "questions_correct": 0,
            "overall_average": 0.0,
            "highest_performing_chapter": None,
            "lowest_performing_chapter": None,
            "recent_trend": {"status": "no_data", "direction": "—", "recent_scores": [], "summary": "No data"},
            "categories": {"strong": [], "average": [], "weak": []},
            "chapter_wise_accuracy": {},
            "chapters": {},
        }

    all_chapters = swat["strengths"] + swat["average_topics"] + swat["weak_topics"]
    sorted_all = sorted(all_chapters, key=lambda x: x["score"], reverse=True)

    highest_ch = {"chapter": sorted_all[0]["chapter"], "accuracy": sorted_all[0]["score"]} if sorted_all else None
    lowest_ch = {"chapter": sorted_all[-1]["chapter"], "accuracy": sorted_all[-1]["score"]} if sorted_all else None

    return {
        "student_id": student_id,
        "has_data": True,
        "total_quizzes": swat["overall"]["quizzes_attempted"],
        "questions_attempted": swat["overall"]["total_questions"],
        "questions_correct": swat["overall"]["total_correct"],
        "overall_average": float(swat["overall"]["average"]),
        "highest_performing_chapter": highest_ch,
        "lowest_performing_chapter": lowest_ch,
        "recent_trend": {
            "status": swat["trend"]["direction"],
            "direction": "↑" if swat["trend"]["direction"] == "improving" else ("↓" if swat["trend"]["direction"] == "declining" else "→"),
            "summary": swat["trend"]["summary"],
        },
        "categories": {
            "strong": [{"chapter": s["chapter"], "accuracy": float(s["score"]), "questions_attempted": s["questions"], "questions_correct": s["correct"], "quizzes_taken": s["attempts"]} for s in swat["strengths"]],
            "average": [{"chapter": s["chapter"], "accuracy": float(s["score"]), "questions_attempted": s["questions"], "questions_correct": s["correct"], "quizzes_taken": s["attempts"]} for s in swat["average_topics"]],
            "weak": [{"chapter": s["chapter"], "accuracy": float(s["score"]), "questions_attempted": s["questions"], "questions_correct": s["correct"], "quizzes_taken": s["attempts"]} for s in swat["weak_topics"]],
        },
        "chapter_wise_accuracy": {c["chapter"]: float(c["score"]) for c in all_chapters},
        "chapters": swat["chapter_breakdown"],
    }


def format_swat_report(swat: Dict[str, Any]) -> str:
    """
    Formats the SWAT data into the clean ASCII profile requested in Phase 10.
    """
    if not swat.get("has_data", True):
        return f"No quiz history available for Student {swat.get('student_id')}."

    # If swat is in get_student_swat format:
    if "overall" in swat:
        student_id = swat["student_id"]
        lines = [
            "=" * 50,
            f"               STUDENT SWAT ({student_id})",
            "=" * 50,
            "",
            "🟢 STRONG (≥ 70%)",
        ]
        if swat["strengths"]:
            for item in swat["strengths"]:
                lines.append(f"  {item['chapter']:<34} {item['score']:>3d}%")
        else:
            lines.append("  (None)")

        lines.append("\n🟡 AVERAGE (50%–69%)")
        if swat["average_topics"]:
            for item in swat["average_topics"]:
                lines.append(f"  {item['chapter']:<34} {item['score']:>3d}%")
        else:
            lines.append("  (None)")

        lines.append("\n🔴 WEAK (< 50%)")
        if swat["weak_topics"]:
            for item in swat["weak_topics"]:
                lines.append(f"  {item['chapter']:<34} {item['score']:>3d}%")
        else:
            lines.append("  (None)")

        lines.extend([
            "\n" + "─" * 50,
            f"Overall Average:            {swat['overall']['average']}%",
            f"Overall Accuracy:           {swat['overall']['accuracy']}%",
            f"Quizzes Attempted:          {swat['overall']['quizzes_attempted']}",
            f"Total Questions:            {swat['overall']['total_questions']} (Correct: {swat['overall']['total_correct']})",
            f"Performance Trend:          {swat['trend']['direction'].upper()} (Earlier: {swat['trend']['earlier_average']}%, Recent: {swat['trend']['recent_average']}%)",
            "=" * 50,
        ])
        return "\n".join(lines)

    # Fallback legacy formatter
    return format_swat_report(get_student_swat(swat["student_id"]))


if __name__ == "__main__":
    print("Testing get_student_swat function...")
    res = get_student_swat("student_001")
    print(json.dumps(res, indent=2))
    print("\n" + format_swat_report(res))
