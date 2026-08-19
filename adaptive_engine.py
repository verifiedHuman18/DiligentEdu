#!/usr/bin/env python3
"""
NCERT Science Adaptive Quiz Engine (Phase 9)
Pure rule-based deterministic progression logic.
No BKT, no mastery model, no LLM required. Zero API cost.
"""

import os
import sys
import json
import logging
from typing import Dict, Any, List, Optional, Union, Tuple

# Reconfigure stdout for UTF-8
sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
MAPPING_FILE = os.path.join(PROJECT_ROOT, "data", "metadata", "ncert_mapping.json")

logger = logging.getLogger(__name__)


def load_ncert_mapping() -> Dict[str, Any]:
    """Load NCERT chapter mapping file."""
    if os.path.exists(MAPPING_FILE):
        try:
            with open(MAPPING_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading ncert_mapping.json: {e}")
    return {}


def get_chapter_sequence(class_level: int) -> List[Dict[str, Any]]:
    """
    Returns ordered list of chapters for a given grade level (Class 9 or Class 10).
    Each entry contains: {'chapter_number': int, 'chapter': str, 'filename': str}
    """
    mapping = load_ncert_mapping()
    class_key = f"class{class_level}"
    class_map = mapping.get(class_key, {})

    chapters = []
    for fname, info in class_map.items():
        chapters.append({
            "chapter_number": int(info.get("chapter_number", 0)),
            "chapter": info.get("chapter", ""),
            "filename": fname,
        })

    chapters.sort(key=lambda x: x["chapter_number"])
    return chapters


def resolve_chapter_info(class_level: int, chapter_identifier: Union[str, int]) -> Tuple[int, str]:
    """
    Resolves chapter name or number into (chapter_number, canonical_chapter_title).
    """
    mapping = load_ncert_mapping()
    class_key = f"class{class_level}"
    class_map = mapping.get(class_key, {})

    if not class_map:
        return 1, "General Science"

    # Integer or digit string
    if isinstance(chapter_identifier, int) or (isinstance(chapter_identifier, str) and chapter_identifier.strip().isdigit()):
        target_num = int(chapter_identifier)
        for fname, info in class_map.items():
            if info.get("chapter_number") == target_num:
                return target_num, info.get("chapter")
        return 1, list(class_map.values())[0].get("chapter", "")

    # String matching
    clean_query = str(chapter_identifier).strip().lower()
    if ":" in clean_query:
        clean_query = clean_query.split(":", 1)[1].strip()
    elif "-" in clean_query:
        clean_query = clean_query.split("-", 1)[1].strip()

    for fname, info in class_map.items():
        ch_title = info.get("chapter", "")
        if clean_query == ch_title.lower() or clean_query in ch_title.lower() or ch_title.lower() in clean_query:
            return info.get("chapter_number"), ch_title

    # Fallback to first chapter if not found
    first_info = list(class_map.values())[0]
    return first_info.get("chapter_number", 1), first_info.get("chapter", "")


def get_next_chapter(class_level: int, current_chapter_num: int) -> Tuple[int, str, bool]:
    """
    Finds the next sequential chapter in the NCERT curriculum.
    Returns: (next_chapter_number, next_chapter_title, has_more_chapters)
    """
    seq = get_chapter_sequence(class_level)
    if not seq:
        return current_chapter_num, "General Science", False

    for idx, ch in enumerate(seq):
        if ch["chapter_number"] == current_chapter_num:
            if idx + 1 < len(seq):
                next_ch = seq[idx + 1]
                return next_ch["chapter_number"], next_ch["chapter"], True
            else:
                # Reached end of syllabus
                return ch["chapter_number"], ch["chapter"], False

    # Default fallback
    return seq[0]["chapter_number"], seq[0]["chapter"], True


def get_next_quiz_config(
    previous_result: Dict[str, Any],
    default_num_questions: int = 5,
) -> Dict[str, Any]:
    """
    Pure rule-based deterministic adaptive quiz engine.
    Calculates the next quiz configuration (chapter, difficulty, question count)
    based on student performance without LLM or BKT.

    Adaptive Logic:
      - percentage < 40%  -> difficulty = "easy",   stay on current chapter (remedial)
      - percentage < 70%  -> difficulty = "medium", stay on current chapter (practice)
      - percentage >= 70% ->
          - If previous difficulty was "easy"   -> difficulty = "medium", stay on current chapter
          - If previous difficulty was "medium" -> difficulty = "hard",   stay on current chapter
          - If previous difficulty was "hard"   -> difficulty = "medium", advance to next chapter

    Args:
        previous_result: Dict containing quiz results. Supported keys:
            - 'class_level': int (default: 10)
            - 'chapter': str or int (e.g. "Electricity" or 11)
            - 'percentage': float (optional, e.g. 35.0)
            - 'score' or 'correct_count': int
            - 'total_questions': int
            - 'difficulty': str ('easy', 'medium', 'hard')
            - 'num_questions': int (optional)

    Returns:
        Structured Dict:
        {
            "class_level": 10,
            "chapter": "Electricity",
            "chapter_number": 11,
            "difficulty": "easy",
            "num_questions": 5,
            "action": "remedial_reinforcement",
            "reasoning": "Score was 35% (< 40%). Recommend practicing foundational concepts on Easy difficulty."
        }
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

    # 3. Resolve canonical current chapter
    ch_num, ch_title = resolve_chapter_info(class_level, raw_chapter)

    # 4. Apply Adaptation Rules
    if percentage < 40.0:
        # Poor performance -> Stay on current chapter, lower/set to Easy
        next_difficulty = "easy"
        next_ch_num = ch_num
        next_ch_title = ch_title
        action = "remedial_reinforcement"
        reasoning = f"Score was {percentage:.0f}% (< 40%). Stay on '{ch_title}' with Easy difficulty to strengthen foundational concepts."

    elif percentage < 70.0:
        # Moderate performance -> Stay on current chapter with Medium difficulty
        next_difficulty = "medium"
        next_ch_num = ch_num
        next_ch_title = ch_title
        action = "conceptual_practice"
        reasoning = f"Score was {percentage:.0f}% (40%–69%). Stay on '{ch_title}' with Medium difficulty to reinforce conceptual understanding."

    else:
        # Good performance (>= 70%)
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
            # Already on Hard with good score (or completed current chapter) -> Progress to Next Chapter!
            adv_ch_num, adv_ch_title, has_more = get_next_chapter(class_level, ch_num)
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


if __name__ == "__main__":
    print("=== Testing Adaptive Quiz Engine ===")

    # Scenario 1: Poor performance (< 40%) -> Stay on chapter, Easy difficulty
    res1 = {"class_level": 10, "chapter": "Electricity", "percentage": 35, "difficulty": "medium"}
    cfg1 = get_next_quiz_config(res1)
    print("\nScenario 1 (35% on Electricity):")
    print(json.dumps(cfg1, indent=2))

    # Scenario 2: Moderate performance (40-69%) -> Stay on chapter, Medium difficulty
    res2 = {"class_level": 10, "chapter": "Electricity", "percentage": 60, "difficulty": "easy"}
    cfg2 = get_next_quiz_config(res2)
    print("\nScenario 2 (60% on Electricity):")
    print(json.dumps(cfg2, indent=2))

    # Scenario 3: High performance on Medium (80%) -> Stay on chapter, Hard difficulty
    res3 = {"class_level": 10, "chapter": "Electricity", "percentage": 80, "difficulty": "medium"}
    cfg3 = get_next_quiz_config(res3)
    print("\nScenario 3 (80% on Medium Electricity):")
    print(json.dumps(cfg3, indent=2))

    # Scenario 4: High performance on Hard (85%) -> Advance to Chapter 12: Magnetic Effects
    res4 = {"class_level": 10, "chapter": "Electricity", "percentage": 85, "difficulty": "hard"}
    cfg4 = get_next_quiz_config(res4)
    print("\nScenario 4 (85% on Hard Electricity):")
    print(json.dumps(cfg4, indent=2))
