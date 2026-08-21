#!/usr/bin/env python3
"""
Test Suite for Phase 10: Student SWAT Analysis Engine
Verifies:
1. Completely UI-independent local execution (Zero LLM calls).
2. Exact output structure of get_student_swat(student_id).
3. Chapter categorization with configurable thresholds:
   - >= 70%  -> strengths (STRONG)
   - 50-69%  -> average_topics (AVERAGE)
   - < 50%   -> weak_topics (WEAK)
4. Overall statistics (average, accuracy, quizzes_attempted, total_questions, total_correct).
5. Trend calculation (earlier average vs recent average comparison).
"""

import json
import os
import sys

# Reconfigure stdout for UTF-8
sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from quiz_storage import clear_student_history, record_quiz_attempt
from swat_analyzer import AVERAGE_THRESHOLD, STRONG_THRESHOLD, format_swat_report, get_student_swat


def run_tests():
    print("=" * 70)
    print("PHASE 10: STUDENT SWAT ANALYSIS ENGINE VERIFICATION")
    print("=" * 70)

    student_id = "student_001_p10"
    clear_student_history(student_id)

    # 1. Populate quiz history with realistic test sequence matching the prompt:
    # Quiz 1: Electricity (score: 2/5 -> 40%)
    record_quiz_attempt(
        student_id,
        {
            "class_level": 10,
            "chapter": "Electricity",
            "difficulty": "easy",
            "questions": [{"question_id": f"e1_q{i}", "correct_answer": "A"} for i in range(1, 6)],
        },
        {f"q_choice_{i}": "A" if i <= 2 else "B" for i in range(1, 6)},
    )

    # Quiz 2: Electricity (score: 3/5 -> 60%)
    record_quiz_attempt(
        student_id,
        {
            "class_level": 10,
            "chapter": "Electricity",
            "difficulty": "medium",
            "questions": [{"question_id": f"e2_q{i}", "correct_answer": "A"} for i in range(1, 6)],
        },
        {f"q_choice_{i}": "A" if i <= 3 else "B" for i in range(1, 6)},
    )

    # Quiz 3: Electricity (score: 4/5 -> 80%)
    record_quiz_attempt(
        student_id,
        {
            "class_level": 10,
            "chapter": "Electricity",
            "difficulty": "hard",
            "questions": [{"question_id": f"e3_q{i}", "correct_answer": "A"} for i in range(1, 6)],
        },
        {f"q_choice_{i}": "A" if i <= 4 else "B" for i in range(1, 6)},
    )

    # Quiz 4: Light (score: 4/5 -> 80%)
    record_quiz_attempt(
        student_id,
        {
            "class_level": 10,
            "chapter": "Light – Reflection and Refraction",
            "difficulty": "medium",
            "questions": [{"question_id": f"l1_q{i}", "correct_answer": "A"} for i in range(1, 6)],
        },
        {f"q_choice_{i}": "A" if i <= 4 else "B" for i in range(1, 6)},
    )

    # Quiz 5: Chemical Reactions (score: 5/5 -> 100%)
    record_quiz_attempt(
        student_id,
        {
            "class_level": 10,
            "chapter": "Chemical Reactions and Equations",
            "difficulty": "medium",
            "questions": [{"question_id": f"c1_q{i}", "correct_answer": "A"} for i in range(1, 6)],
        },
        {f"q_choice_{i}": "A" for i in range(1, 6)},
    )

    # Quiz 6: Magnetic Effects (score: 2/5 -> 40%)
    record_quiz_attempt(
        student_id,
        {
            "class_level": 10,
            "chapter": "Magnetic Effects of Electric Current",
            "difficulty": "hard",
            "questions": [{"question_id": f"m1_q{i}", "correct_answer": "A"} for i in range(1, 6)],
        },
        {f"q_choice_{i}": "A" if i <= 2 else "B" for i in range(1, 6)},
    )

    # 2. Call get_student_swat
    swat = get_student_swat(student_id)

    # 3. Print Structured JSON Output
    print("\n--- 1. get_student_swat(...) JSON Output ---")
    print(json.dumps(swat, indent=2))

    # 4. Print Formatted Report
    print("\n--- 2. Formatted ASCII Report ---")
    print(format_swat_report(swat))

    # 5. Assertions
    print("\n--- 3. Running Engine Assertions ---")

    # Verify overall fields
    assert "overall" in swat
    assert swat["overall"]["quizzes_attempted"] == 6
    assert swat["overall"]["total_questions"] == 30
    assert swat["overall"]["total_correct"] == 2 + 3 + 4 + 4 + 5 + 2  # 20
    assert swat["overall"]["accuracy"] == int(round((20.0 / 30.0) * 100))  # 67%
    assert swat["overall"]["average"] == int(round((40 + 60 + 80 + 80 + 100 + 40) / 6))  # 67%
    print(
        f"✓ Overall Stats Verified: Average={swat['overall']['average']}%, Accuracy={swat['overall']['accuracy']}%"
    )

    # Verify chapter categories:
    # Electricity: (40 + 60 + 80)/3 = 60% -> average_topics
    # Light: 80% -> strengths
    # Chemical Reactions: 100% -> strengths
    # Magnetic Effects: 40% -> weak_topics
    strength_names = [s["chapter"] for s in swat["strengths"]]
    avg_names = [a["chapter"] for a in swat["average_topics"]]
    weak_names = [w["chapter"] for w in swat["weak_topics"]]

    print(f"✓ Strengths (>= {STRONG_THRESHOLD}%): {strength_names}")
    print(f"✓ Average Topics ({AVERAGE_THRESHOLD}% - {STRONG_THRESHOLD-1}%): {avg_names}")
    print(f"✓ Weak Topics (< {AVERAGE_THRESHOLD}%): {weak_names}")

    assert "Chemical Reactions and Equations" in strength_names
    assert "Light – Reflection and Refraction" in strength_names
    assert "Electricity" in avg_names
    assert "Magnetic Effects of Electric Current" in weak_names

    # Verify trend:
    # First 3 quizzes: 40, 60, 80 -> mean = 60.0%
    # Last 3 quizzes: 80, 100, 40 -> mean = 73.3%
    # Trend = IMPROVING (60% -> 73%)
    assert swat["trend"]["direction"] == "improving"
    print(
        f"✓ Trend Verified: {swat['trend']['direction']} (Earlier: {swat['trend']['earlier_average']}%, Recent: {swat['trend']['recent_average']}%)"
    )

    print("\n" + "=" * 70)
    print("🎉 ALL PHASE 10 SWAT ENGINE TESTS PASSED!")
    print("=" * 70)


if __name__ == "__main__":
    run_tests()
