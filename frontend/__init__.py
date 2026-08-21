"""Frontend package for NCERT Academic Science Assistant."""

from frontend.components import (
    get_status_badge_html,
    render_citation_box,
    render_header,
    render_metric_card,
    render_navbar,
    render_sidebar,
    render_theme_switcher,
)
from frontend.screens import (
    render_home_screen,
    render_quiz_screen,
    render_settings_screen,
    render_swat_screen,
    render_teacher_screen,
    render_tutor_screen,
)
from frontend.state import get_state, init_session_state, navigate_to, set_state
from frontend.styles import THEMES, get_current_theme, inject_custom_css

__all__ = [
    "inject_custom_css",
    "get_current_theme",
    "THEMES",
    "init_session_state",
    "get_state",
    "set_state",
    "navigate_to",
    "render_navbar",
    "render_header",
    "render_sidebar",
    "render_theme_switcher",
    "render_metric_card",
    "render_citation_box",
    "get_status_badge_html",
    "render_home_screen",
    "render_tutor_screen",
    "render_quiz_screen",
    "render_swat_screen",
    "render_teacher_screen",
    "render_settings_screen",
]
