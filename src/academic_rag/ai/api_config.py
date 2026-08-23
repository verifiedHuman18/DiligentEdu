"""Centralized Gemini API Key Configuration and Resolver (Phases 2, 3, 4, 5, 7, 8, 10, 11, 14, 18, 19).

Architecture:
- Primary Key: Loaded automatically from Streamlit Secrets or Environment Variables. Kept hidden.
- Fallback Key: Provided optionally by the user/judge in Settings, stored strictly in Streamlit session state.
- Priority: Primary first -> automatic failover to Fallback on quota/auth failure.
"""

import logging
import os
from typing import Any, Dict, Optional, Tuple

from openai import OpenAI

from src.academic_rag.config import config

logger = logging.getLogger(__name__)


def get_primary_api_key() -> Optional[str]:
    """
    Retrieves the primary application Gemini API key.
    Sources (in order):
      1. Streamlit Secrets (st.secrets["GEMINI_API_KEY"] or st.secrets["GOOGLE_API_KEY"])
      2. Environment Variables (GEMINI_API_KEY or GOOGLE_API_KEY)

    Returns:
        Cleaned API key string or None if not configured.
    """
    try:
        import streamlit as st

        if hasattr(st, "secrets"):
            if "GEMINI_API_KEY" in st.secrets and str(st.secrets["GEMINI_API_KEY"]).strip():
                return str(st.secrets["GEMINI_API_KEY"]).strip()
            if "GOOGLE_API_KEY" in st.secrets and str(st.secrets["GOOGLE_API_KEY"]).strip():
                return str(st.secrets["GOOGLE_API_KEY"]).strip()
    except Exception:
        pass

    env_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if env_key and str(env_key).strip():
        return str(env_key).strip()

    return None


def get_user_fallback_api_key() -> Optional[str]:
    """
    Retrieves the user-provided fallback Gemini API key stored in Streamlit session state.

    Returns:
        Cleaned user fallback key or None if not set.
    """
    try:
        import streamlit as st

        if "user_gemini_api_key" in st.session_state and st.session_state.user_gemini_api_key:
            user_key = str(st.session_state.user_gemini_api_key).strip()
            if user_key:
                return user_key
    except Exception:
        pass
    return None


def has_primary_api_key() -> bool:
    """Returns True if the primary application API key is configured."""
    return get_primary_api_key() is not None


def has_user_fallback_api_key() -> bool:
    """Returns True if a session fallback API key is configured."""
    return get_user_fallback_api_key() is not None


def get_active_api_mode() -> str:
    """
    Returns active API mode indicator: 'primary', 'fallback', or 'none'.
    """
    if has_primary_api_key():
        return "primary"
    if has_user_fallback_api_key():
        return "fallback"
    return "none"


def get_api_status() -> Dict[str, Any]:
    """
    Returns non-sensitive metadata for UI status rendering without exposing raw keys.
    """
    primary_avail = has_primary_api_key()
    fallback_avail = has_user_fallback_api_key()
    mode = get_active_api_mode()

    return {
        "primary_configured": primary_avail,
        "fallback_configured": fallback_avail,
        "active_mode": mode,
        "status_label": (
            "Application AI Service"
            if mode == "primary"
            else ("Session Fallback API" if mode == "fallback" else "Not Configured")
        ),
    }


def set_user_fallback_api_key(key: str) -> None:
    """
    Stores the user/judge fallback API key into Streamlit session state.

    Args:
        key: Gemini API key string.
    """
    if not key or not str(key).strip():
        raise ValueError("API key cannot be empty.")

    clean_key = str(key).strip()
    try:
        import streamlit as st

        st.session_state.user_gemini_api_key = clean_key
    except Exception:
        pass


def remove_user_fallback_api_key() -> None:
    """
    Deletes the user/judge fallback API key from Streamlit session state.
    """
    try:
        import streamlit as st

        if "user_gemini_api_key" in st.session_state:
            del st.session_state["user_gemini_api_key"]
    except Exception:
        pass


def test_gemini_api_key(api_key: str, model_name: Optional[str] = None) -> Tuple[bool, str]:
    """
    Performs a single lightweight test request (1 token ping) to verify the given key.

    Args:
        api_key: Gemini API key to test.
        model_name: Optional model to test against.

    Returns:
        Tuple of (is_valid: bool, message: str)
    """
    if not api_key or not str(api_key).strip():
        return False, "API key cannot be empty."

    clean_key = str(api_key).strip()
    target_model = model_name or config.default_llm_model

    try:
        client = OpenAI(
            base_url=config.gemini_base_url,
            api_key=clean_key,
        )
        # 1-token minimal test request
        client.chat.completions.create(
            model=target_model,
            messages=[{"role": "user", "content": "ping"}],
            max_tokens=1,
            temperature=0.0,
        )
        return True, "API key verified successfully. Ready for session use."
    except Exception as e:
        err_msg = str(e).lower()
        if "429" in err_msg or "quota" in err_msg or "resource_exhausted" in err_msg:
            return (
                False,
                "API key quota exhausted (HTTP 429). Please verify your Google AI Studio quota.",
            )
        if (
            "401" in err_msg
            or "403" in err_msg
            or "invalid" in err_msg
            or "unauthorized" in err_msg
        ):
            return (
                False,
                "Invalid API key or unauthorized (HTTP 401/403). Please verify the key string.",
            )
        return False, f"API test failed: {e}"
