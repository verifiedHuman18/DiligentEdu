"""Centralized Gemini Client Factory and Request Dispatcher (Phases 4, 5, 6, 12, 13, 15, 17, 20).

Provides:
- get_gemini_client / get_async_gemini_client
- execute_chat_completion (sync structured/JSON execution with automatic failover)
- stream_chat_completion (async token streaming with automatic failover)
- classify_gemini_error (proper error categorization)
- Sanitized logging (never logs API keys)
"""

import logging
from typing import Any, AsyncGenerator, Dict, List, Optional

from openai import AsyncOpenAI, OpenAI

from backend.ai.api_config import (
    get_primary_api_key,
    get_user_fallback_api_key,
)
from backend.config import config
from backend.exceptions import (
    GeminiAPIError,
    GeminiAuthError,
    GeminiConfigurationError,
    GeminiQuotaExhaustedError,
    GeminiUnavailableError,
)

logger = logging.getLogger(__name__)


def classify_gemini_error(exc: Exception) -> str:
    """
    Classifies an exception from the Gemini API into a standard category:
    - 'QUOTA_EXHAUSTED': Rate limits, 429, resource exhausted.
    - 'AUTH_ERROR': 401, 403, invalid key, unauthorized.
    - 'SERVER_ERROR': 500, 502, 503, 504, timeout, network error.
    - 'INVALID_REQUEST': 400, invalid argument, malformed payload.
    - 'UNKNOWN_ERROR': Any other unclassified error.
    """
    status_code = getattr(exc, "status_code", None)
    err_str = str(exc).lower()

    if (
        status_code == 429
        or "429" in err_str
        or "quota" in err_str
        or "resource_exhausted" in err_str
    ):
        return "QUOTA_EXHAUSTED"

    if (
        status_code in (401, 403)
        or "401" in err_str
        or "403" in err_str
        or "api_key_invalid" in err_str
        or "unauthorized" in err_str
        or "permission_denied" in err_str
        or "invalid api key" in err_str
    ):
        return "AUTH_ERROR"

    if (
        status_code in (500, 502, 503, 504)
        or "500" in err_str
        or "503" in err_str
        or "unavailable" in err_str
        or "deadline_exceeded" in err_str
        or "timeout" in err_str
        or "connection error" in err_str
    ):
        return "SERVER_ERROR"

    if (
        status_code == 400
        or "400" in err_str
        or "invalid_argument" in err_str
        or "bad request" in err_str
    ):
        return "INVALID_REQUEST"

    return "UNKNOWN_ERROR"


_sync_clients: Dict[str, OpenAI] = {}
_async_clients: Dict[str, AsyncOpenAI] = {}


def get_gemini_client(api_key: Optional[str] = None) -> OpenAI:
    """
    Creates or reuses a cached synchronous OpenAI-compatible client targeting Google Gemini (Phases 5 & 6).
    Reuses existing client connection pools per effective API key.
    """
    effective_key = api_key or get_primary_api_key() or get_user_fallback_api_key()
    if not effective_key:
        raise GeminiConfigurationError("No Gemini API key is configured.")

    key_str = str(effective_key).strip()
    if key_str not in _sync_clients:
        _sync_clients[key_str] = OpenAI(
            base_url=config.gemini_base_url,
            api_key=key_str,
        )

    return _sync_clients[key_str]


def get_async_gemini_client(api_key: Optional[str] = None) -> AsyncOpenAI:
    """
    Creates or reuses a cached asynchronous OpenAI-compatible client targeting Google Gemini (Phases 5 & 6).
    Reuses existing client connection pools per effective API key.
    """
    effective_key = api_key or get_primary_api_key() or get_user_fallback_api_key()
    if not effective_key:
        raise GeminiConfigurationError("No Gemini API key is configured.")

    key_str = str(effective_key).strip()
    if key_str not in _async_clients:
        _async_clients[key_str] = AsyncOpenAI(
            base_url=config.gemini_base_url,
            api_key=key_str,
        )

    return _async_clients[key_str]


def execute_chat_completion(
    messages: List[Dict[str, str]],
    model: Optional[str] = None,
    response_format: Optional[Dict[str, str]] = None,
    temperature: float = 0.3,
    override_api_key: Optional[str] = None,
    **kwargs: Any,
) -> Any:
    """
    Executes a chat completion request with automatic primary -> session fallback resolution.

    Priority & Fallback Logic (Phase 5 & 6):
      1. Use override_api_key if explicitly provided.
      2. Otherwise, attempt with Primary API key.
      3. If Primary fails with Quota (429) or Auth (401/403), check if Session Fallback key exists.
      4. If Fallback key exists, execute request with Fallback key.
      5. If both fail or no Fallback exists, raise categorized exception.
      6. Programming / Invalid Request errors do not trigger fallback (prevents masking code bugs).
    """
    target_model = model or config.default_llm_model

    # Explicit override takes direct precedence if provided
    if override_api_key and str(override_api_key).strip():
        logger.info("Using explicitly provided override Gemini API key")
        client = get_gemini_client(api_key=str(override_api_key).strip())
        create_kwargs: Dict[str, Any] = {
            "model": target_model,
            "messages": messages,
            "temperature": temperature,
            **kwargs,
        }
        if response_format:
            create_kwargs["response_format"] = response_format
        return client.chat.completions.create(**create_kwargs)

    primary_key = get_primary_api_key()
    fallback_key = get_user_fallback_api_key()

    if not primary_key and not fallback_key:
        raise GeminiConfigurationError(
            "No Gemini API key configured. Please configure an application secret or session fallback API key in Settings."
        )

    create_kwargs: Dict[str, Any] = {
        "model": target_model,
        "messages": messages,
        "temperature": temperature,
        **kwargs,
    }
    if response_format:
        create_kwargs["response_format"] = response_format

    # 1. Attempt Primary API
    if primary_key:
        logger.info("Using primary Gemini API")
        try:
            client = get_gemini_client(api_key=primary_key)
            return client.chat.completions.create(**create_kwargs)
        except Exception as primary_err:
            category = classify_gemini_error(primary_err)
            logger.warning(
                f"Primary Gemini API request failed with category '{category}': {primary_err}"
            )

            # Do not fallback on programming/schema errors
            if category == "INVALID_REQUEST":
                raise GeminiAPIError(f"Gemini API invalid request: {primary_err}") from primary_err

            # For Quota, Auth, Server, or Unknown errors, attempt Fallback API if available
            if fallback_key:
                logger.info("Using session fallback Gemini API")
                try:
                    fb_client = get_gemini_client(api_key=fallback_key)
                    return fb_client.chat.completions.create(**create_kwargs)
                except Exception as fb_err:
                    fb_cat = classify_gemini_error(fb_err)
                    logger.error(f"Fallback Gemini API failed with category '{fb_cat}': {fb_err}")
                    if fb_cat == "QUOTA_EXHAUSTED":
                        raise GeminiQuotaExhaustedError(
                            "Provided session fallback Gemini API quota exhausted (HTTP 429)."
                        ) from fb_err
                    if fb_cat == "AUTH_ERROR":
                        raise GeminiAuthError(
                            "Provided session fallback Gemini API key is invalid or unauthorized (HTTP 401/403)."
                        ) from fb_err
                    raise GeminiAPIError(
                        f"Session fallback Gemini API request failed: {fb_err}"
                    ) from fb_err

            # No fallback available
            if category == "QUOTA_EXHAUSTED":
                raise GeminiQuotaExhaustedError(
                    "The configured AI service has reached its usage limit. "
                    "You can add your own Gemini API key in Settings to continue."
                ) from primary_err
            if category == "AUTH_ERROR":
                raise GeminiAuthError(
                    "Application Gemini API key authentication failed. "
                    "Please configure a session fallback API key in Settings."
                ) from primary_err
            if category == "SERVER_ERROR":
                raise GeminiUnavailableError(
                    f"Gemini API is temporarily unavailable ({primary_err})."
                ) from primary_err

            raise GeminiAPIError(f"Gemini API request failed: {primary_err}") from primary_err

    # 2. If only Fallback key is available
    logger.info("Using session fallback Gemini API")
    try:
        client = get_gemini_client(api_key=fallback_key)
        create_kwargs = {
            "model": target_model,
            "messages": messages,
            "temperature": temperature,
            **kwargs,
        }
        if response_format:
            create_kwargs["response_format"] = response_format
        return client.chat.completions.create(**create_kwargs)
    except Exception as fb_err:
        fb_cat = classify_gemini_error(fb_err)
        logger.error(f"Fallback Gemini API failed with category '{fb_cat}': {fb_err}")
        if fb_cat == "QUOTA_EXHAUSTED":
            raise GeminiQuotaExhaustedError(
                "Provided session fallback Gemini API quota exhausted (HTTP 429)."
            ) from fb_err
        if fb_cat == "AUTH_ERROR":
            raise GeminiAuthError(
                "Provided session fallback Gemini API key is invalid or unauthorized (HTTP 401/403)."
            ) from fb_err
        raise GeminiAPIError(f"Session fallback Gemini API request failed: {fb_err}") from fb_err


async def stream_chat_completion(
    messages: List[Dict[str, str]],
    model: Optional[str] = None,
    temperature: float = 0.2,
    override_api_key: Optional[str] = None,
    **kwargs: Any,
) -> AsyncGenerator[str, None]:
    """
    Streams chat completion chunks token-by-token with automatic primary -> session fallback resolution.
    """
    target_model = model or config.default_llm_model

    # Explicit override takes direct precedence if provided
    if override_api_key and str(override_api_key).strip():
        logger.info("Using explicitly provided override Gemini API key for streaming")
        client = get_async_gemini_client(api_key=str(override_api_key).strip())
        stream_resp = await client.chat.completions.create(
            model=target_model,
            messages=messages,
            stream=True,
            temperature=temperature,
            **kwargs,
        )
        async for chunk in stream_resp:
            if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
        return

    primary_key = get_primary_api_key()
    fallback_key = get_user_fallback_api_key()

    if not primary_key and not fallback_key:
        raise GeminiConfigurationError(
            "No Gemini API key configured. Please configure an application secret or session fallback API key in Settings."
        )

    # 1. Attempt Primary API
    if primary_key:
        logger.info("Using primary Gemini API")
        try:
            client = get_async_gemini_client(api_key=primary_key)
            stream_resp = await client.chat.completions.create(
                model=target_model,
                messages=messages,
                stream=True,
                temperature=temperature,
                **kwargs,
            )
            async for chunk in stream_resp:
                if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
            return
        except Exception as primary_err:
            category = classify_gemini_error(primary_err)
            logger.warning(
                f"Primary Gemini streaming failed with category '{category}': {primary_err}"
            )

            if category == "INVALID_REQUEST":
                raise GeminiAPIError(f"Gemini API invalid request: {primary_err}") from primary_err

            if fallback_key:
                logger.info("Using session fallback Gemini API for streaming")
                try:
                    fb_client = get_async_gemini_client(api_key=fallback_key)
                    stream_resp = await fb_client.chat.completions.create(
                        model=target_model,
                        messages=messages,
                        stream=True,
                        temperature=temperature,
                        **kwargs,
                    )
                    async for chunk in stream_resp:
                        if (
                            chunk.choices
                            and chunk.choices[0].delta
                            and chunk.choices[0].delta.content
                        ):
                            yield chunk.choices[0].delta.content
                    return
                except Exception as fb_err:
                    fb_cat = classify_gemini_error(fb_err)
                    logger.error(f"Fallback streaming failed with category '{fb_cat}': {fb_err}")
                    if fb_cat == "QUOTA_EXHAUSTED":
                        raise GeminiQuotaExhaustedError(
                            "Provided session fallback Gemini API quota exhausted (HTTP 429)."
                        ) from fb_err
                    if fb_cat == "AUTH_ERROR":
                        raise GeminiAuthError(
                            "Provided session fallback Gemini API key is invalid (HTTP 401/403)."
                        ) from fb_err
                    raise GeminiAPIError(f"Fallback streaming failed: {fb_err}") from fb_err

            if category == "QUOTA_EXHAUSTED":
                raise GeminiQuotaExhaustedError(
                    "The configured AI service has reached its usage limit. "
                    "You can add your own Gemini API key in Settings to continue."
                ) from primary_err
            if category == "AUTH_ERROR":
                raise GeminiAuthError(
                    "Application Gemini API key authentication failed. "
                    "Please configure a session fallback API key in Settings."
                ) from primary_err
            if category == "SERVER_ERROR":
                raise GeminiUnavailableError(
                    f"Gemini API is temporarily unavailable ({primary_err})."
                ) from primary_err

            raise GeminiAPIError(f"Gemini streaming failed: {primary_err}") from primary_err

    # 2. If only Fallback key is available
    logger.info("Using session fallback Gemini API for streaming")
    try:
        client = AsyncOpenAI(base_url=config.gemini_base_url, api_key=fallback_key)
        stream_resp = await client.chat.completions.create(
            model=target_model,
            messages=messages,
            stream=True,
            temperature=temperature,
            **kwargs,
        )
        async for chunk in stream_resp:
            if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    except Exception as fb_err:
        fb_cat = classify_gemini_error(fb_err)
        logger.error(f"Fallback streaming failed with category '{fb_cat}': {fb_err}")
        if fb_cat == "QUOTA_EXHAUSTED":
            raise GeminiQuotaExhaustedError(
                "Provided session fallback Gemini API quota exhausted (HTTP 429)."
            ) from fb_err
        if fb_cat == "AUTH_ERROR":
            raise GeminiAuthError(
                "Provided session fallback Gemini API key is invalid (HTTP 401/403)."
            ) from fb_err
        raise GeminiAPIError(f"Fallback streaming failed: {fb_err}") from fb_err
