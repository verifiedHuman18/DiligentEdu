"""Deterministic Adaptive Quiz Engine (Zero LLM / Zero Cost)."""

import logging
from typing import Dict, Any, Union, Tuple, List

from src.academic_rag.curriculum.service import curriculum_service

logger = logging.getLogger(__name__)


def get_next_quiz_config(
    previous_result: Dict[str, Any],
    default_num_questions: int = 5,
) -> Dict[str, Any]:
    """
    Pure rule-based deterministic adaptive quiz engine.
    Calculates next quiz configuration (chapter, difficulty, question count)
    based on student performance without LLM or BKT.

    Adaptive Logic:
      - percentage < 40%  -> difficulty = "easy",   stay on current chapter (remedial)
      - percentage < 70%  -> difficulty = "medium", stay on current chapter (practice)
      - percentage >= 70% ->
          - If previous difficulty was "easy"   -> difficulty = "medium", stay on current chapter
          - If previous difficulty was "medium" -> difficulty = "hard",   stay on current chapter
          - If previous difficulty was "hard"   -> difficulty = "medium", advance to next chapter
    """
    # 1. Extract and compute percentage
    percentage: float = 0.0
    if "percentage" in previous_result:
        percentage = float(previous_result["percentage"])
    else:
        score = previous_result.get("score", previous_result.get("correct_count", 0))
        total = previous_result.get("total_questions", default_num_questions)
        percentage = (float(score) / float(total) * 100.0) if total > 0 else 0.0

    percentage = max(0.0, min(100.0, percentage))

    # 2. Extract metadata
    class_level = int(previous_result.get("class_level", 10))
    raw_chapter = previous_result.get("chapter", "Electricity")
    prev_difficulty = str(previous_result.get("difficulty", "medium")).lower().strip()
    num_questions = int(previous_result.get("num_questions", default_num_questions))

    # 3. Resolve canonical chapter
    ch_num, ch_title = curriculum_service.resolve_chapter(class_level, raw_chapter)

    # 4. Apply Adaptation Rules
    if percentage < 40.0:
        next_difficulty = "easy"
        next_ch_num = ch_num
        next_ch_title = ch_title
        action = "remedial_reinforcement"
        reasoning = f"Score was {percentage:.0f}% (< 40%). Stay on '{ch_title}' with Easy difficulty to strengthen foundational concepts."

    elif percentage < 70.0:
        next_difficulty = "medium"
        next_ch_num = ch_num
        next_ch_title = ch_title
        action = "conceptual_practice"
        reasoning = f"Score was {percentage:.0f}% (40%–69%). Stay on '{ch_title}' with Medium difficulty to reinforce conceptual understanding."

    else:
        if prev_difficulty == "easy":
            next_difficulty = "medium"
            next_ch_num = ch_num
            next_ch_title = ch_title
            action = "step_up_difficulty"
            reasoning = f"Score was {percentage:.0f}% (≥ 70%). Stepping up from Easy to Medium difficulty on '{ch_title}'."

        elif prev_difficulty == "medium":
            next_difficulty = "hard"
            next_ch_num = ch_num
            next_ch_title = ch_title
            action = "step_up_difficulty"
            reasoning = f"Score was {percentage:.0f}% (≥ 70%). Stepping up from Medium to Hard difficulty on '{ch_title}'."

        else:
            adv_ch_num, adv_ch_title, has_more = curriculum_service.get_next_chapter(class_level, ch_num)
            if has_more:
                next_difficulty = "medium"
                next_ch_num = adv_ch_num
                next_ch_title = adv_ch_title
                action = "advance_chapter"
                reasoning = f"Mastery achieved on '{ch_title}' ({percentage:.0f}% on Hard)! Advancing to next chapter: '{adv_ch_title}'."
            else:
                next_difficulty = "hard"
                next_ch_num = ch_num
                next_ch_title = ch_title
                action = "syllabus_mastery"
                reasoning = f"Outstanding performance ({percentage:.0f}% on Hard)! You have mastered the final chapter '{ch_title}' in Class {class_level} Science."

    return {
        "class_level": class_level,
        "chapter": next_ch_title,
        "chapter_number": next_ch_num,
        "difficulty": next_difficulty,
        "num_questions": num_questions,
        "action": action,
        "reasoning": reasoning,
        "previous_performance": {
            "percentage": round(percentage, 1),
            "previous_chapter": ch_title,
            "previous_difficulty": prev_difficulty,
        },
    }
