"""Streamlit session state management and initialization."""

import streamlit as st

from backend.config import config


def init_session_state() -> None:
    """Initializes default keys in Streamlit session state."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "selected_class" not in st.session_state:
        st.session_state.selected_class = "All Classes"
    if "student_id" not in st.session_state:
        st.session_state.student_id = "student_001"
    if "model" not in st.session_state:
        st.session_state.model = config.default_llm_model
    if "user_gemini_api_key" not in st.session_state:
        st.session_state.user_gemini_api_key = None
    if "current_quiz" not in st.session_state:
        st.session_state.current_quiz = None
    if "quiz_submitted" not in st.session_state:
        st.session_state.quiz_submitted = False
    if "quiz_user_answers" not in st.session_state:
        st.session_state.quiz_user_answers = {}
    if "last_submission_result" not in st.session_state:
        st.session_state.last_submission_result = None
