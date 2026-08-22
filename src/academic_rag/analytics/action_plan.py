"""Action-Plan Recommendation Engine (Zero LLM calls, 100% Deterministic Rules)."""

import logging
from typing import Any, Dict, List, Optional

from src.academic_rag.analytics.swat import get_student_swat

logger = logging.getLogger(__name__)


def generate_action_plan(
    student_id: str,
    class_level: Optional[int] = None,
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Generates a prioritized, explainable, and actionable study recommendation plan
    based on the student's unified SWAT performance and unattempted chapters.

    Recommendation Priority:
      1. Priority 1 (High)   — Weak chapters (< 50%) -> Practice quiz (medium/easy)
      2. Priority 2 (Medium) — Unattempted chapters   -> Diagnostic quiz (easy)
      3. Priority 3 (Normal) — Average chapters (50%-69%) -> Reinforce practice (medium)
      4. Priority 4 (Low)    — Strong chapters (≥ 70%) -> Advanced challenge (hard)

    Returns:
        Structured Dict containing overall urgency, summary, and ordered actionable items.
    """
    swat = get_student_swat(student_id, class_level=class_level, db_path=db_path)
    target_class = swat.get("class_level") or (int(class_level) if class_level is not None else 10)

    actions: List[Dict[str, Any]] = []

    # Priority 1 — Weak chapters (HIGH PRIORITY)
    for item in swat.get("weak", []):
        score_val = item["score"]
        diff = "medium" if score_val >= 30 else "easy"
        actions.append(
            {
                "chapter": item["chapter"],
                "chapter_number": item.get("chapter_number"),
                "status": "weak",
                "score": score_val,
                "attempts": item.get("attempts", 1),
                "scores": item.get("scores", [score_val]),
                "recent_performance": item.get("recent_performance", f"{score_val}%"),
                "action": "practice",
                "action_label": f"Practice {item['chapter']}",
                "button_text": f"Practice {item['chapter']}",
                "difficulty": diff,
                "reason": f"Your performance is below target ({score_val}%).",
                "priority_rank": 1,
                "priority_label": "HIGH PRIORITY",
                "priority_icon": "🔴",
            }
        )

    # Priority 2 — Unattempted chapters (NEW TOPIC)
    for item in swat.get("unattempted", []):
        actions.append(
            {
                "chapter": item["chapter"],
                "chapter_number": item.get("chapter_number"),
                "status": "unattempted",
                "score": None,
                "attempts": 0,
                "scores": [],
                "recent_performance": "Not attempted yet",
                "action": "diagnostic",
                "action_label": "Take Diagnostic Quiz",
                "button_text": "Take Diagnostic Quiz",
                "difficulty": "easy",
                "reason": "Not attempted yet. Take a diagnostic quiz to establish baseline mastery.",
                "priority_rank": 2,
                "priority_label": "NEW TOPIC",
                "priority_icon": "⚪",
            }
        )

    # Priority 3 — Average chapters (CONTINUE PRACTICE)
    for item in swat.get("average", []):
        score_val = item["score"]
        actions.append(
            {
                "chapter": item["chapter"],
                "chapter_number": item.get("chapter_number"),
                "status": "average",
                "score": score_val,
                "attempts": item.get("attempts", 1),
                "scores": item.get("scores", [score_val]),
                "recent_performance": item.get("recent_performance", f"{score_val}%"),
                "action": "practice",
                "action_label": f"Practice {item['chapter']}",
                "button_text": "Practice",
                "difficulty": "medium",
                "reason": f"Performance is moderate ({score_val}%). Practice to achieve strong mastery.",
                "priority_rank": 3,
                "priority_label": "CONTINUE PRACTICE",
                "priority_icon": "🟡",
            }
        )

    # Priority 4 — Strong chapters (ADVANCED PRACTICE)
    for item in swat.get("strong", []):
        score_val = item["score"]
        actions.append(
            {
                "chapter": item["chapter"],
                "chapter_number": item.get("chapter_number"),
                "status": "strong",
                "score": score_val,
                "attempts": item.get("attempts", 1),
                "scores": item.get("scores", [score_val]),
                "recent_performance": item.get("recent_performance", f"{score_val}%"),
                "action": "mastery",
                "action_label": "Advanced Challenge",
                "button_text": "Advanced Challenge",
                "difficulty": "hard",
                "reason": f"Strong performance ({score_val}%). Optional advanced practice to maintain mastery.",
                "priority_rank": 4,
                "priority_label": "ADVANCED PRACTICE",
                "priority_icon": "🟢",
            }
        )

    # Overall Priority Determination
    if swat.get("weak"):
        overall_priority = "high"
        summary = f"High priority: Focus on {len(swat['weak'])} weak topic(s) to raise mastery above 50%."
    elif swat.get("unattempted"):
        overall_priority = "medium"
        summary = f"Medium priority: Attempt {len(swat['unattempted'])} unattempted chapter(s) to establish baseline mastery."
    elif swat.get("average"):
        overall_priority = "normal"
        summary = f"Normal priority: Practice {len(swat['average'])} average chapter(s) to push into strong mastery."
    else:
        overall_priority = "low"
        summary = "All chapters mastered! Optional advanced practice available."

    return {
        "student_id": student_id,
        "class_level": target_class,
        "priority": overall_priority,
        "summary": summary,
        "actions": actions,
        "action_counts": {
            "weak": len(swat.get("weak", [])),
            "unattempted": len(swat.get("unattempted", [])),
            "average": len(swat.get("average", [])),
            "strong": len(swat.get("strong", [])),
            "total_recommendations": len(actions),
        },
    }
