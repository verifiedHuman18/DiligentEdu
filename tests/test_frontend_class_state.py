"""Unit tests for Frontend Master Class State & Quiz Chapter Isolation (Phases 1-7)."""

import unittest

import streamlit as st

from frontend.state import (
    get_student_class_level,
    get_student_profile,
    init_session_state,
    set_student_class_level,
)
from src.academic_rag.analytics.swat import get_available_chapters


class TestFrontendClassState(unittest.TestCase):
    """Verifies that master class state only allows 9 or 10, and chapters never cross-contaminate."""

    def setUp(self):
        # Reset session state dictionary for each test
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        init_session_state()

    def test_default_master_class_state(self):
        """Default class state should resolve to 10."""
        self.assertEqual(get_student_class_level(), 10)
        prof = get_student_profile()
        self.assertEqual(prof["class_level"], 10)

    def test_set_valid_class_levels(self):
        """Setting class level to 9 and 10 should succeed."""
        set_student_class_level(9)
        self.assertEqual(get_student_class_level(), 9)
        self.assertEqual(st.session_state.selected_class, "Class 9")

        set_student_class_level(10)
        self.assertEqual(get_student_class_level(), 10)
        self.assertEqual(st.session_state.selected_class, "Class 10")

    def test_reject_invalid_class_levels(self):
        """Setting invalid class levels (e.g. 11, 'Both', 0) must be rejected with ValueError."""
        with self.assertRaises(ValueError):
            set_student_class_level(11)

        with self.assertRaises(ValueError):
            set_student_class_level("Both")

        with self.assertRaises(ValueError):
            set_student_class_level(0)

    def test_quiz_chapter_strict_isolation_class_9(self):
        """When class_level == 9, only Class 9 NCERT chapters must be retrieved."""
        chs_9 = get_available_chapters(9)
        self.assertEqual(len(chs_9), 13)

        c9_titles = [c["chapter"] for c in chs_9]
        self.assertIn("Describing Motion Around Us", c9_titles)
        self.assertIn("Exploration: Entering the World of Secondary Science", c9_titles)

        # Zero Class 10 chapters
        self.assertNotIn("Electricity", c9_titles)
        self.assertNotIn("Chemical Reactions and Equations", c9_titles)
        self.assertNotIn("Light – Reflection and Refraction", c9_titles)

    def test_quiz_chapter_strict_isolation_class_10(self):
        """When class_level == 10, only Class 10 NCERT chapters must be retrieved."""
        chs_10 = get_available_chapters(10)
        self.assertEqual(len(chs_10), 13)

        c10_titles = [c["chapter"] for c in chs_10]
        self.assertIn("Electricity", c10_titles)
        self.assertIn("Chemical Reactions and Equations", c10_titles)
        self.assertIn("Light – Reflection and Refraction", c10_titles)

        # Zero Class 9 chapters
        self.assertNotIn("Describing Motion Around Us", c10_titles)
        self.assertNotIn("Exploration: Entering the World of Secondary Science", c10_titles)


if __name__ == "__main__":
    unittest.main()
