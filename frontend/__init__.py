"""Frontend package for NCERT Academic Science Assistant."""

from frontend.styles import inject_custom_css, get_current_theme, THEMES
from frontend.state import init_session_state, get_state, set_state
from frontend.components import (
    render_header,
    render_sidebar,
    render_theme_switcher,
    render_metric_card,
    render_citation_box,
    get_status_badge_html,
)
from frontend.screens import (
    render_tutor_screen,
    render_quiz_screen,
    render_swat_screen,
    render_teacher_screen,
)

__all__ = [
    "inject_custom_css",
    "get_current_theme",
    "THEMES",
    "init_session_state",
    "get_state",
    "set_state",
    "render_header",
    "render_sidebar",
    "render_theme_switcher",
    "render_metric_card",
    "render_citation_box",
    "get_status_badge_html",
    "render_tutor_screen",
    "render_quiz_screen",
    "render_swat_screen",
    "render_teacher_screen",
]
