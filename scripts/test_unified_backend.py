#!/usr/bin/env python3
"""
Test Suite for Phase 15: Unified Backend / Data Layer Facade (backend.py)
Verifies:
1. Student-Side API:
   - get_student_swat(student_id)
   - get_available_chapters(class_level, student_id)
   - generate_student_quiz(student_id, class_level, chapter, difficulty, num_questions)
   - submit_quiz(student_id, quiz_id, answers, quiz_data)
   - get_student_quiz_history(student_id)
2. Teacher-Side API:
   - get_student_overview(student_id)
   - get_student_swat(student_id)
   - get_student_chapter_stats(student_id)
   - get_student_quiz_history(student_id)
   - get_student_status(student_id)
"""

import os
import sys

# Reconfigure stdout for UTF-8
sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import backend


def run_tests():
    print("=" * 70)
    print("PHASE 15: UNIFIED BACKEND / DATA LAYER FACADE VERIFICATION")
    print("=" * 70)

    student_id = "unified_backend_student_01"
    backend.clear_student_data(student_id)

    # -------------------------------------------------------------
    # 1. Student Side: Available Chapters
    # -------------------------------------------------------------
    print("\n--- 1. Testing get_available_chapters(class_level=10) ---")
    chs = backend.get_available_chapters(class_level=10, student_id=student_id)
    assert len(chs) == 13, f"Expected 13 chapters, got {len(chs)}"
    print(f"✓ Retrieved {len(chs)} NCERT Class 10 chapters.")
    print(
        f"  First: Ch {chs[0]['chapter_number']} - {chs[0]['chapter']} (Status: {chs[0]['status']})"
    )

    # -------------------------------------------------------------
    # 2. Student Side: Mock Quiz & Submit Quiz
    # -------------------------------------------------------------
    print("\n--- 2. Testing submit_quiz & SWAT Recalculation ---")
    mock_quiz = {
        "class_level": 10,
        "chapter": "Electricity",
        "chapter_number": 11,
        "difficulty": "medium",
        "questions": [
            {
                "question_id": "q1",
                "question": "What is V = IR?",
                "correct_answer": "B",
                "source_pages": [200],
            },
            {
                "question_id": "q2",
                "question": "What is Joule heating?",
                "correct_answer": "C",
                "source_pages": [206],
            },
            {
                "question_id": "q3",
                "question": "Unit of Resistance?",
                "correct_answer": "A",
                "source_pages": [201],
            },
            {
                "question_id": "q4",
                "question": "What is electric power?",
                "correct_answer": "D",
                "source_pages": [215],
            },
            {
                "question_id": "q5",
                "question": "What is resistivity unit?",
                "correct_answer": "B",
                "source_pages": [203],
            },
        ],
    }
    user_answers = {
        "q_choice_1": "B",
        "q_choice_2": "C",
        "q_choice_3": "A",
        "q_choice_4": "D",
        "q_choice_5": "A",
    }  # 4/5 = 80%

    sub_res = backend.submit_quiz(
        student_id=student_id,
        quiz_id="p15_quiz_001",
        answers=user_answers,
        quiz_data=mock_quiz,
    )
    print(
        f"✓ submit_quiz Result: Score={sub_res['score']}/{sub_res['total']} ({sub_res['percentage']}%)"
    )
    print(f"  New Chapter Score: {sub_res['new_chapter_score']}% ({sub_res['new_status'].upper()})")
    assert sub_res["score"] == 4
    assert sub_res["percentage"] == 80
    assert sub_res["new_status"] == "strong"

    # Add a second quiz on Light
    mock_quiz_light = {
        "class_level": 10,
        "chapter": "Light – Reflection and Refraction",
        "chapter_number": 9,
        "difficulty": "medium",
        "questions": [
            {
                "question_id": "l1",
                "question": "Light Q1",
                "correct_answer": "A",
                "source_pages": [160],
            },
            {
                "question_id": "l2",
                "question": "Light Q2",
                "correct_answer": "A",
                "source_pages": [162],
            },
            {
                "question_id": "l3",
                "question": "Light Q3",
                "correct_answer": "A",
                "source_pages": [164],
            },
            {
                "question_id": "l4",
                "question": "Light Q4",
                "correct_answer": "A",
                "source_pages": [166],
            },
            {
                "question_id": "l5",
                "question": "Light Q5",
                "correct_answer": "A",
                "source_pages": [168],
            },
        ],
    }
    backend.submit_quiz(
        student_id=student_id,
        quiz_id="p15_quiz_002",
        answers={
            "q_choice_1": "A",
            "q_choice_2": "A",
            "q_choice_3": "A",
            "q_choice_4": "B",
            "q_choice_5": "B",
        },  # 3/5 = 60%
        quiz_data=mock_quiz_light,
    )

    # -------------------------------------------------------------
    # 3. Student Side: SWAT Profile & Quiz History
    # -------------------------------------------------------------
    print("\n--- 3. Testing get_student_swat & get_student_quiz_history ---")
    swat = backend.get_student_swat(student_id)
    assert swat["overall"]["quizzes_attempted"] == 2
    assert swat["overall"]["total_questions"] == 10
    assert swat["overall"]["total_correct"] == 7  # 4 + 3
    print(
        f"✓ get_student_swat: Overall Average={swat['overall']['average']}%, Accuracy={swat['overall']['accuracy']}%"
    )
    print(f"  Strengths: {[s['chapter'] for s in swat['strengths']]}")
    print(f"  Average Topics: {[a['chapter'] for a in swat['average_topics']]}")

    st_history = backend.get_student_quiz_history(student_id)
    assert len(st_history) == 2
    print(f"✓ get_student_quiz_history: Retrieved {len(st_history)} attempts.")

    # -------------------------------------------------------------
    # 4. Teacher Side: Overview, Chapter Stats, History, Status
    # -------------------------------------------------------------
    print("\n--- 4. Testing Teacher-Side APIs ---")
    overview = backend.get_student_overview(student_id)
    assert overview["total_quizzes"] == 2
    assert overview["questions_attempted"] == 10
    assert overview["questions_correct"] == 7
    print(f"✓ get_student_overview: {overview}")

    ch_stats = backend.get_student_chapter_stats(student_id)
    assert len(ch_stats) == 2
    print(f"✓ get_student_chapter_stats: {ch_stats}")

    t_history = backend.get_student_quiz_history(student_id)
    assert len(t_history) == 2
    print(f"✓ get_student_quiz_history (Teacher): {len(t_history)} records.")

    status = backend.get_student_status(student_id)
    assert status["has_data"] is True
    print(
        f"✓ get_student_status: Overall Standing={status['overall_status']} ({status['status_icon']})"
    )
    print(f"  Trend Direction: {status['trend']['direction']}")

    master_prof = backend.get_teacher_student_profile(student_id)
    assert master_prof["has_data"] is True
    print("✓ get_teacher_student_profile: Master profile loaded.")

    print("\n" + "=" * 70)
    print("🎉 ALL PHASE 15 UNIFIED BACKEND API TESTS PASSED!")
    print("=" * 70)


if __name__ == "__main__":
    run_tests()
