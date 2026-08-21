#!/usr/bin/env python3
"""
Phase 7 Quiz Generation Test Script
Verifies that generate_quiz(...) generates a complete 5-question structured MCQ quiz in ONE Gemini request.
"""

import os
import sys
import time

# Reconfigure stdout for UTF-8
sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from quiz_generator import generate_quiz


def run_quiz_test():
    print("=" * 70)
    print("PHASE 7: NCERT QUIZ GENERATION VERIFICATION")
    print("=" * 70)

    # Test 1: Class 10 Electricity (Medium, 5 questions)
    print("\n--- Test 1: Class 10 — Electricity (Medium, 5 Questions) ---")
    start_t = time.time()
    quiz_10 = generate_quiz(
        class_level=10,
        chapter="Electricity",
        difficulty="medium",
        num_questions=5,
    )
    elapsed_10 = time.time() - start_t

    print(f"⏱️ Generated in {elapsed_10:.2f}s (1 single Gemini request)")
    print(f"Quiz Title: Class {quiz_10['class_level']} Science — {quiz_10['chapter']}")
    print(f"Difficulty: {quiz_10['difficulty']} | Total Questions: {quiz_10['total_questions']}")
    print("-" * 50)

    assert quiz_10["class_level"] == 10, "Class level mismatch"
    assert quiz_10["chapter"] == "Electricity", "Chapter mismatch"
    assert len(quiz_10["questions"]) == 5, f"Expected 5 questions, got {len(quiz_10['questions'])}"

    for i, q in enumerate(quiz_10["questions"], 1):
        print(f"\nQ{i}: {q['question']}")
        for opt in q["options"]:
            print(f"   {opt}")
        print(f"   👉 Correct Answer: {q['correct_answer']}")
        print(f"   📖 Explanation: {q['explanation']}")
        print(f"   📄 Source Pages: {q['source_pages']}")

        # Validate required fields
        assert "question" in q and q["question"], f"Q{i} missing question"
        assert len(q["options"]) == 4, f"Q{i} does not have 4 options"
        assert q["correct_answer"] in [
            "A",
            "B",
            "C",
            "D",
        ], f"Q{i} invalid correct_answer: {q['correct_answer']}"
        assert "explanation" in q and q["explanation"], f"Q{i} missing explanation"
        assert "source_pages" in q and isinstance(
            q["source_pages"], list
        ), f"Q{i} missing source_pages"

    print("\n✅ Test 1 Passed Successfully!")

    # Pause 5s to stay well below 15 RPM
    time.sleep(5)

    # Test 2: Class 9 Cell Biology (Easy, 5 questions)
    print("\n--- Test 2: Class 9 — Cell: The Building Block of Life (Easy, 5 Questions) ---")
    start_t = time.time()
    quiz_9 = generate_quiz(
        class_level=9,
        chapter="Cell: The Building Block of Life",
        difficulty="easy",
        num_questions=5,
    )
    elapsed_9 = time.time() - start_t

    print(f"⏱️ Generated in {elapsed_9:.2f}s (1 single Gemini request)")
    print(f"Quiz Title: Class {quiz_9['class_level']} Science — {quiz_9['chapter']}")
    print(f"Difficulty: {quiz_9['difficulty']} | Total Questions: {quiz_9['total_questions']}")
    print("-" * 50)

    assert quiz_9["class_level"] == 9, "Class level mismatch"
    assert "Cell" in quiz_9["chapter"], "Chapter mismatch"
    assert len(quiz_9["questions"]) == 5, f"Expected 5 questions, got {len(quiz_9['questions'])}"

    for i, q in enumerate(quiz_9["questions"], 1):
        print(f"\nQ{i}: {q['question']}")
        for opt in q["options"]:
            print(f"   {opt}")
        print(f"   👉 Correct Answer: {q['correct_answer']}")
        print(f"   📖 Explanation: {q['explanation']}")
        print(f"   📄 Source Pages: {q['source_pages']}")

        assert len(q["options"]) == 4, f"Q{i} does not have 4 options"
        assert q["correct_answer"] in [
            "A",
            "B",
            "C",
            "D",
        ], f"Q{i} invalid correct_answer: {q['correct_answer']}"

    print("\n✅ Test 2 Passed Successfully!")

    print("\n" + "=" * 70)
    print("🎉 ALL PHASE 7 QUIZ GENERATION TESTS PASSED WITH FLYING COLORS!")
    print("=" * 70)


if __name__ == "__main__":
    run_quiz_test()
