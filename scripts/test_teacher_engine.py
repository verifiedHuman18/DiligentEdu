#!/usr/bin/env python3
"""
Test Suite for Phases 13 & 14: Teacher Analytics & Early-Warning Engine
Verifies:
1. Phase 13 Teacher Analytics:
   - get_teacher_student_overview(...)
   - get_teacher_chapter_statistics(...)
   - get_teacher_quiz_history(...)
   - get_teacher_swat_summary(...)
2. Phase 14 Early-Warning Rules:
   - 14.1 Overall status (Performing Well 🟢, Monitor 🟡, Needs Attention 🔴)
   - 14.2 Weak-topic flags for chapters < 50% (e.g. Electricity -> 42%)
   - 14.3 Declining trend alerts (e.g. 80% -> 70% -> 58% -> 45%)
   - 14.4 Improving trend protection (e.g. 35% -> 48% -> 61% -> 72%)
"""

import os
import sys
import json
import time

# Reconfigure stdout for UTF-8
sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from quiz_storage import record_quiz_attempt, clear_student_history
from teacher_engine import (
    get_teacher_student_overview,
    get_teacher_chapter_statistics,
    get_teacher_quiz_history,
    get_teacher_swat_summary,
    get_student_status,
    get_teacher_student_profile,
)


def run_tests():
    print("=" * 70)
    print("PHASES 13 & 14: TEACHER ANALYTICS & EARLY-WARNING ENGINE TESTS")
    print("=" * 70)

    # -------------------------------------------------------------
    # Test 1: Standard Student Overview & Analytics (Phase 13)
    # -------------------------------------------------------------
    print("\n--- 1. Testing Phase 13 Teacher Analytics Engine ---")
    student_id = "teacher_test_student_01"
    clear_student_history(student_id)

    # 4 attempts across Electricity and Light
    record_quiz_attempt(student_id, {
        "class_level": 10,
        "chapter": "Electricity",
        "difficulty": "easy",
        "questions": [{"question_id": f"q_{i}", "correct_answer": "A"} for i in range(1, 6)]
    }, {f"q_choice_{i}": "A" if i <= 2 else "B" for i in range(1, 6)})  # 2/5 = 40%

    record_quiz_attempt(student_id, {
        "class_level": 10,
        "chapter": "Light – Reflection and Refraction",
        "difficulty": "medium",
        "questions": [{"question_id": f"q_{i}", "correct_answer": "A"} for i in range(1, 6)]
    }, {f"q_choice_{i}": "A" if i <= 4 else "B" for i in range(1, 6)})  # 4/5 = 80%

    record_quiz_attempt(student_id, {
        "class_level": 10,
        "chapter": "Electricity",
        "difficulty": "medium",
        "questions": [{"question_id": f"q_{i}", "correct_answer": "A"} for i in range(1, 6)]
    }, {f"q_choice_{i}": "A" if i <= 3 else "B" for i in range(1, 6)})  # 3/5 = 60%

    record_quiz_attempt(student_id, {
        "class_level": 10,
        "chapter": "Electricity",
        "difficulty": "hard",
        "questions": [{"question_id": f"q_{i}", "correct_answer": "A"} for i in range(1, 6)]
    }, {f"q_choice_{i}": "A" if i <= 4 else "B" for i in range(1, 6)})  # 4/5 = 80%

    # 13.1 Overview
    overview = get_teacher_student_overview(student_id)
    print("\n[13.1 Student Overview]:")
    print(json.dumps(overview, indent=2))
    assert overview["total_quizzes"] == 4
    assert overview["questions_attempted"] == 20
    assert overview["questions_correct"] == 2 + 4 + 3 + 4  # 13
    assert overview["overall_average"] == int(round((40 + 80 + 60 + 80) / 4))  # 65%

    # 13.2 Chapter Statistics
    ch_stats = get_teacher_chapter_statistics(student_id)
    print("\n[13.2 Chapter Statistics]:")
    print(json.dumps(ch_stats, indent=2))
    assert len(ch_stats) == 2
    elec_stat = next(c for c in ch_stats if c["chapter"] == "Electricity")
    assert elec_stat["attempts"] == 3
    assert elec_stat["average"] == int(round((40 + 60 + 80) / 3))  # 60%

    # 13.3 Quiz History
    history = get_teacher_quiz_history(student_id)
    print("\n[13.3 Quiz History]:")
    for row in history:
        print(f"  {row['date']:<8} | {row['chapter']:<34} | {row['difficulty']:<8} | {row['score_display']}")
    assert len(history) == 4

    # 13.4 SWAT Summary
    swat_sum = get_teacher_swat_summary(student_id)
    print("\n[13.4 SWAT Summary]:")
    print(json.dumps(swat_sum, indent=2))
    assert len(swat_sum["strengths"]) >= 1

    print("\n✅ Phase 13 Teacher Analytics Engine Verified!")

    # -------------------------------------------------------------
    # Test 2: Declining Trend Alert (Phase 14.3)
    # -------------------------------------------------------------
    print("\n--- 2. Testing Phase 14.3 Declining Trend Alert ---")
    declining_student = "declining_student_01"
    clear_student_history(declining_student)

    # Scores: 80% -> 70% -> 58% -> 45%
    for ch_name, score_num in [("Chemical Reactions", 4), ("Light", 3), ("Life Processes", 3), ("Electricity", 2)]:
        record_quiz_attempt(declining_student, {
            "class_level": 10,
            "chapter": ch_name,
            "difficulty": "medium",
            "questions": [{"question_id": f"q_{i}", "correct_answer": "A"} for i in range(1, 6)]
        }, {f"q_choice_{i}": "A" if i <= score_num else "B" for i in range(1, 6)})

    dec_status = get_student_status(declining_student)
    print("\n[Declining Student Status Result]:")
    print(json.dumps(dec_status, indent=2))

    assert dec_status["trend"]["direction"] == "declining"
    assert dec_status["trend"]["alert"] is True
    assert any("declining" in str(a["message"]).lower() for a in dec_status["alerts"])
    print("✅ Declining Trend Alert correctly triggered!")

    # -------------------------------------------------------------
    # Test 3: Weak-Topic Flag (Phase 14.2)
    # -------------------------------------------------------------
    print("\n--- 3. Testing Phase 14.2 Weak-Topic Flag (< 50%) ---")
    weak_student = "weak_topic_student_01"
    clear_student_history(weak_student)

    # Electricity = 40% (< 50%)
    record_quiz_attempt(weak_student, {
        "class_level": 10,
        "chapter": "Electricity",
        "difficulty": "medium",
        "questions": [{"question_id": f"q_{i}", "correct_answer": "A"} for i in range(1, 6)]
    }, {f"q_choice_{i}": "A" if i <= 2 else "B" for i in range(1, 6)})

    weak_status = get_student_status(weak_student)
    print("\n[Weak Topic Status Result]:")
    print(json.dumps(weak_status, indent=2))

    assert "Electricity" in weak_status["weak_topics"]
    assert any(a.get("chapter") == "Electricity" for a in weak_status["alerts"])
    print("✅ Weak-Topic Flag for Electricity (<50%) correctly raised!")

    # -------------------------------------------------------------
    # Test 4: Improving Trend Protection (Phase 14.4)
    # -------------------------------------------------------------
    print("\n--- 4. Testing Phase 14.4 Improving Trend Protection ---")
    improving_student = "improving_student_01"
    clear_student_history(improving_student)

    # Scores: 35% -> 48% -> 61% -> 72%
    # (e.g. 1/5=20%, 2/5=40%, 3/5=60%, 4/5=80%)
    for score_num in [1, 2, 3, 4]:
        record_quiz_attempt(improving_student, {
            "class_level": 10,
            "chapter": "Electricity",
            "difficulty": "medium",
            "questions": [{"question_id": f"q_{i}", "correct_answer": "A"} for i in range(1, 6)]
        }, {f"q_choice_{i}": "A" if i <= score_num else "B" for i in range(1, 6)})

    imp_status = get_student_status(improving_student)
    print("\n[Improving Student Status Result]:")
    print(json.dumps(imp_status, indent=2))

    assert imp_status["trend"]["direction"] == "improving"
    assert imp_status["trend"]["alert"] is False
    assert len(imp_status["positive_notes"]) > 0
    assert "Improving" in imp_status["overall_status"]
    print("✅ Improving student correctly identified and protected from at-risk flagging!")

    # -------------------------------------------------------------
    # Test 5: Full Master Profile (Phases 13 & 14 Unified)
    # -------------------------------------------------------------
    print("\n--- 5. Testing Unified Master Profile ---")
    master_prof = get_teacher_student_profile(student_id)
    assert "overview" in master_prof
    assert "chapter_statistics" in master_prof
    assert "quiz_history" in master_prof
    assert "swat_summary" in master_prof
    assert "status" in master_prof
    print("✅ Full Unified Teacher Profile verified successfully!")

    print("\n" + "=" * 70)
    print("🎉 ALL PHASES 13 & 14 TEACHER ENGINE TESTS PASSED!")
    print("=" * 70)


if __name__ == "__main__":
    run_tests()
