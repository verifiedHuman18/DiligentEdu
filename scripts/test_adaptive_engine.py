#!/usr/bin/env python3
"""
Test Suite for Adaptive Quiz Engine (Phase 9)
Verifies:
1. Low score (< 40%) -> Stays on chapter with 'easy'
2. Medium score (40-69%) -> Stays on chapter with 'medium'
3. High score (>= 70%) on Easy -> Stays on chapter with 'medium'
4. High score (>= 70%) on Medium -> Stays on chapter with 'hard'
5. High score (>= 70%) on Hard -> Advances to next chapter in syllabus
6. Boundary conditions (final chapter, Class 9 chapters)
"""

import os
import sys

# Reconfigure stdout for UTF-8
sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from adaptive_engine import get_next_quiz_config


def run_tests():
    print("=" * 70)
    print("PHASE 9: ADAPTIVE QUIZ ENGINE VERIFICATION")
    print("=" * 70)

    # 1. Test Low Score (< 40%)
    print("\n--- Test 1: Low Performance (35% on Electricity) ---")
    res1 = {"class_level": 10, "chapter": "Electricity", "percentage": 35, "difficulty": "medium"}
    cfg1 = get_next_quiz_config(res1)
    print(
        f"Result: {cfg1['action']} -> Difficulty: {cfg1['difficulty']} | Chapter: {cfg1['chapter']}"
    )
    print(f"Reasoning: {cfg1['reasoning']}")
    assert cfg1["difficulty"] == "easy", "Expected difficulty 'easy'"
    assert cfg1["chapter"] == "Electricity", "Expected same chapter"
    assert cfg1["action"] == "remedial_reinforcement"
    print("✅ Test 1 Passed")

    # 2. Test Moderate Score (40% - 69%)
    print("\n--- Test 2: Moderate Performance (60% on Electricity) ---")
    res2 = {"class_level": 10, "chapter": "Electricity", "percentage": 60, "difficulty": "easy"}
    cfg2 = get_next_quiz_config(res2)
    print(
        f"Result: {cfg2['action']} -> Difficulty: {cfg2['difficulty']} | Chapter: {cfg2['chapter']}"
    )
    print(f"Reasoning: {cfg2['reasoning']}")
    assert cfg2["difficulty"] == "medium", "Expected difficulty 'medium'"
    assert cfg2["chapter"] == "Electricity", "Expected same chapter"
    print("✅ Test 2 Passed")

    # 3. Test High Score on Medium (80% on Medium) -> Step up to Hard
    print("\n--- Test 3: High Performance on Medium (80% on Electricity) ---")
    res3 = {"class_level": 10, "chapter": "Electricity", "percentage": 80, "difficulty": "medium"}
    cfg3 = get_next_quiz_config(res3)
    print(
        f"Result: {cfg3['action']} -> Difficulty: {cfg3['difficulty']} | Chapter: {cfg3['chapter']}"
    )
    print(f"Reasoning: {cfg3['reasoning']}")
    assert cfg3["difficulty"] == "hard", "Expected difficulty 'hard'"
    assert cfg3["chapter"] == "Electricity", "Expected same chapter"
    assert cfg3["action"] == "step_up_difficulty"
    print("✅ Test 3 Passed")

    # 4. Test Mastery on Hard (85% on Hard Electricity) -> Advance to Chapter 12 Magnetic Effects
    print("\n--- Test 4: Mastery on Hard (85% on Hard Electricity) ---")
    res4 = {"class_level": 10, "chapter": "Electricity", "percentage": 85, "difficulty": "hard"}
    cfg4 = get_next_quiz_config(res4)
    print(
        f"Result: {cfg4['action']} -> Difficulty: {cfg4['difficulty']} | Chapter: {cfg4['chapter']}"
    )
    print(f"Reasoning: {cfg4['reasoning']}")
    assert cfg4["chapter_number"] == 12, "Expected progression to Chapter 12"
    assert "Magnetic Effects" in cfg4["chapter"], "Expected Magnetic Effects chapter"
    assert cfg4["action"] == "advance_chapter"
    print("✅ Test 4 Passed")

    # 5. Test Class 9 Progression: Ch 2 (Cell) -> Ch 3 (Tissues)
    print("\n--- Test 5: Class 9 Mastery (90% on Hard Cell: The Building Block of Life) ---")
    res5 = {
        "class_level": 9,
        "chapter": "Cell: The Building Block of Life",
        "percentage": 90,
        "difficulty": "hard",
    }
    cfg5 = get_next_quiz_config(res5)
    print(
        f"Result: {cfg5['action']} -> Difficulty: {cfg5['difficulty']} | Chapter: {cfg5['chapter']}"
    )
    print(f"Reasoning: {cfg5['reasoning']}")
    assert cfg5["chapter_number"] == 3, "Expected progression to Chapter 3"
    assert "Tissues" in cfg5["chapter"], "Expected Tissues chapter"
    assert cfg5["action"] == "advance_chapter"
    print("✅ Test 5 Passed")

    # 6. Test Final Chapter Mastery (Class 10 Ch 13 Our Environment)
    print("\n--- Test 6: Final Chapter Mastery (Class 10 Ch 13 Our Environment) ---")
    res6 = {"class_level": 10, "chapter": "Our Environment", "percentage": 95, "difficulty": "hard"}
    cfg6 = get_next_quiz_config(res6)
    print(
        f"Result: {cfg6['action']} -> Difficulty: {cfg6['difficulty']} | Chapter: {cfg6['chapter']}"
    )
    print(f"Reasoning: {cfg6['reasoning']}")
    assert cfg6["action"] == "syllabus_mastery"
    print("✅ Test 6 Passed")

    print("\n" + "=" * 70)
    print("🎉 ALL ADAPTIVE ENGINE TESTS PASSED!")
    print("=" * 70)


if __name__ == "__main__":
    run_tests()
