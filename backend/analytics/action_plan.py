"""Action-Plan Recommendation Engine (Zero LLM calls, Deterministic Rules + Teacher Customization)."""

import logging
from typing import Any, Dict, List, Optional

from backend.analytics.swat import get_student_swat
from backend.storage.repository import QuizRepository, quiz_repository

logger = logging.getLogger(__name__)


def generate_action_plan(
    student_id: str,
    class_level: Optional[int] = None,
    db_path: Optional[str] = None,
    check_custom: bool = True,
) -> Dict[str, Any]:
    """
    Generates a prioritized, explainable, and actionable study recommendation plan
    based on the student's unified SWAT performance, unattempted chapters,
    or active Teacher Customizations.

    Recommendation Priority (when not customized):
      1. Priority 1 (High)   — Weak chapters (< 50%) -> Practice quiz (medium/easy)
      2. Priority 2 (Medium) — Unattempted chapters   -> Diagnostic quiz (easy)
      3. Priority 3 (Normal) — Average chapters (50%-69%) -> Reinforce practice (medium)
      4. Priority 4 (Low)    — Strong chapters (≥ 70%) -> Advanced challenge (hard)

    Returns:
        Structured Dict containing overall urgency, summary, ordered actionable items,
        and customization metadata.
    """
    swat = get_student_swat(student_id, class_level=class_level, db_path=db_path)
    target_class = swat.get("class_level") or (int(class_level) if class_level is not None else 10)
    repo = quiz_repository if db_path is None else QuizRepository(db_path=db_path)

    # 1. Check for Active Teacher Custom Action Plan
    custom_record = repo.get_teacher_custom_plan(student_id, target_class) if check_custom else None

    if custom_record and custom_record.get("plan_data"):
        return _build_custom_teacher_action_plan(
            student_id=student_id,
            target_class=target_class,
            swat=swat,
            custom_record=custom_record,
        )

    # 2. Build Automated SWAT Action Plan
    return _build_automated_swat_action_plan(
        student_id=student_id,
        target_class=target_class,
        swat=swat,
    )


def _build_automated_swat_action_plan(
    student_id: str,
    target_class: int,
    swat: Dict[str, Any],
) -> Dict[str, Any]:
    """Generates standard rule-based action plan purely from SWAT analytics."""
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
                "priority_icon": "",
                "is_teacher_assigned": False,
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
                "priority_icon": "",
                "is_teacher_assigned": False,
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
                "priority_icon": "",
                "is_teacher_assigned": False,
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
                "priority_icon": "",
                "is_teacher_assigned": False,
            }
        )

    # Overall Priority Determination
    if swat.get("weak"):
        overall_priority = "high"
        summary = (
            f"High priority: Focus on {len(swat['weak'])} weak topic(s) to raise mastery above 50%."
        )
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
        "is_customized": False,
        "customized_by": None,
        "teacher_notes": None,
        "updated_at": None,
        "action_counts": {
            "weak": len(swat.get("weak", [])),
            "unattempted": len(swat.get("unattempted", [])),
            "average": len(swat.get("average", [])),
            "strong": len(swat.get("strong", [])),
            "total_recommendations": len(actions),
        },
    }


def _build_custom_teacher_action_plan(
    student_id: str,
    target_class: int,
    swat: Dict[str, Any],
    custom_record: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Constructs an enriched action plan incorporating Teacher-assigned priority chapters,
    difficulties, pedagogical notes, and real-time SWAT telemetry.
    """
    plan_data = custom_record.get("plan_data", {})
    raw_custom_actions = plan_data.get("actions", [])
    teacher_notes = custom_record.get("teacher_notes")
    updated_at = custom_record.get("updated_at")

    chapter_breakdown = swat.get("chapter_breakdown", {})
    enriched_custom_actions: List[Dict[str, Any]] = []
    seen_chapters = set()

    for idx, c_act in enumerate(raw_custom_actions, 1):
        ch_title = c_act.get("chapter", "").strip()
        if not ch_title:
            continue

        ch_data = chapter_breakdown.get(ch_title, {})
        status = ch_data.get("status") or ch_data.get("category", "unattempted")
        score = ch_data.get("score")
        attempts = ch_data.get("attempts", 0)
        recent_perf = ch_data.get("recent_performance", "Not attempted yet")
        ch_num = ch_data.get("chapter_number") or c_act.get("chapter_number")

        difficulty = str(c_act.get("difficulty", "medium")).lower()
        act_type = str(c_act.get("action", "practice")).lower()
        custom_reason = c_act.get("reason") or c_act.get("teacher_note")
        if not custom_reason:
            if status == "weak":
                custom_reason = (
                    f"Teacher priority: strengthen performance ({score}% current score)."
                )
            elif status == "unattempted":
                custom_reason = "Teacher priority: complete diagnostic baseline for this topic."
            else:
                custom_reason = "Teacher assigned practice to reinforce mastery."

        action_label = c_act.get("action_label") or f"Practice {ch_title}"
        button_text = c_act.get("button_text") or (
            f"Practice {ch_title}" if act_type == "practice" else "Start Quiz"
        )
        p_label = c_act.get("priority_label") or "TEACHER ASSIGNED"

        enriched_custom_actions.append(
            {
                "chapter": ch_title,
                "chapter_number": ch_num,
                "status": status,
                "score": score,
                "attempts": attempts,
                "scores": ch_data.get("scores", []),
                "recent_performance": recent_perf,
                "action": act_type,
                "action_label": action_label,
                "button_text": button_text,
                "difficulty": difficulty,
                "reason": custom_reason,
                "priority_rank": idx,
                "priority_label": p_label,
                "priority_icon": "",
                "is_teacher_assigned": True,
                "teacher_note": c_act.get("teacher_note") or custom_reason,
            }
        )
        seen_chapters.add(ch_title)

    # Append standard SWAT actions for non-customized chapters to ensure complete coverage
    auto_plan = _build_automated_swat_action_plan(student_id, target_class, swat)
    remaining_actions = []
    current_rank = len(enriched_custom_actions) + 1

    for act in auto_plan["actions"]:
        if act["chapter"] not in seen_chapters:
            act_copy = dict(act)
            act_copy["priority_rank"] = current_rank
            act_copy["is_teacher_assigned"] = False
            remaining_actions.append(act_copy)
            seen_chapters.add(act["chapter"])
            current_rank += 1

    combined_actions = enriched_custom_actions + remaining_actions

    count_custom = len(enriched_custom_actions)
    summary = f"Teacher assigned focus: {count_custom} chapter(s) designated for prioritized study."
    if teacher_notes:
        summary += f" Note: {teacher_notes}"

    return {
        "student_id": student_id,
        "class_level": target_class,
        "priority": "high" if enriched_custom_actions else auto_plan["priority"],
        "summary": summary,
        "actions": combined_actions,
        "is_customized": True,
        "customized_by": "teacher",
        "teacher_notes": teacher_notes,
        "updated_at": updated_at,
        "action_counts": {
            "custom_assigned": count_custom,
            "weak": len(swat.get("weak", [])),
            "unattempted": len(swat.get("unattempted", [])),
            "average": len(swat.get("average", [])),
            "strong": len(swat.get("strong", [])),
            "total_recommendations": len(combined_actions),
        },
    }


def save_teacher_action_plan(
    student_id: str,
    class_level: int,
    actions: List[Dict[str, Any]],
    teacher_notes: Optional[str] = None,
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Saves a customized teacher action plan and returns the updated plan structure.

    Args:
        student_id: Target student ID
        class_level: Grade level (9 or 10)
        actions: Ordered list of action dicts (must contain 'chapter', optional: 'difficulty', 'reason', 'action')
        teacher_notes: Optional global pedagogical guidance note
        db_path: Optional custom DB path
    """
    if not student_id or not str(student_id).strip():
        raise ValueError("student_id cannot be empty.")
    class_int = int(class_level)
    if class_int not in (9, 10):
        raise ValueError(f"Invalid class_level: {class_level}. Must be 9 or 10.")

    repo = quiz_repository if db_path is None else QuizRepository(db_path=db_path)
    plan_data = {"actions": actions}
    repo.save_teacher_action_plan(
        student_id=str(student_id).strip(),
        class_level=class_int,
        plan_data=plan_data,
        teacher_notes=teacher_notes,
    )
    return generate_action_plan(str(student_id).strip(), class_level=class_int, db_path=db_path)


def reset_teacher_action_plan(
    student_id: str,
    class_level: int,
    db_path: Optional[str] = None,
) -> bool:
    """
    Deletes any active teacher action plan customizations, restoring standard automated SWAT recommendations.
    """
    if not student_id or not str(student_id).strip():
        raise ValueError("student_id cannot be empty.")
    class_int = int(class_level)
    repo = quiz_repository if db_path is None else QuizRepository(db_path=db_path)
    return repo.delete_teacher_action_plan(
        student_id=str(student_id).strip(), class_level=class_int
    )


def get_teacher_action_plan(
    student_id: str,
    class_level: Optional[int] = None,
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Retrieves the active action plan for teacher view."""
    return generate_action_plan(student_id, class_level=class_level, db_path=db_path)
