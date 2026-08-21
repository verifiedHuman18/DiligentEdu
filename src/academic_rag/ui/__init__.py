"""UI Package backward-compatibility layer (re-exports from frontend)."""

import os
import sys

# Ensure root is in sys.path so frontend is accessible
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from frontend import (
    inject_custom_css,
    init_session_state,
    navigate_to,
    render_navbar,
    render_header,
    render_sidebar,
    render_home_screen,
    render_tutor_screen,
    render_quiz_screen,
    render_swat_screen,
    render_teacher_screen,
    render_settings_screen,
    render_theme_switcher,
)

# Aliases for backwards compatibility
render_chat_tab = render_tutor_screen
render_quiz_tab = render_quiz_screen
render_swat_tab = render_swat_screen
render_teacher_tab = render_teacher_screen

__all__ = [
    "inject_custom_css",
    "init_session_state",
    "navigate_to",
    "render_navbar",
    "render_header",
    "render_sidebar",
    "render_theme_switcher",
    "render_home_screen",
    "render_tutor_screen",
    "render_quiz_screen",
    "render_swat_screen",
    "render_teacher_screen",
    "render_settings_screen",
    "render_chat_tab",
    "render_quiz_tab",
    "render_swat_tab",
    "render_teacher_tab",
]
