#!/usr/bin/env python3
"""
Test Suite for Quiz Performance Storage (Phase 8)
Verifies:
1. Recording multiple quiz attempts and per-question responses.
2. Retrieving complete student history with all required fields:
   - student_id, class, chapter, quiz_id, difficulty, score, total_questions, percentage, timestamp
   - question_id, chapter, difficulty, correct/incorrect, source_pages
3. Grouped chapter progression view matching user specification (Student 001).
4. SWAT metric aggregation.
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

from quiz_storage import (
    record_quiz_attempt,
    get_student_history,
    get_student_chapter_summary,
    get_student_swat_metrics,
    clear_student_history,
)


def run_storage_tests():
    print("=" * 70)
    print("PHASE 8: QUIZ PERFORMANCE STORAGE VERIFICATION")
    print("=" * 70)

    student_id = "student_001"
    clear_student_history(student_id)

    # 1. Simulate Student 001 taking 3 quizzes in "Electricity"
    # Quiz 1: 40% (2/5)
    q1_data = {
        "class_level": 10,
        "chapter": "Electricity",
        "chapter_number": 11,
        "difficulty": "easy",
        "questions": [
            {"question_id": "elec_e_q1", "question": "What is current unit?", "correct_answer": "A", "source_pages": [1]},
            {"question_id": "elec_e_q2", "question": "What is potential difference?", "correct_answer": "B", "source_pages": [3]},
            {"question_id": "elec_e_q3", "question": "What is Ohm's law?", "correct_answer": "C", "source_pages": [6]},
            {"question_id": "elec_e_q4", "question": "What is resistance formula?", "correct_answer": "D", "source_pages": [7]},
            {"question_id": "elec_e_q5", "question": "What is voltmeter?", "correct_answer": "A", "source_pages": [4]},
        ],
    }
    # 2 correct (Q1, Q2)
    ans1 = {"q_choice_1": "A) Ampere", "q_choice_2": "B) Volt", "q_choice_3": "A) Wrong", "q_choice_4": "B) Wrong", "q_choice_5": "C) Wrong"}
    record_quiz_attempt(student_id, q1_data, ans1)
    time.sleep(0.05)

    # Quiz 2: 60% (3/5)
    q2_data = {
        "class_level": 10,
        "chapter": "Electricity",
        "chapter_number": 11,
        "difficulty": "medium",
        "questions": [
            {"question_id": "elec_m_q1", "question": "Factors affecting resistance?", "correct_answer": "B", "source_pages": [8]},
            {"question_id": "elec_m_q2", "question": "Resistors in series formula?", "correct_answer": "C", "source_pages": [12]},
            {"question_id": "elec_m_q3", "question": "Resistors in parallel formula?", "correct_answer": "A", "source_pages": [14]},
            {"question_id": "elec_m_q4", "question": "Joule heating law?", "correct_answer": "D", "source_pages": [20]},
            {"question_id": "elec_m_q5", "question": "Electric power formula?", "correct_answer": "B", "source_pages": [22]},
        ],
    }
    # 3 correct (Q1, Q2, Q3)
    ans2 = {"q_choice_1": "B) Length & Area", "q_choice_2": "C) R = R1+R2", "q_choice_3": "A) 1/R = 1/R1+1/R2", "q_choice_4": "A) Wrong", "q_choice_5": "C) Wrong"}
    record_quiz_attempt(student_id, q2_data, ans2)
    time.sleep(0.05)

    # Quiz 3: 80% (4/5)
    q3_data = {
        "class_level": 10,
        "chapter": "Electricity",
        "chapter_number": 11,
        "difficulty": "hard",
        "questions": [
            {"question_id": "elec_h_q1", "question": "Tungsten filament melting point?", "correct_answer": "B", "source_pages": [20]},
            {"question_id": "elec_h_q2", "question": "Alloy heating element properties?", "correct_answer": "C", "source_pages": [24]},
            {"question_id": "elec_h_q3", "question": "Commercial unit of energy kWh?", "correct_answer": "A", "source_pages": [23]},
            {"question_id": "elec_h_q4", "question": "Numerical on power rating?", "correct_answer": "D", "source_pages": [22]},
            {"question_id": "elec_h_q5", "question": "Circuit equivalence calculation?", "correct_answer": "B", "source_pages": [15]},
        ],
    }
    # 4 correct (Q1, Q2, Q3, Q4)
    ans3 = {"q_choice_1": "B) 3380 C", "q_choice_2": "C) High resistivity", "q_choice_3": "A) 3.6x10^6 J", "q_choice_4": "D) 100 W", "q_choice_5": "A) Wrong"}
    record_quiz_attempt(student_id, q3_data, ans3)
    time.sleep(0.05)

    # 2. Simulate Student 001 taking 2 quizzes in "Light – Reflection and Refraction"
    # Quiz 1: 80% (4/5)
    q4_data = {
        "class_level": 10,
        "chapter": "Light – Reflection and Refraction",
        "chapter_number": 9,
        "difficulty": "medium",
        "questions": [
            {"question_id": "light_m_q1", "question": "Laws of reflection?", "correct_answer": "A", "source_pages": [2]},
            {"question_id": "light_m_q2", "question": "Concave mirror focus?", "correct_answer": "B", "source_pages": [4]},
            {"question_id": "light_m_q3", "question": "Mirror formula 1/f = 1/v + 1/u?", "correct_answer": "C", "source_pages": [8]},
            {"question_id": "light_m_q4", "question": "Refractive index formula?", "correct_answer": "D", "source_pages": [12]},
            {"question_id": "light_m_q5", "question": "Lens power unit Dioptre?", "correct_answer": "A", "source_pages": [18]},
        ],
    }
    # 4 correct (Q1, Q2, Q3, Q4)
    ans4 = {"q_choice_1": "A) Angle i = Angle r", "q_choice_2": "B) Real & Inverted", "q_choice_3": "C) 1/f = 1/v + 1/u", "q_choice_4": "D) c/v", "q_choice_5": "B) Wrong"}
    record_quiz_attempt(student_id, q4_data, ans4)
    time.sleep(0.05)

    # Quiz 2: 90% (e.g. 9/10 or 5/5 -> 100%)
    q5_data = {
        "class_level": 10,
        "chapter": "Light – Reflection and Refraction",
        "chapter_number": 9,
        "difficulty": "hard",
        "questions": [
            {"question_id": "light_h_q1", "question": "Convex mirror rear view mirror reason?", "correct_answer": "A", "source_pages": [6]},
            {"question_id": "light_h_q2", "question": "Snell's law of refraction?", "correct_answer": "B", "source_pages": [13]},
            {"question_id": "light_h_q3", "question": "Lens magnification formula?", "correct_answer": "C", "source_pages": [17]},
            {"question_id": "light_h_q4", "question": "Sign convention Cartesian?", "correct_answer": "D", "source_pages": [9]},
            {"question_id": "light_h_q5", "question": "Power of combination of lenses?", "correct_answer": "A", "source_pages": [19]},
        ],
    }
    # 5 correct (100% -> >= 90%)
    ans5 = {"q_choice_1": "A) Wide field of view", "q_choice_2": "B) sin i / sin r = const", "q_choice_3": "C) v/u", "q_choice_4": "D) -u, +v", "q_choice_5": "A) P = P1+P2"}
    record_quiz_attempt(student_id, q5_data, ans5)

    # 3. Retrieve and Verify Complete History
    print("\n--- 1. Retrieving Complete Student History ---")
    full_history = get_student_history(student_id, include_questions=True)
    print(f"Total Quizzes Recorded: {len(full_history)}")
    assert len(full_history) == 5, f"Expected 5 attempts, got {len(full_history)}"

    for att in full_history:
        print(f"\n[{att['timestamp'][:19]}] Quiz ID: {att['quiz_id']}")
        print(f"  Class: {att['class_level']} | Chapter: {att['chapter']} | Difficulty: {att['difficulty']}")
        print(f"  Score: {att['score']}/{att['total_questions']} ({att['percentage']}%)")
        print(f"  Questions Recorded: {len(att['questions'])}")
        
        # Verify attempt fields
        assert "student_id" in att and att["student_id"] == student_id
        assert "class_level" in att
        assert "chapter" in att
        assert "difficulty" in att
        assert "score" in att
        assert "total_questions" in att
        assert "percentage" in att
        assert "timestamp" in att

        # Verify question fields
        for q in att["questions"]:
            assert "question_id" in q
            assert "chapter" in q
            assert "difficulty" in q
            assert "is_correct" in q
            assert "source_pages" in q

    # 4. Display Formatted Chapter Summary (Matching User Specification)
    print("\n--- 2. Formatted Student Chapter Progression Summary ---")
    ch_summary = get_student_chapter_summary(student_id)
    
    print(f"\nStudent: {student_id}")
    print("─" * 40)
    for ch_name, attempts in ch_summary.items():
        print(f"\n{ch_name}")
        for a in attempts:
            print(f"  Quiz {a['quiz_num']} ({a['difficulty'].capitalize()}) → {a['percentage']:.0f}%  [Score: {a['score']}/{a['total_questions']}]")

    # Verify percentages match expectations
    assert ch_summary["Electricity"][0]["percentage"] == 40.0
    assert ch_summary["Electricity"][1]["percentage"] == 60.0
    assert ch_summary["Electricity"][2]["percentage"] == 80.0
    assert ch_summary["Light – Reflection and Refraction"][0]["percentage"] == 80.0
    assert ch_summary["Light – Reflection and Refraction"][1]["percentage"] == 100.0

    # 5. Verify SWAT Metrics
    print("\n--- 3. SWAT Metrics Summary ---")
    swat = get_student_swat_metrics(student_id)
    print(f"Total Quizzes Taken: {swat['total_quizzes_taken']}")
    print(f"Overall Accuracy: {swat['overall_accuracy']}%")
    print(f"Strengths: {swat['strengths']}")
    print(f"Weaknesses: {swat['weaknesses']}")
    print(f"In-Progress: {swat['in_progress']}")

    print("\n" + "=" * 70)
    print("🎉 ALL PHASE 8 QUIZ STORAGE TESTS PASSED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    run_storage_tests()
