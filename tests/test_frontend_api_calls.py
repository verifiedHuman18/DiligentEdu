"""Unit tests for Phase 8, 9, 10 & 11: Master Profile Class Binding across all Frontend APIs."""

import os
import tempfile
import unittest

import streamlit as st

import backend
from backend.storage.repository import QuizRepository
from frontend.state import (
    get_student_class_level,
    init_session_state,
    set_student_class_level,
)


class TestFrontendApiCalls(unittest.TestCase):
    """
    Verifies that all frontend components bind directly to the master profile's class_level
    and that API calls (SWAT, Action Plan, Chapters, RAG) operate with strict class isolation.
    """

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.db_path = os.path.join(self.temp_dir.name, "test_frontend_api_calls.db")
        self.repo = QuizRepository(db_path=self.db_path)
        self.student_id = "student_frontend_test"

        # Clear session state
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        init_session_state()

        # Record Class 9 attempt: Matter (80%)
        self.repo.record_attempt(
            self.student_id,
            {
                "class_level": 9,
                "chapter": "Describing Motion Around Us",
                "chapter_number": 4,
                "difficulty": "medium",
                "questions": [
                    {"question_id": f"c9_{i}", "correct_answer": "A"} for i in range(1, 6)
                ],
            },
            {f"q_choice_{i}": "A" if i <= 4 else "B" for i in range(1, 6)},
        )

        # Record Class 10 attempt: Electricity (40%)
        self.repo.record_attempt(
            self.student_id,
            {
                "class_level": 10,
                "chapter": "Electricity",
                "chapter_number": 11,
                "difficulty": "hard",
                "questions": [
                    {"question_id": f"c10_{i}", "correct_answer": "A"} for i in range(1, 6)
                ],
            },
            {f"q_choice_{i}": "A" if i <= 2 else "B" for i in range(1, 6)},
        )

    def tearDown(self):
        try:
            self.temp_dir.cleanup()
        except Exception:
            pass

    def test_swat_and_action_plan_master_class_binding_class_10(self):
        """Phase 8 & 9: When profile standard is Class 10, SWAT and Action Plan evaluate Class 10."""
        set_student_class_level(10)
        cls = get_student_class_level()
        self.assertEqual(cls, 10)

        # 1. SWAT call
        swat = backend.get_student_swat(self.student_id, class_level=cls, db_path=self.db_path)
        self.assertEqual(swat["class_level"], 10)
        ch_names = list(swat["chapter_breakdown"].keys())
        self.assertIn("Electricity", ch_names)
        self.assertNotIn("Describing Motion Around Us", ch_names)

        # 2. Action Plan call
        plan = backend.get_student_action_plan(
            self.student_id, class_level=cls, db_path=self.db_path
        )
        self.assertEqual(plan["class_level"], 10)
        self.assertEqual(plan["actions"][0]["chapter"], "Electricity")
        self.assertEqual(plan["actions"][0]["status"], "weak")

    def test_swat_and_action_plan_master_class_binding_class_9(self):
        """Phase 8 & 9: When profile standard is Class 9, SWAT and Action Plan evaluate Class 9."""
        set_student_class_level(9)
        cls = get_student_class_level()
        self.assertEqual(cls, 9)

        # 1. SWAT call
        swat = backend.get_student_swat(self.student_id, class_level=cls, db_path=self.db_path)
        self.assertEqual(swat["class_level"], 9)
        ch_names = list(swat["chapter_breakdown"].keys())
        self.assertIn("Describing Motion Around Us", ch_names)
        self.assertNotIn("Electricity", ch_names)

        # 2. Action Plan call
        plan = backend.get_student_action_plan(
            self.student_id, class_level=cls, db_path=self.db_path
        )
        self.assertEqual(plan["class_level"], 9)
        # Unattempted chapters are Priority 2, strong chapter is Priority 4
        self.assertEqual(plan["actions"][0]["status"], "unattempted")
        self.assertEqual(plan["actions"][-1]["chapter"], "Describing Motion Around Us")
        self.assertEqual(plan["actions"][-1]["status"], "strong")

    def test_frontend_api_class_propagation(self):
        """Phase 11: Verify backend functions accept class_level explicitly."""
        # get_chapters_with_status
        chs_9 = backend.get_chapters_with_status(
            self.student_id, class_level=9, db_path=self.db_path
        )
        self.assertEqual(len(chs_9), 13)

        chs_10 = backend.get_chapters_with_status(
            self.student_id, class_level=10, db_path=self.db_path
        )
        self.assertEqual(len(chs_10), 13)


if __name__ == "__main__":
    unittest.main()
