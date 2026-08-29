"""UI Components package."""

from backend.ui.components.chat_tab import render_chat_tab
from backend.ui.components.quiz_tab import render_quiz_tab
from backend.ui.components.swat_tab import render_swat_tab
from backend.ui.components.teacher_tab import render_teacher_tab

__all__ = [
    "render_chat_tab",
    "render_quiz_tab",
    "render_swat_tab",
    "render_teacher_tab",
]
