"""Unit tests for Global Rendering Architecture, Transition Lifecycle, and State Invalidation (Phases 1-30)."""

import unittest

import streamlit as st

from frontend.components.transition import (
    render_error_boundary,
    render_screen_loader,
    render_skeleton_card,
)
from frontend.state import (
    bootstrap_authenticated_session,
    get_student_class_level,
    get_student_subject,
    get_user_role,
    init_session_state,
    invalidate_class_dependent_state,
    logout,
    navigate_to,
    set_student_class_level,
    set_student_subject,
)


class TestTransitionLifecycle(unittest.TestCase):
    """Verifies atomic authentication bootstrap, state invalidation, and smooth navigation lifecycles."""

    def setUp(self):
        st.session_state.clear()
        if hasattr(st, "query_params"):
            st.query_params.clear()
        init_session_state()

    def test_init_session_state_defaults(self):
        """Initial state contains default keys, default dark theme, and default screen."""
        self.assertEqual(st.session_state.get("current_screen"), "login")
        self.assertIsNone(st.session_state.get("user_role"))
        self.assertEqual(st.session_state.get("class_level"), 10)
        self.assertEqual(st.session_state.get("subject"), "Science")
        self.assertFalse(st.session_state.get("is_transitioning"))

    def test_atomic_auth_bootstrap_student(self):
        """Bootstrap initializes student identity, class scope, subject, and home screen atomically."""
        bootstrap_authenticated_session(
            user_id="student_123",
            role="student",
            name="Aarav Sharma",
            class_level=9,
            subject="Science",
        )

        self.assertEqual(st.session_state.get("user_role"), "student")
        self.assertEqual(st.session_state.get("user_name"), "Aarav Sharma")
        self.assertEqual(st.session_state.get("student_id"), "student_123")
        self.assertEqual(get_student_class_level(), 9)
        self.assertEqual(get_student_subject(), "Science")
        self.assertEqual(st.session_state.get("current_screen"), "home")
        self.assertEqual(st.query_params.get("uid"), "student_123")
        self.assertEqual(st.query_params.get("screen"), "home")

    def test_atomic_auth_bootstrap_teacher(self):
        """Bootstrap initializes teacher identity and routes to teacher portal."""
        bootstrap_authenticated_session(
            user_id="teacher_456",
            role="teacher",
            name="Ms. Neha",
            class_level=10,
            subject="Mathematics",
        )

        self.assertEqual(st.session_state.get("user_role"), "teacher")
        self.assertEqual(st.session_state.get("teacher_id"), "teacher_456")
        self.assertEqual(get_student_subject(), "Mathematics")
        self.assertEqual(st.session_state.get("current_screen"), "teacher")

    def test_atomic_auth_bootstrap_admin(self):
        """Bootstrap initializes admin identity and routes to admin dashboard."""
        bootstrap_authenticated_session(
            user_id="admin_789",
            role="admin",
            name="Admin User",
            class_level=9,
        )

        self.assertEqual(st.session_state.get("user_role"), "admin")
        self.assertEqual(st.session_state.get("admin_id"), "admin_789")
        self.assertEqual(get_student_class_level(), 9)
        self.assertEqual(st.session_state.get("current_screen"), "admin_home")

    def test_invalidate_class_dependent_state(self):
        """Invalidating state clears active quiz, answers, hints, and tutor cache."""
        st.session_state.current_quiz = {"questions": [1, 2, 3]}
        st.session_state.quiz_submitted = True
        st.session_state.quiz_user_answers = {"q1": "A"}
        st.session_state.socrates_active_q = 3
        st.session_state.tutor_needs_refresh = False

        invalidate_class_dependent_state()

        self.assertIsNone(st.session_state.get("current_quiz"))
        self.assertFalse(st.session_state.get("quiz_submitted"))
        self.assertEqual(st.session_state.get("quiz_user_answers"), {})
        self.assertEqual(st.session_state.get("socrates_active_q"), 1)
        self.assertTrue(st.session_state.get("tutor_needs_refresh"))

    def test_class_switch_triggers_atomic_invalidation(self):
        """Switching from Class 9 to Class 10 automatically wipes quiz state to prevent cross-class leakage."""
        set_student_class_level(9)
        st.session_state.current_quiz = {"questions": [1, 2, 3]}
        st.session_state.quiz_submitted = True

        # Change class to 10
        set_student_class_level(10)

        self.assertEqual(get_student_class_level(), 10)
        self.assertIsNone(st.session_state.get("current_quiz"))
        self.assertFalse(st.session_state.get("quiz_submitted"))

    def test_invalid_class_level_rejected(self):
        """Class levels other than 9 and 10 raise ValueError."""
        with self.assertRaises(ValueError):
            set_student_class_level(11)

    def test_subject_switch_triggers_atomic_invalidation(self):
        """Switching from Science to Mathematics wipes quiz state to prevent cross-subject leakage."""
        set_student_subject("Science")
        st.session_state.current_quiz = {"subject": "Science"}

        set_student_subject("Mathematics")

        self.assertEqual(get_student_subject(), "Mathematics")
        self.assertIsNone(st.session_state.get("current_quiz"))

    def test_navigate_to_updates_screen_and_query_params(self):
        """Navigating to a new screen updates current_screen and query_params without extra intermediate state."""
        navigate_to("quiz")
        self.assertEqual(st.session_state.get("current_screen"), "quiz")
        self.assertEqual(st.query_params.get("screen"), "quiz")

        navigate_to("tutor")
        self.assertEqual(st.session_state.get("current_screen"), "tutor")
        self.assertEqual(st.query_params.get("screen"), "tutor")
        self.assertTrue(st.session_state.get("tutor_needs_refresh"))

    def test_logout_resets_session_cleanly(self):
        """Logging out clears role and resets state to login screen."""
        bootstrap_authenticated_session(user_id="student_1", role="student")
        self.assertEqual(get_user_role(), "student")

        logout()

        self.assertIsNone(get_user_role())
        self.assertEqual(st.session_state.get("current_screen"), "login")
        self.assertNotIn("uid", st.query_params)
        self.assertNotIn("screen", st.query_params)

    def test_transition_components_render(self):
        """Verifies that transition loaders and error boundaries execute cleanly."""
        # Should not raise exception
        render_screen_loader(title="DiligentEdu", subtitle="Opening Quiz...")
        render_skeleton_card(height_px=140, count=2)
        render_error_boundary(
            title="Connection Error",
            message="Could not reach database",
            key_suffix="test_error",
        )

    def test_transition_controller_lifecycle(self):
        """Verifies TransitionController start, query, contextual messaging, and completion."""
        from frontend.components.transition import (
            MODULE_TRANSITION_MESSAGES,
            finish_transition,
            get_transition_message,
            is_transitioning,
            render_global_transition_layer,
            start_transition,
        )

        self.assertFalse(is_transitioning())

        # Start transition to Quiz
        start_transition("quiz")
        self.assertTrue(is_transitioning())
        self.assertEqual(get_transition_message(), MODULE_TRANSITION_MESSAGES["quiz"])

        # Render layer (should not error)
        render_global_transition_layer()

        # Finish transition
        finish_transition()
        self.assertFalse(is_transitioning())
        self.assertIsNone(st.session_state.get("transition_target"))

    def test_navigate_to_starts_transition_with_contextual_message(self):
        """Verifies navigate_to automatically activates the TransitionController with the proper message."""
        from frontend.components.transition import get_transition_message, is_transitioning

        navigate_to("swat")
        self.assertEqual(st.session_state.get("current_screen"), "swat")
        self.assertTrue(is_transitioning())
        self.assertEqual(get_transition_message(), "Loading your performance analytics...")

    def test_transition_controller_timeout_failsafe(self):
        """Verifies transition auto-expires after timeout to prevent hanging overlays (Phase 17)."""
        import time

        from frontend.components.transition import (
            is_transitioning,
            start_transition,
        )

        start_transition("tutor")
        self.assertTrue(is_transitioning())

        # Simulate 9 seconds elapsed
        st.session_state.transition_start_time = time.time() - 9.0
        self.assertFalse(is_transitioning())


if __name__ == "__main__":
    unittest.main()
