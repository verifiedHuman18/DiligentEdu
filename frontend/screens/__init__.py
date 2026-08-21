"""Screens package exports."""

from frontend.screens.home_screen import render_home_screen
from frontend.screens.tutor_screen import render_tutor_screen
from frontend.screens.quiz_screen import render_quiz_screen
from frontend.screens.swat_screen import render_swat_screen
from frontend.screens.teacher_screen import render_teacher_screen
from frontend.screens.settings_screen import render_settings_screen

__all__ = [
    "render_home_screen",
    "render_tutor_screen",
    "render_quiz_screen",
    "render_swat_screen",
    "render_teacher_screen",
    "render_settings_screen",
]
