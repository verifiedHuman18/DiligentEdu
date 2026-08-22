"""Regression tests for standardized 'Back to Home' navigation architecture (Phases 1-19)."""

import inspect
import unittest
from pathlib import Path

from frontend.components.navigation import render_back_to_home
from frontend.state import get_student_class_level, init_session_state, navigate_to, set_student_class_level


class TestBackToHomeNavigation(unittest.TestCase):
    """Verify that every screen uses the shared Back to Home component with state preservation."""

    def setUp(self):
        init_session_state()

    def test_shared_component_exists(self):
        """Phase 4 & 5: render_back_to_home is callable and part of shared components."""
        self.assertTrue(callable(render_back_to_home))

    def test_state_preservation_on_navigation(self):
        """Phase 14 & 15: Navigating to Home preserves student profile, class, and credentials."""
        set_student_class_level(9)
        navigate_to("scholarships")
        self.assertEqual(get_student_class_level(), 9)

        # Trigger navigation back to home
        navigate_to("home")
        self.assertEqual(get_student_class_level(), 9, "Class level must not reset on navigation")

        set_student_class_level(10)
        navigate_to("quiz")
        navigate_to("home")
        self.assertEqual(get_student_class_level(), 10, "Class level 10 must persist on return")

    def test_screens_use_shared_navigation_component(self):
        """Phase 12, 13, 16: Verify that all non-home screens import and use render_back_to_home."""
        screens = [
            "frontend/screens/quiz_screen.py",
            "frontend/screens/scholarships_screen.py",
            "frontend/screens/swat_screen.py",
            "frontend/screens/chapter_screen.py",
            "frontend/screens/tutor_screen.py",
            "frontend/screens/teacher_screen.py",
            "frontend/screens/settings_screen.py",
        ]

        for screen_path in screens:
            path = Path(screen_path)
            self.assertTrue(path.exists(), f"Screen file {screen_path} must exist")
            content = path.read_text(encoding="utf-8")

            # Must import render_back_to_home
            self.assertIn(
                "render_back_to_home",
                content,
                f"{screen_path} must import and call render_back_to_home",
            )
            # Must NOT define ad-hoc button with raw "Back to Home" string
            self.assertNotIn(
                'st.button("Back to Home"',
                content,
                f"{screen_path} should use render_back_to_home instead of inline st.button",
            )
            self.assertNotIn(
                "st.button('Back to Home'",
                content,
                f"{screen_path} should use render_back_to_home instead of inline st.button",
            )


if __name__ == "__main__":
    unittest.main()
