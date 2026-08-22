"""Unit tests for Phase 12-18: Quiz State Invalidation on Class Change & Teacher View."""

import unittest
import streamlit as st

import backend
from frontend.state import (
    get_student_class_level,
    init_session_state,
    set_student_class_level,
)


class TestClassStateInvalidation(unittest.TestCase):
    """
    Verifies that changing the master class level invalidates any active quiz session,
    resets chapter selection to prevent cross-class leakage, and validates teacher isolation.
    """

    def setUp(self):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        init_session_state()

    def test_quiz_state_invalidation_on_class_change(self):
        """Phase 14 & 15: Changing class level clears active quiz, answers, and chapter selection."""
        # 1. Start with Class 10 and populate mock quiz state
        set_student_class_level(10)
        st.session_state.current_quiz = {
            "quiz_id": "q_class10_elec",
            "class_level": 10,
            "chapter": "Electricity",
            "questions": [{"question_id": "q1", "question": "What is Ohm's law?"}],
        }
        st.session_state.quiz_submitted = True
        st.session_state.quiz_user_answers = {"q1": "A"}
        st.session_state.last_submission_result = {"score": 100}
        st.session_state.selected_chapter = "Electricity"

        # Verify state is populated
        self.assertIsNotNone(st.session_state.current_quiz)
        self.assertTrue(st.session_state.quiz_submitted)
        self.assertEqual(st.session_state.selected_chapter, "Electricity")

        # 2. Switch master profile standard from Class 10 to Class 9
        set_student_class_level(9)

        # 3. Assert full invalidation occurred
        self.assertEqual(get_student_class_level(), 9)
        self.assertIsNone(st.session_state.current_quiz)
        self.assertFalse(st.session_state.quiz_submitted)
        self.assertEqual(st.session_state.quiz_user_answers, {})
        self.assertIsNone(st.session_state.last_submission_result)
        self.assertEqual(st.session_state.selected_chapter, "All Chapters")

    def test_reasserting_same_class_level_does_not_clear_quiz(self):
        """Setting the same class level (e.g. 10 -> 10) does not clear in-progress quiz."""
        set_student_class_level(10)
        st.session_state.current_quiz = {"quiz_id": "q_active_10"}
        st.session_state.selected_chapter = "Electricity"

        # Reassert Class 10
        set_student_class_level(10)

        # In-progress quiz remains intact
        self.assertIsNotNone(st.session_state.current_quiz)
        self.assertEqual(st.session_state.selected_chapter, "Electricity")

    def test_strict_teacher_binary_view(self):
        """Phase 17: Teacher view contracts strictly support only class_level 9 or 10."""
        # Querying with valid class levels should not raise error
        overview_9 = backend.get_teacher_student_overview("student_001", class_level=9)
        self.assertIn("student_id", overview_9)
        self.assertEqual(overview_9.get("class_level"), 9)

        overview_10 = backend.get_teacher_student_overview("student_001", class_level=10)
        self.assertIn("student_id", overview_10)
        self.assertEqual(overview_10.get("class_level"), 10)


if __name__ == "__main__":
    unittest.main()
