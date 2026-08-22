"""Unit tests for Role Selection & Teacher vs Student Segregation."""

import unittest

import streamlit as st

from frontend.components.navbar import render_navbar
from frontend.screens.home_screen import render_home_screen
from frontend.screens.login_screen import render_login_screen
from frontend.screens.teacher_screen import render_teacher_screen
from frontend.state import (
    get_user_role,
    init_session_state,
    logout,
    set_student_class_level,
    set_user_role,
)


class TestRoleSegregation(unittest.TestCase):
    """Tests for role-based authentication, segregation, and navigation."""

    def setUp(self):
        st.session_state.clear()
        init_session_state()

    def test_default_role_state(self):
        """Default session state has None role and 'login' screen."""
        self.assertIsNone(get_user_role())
        self.assertEqual(st.session_state.get("current_screen"), "login")

    def test_set_student_role(self):
        """Setting student role updates role and navigates to home."""
        set_user_role("student")
        self.assertEqual(get_user_role(), "student")
        self.assertEqual(st.session_state.get("current_screen"), "home")

    def test_set_teacher_role(self):
        """Setting teacher role updates role and navigates to teacher."""
        set_user_role("teacher")
        self.assertEqual(get_user_role(), "teacher")
        self.assertEqual(st.session_state.get("current_screen"), "teacher")

    def test_invalid_role_raises_value_error(self):
        """Invalid roles like 'admin' or 'guest' raise ValueError."""
        with self.assertRaises(ValueError):
            set_user_role("admin")

    def test_logout(self):
        """Logging out clears role and resets screen to login."""
        set_user_role("student")
        self.assertEqual(get_user_role(), "student")
        logout()
        self.assertIsNone(get_user_role())
        self.assertEqual(st.session_state.get("current_screen"), "login")

    def test_render_login_screen_steps(self):
        """Login screen renders Step 1 (Role Selection), Step 2A (Student Login), and Step 2B (Teacher Login)."""
        # Step 1: Role Selection
        st.session_state.login_step = "select_role"
        render_login_screen()

        # Step 2A: Student Login
        st.session_state.login_step = "student_login"
        render_login_screen()

        # Step 2B: Teacher Login
        st.session_state.login_step = "teacher_login"
        render_login_screen()

    def test_navbar_for_student_and_teacher(self):
        """Navbar renders student and teacher badges appropriately."""
        set_user_role("student")
        active = render_navbar(selected_class="Class 10", student_id="student_001")
        self.assertEqual(active, "home")

        set_user_role("teacher")
        active_t = render_navbar(selected_class="Class 10", student_id="student_001")
        self.assertEqual(active_t, "teacher")

    def test_student_home_screen_renders(self):
        """Student home screen renders smoothly."""
        set_user_role("student")
        set_student_class_level(10)
        render_home_screen(selected_class="Class 10", student_id="student_001")

    def test_teacher_screen_renders(self):
        """Teacher screen renders smoothly with student selector."""
        set_user_role("teacher")
        render_teacher_screen(student_id="student_001", selected_class="Class 10")


if __name__ == "__main__":
    unittest.main()
