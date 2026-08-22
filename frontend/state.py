"""Session state initialization and helpers for Academic RAG Assistant."""

from typing import Any, Dict

import streamlit as st

from src.academic_rag.config import config

VALID_CLASS_LEVELS = (9, 10)


def init_session_state() -> None:
    """Initializes default keys in Streamlit session state."""
    defaults = {
        "theme": "Dark",
        "current_screen": "home",
        "messages": [],
        "class_level": 10,
        "selected_class": "Class 10",
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


def get_student_class_level() -> int:
    """
    Returns the student's validated single master class level (strictly 9 or 10).
    """
    raw_val = st.session_state.get("class_level")
    if raw_val in VALID_CLASS_LEVELS:
        return int(raw_val)

    # Fallback check on selected_class string
    raw_str = st.session_state.get("selected_class", "Class 10")
    if "9" in str(raw_str):
        st.session_state.class_level = 9
        st.session_state.selected_class = "Class 9"
        return 9

    st.session_state.class_level = 10
    st.session_state.selected_class = "Class 10"
    return 10


def set_student_class_level(class_level: int) -> None:
    """
    Sets and validates the student's single master class level.
    Only 9 and 10 are valid; all other values are strictly rejected.
    When the class level changes, clears active quiz and chapter state to prevent cross-class leakage (Phase 15).
    """
    if class_level not in VALID_CLASS_LEVELS:
        raise ValueError(
            f"Invalid class level {class_level!r}. Only Class 9 and Class 10 are supported."
        )
    prev_level = st.session_state.get("class_level")
    target_level = int(class_level)
    st.session_state.class_level = target_level
    st.session_state.selected_class = f"Class {target_level}"

    # Phase 15: If class level changed, reset current quiz and stale chapter selection
    if prev_level is not None and prev_level != target_level:
        st.session_state.current_quiz = None
        st.session_state.quiz_submitted = False
        st.session_state.quiz_user_answers = {}
        st.session_state.last_submission_result = None
        st.session_state.selected_chapter = "All Chapters"


def get_student_profile() -> Dict[str, Any]:
    """Returns the master student profile dictionary."""
    return {
        "student_id": st.session_state.get("student_id", "student_001"),
        "class_level": get_student_class_level(),
        "selected_chapter": st.session_state.get("selected_chapter", "All Chapters"),
        "model": st.session_state.get("model", "gemini-3.5-flash-lite"),
    }


def get_state(key: str, default: Any = None) -> Any:
    """Safely retrieves a value from session state."""
    return st.session_state.get(key, default)


def set_state(key: str, value: Any) -> None:
    """Safely sets a value in session state."""
    st.session_state[key] = value


def navigate_to(screen_name: str) -> None:
    """Navigates to a specific screen."""
    st.session_state.current_screen = screen_name
