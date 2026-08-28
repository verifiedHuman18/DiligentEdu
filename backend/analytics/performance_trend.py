"""Student Performance Over Time and Trend Analytics Service (Teacher Portal).

Calculates chronological assessment trajectories, regression slopes, window averages,
and classifies student performance trends into Improving, Declining, Stagnant, or Insufficient Data.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

from backend.storage.repository import quiz_repository

logger = logging.getLogger(__name__)

# Configurable Slope Thresholds (Percentage points per assessment)
IMPROVEMENT_SLOPE_THRESHOLD: float = 2.0
DECLINE_SLOPE_THRESHOLD: float = -2.0

# Window Threshold for Simple Difference when points are few (e.g. 2-3 points)
MIN_POINTS_FOR_PRELIMINARY: int = 2
MIN_POINTS_FOR_RELIABLE: int = 4


def _format_point_date(iso_str: Optional[str]) -> str:
    """Formats an ISO timestamp into a human-readable abbreviated date like 'Aug 22'."""
    if not iso_str:
        return "N/A"
    try:
        parts = iso_str.split("T")[0].split("-")
        if len(parts) == 3:
            months = [
                "", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
            ]
            y, m, d = parts[0], int(parts[1]), int(parts[2])
            return f"{months[m]} {d}"
    except Exception:
        pass
    return iso_str[:10] if len(iso_str) >= 10 else iso_str


def calculate_linear_regression(y_vals: List[float]) -> Tuple[float, float, float]:
    """Calculates Ordinary Least Squares (OLS) regression slope (m), intercept (b), and R^2.
    
    x values are assumed to be chronological assessment indices (0, 1, 2, ..., N-1).
    """
    n = len(y_vals)
    if n < 2:
        return 0.0, (y_vals[0] if n == 1 else 0.0), 0.0

    x_vals = list(range(n))
    sum_x = sum(x_vals)
    sum_y = sum(y_vals)
    sum_x_sq = sum(x * x for x in x_vals)
    sum_xy = sum(x * y for x, y in zip(x_vals, y_vals))

    denom = (n * sum_x_sq) - (sum_x ** 2)
    if denom == 0:
        return 0.0, sum_y / n, 0.0

    slope = ((n * sum_xy) - (sum_x * sum_y)) / denom
    intercept = (sum_y - (slope * sum_x)) / n

    # Calculate R-squared
    y_mean = sum_y / n
    ss_tot = sum((y - y_mean) ** 2 for y in y_vals)
    ss_res = sum((y - (slope * x + intercept)) ** 2 for x, y in zip(x_vals, y_vals))
    r_squared = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 1.0

    return round(slope, 3), round(intercept, 3), round(max(0.0, min(1.0, r_squared)), 3)


def classify_trend_from_scores(scores: List[float]) -> Dict[str, Any]:
    """Classifies a list of chronological scores into a trend dictionary.
    
    Handles sparse data (0-1: insufficient, 2-3: preliminary, 4+: reliable)
    and applies OLS regression slope + window difference.
    """
    n = len(scores)
    if n == 0:
        return {
            "status": "insufficient_data",
            "status_label": "⚪ Insufficient Data",
            "status_title": "Insufficient Data",
            "confidence": "insufficient",
            "slope": 0.0,
            "current_performance": 0.0,
            "previous_average": 0.0,
            "change_pct_points": 0.0,
            "explanation": "No assessment data available for this subject.",
            "assessment_count": 0,
        }

    current_score = round(scores[-1], 1)

    if n == 1:
        return {
            "status": "insufficient_data",
            "status_label": "⚪ Insufficient Data",
            "status_title": "Insufficient Data",
            "confidence": "insufficient",
            "slope": 0.0,
            "current_performance": current_score,
            "previous_average": current_score,
            "change_pct_points": 0.0,
            "explanation": "At least 2 assessments are required to calculate a performance trend.",
            "assessment_count": 1,
        }

    slope, intercept, r_squared = calculate_linear_regression(scores)

    # Window baseline vs recent calculation
    if n <= 3:
        confidence = "preliminary"
        prev_avg = round(scores[0], 1)
        recent_avg = round(sum(scores[1:]) / (n - 1), 1)
        change_pp = round(recent_avg - prev_avg, 1)
    else:
        confidence = "reliable"
        split_idx = n // 2
        prev_scores = scores[:split_idx]
        recent_scores = scores[split_idx:]
        prev_avg = round(sum(prev_scores) / len(prev_scores), 1)
        recent_avg = round(sum(recent_scores) / len(recent_scores), 1)
        change_pp = round(recent_avg - prev_avg, 1)

    # Determine status based on regression slope
    if slope >= IMPROVEMENT_SLOPE_THRESHOLD:
        status = "improving"
        status_label = "🟢 Improving"
        status_title = "Improving"
        explanation = (
            f"Performance is trending upward by +{slope:.1f} pp/quiz (+{change_pp:+.1f} pp window change) "
            f"across the last {n} assessments."
        )
    elif slope <= DECLINE_SLOPE_THRESHOLD:
        status = "declining"
        status_label = "🔴 Declining"
        status_title = "Declining"
        explanation = (
            f"Performance is trending downward by {slope:.1f} pp/quiz ({change_pp:+.1f} pp window change) "
            f"across the last {n} assessments."
        )
    else:
        status = "stagnant"
        status_label = "🟡 Stagnant"
        status_title = "Stagnant"
        explanation = (
            f"Performance is holding steady ({slope:+.1f} pp/quiz, {change_pp:+.1f} pp change) "
            f"across the last {n} assessments."
        )

    return {
        "status": status,
        "status_label": status_label,
        "status_title": status_title,
        "confidence": confidence,
        "slope": slope,
        "r_squared": r_squared,
        "current_performance": current_score,
        "previous_average": prev_avg,
        "recent_average": recent_avg,
        "change_pct_points": change_pp,
        "explanation": explanation,
        "assessment_count": n,
    }


def get_student_performance_trend(
    student_id: str,
    class_level: Optional[int] = None,
    subject: str = "Science",
    db_path: Optional[str] = None,
    max_window: int = 15,
) -> Dict[str, Any]:
    """Extracts chronological quiz attempts, builds performance points, and calculates performance trend.
    
    Strictly isolated by student_id, class_level, and subject.
    """
    clean_subj = "Mathematics" if "math" in str(subject).lower() else "Science"
    repo = quiz_repository if db_path is None else type(quiz_repository)(db_path=db_path)

    # Fetch attempts sorted chronologically (timestamp ASC)
    history = repo.get_student_history(
        student_id=student_id,
        class_level=class_level,
        subject=clean_subj,
        include_questions=False,
    )

    if not history:
        trend = classify_trend_from_scores([])
        return {
            "student_id": student_id,
            "class_level": class_level,
            "subject": clean_subj,
            "has_data": False,
            "points": [],
            "trend": trend,
            "summary": {
                "total_assessments": 0,
                "latest_score": None,
                "average_score": 0.0,
            },
        }

    # Slice to the most recent window of assessments
    recent_attempts = history[-max_window:]

    points: List[Dict[str, Any]] = []
    scores: List[float] = []

    for idx, att in enumerate(recent_attempts, 1):
        raw_score = att.get("score", 0)
        tot_q = att.get("total_questions", 0)
        pct = (
            float(att.get("percentage"))
            if att.get("percentage") is not None
            else ((float(raw_score) / float(tot_q) * 100.0) if tot_q > 0 else 0.0)
        )
        pct = round(pct, 1)
        scores.append(pct)

        ts = att.get("timestamp")
        date_str = _format_point_date(ts)
        ch_name = att.get("chapter", "General Assessment")

        points.append(
            {
                "index": idx,
                "quiz_id": att.get("quiz_id"),
                "date": date_str,
                "timestamp": ts,
                "chapter": ch_name,
                "chapter_number": att.get("chapter_number", 0),
                "score": raw_score,
                "total_questions": tot_q,
                "score_fraction": f"{raw_score}/{tot_q}",
                "performance": pct,
                "difficulty": str(att.get("difficulty", "medium")).capitalize(),
            }
        )

    # Calculate trend metrics
    trend = classify_trend_from_scores(scores)

    avg_score = round(sum(scores) / len(scores), 1) if scores else 0.0

    return {
        "student_id": student_id,
        "class_level": class_level,
        "subject": clean_subj,
        "has_data": True,
        "points": points,
        "trend": trend,
        "summary": {
            "total_assessments": len(history),
            "window_assessments": len(points),
            "latest_score": scores[-1] if scores else None,
            "average_score": avg_score,
        },
    }
