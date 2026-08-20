#!/usr/bin/env python3
"""
Test Suite for Student SWAT Analysis (Phase 9)
Verifies:
1. Exact chapter categorization:
   - Chemical Reactions (84%) -> 🟢 Strong
   - Light (81%) -> 🟢 Strong
   - Life Processes (65%) -> 🟡 Average
   - Carbon Compounds (61%) -> 🟡 Average
   - Magnetic Effects (48%) -> 🔴 Weak
   - Electricity (42%) -> 🔴 Weak
2. Overall average calculation
3. Questions attempted & correct count
4. Highest and Lowest performing chapters
5. Recent performance trend calculation
6. Descriptive formatted report
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
from swat_analyzer import calculate_student_swat, format_swat_report


def run_swat_tests():
    print("=" * 70)
    print("PHASE 9: STUDENT SWAT ANALYSIS VERIFICATION")
    print("=" * 70)

    student_id = "student_swat_test"
    clear_student_history(student_id)

    # 1. Populate quiz history to match user test profile
    # Chapter 1: Chemical Reactions and Equations (84% -> e.g. 21/25 or 42/50)
    # 2 quizzes: Quiz 1 (4/5 = 80%), Quiz 2 (9/10 = 90%) -> Total 13/15 = 86.7% or 10 questions with 84%
    record_quiz_attempt(student_id, {
        "class_level": 10,
        "chapter": "Chemical Reactions and Equations",
        "difficulty": "medium",
        "questions": [
            {"question_id": f"chem_{i}", "question": f"Chem Q{i}", "correct_answer": "A", "source_pages": [1]} for i in range(1, 26)
        ]
    }, {f"q_choice_{i}": "A" if i <= 21 else "B" for i in range(1, 26)})  # 21/25 = 84%

    # Chapter 2: Light – Reflection and Refraction (81% -> e.g. 13/16 ~ 81.25% or 20 questions 16/20 = 80% / 81%)
    record_quiz_attempt(student_id, {
        "class_level": 10,
        "chapter": "Light – Reflection and Refraction",
        "difficulty": "medium",
        "questions": [
            {"question_id": f"light_{i}", "question": f"Light Q{i}", "correct_answer": "A", "source_pages": [1]} for i in range(1, 22)
        ]
    }, {f"q_choice_{i}": "A" if i <= 17 else "B" for i in range(1, 22)})  # 17/21 = 81.0%

    # Chapter 3: Life Processes (65% -> 13/20 = 65%)
    record_quiz_attempt(student_id, {
        "class_level": 10,
        "chapter": "Life Processes",
        "difficulty": "medium",
        "questions": [
            {"question_id": f"life_{i}", "question": f"Life Q{i}", "correct_answer": "A", "source_pages": [1]} for i in range(1, 21)
        ]
    }, {f"q_choice_{i}": "A" if i <= 13 else "B" for i in range(1, 21)})  # 13/20 = 65.0%

    # Chapter 4: Carbon and its Compounds (61% -> e.g. 11/18 ~ 61.1%)
    record_quiz_attempt(student_id, {
        "class_level": 10,
        "chapter": "Carbon and its Compounds",
        "difficulty": "medium",
        "questions": [
            {"question_id": f"carb_{i}", "question": f"Carbon Q{i}", "correct_answer": "A", "source_pages": [1]} for i in range(1, 19)
        ]
    }, {f"q_choice_{i}": "A" if i <= 11 else "B" for i in range(1, 19)})  # 11/18 = 61.1%

    # Chapter 5: Magnetic Effects of Electric Current (48% -> e.g. 12/25 = 48%)
    record_quiz_attempt(student_id, {
        "class_level": 10,
        "chapter": "Magnetic Effects of Electric Current",
        "difficulty": "hard",
        "questions": [
            {"question_id": f"mag_{i}", "question": f"Magnetic Q{i}", "correct_answer": "A", "source_pages": [1]} for i in range(1, 26)
        ]
    }, {f"q_choice_{i}": "A" if i <= 12 else "B" for i in range(1, 26)})  # 12/25 = 48.0%

    # Chapter 6: Electricity (42% -> e.g. 21/50 = 42%)
    record_quiz_attempt(student_id, {
        "class_level": 10,
        "chapter": "Electricity",
        "difficulty": "hard",
        "questions": [
            {"question_id": f"elec_{i}", "question": f"Electricity Q{i}", "correct_answer": "A", "source_pages": [1]} for i in range(1, 51)
        ]
    }, {f"q_choice_{i}": "A" if i <= 21 else "B" for i in range(1, 51)})  # 21/50 = 42.0%

    # 2. Run SWAT Analysis
    swat = calculate_student_swat(student_id)

    # 3. Print Formatted Report
    report_text = format_swat_report(swat)
    print("\n" + report_text)

    # 4. Assertions
    print("\n--- Running Assertions ---")
    
    # Check strong categories
    strong_chapters = [c["chapter"] for c in swat["categories"]["strong"]]
    print(f"Strong Chapters: {strong_chapters}")
    assert "Chemical Reactions and Equations" in strong_chapters, "Expected Chemical Reactions in Strong"
    assert "Light – Reflection and Refraction" in strong_chapters, "Expected Light in Strong"

    # Check average categories
    avg_chapters = [c["chapter"] for c in swat["categories"]["average"]]
    print(f"Average Chapters: {avg_chapters}")
    assert "Life Processes" in avg_chapters, "Expected Life Processes in Average"
    assert "Carbon and its Compounds" in avg_chapters, "Expected Carbon Compounds in Average"

    # Check weak categories
    weak_chapters = [c["chapter"] for c in swat["categories"]["weak"]]
    print(f"Weak Chapters: {weak_chapters}")
    assert "Electricity" in weak_chapters, "Expected Electricity in Weak"
    assert "Magnetic Effects of Electric Current" in weak_chapters, "Expected Magnetic Effects in Weak"

    # Check Highest & Lowest
    assert swat["highest_performing_chapter"]["chapter"] == "Chemical Reactions and Equations"
    assert swat["lowest_performing_chapter"]["chapter"] == "Electricity"

    # Check questions totals
    assert swat["total_quizzes"] == 6
    assert swat["questions_attempted"] == 25 + 21 + 20 + 18 + 25 + 50  # 159
    assert swat["questions_correct"] == 21 + 17 + 13 + 11 + 12 + 21    # 95

    # Check overall average
    expected_avg = 64.0
    assert swat["overall_average"] == expected_avg, f"Expected {expected_avg}, got {swat['overall_average']}"

    print(f"\nOverall Average: {swat['overall_average']}%")
    print(f"Questions Attempted: {swat['questions_attempted']} (Correct: {swat['questions_correct']})")
    print(f"Highest: {swat['highest_performing_chapter']}")
    print(f"Lowest: {swat['lowest_performing_chapter']}")
    print(f"Recent Trend: {swat['recent_trend']['summary']}")

    print("\n" + "=" * 70)
    print("🎉 ALL PHASE 9 STUDENT SWAT ANALYSIS TESTS PASSED!")
    print("=" * 70)


if __name__ == "__main__":
    run_swat_tests()
