"""Session state initialization and helpers for Academic RAG Assistant."""

from typing import Any

import streamlit as st

from src.academic_rag.config import config


def init_session_state() -> None:
    """Initializes default keys in Streamlit session state."""
    defaults = {
        "theme": "Dark",
        "current_screen": "home",
        "messages": [],
        "selected_class": "All Classes",
        "selected_chapter": "All Chapters",
        "student_id": "student_001",
        "model": config.default_llm_model
        if hasattr(config, "default_llm_model")
        else "gemini-3.5-flash-lite",
        "api_key": config.get_google_api_key() or "",
        "current_quiz": None,
        "quiz_submitted": False,
        "quiz_user_answers": {},
        "last_submission_result": None,
        "active_prompt": None,
    }

    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def get_state(key: str, default: Any = None) -> Any:
    """Safely retrieves a value from session state."""
    return st.session_state.get(key, default)


def set_state(key: str, value: Any) -> None:
    """Safely sets a value in session state."""
    st.session_state[key] = value


def navigate_to(screen_name: str) -> None:
    """Navigates to a specific screen."""
    st.session_state.current_screen = screen_name
