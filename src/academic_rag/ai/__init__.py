"""Centralized AI Services and API Configuration for DiligentEdu."""

from src.academic_rag.ai.api_config import (
    get_active_api_mode,
    get_api_status,
    get_primary_api_key,
    get_user_fallback_api_key,
    has_primary_api_key,
    has_user_fallback_api_key,
    remove_user_fallback_api_key,
    set_user_fallback_api_key,
    test_gemini_api_key,
)
from src.academic_rag.ai.client_factory import (
    classify_gemini_error,
    execute_chat_completion,
    get_async_gemini_client,
    get_gemini_client,
    stream_chat_completion,
)

__all__ = [
    "get_primary_api_key",
    "get_user_fallback_api_key",
    "has_primary_api_key",
    "has_user_fallback_api_key",
    "get_active_api_mode",
    "get_api_status",
    "set_user_fallback_api_key",
    "remove_user_fallback_api_key",
    "test_gemini_api_key",
    "get_gemini_client",
    "get_async_gemini_client",
    "execute_chat_completion",
    "stream_chat_completion",
    "classify_gemini_error",
]
