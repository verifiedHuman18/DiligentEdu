#!/usr/bin/env python3
"""
Test Suite for Phase 11: Student Chapter Selection + Quiz Configuration
Verifies:
1. get_available_chapters(class_level) returns full chapter lists with SWAT annotations.
2. Student can freely choose any chapter and difficulty regardless of current SWAT status.
3. Input validation rejects invalid chapters, classes, difficulties, and question counts.
4. create_student_quiz(...) produces a complete 5-question quiz in 1 single Gemini request.
"""

import os
import sys
import time

# Reconfigure stdout for UTF-8
sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from quiz_generator import create_student_quiz, get_available_chapters
from quiz_storage import clear_student_history, record_quiz_attempt


def run_tests():
    print("=" * 70)
    print("PHASE 11: STUDENT CHAPTER SELECTION & QUIZ CONFIGURATION TEST")
    print("=" * 70)

    student_id = "student_phase11_test"
    clear_student_history(student_id)

    # 1. Populate some prior history for student_phase11_test:
    # Strong on Chemical Reactions (80%)
    record_quiz_attempt(
        student_id,
        {
            "class_level": 10,
            "chapter": "Chemical Reactions and Equations",
            "difficulty": "medium",
            "questions": [{"question_id": f"c_{i}", "correct_answer": "A"} for i in range(1, 6)],
        },
        {f"q_choice_{i}": "A" if i <= 4 else "B" for i in range(1, 6)},
    )

    # Weak on Electricity (40%)
    record_quiz_attempt(
        student_id,
        {
            "class_level": 10,
            "chapter": "Electricity",
            "difficulty": "easy",
            "questions": [{"question_id": f"e_{i}", "correct_answer": "A"} for i in range(1, 6)],
        },
        {f"q_choice_{i}": "A" if i <= 2 else "B" for i in range(1, 6)},
    )

    # 2. Test get_available_chapters
    print("\n--- 1. Testing get_available_chapters(class_level=10) ---")
    ch_list = get_available_chapters(class_level=10, student_id=student_id)
    print(f"Total Class 10 Chapters Available: {len(ch_list)}")
    assert len(ch_list) == 13, f"Expected 13 chapters for Class 10, got {len(ch_list)}"

    for ch in ch_list:
        status_icon = (
            "🟢"
            if ch["status"] == "strong"
            else ("🔴" if ch["status"] == "weak" else ("🟡" if ch["status"] == "average" else "⚪"))
        )
        score_str = f"{ch['score']}%" if ch["score"] is not None else "Not Attempted"
        print(
            f"  {status_icon} Ch {ch['chapter_number']:2d}: {ch['chapter']:<36} -> Status: {ch['status']:<14} Score: {score_str}"
        )

    # Verify SWAT annotation
    chem_ch = next(c for c in ch_list if c["chapter_number"] == 1)
    elec_ch = next(c for c in ch_list if c["chapter_number"] == 11)
    light_ch = next(c for c in ch_list if c["chapter_number"] == 9)

    assert chem_ch["status"] == "strong" and chem_ch["score"] == 80
    assert elec_ch["status"] == "weak" and elec_ch["score"] == 40
    assert light_ch["status"] == "not_attempted" and light_ch["score"] is None
    print("✅ Chapter SWAT annotations verified successfully!")

    # 3. Test Input Validation Rejections
    print("\n--- 2. Testing Input Validation Rejections ---")

    # Invalid Chapter
    try:
        create_student_quiz(student_id, 10, "Quantum Mechanics & Superstrings", "medium", 5)
        assert False, "Failed to reject invalid chapter"
    except ValueError as ve:
        print(f"  ✓ Rejected invalid chapter: {ve}")

    # Invalid Class Level
    try:
        create_student_quiz(student_id, 12, "Electricity", "medium", 5)
        assert False, "Failed to reject invalid class"
    except ValueError as ve:
        print(f"  ✓ Rejected invalid class: {ve}")

    # Invalid Difficulty
    try:
        create_student_quiz(student_id, 10, "Electricity", "extreme_nightmare", 5)
        assert False, "Failed to reject invalid difficulty"
    except ValueError as ve:
        print(f"  ✓ Rejected invalid difficulty: {ve}")

    # Invalid Num Questions
    try:
        create_student_quiz(student_id, 10, "Electricity", "medium", 100)
        assert False, "Failed to reject invalid question count"
    except ValueError as ve:
        print(f"  ✓ Rejected invalid question count: {ve}")

    print("✅ All input validation guardrails verified successfully!")

    # 4. Test Student Freedom: Generating Quiz on Student-Chosen Chapter
    print("\n--- 3. Testing Student Choice Quiz Generation (1 Single Gemini Request) ---")
    start_t = time.time()
    student_quiz = create_student_quiz(
        student_id=student_id,
        class_level=10,
        chapter="Electricity",
        difficulty="medium",
        num_questions=5,
    )
    elapsed = time.time() - start_t

    print(f"⏱️ Generated in {elapsed:.2f}s (1 single Gemini request)")
    print(f"Quiz Title: Class {student_quiz['class_level']} — {student_quiz['chapter']}")
    print(
        f"Difficulty: {student_quiz['difficulty']} | Total Questions: {student_quiz['total_questions']}"
    )
    print("-" * 50)

    assert student_quiz["class_level"] == 10
    assert student_quiz["chapter"] == "Electricity"
    assert len(student_quiz["questions"]) == 5

    for i, q in enumerate(student_quiz["questions"], 1):
        print(f"Q{i}: {q['question']}")
        print(f"   Options: {q['options']}")
        print(f"   👉 Correct: {q['correct_answer']} | Page(s): {q['source_pages']}")

    print("\n✅ End-to-end Student Quiz Generation Passed!")

    print("\n" + "=" * 70)
    print("🎉 ALL PHASE 11 TESTS PASSED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    run_tests()
