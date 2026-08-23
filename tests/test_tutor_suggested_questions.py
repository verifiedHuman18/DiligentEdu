"""Unit tests for Tutor Screen Auto-Updating Suggested Questions on Navigation."""

import asyncio
import unittest
from unittest.mock import MagicMock, patch

import streamlit as st

from frontend.screens.tutor_screen import (
    CLASS_9_SUGGESTIONS,
    CLASS_10_SUGGESTIONS,
    _get_fresh_suggestions,
    render_tutor_screen,
)
from frontend.state import init_session_state, navigate_to, set_student_class_level


class TestTutorSuggestedQuestions(unittest.TestCase):
    """Verifies that tutor suggested questions rotate and auto-update upon page navigation."""

    def setUp(self):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        init_session_state()

    def test_pool_contains_rich_conceptual_questions(self):
        """Ensure both Class 9 and Class 10 pools have at least 15 comprehensive questions."""
        self.assertGreaterEqual(len(CLASS_9_SUGGESTIONS), 15)
        self.assertGreaterEqual(len(CLASS_10_SUGGESTIONS), 15)

    def test_fresh_suggestions_sampling(self):
        """_get_fresh_suggestions should return 4 distinct questions from the correct class pool."""
        c9_samples = _get_fresh_suggestions(9)
        self.assertEqual(len(c9_samples), 4)
        for label, prompt in c9_samples:
            self.assertIn((label, prompt), CLASS_9_SUGGESTIONS)

        c10_samples = _get_fresh_suggestions(10)
        self.assertEqual(len(c10_samples), 4)
        for label, prompt in c10_samples:
            self.assertIn((label, prompt), CLASS_10_SUGGESTIONS)

    def test_navigate_to_tutor_sets_refresh_flag(self):
        """Navigating to 'tutor' from another screen sets tutor_needs_refresh to True."""
        st.session_state.current_screen = "home"
        st.session_state.tutor_needs_refresh = False

        navigate_to("tutor")
        self.assertEqual(st.session_state.current_screen, "tutor")
        self.assertTrue(st.session_state.tutor_needs_refresh)

    def test_class_change_sets_refresh_flag(self):
        """Changing master class level flags tutor suggested questions for refresh."""
        set_student_class_level(10)
        st.session_state.tutor_needs_refresh = False

        set_student_class_level(9)
        self.assertTrue(st.session_state.tutor_needs_refresh)

    @patch("streamlit.button")
    @patch("streamlit.columns")
    @patch("streamlit.markdown")
    @patch("streamlit.caption")
    @patch("streamlit.write")
    def test_render_tutor_screen_auto_updates_on_navigation(
        self, mock_write, mock_caption, mock_markdown, mock_cols, mock_button
    ):
        """render_tutor_screen consumes tutor_needs_refresh and updates stored suggestions."""
        mock_col = MagicMock()
        mock_cols.return_value = [mock_col, mock_col, mock_col, mock_col]
        mock_button.return_value = False

        set_student_class_level(10)
        st.session_state.tutor_needs_refresh = True
        st.session_state.tutor_suggested_questions = None

        # First run (navigation to tutor)
        asyncio.run(render_tutor_screen("gemini-3.5-flash-lite", ""))

        first_suggestions = st.session_state.tutor_suggested_questions
        self.assertIsNotNone(first_suggestions)
        self.assertEqual(len(first_suggestions), 4)
        self.assertFalse(st.session_state.tutor_needs_refresh)
        self.assertEqual(st.session_state.tutor_suggested_class, 10)

        # Re-run on the same page (tutor_needs_refresh is False)
        asyncio.run(render_tutor_screen("gemini-3.5-flash-lite", ""))
        self.assertEqual(st.session_state.tutor_suggested_questions, first_suggestions)

        # Navigating back from home to tutor triggers refresh
        navigate_to("home")
        navigate_to("tutor")
        self.assertTrue(st.session_state.tutor_needs_refresh)


if __name__ == "__main__":
    unittest.main()
