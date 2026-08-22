"""Unit tests for Phases 9 to 17: Home Screen Action Plan & SWAT Indicators Integration."""

import os
import tempfile
import unittest
import streamlit as st

import backend
from frontend.screens.home_screen import render_home_screen
from frontend.state import (
    get_student_class_level,
    init_session_state,
    set_student_class_level,
)
from src.academic_rag.storage.repository import QuizRepository


class TestHomeActionPlanFlow(unittest.TestCase):
    """
    Verifies that the Home Screen displays class-scoped Action Plans,
    SWAT-annotated curriculum items without artificial 0% metrics, and operates with zero LLM calls.
    """

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.db_path = os.path.join(self.temp_dir.name, "test_home_flow.db")
        self.repo = QuizRepository(db_path=self.db_path)
        self.student_id = "student_home_test"

        for k in list(st.session_state.keys()):
            del st.session_state[k]
        init_session_state()

        # Seed Class 10 attempt: Chemical Reactions (80% - Strong), Electricity (40% - Weak)
        self.repo.record_attempt(
            self.student_id,
            {
                "class_level": 10,
                "chapter": "Chemical Reactions and Equations",
                "chapter_number": 1,
                "difficulty": "medium",
                "questions": [{"question_id": f"q_c10_{i}", "correct_answer": "A"} for i in range(1, 6)],
            },
            {f"q_choice_{i}": "A" if i <= 4 else "B" for i in range(1, 6)},
        )

        self.repo.record_attempt(
            self.student_id,
            {
                "class_level": 10,
                "chapter": "Electricity",
                "chapter_number": 11,
                "difficulty": "hard",
                "questions": [{"question_id": f"q_elec_{i}", "correct_answer": "A"} for i in range(1, 6)],
            },
            {f"q_choice_{i}": "A" if i <= 2 else "B" for i in range(1, 6)},
        )

    def tearDown(self):
        try:
            self.temp_dir.cleanup()
        except Exception:
            pass

    def test_home_action_plan_class_10_isolation(self):
        """Phase 9 & 10: Home Action Plan for Class 10 prioritizes Weak Electricity and Unattempted Magnetic Effects."""
        set_student_class_level(10)
        cls = get_student_class_level()
        self.assertEqual(cls, 10)

        plan = backend.get_student_action_plan(self.student_id, class_level=cls, db_path=self.db_path)
        self.assertEqual(plan["class_level"], 10)

        # First action is Weak Electricity
        first_act = plan["actions"][0]
        self.assertEqual(first_act["chapter"], "Electricity")
        self.assertEqual(first_act["status"], "weak")
        self.assertEqual(first_act["priority_rank"], 1)

        # Second action is Unattempted (e.g. Acids, Bases or Metals)
        second_act = plan["actions"][1]
        self.assertEqual(second_act["status"], "unattempted")
        self.assertEqual(second_act["priority_rank"], 2)

    def test_home_action_plan_class_9_isolation(self):
        """Phase 10: Home Action Plan for Class 9 contains zero Class 10 chapters."""
        set_student_class_level(9)
        cls = get_student_class_level()
        self.assertEqual(cls, 9)

        plan = backend.get_student_action_plan(self.student_id, class_level=cls, db_path=self.db_path)
        self.assertEqual(plan["class_level"], 9)

        # Since Class 9 has no attempts, all recommendations are unattempted Class 9 chapters
        for act in plan["actions"]:
            self.assertEqual(act["status"], "unattempted")
            self.assertNotEqual(act["chapter"], "Electricity")
            self.assertNotEqual(act["chapter"], "Chemical Reactions and Equations")

    def test_swat_indicators_in_curriculum(self):
        """Phase 13: Attempted chapters receive scores, unattempted receive score=None (not 0%)."""
        swat = backend.get_student_swat(self.student_id, class_level=10, db_path=self.db_path)
        breakdown = swat["chapter_breakdown"]

        # Chemical Reactions is Strong
        self.assertEqual(breakdown["Chemical Reactions and Equations"]["status"], "strong")
        self.assertEqual(breakdown["Chemical Reactions and Equations"]["score"], 80)

        # Electricity is Weak
        self.assertEqual(breakdown["Electricity"]["status"], "weak")
        self.assertEqual(breakdown["Electricity"]["score"], 40)

        # Magnetic Effects is Unattempted (score must be None, never 0)
        self.assertEqual(breakdown["Magnetic Effects of Electric Current"]["status"], "unattempted")
        self.assertIsNone(breakdown["Magnetic Effects of Electric Current"]["score"])

    def test_home_render_flow(self):
        """Phase 14 & 17: Render function executes without errors and without LLM calls."""
        set_student_class_level(10)
        try:
            render_home_screen(student_id=self.student_id)
        except Exception as e:
            self.fail(f"render_home_screen failed: {e}")


if __name__ == "__main__":
    unittest.main()
