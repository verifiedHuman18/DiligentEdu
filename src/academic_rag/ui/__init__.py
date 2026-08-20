"""UI Package."""

from src.academic_rag.ui.styles import inject_custom_css
from src.academic_rag.ui.state import init_session_state
from src.academic_rag.ui.components import (
    render_sidebar,
    render_chat_tab,
    render_quiz_tab,
    render_swat_tab,
    render_teacher_tab,
)

__all__ = [
    "inject_custom_css",
    "init_session_state",
    "render_sidebar",
    "render_chat_tab",
    "render_quiz_tab",
    "render_swat_tab",
    "render_teacher_tab",
]
