"""Session state initialization and helpers for DiligentEdu."""

from typing import Any, Dict, Optional

import streamlit as st

from backend.config import config

VALID_CLASS_LEVELS = (9, 10)
VALID_SUBJECTS = ("Science", "Mathematics")


def init_session_state() -> None:
    """Initializes default keys in Streamlit session state."""
    defaults = {
        "theme": "Dark",
        "user_role": None,
        "login_step": "select_role",
        "teacher_id": "teacher_001",
        "current_screen": "login",
        "is_transitioning": False,
        "transition_target": None,
        "messages": [],
        "class_level": 10,
        "selected_class": "Class 10",
        "subject": "Science",
        "selected_subject": "Science",
        "student_id": "student_001",
        "model": config.default_llm_model
        if hasattr(config, "default_llm_model")
        else "gemini-3.5-flash-lite",
        "user_gemini_api_key": None,
        "current_quiz": None,
        "quiz_submitted": False,
        "quiz_user_answers": {},
        "last_submission_result": None,
        "active_prompt": None,
        "quiz_mode": "socrates",
        "socrates_active_q": 1,
        "socrates_hints_revealed": {},
        "socrates_chat_history": {},
        "socrates_attempts": {},
        "socrates_completed": False,
        "tutor_needs_refresh": True,
        "tutor_suggested_questions": None,
        "tutor_suggested_class": None,
        "tutor_input_mode": "keyboard",
        "voice_transcript": "",
        "voice_recording_state": "IDLE",
        "voice_review_pending": False,
    }

    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def invalidate_class_dependent_state() -> None:
    """
    Atomically clears all class/subject-dependent state (quizzes, hints, chat history, suggestions)
    to prevent cross-class or cross-subject leakage during transitions (Phases 12 & 15).
    """
    st.session_state.current_quiz = None
    st.session_state.quiz_submitted = False
    st.session_state.quiz_user_answers = {}
    st.session_state.last_submission_result = None
    st.session_state.socrates_active_q = 1
    st.session_state.socrates_hints_revealed = {}
    st.session_state.socrates_chat_history = {}
    st.session_state.socrates_attempts = {}
    st.session_state.socrates_completed = False
    st.session_state.tutor_needs_refresh = True
    st.session_state.tutor_suggested_questions = None
    st.session_state.messages = []


def bootstrap_authenticated_session(
    user_id: str,
    role: str,
    name: Optional[str] = None,
    class_level: Optional[int] = 10,
    subject: Optional[str] = "Science",
    restore_screen: bool = False,
) -> None:
    """
    Atomically initializes all authentication, role, class scope, and identity state
    before the authenticated application shell renders (Phases 10 & 11).
    """
    st.session_state.user_role = role
    st.session_state.user_name = name or user_id

    # Resolve class scope
    cls_int = class_level if class_level in VALID_CLASS_LEVELS else 10
    st.session_state.class_level = cls_int
    st.session_state.selected_class = f"Class {cls_int}"

    # Resolve subject
    target_subj = "Mathematics" if subject and "math" in str(subject).lower() else "Science"
    st.session_state.subject = target_subj
    st.session_state.selected_subject = target_subj

    # Store role-specific IDs
    if role == "teacher":
        st.session_state.teacher_id = user_id
        st.session_state.teacher_subject = target_subj
        target_screen = "teacher"
    elif role == "admin":
        st.session_state.admin_id = user_id
        target_screen = "admin_home"
    else:
        st.session_state.student_id = user_id
        target_screen = "home"

    if not restore_screen:
        st.session_state.current_screen = target_screen
        st.query_params["screen"] = target_screen
    elif "screen" in st.query_params:
        st.session_state.current_screen = st.query_params["screen"]

    st.query_params["uid"] = user_id
    invalidate_class_dependent_state()


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

    if prev_level is not None and prev_level != target_level:
        invalidate_class_dependent_state()


def get_student_subject() -> str:
    """
    Returns the student's active subject ('Science' or 'Mathematics').
    """
    raw_val = (
        st.session_state.get("subject") or st.session_state.get("selected_subject") or "Science"
    )
    if "math" in str(raw_val).lower():
        return "Mathematics"
    return "Science"


def set_student_subject(subject: str) -> None:
    """
    Sets the active subject and triggers complete cross-subject state invalidation.
    """
    target_subject = "Mathematics" if "math" in str(subject).lower() else "Science"
    prev_subject = st.session_state.get("subject")

    st.session_state.subject = target_subject
    st.session_state.selected_subject = target_subject

    if prev_subject is not None and prev_subject != target_subject:
        invalidate_class_dependent_state()


def get_student_profile() -> Dict[str, Any]:
    """Returns the master student profile dictionary."""
    return {
        "student_id": st.session_state.get("student_id", "student_001"),
        "class_level": get_student_class_level(),
        "subject": get_student_subject(),
        "model": st.session_state.get("model", "gemini-3.5-flash-lite"),
    }


def get_state(key: str, default: Any = None) -> Any:
    """Safely retrieves a value from session state."""
    return st.session_state.get(key, default)


def set_state(key: str, value: Any) -> None:
    """Safely sets a value in session state."""
    st.session_state[key] = value


def navigate_to(screen_name: str, message: Optional[str] = None) -> None:
    """Navigates to a specific screen with centralized TransitionController lifecycle management (Phases 3-7, 11-13)."""
    current = st.session_state.get("current_screen")
    if screen_name != current:
        if screen_name == "tutor":
            st.session_state.tutor_needs_refresh = True
        try:
            from frontend.components.transition import start_transition

            start_transition(screen_name, message)
        except Exception:
            pass

    st.session_state.current_screen = screen_name
    st.query_params["screen"] = screen_name


def get_user_role() -> Any:
    """Returns the active user role ('student', 'teacher', 'admin', or None)."""
    return st.session_state.get("user_role")


def set_user_role(role: Any, restore_screen: bool = False) -> None:
    """Sets the active user role ('student', 'teacher', or 'admin') and routes to the role's default landing screen."""
    if role not in ("student", "teacher", "admin", None):
        raise ValueError(
            f"Invalid role {role!r}. Allowed roles are 'student', 'teacher', 'admin', or None."
        )
    st.session_state.user_role = role

    if not restore_screen:
        if role == "student":
            st.session_state.current_screen = "home"
            st.query_params["screen"] = "home"
        elif role == "teacher":
            st.session_state.current_screen = "teacher"
            st.query_params["screen"] = "teacher"
        elif role == "admin":
            st.session_state.current_screen = "admin_home"
            st.query_params["screen"] = "admin_home"
        else:
            st.session_state.current_screen = "login"


def logout() -> None:
    """Logs out the current user, clears role, and routes back to the login / role selection screen."""
    st.session_state.clear()
    init_session_state()

    if "uid" in st.query_params:
        del st.query_params["uid"]
    if "screen" in st.query_params:
        del st.query_params["screen"]
