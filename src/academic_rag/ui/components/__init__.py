"""UI Components package."""

from src.academic_rag.ui.components.sidebar import render_sidebar
from src.academic_rag.ui.components.chat_tab import render_chat_tab
from src.academic_rag.ui.components.quiz_tab import render_quiz_tab
from src.academic_rag.ui.components.swat_tab import render_swat_tab
from src.academic_rag.ui.components.teacher_tab import render_teacher_tab

__all__ = [
    "render_sidebar",
    "render_chat_tab",
    "render_quiz_tab",
    "render_swat_tab",
    "render_teacher_tab",
]
