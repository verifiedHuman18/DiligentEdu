"""Unit tests for Phases 1 to 4: Class-Scoped Curriculum Contract & Home Screen."""

import unittest
import streamlit as st

import backend
from frontend.screens.home_screen import render_home_screen
from frontend.state import (
    init_session_state,
    set_student_class_level,
)


class TestHomeCurriculum(unittest.TestCase):
    """Verifies that get_ncert_curriculum returns strictly class-scoped chapters without leakage."""

    def setUp(self):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        init_session_state()

    def test_get_ncert_curriculum_class_9(self):
        """Phase 4: get_ncert_curriculum(9) must return only Class 9 chapters."""
        chs_9 = backend.get_ncert_curriculum(9)
        self.assertEqual(len(chs_9), 13)

        titles_9 = [c["chapter"] for c in chs_9]
        self.assertEqual(chs_9[0]["chapter_number"], 1)
        self.assertEqual(chs_9[0]["chapter"], "Exploration: Entering the World of Secondary Science")
        self.assertIn("Describing Motion Around Us", titles_9)
        self.assertIn("Cell: The Building Block of Life", titles_9)

        # Zero Class 10 chapters
        self.assertNotIn("Chemical Reactions and Equations", titles_9)
        self.assertNotIn("Electricity", titles_9)
        self.assertNotIn("Light – Reflection and Refraction", titles_9)

    def test_get_ncert_curriculum_class_10(self):
        """Phase 4: get_ncert_curriculum(10) must return only Class 10 chapters."""
        chs_10 = backend.get_ncert_curriculum(10)
        self.assertEqual(len(chs_10), 13)

        titles_10 = [c["chapter"] for c in chs_10]
        self.assertEqual(chs_10[0]["chapter_number"], 1)
        self.assertEqual(chs_10[0]["chapter"], "Chemical Reactions and Equations")
        self.assertIn("Electricity", titles_10)
        self.assertIn("Light – Reflection and Refraction", titles_10)

        # Zero Class 9 chapters
        self.assertNotIn("Exploration: Entering the World of Secondary Science", titles_10)
        self.assertNotIn("Describing Motion Around Us", titles_10)

    def test_get_ncert_curriculum_invalid_inputs(self):
        """Invalid class levels (e.g. 11, 'both', 0) must raise ValueError."""
        with self.assertRaises(ValueError):
            backend.get_ncert_curriculum(11)

        with self.assertRaises(ValueError):
            backend.get_ncert_curriculum("both")

        with self.assertRaises(ValueError):
            backend.get_ncert_curriculum(0)

    def test_home_screen_renders_for_both_classes(self):
        """Phase 2 & 3: render_home_screen executes without error for both Class 9 and Class 10."""
        set_student_class_level(9)
        # Verify render succeeds without exception
        try:
            render_home_screen()
        except Exception as e:
            self.fail(f"render_home_screen failed for Class 9: {e}")

        set_student_class_level(10)
        try:
            render_home_screen()
        except Exception as e:
            self.fail(f"render_home_screen failed for Class 10: {e}")


if __name__ == "__main__":
    unittest.main()
