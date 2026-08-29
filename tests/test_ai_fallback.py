"""Unit tests for Phase 5, 6, 12, 13, 17, 20, 22: Centralized AI Failover and Error Classification."""

import asyncio
import os
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

import streamlit as st

from backend.ai.client_factory import (
    classify_gemini_error,
    execute_chat_completion,
    stream_chat_completion,
)
from backend.exceptions import (
    GeminiAPIError,
    GeminiAuthError,
    GeminiQuotaExhaustedError,
)


class TestAIFallback(unittest.TestCase):
    """Verifies that the centralized factory handles primary execution and automated fallback."""

    def setUp(self):
        # Clear Streamlit session state
        for k in list(st.session_state.keys()):
            del st.session_state[k]

        from backend.ai import client_factory

        client_factory._sync_clients.clear()
        client_factory._async_clients.clear()

        # Patch st.secrets to empty dict by default
        self.secrets_patcher = patch.object(st, "secrets", {}, create=True)
        self.secrets_patcher.start()

        # Backup environment
        self.orig_env_gemini = os.environ.get("GEMINI_API_KEY")
        self.orig_env_google = os.environ.get("GOOGLE_API_KEY")

        if "GEMINI_API_KEY" in os.environ:
            del os.environ["GEMINI_API_KEY"]
        if "GOOGLE_API_KEY" in os.environ:
            del os.environ["GOOGLE_API_KEY"]

    def tearDown(self):
        from backend.ai import client_factory

        client_factory._sync_clients.clear()
        client_factory._async_clients.clear()

        self.secrets_patcher.stop()

        # Restore environment
        if self.orig_env_gemini is not None:
            os.environ["GEMINI_API_KEY"] = self.orig_env_gemini
        elif "GEMINI_API_KEY" in os.environ:
            del os.environ["GEMINI_API_KEY"]

        if self.orig_env_google is not None:
            os.environ["GOOGLE_API_KEY"] = self.orig_env_google
        elif "GOOGLE_API_KEY" in os.environ:
            del os.environ["GOOGLE_API_KEY"]

    def test_classify_gemini_error(self):
        """Phase 6: Verifies exact error classification across various status codes and messages."""
        err_429 = Exception(
            "Error code: 429 - {'error': {'message': 'Resource has been exhausted (e.g. check quota)'}}"
        )
        self.assertEqual(classify_gemini_error(err_429), "QUOTA_EXHAUSTED")

        err_401 = Exception(
            "Error code: 401 - API_KEY_INVALID: API key not valid. Please pass a valid API key."
        )
        self.assertEqual(classify_gemini_error(err_401), "AUTH_ERROR")

        err_503 = Exception("Error code: 503 - The service is currently unavailable.")
        self.assertEqual(classify_gemini_error(err_503), "SERVER_ERROR")

        err_400 = Exception("Error code: 400 - INVALID_ARGUMENT: Schema validation error")
        self.assertEqual(classify_gemini_error(err_400), "INVALID_REQUEST")

    @patch("backend.ai.client_factory.OpenAI")
    def test_normal_operation_uses_primary_key(self, mock_openai_cls):
        """Test A (Phase 22): Normal operation with primary key available."""
        os.environ["GEMINI_API_KEY"] = "primary-app-key"
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_resp = MagicMock()
        mock_resp.choices = [MagicMock(message=MagicMock(content="Primary Success"))]
        mock_client.chat.completions.create.return_value = mock_resp

        messages = [{"role": "user", "content": "Hello"}]
        result = execute_chat_completion(messages)

        self.assertEqual(result.choices[0].message.content, "Primary Success")
        mock_openai_cls.assert_called_once_with(
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            api_key="primary-app-key",
        )

    @patch("backend.ai.client_factory.OpenAI")
    def test_fallback_on_primary_429_quota_exhausted(self, mock_openai_cls):
        """Test B (Phase 22): When primary hits 429 quota exhaustion, fails over to fallback key."""
        os.environ["GEMINI_API_KEY"] = "primary-app-key"
        st.session_state.user_gemini_api_key = "user-fallback-key"

        primary_client = MagicMock()
        primary_client.chat.completions.create.side_effect = Exception(
            "429 Resource has been exhausted (quota limit reached)"
        )

        fallback_client = MagicMock()
        fallback_resp = MagicMock()
        fallback_resp.choices = [MagicMock(message=MagicMock(content="Fallback Success"))]
        fallback_client.chat.completions.create.return_value = fallback_resp

        def client_side_effect(base_url, api_key):
            if api_key == "primary-app-key":
                return primary_client
            if api_key == "user-fallback-key":
                return fallback_client
            raise ValueError(f"Unexpected api_key {api_key}")

        mock_openai_cls.side_effect = client_side_effect

        messages = [{"role": "user", "content": "Hello"}]
        result = execute_chat_completion(messages)

        self.assertEqual(result.choices[0].message.content, "Fallback Success")
        self.assertEqual(mock_openai_cls.call_count, 2)

    @patch("backend.ai.client_factory.OpenAI")
    def test_no_fallback_raises_quota_exhausted_error(self, mock_openai_cls):
        """Test C (Phase 22): Primary fails with 429 and no user key is configured -> raises GeminiQuotaExhaustedError."""
        os.environ["GEMINI_API_KEY"] = "primary-app-key"

        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception(
            "429 Resource has been exhausted (quota limit reached)"
        )
        mock_openai_cls.return_value = mock_client

        messages = [{"role": "user", "content": "Hello"}]
        with self.assertRaises(GeminiQuotaExhaustedError) as ctx:
            execute_chat_completion(messages)

        self.assertIn("usage limit", str(ctx.exception).lower())

    @patch("backend.ai.client_factory.OpenAI")
    def test_invalid_fallback_raises_auth_error(self, mock_openai_cls):
        """Test D (Phase 20 & 22): Primary fails with 429, fallback is invalid 401 -> raises GeminiAuthError."""
        os.environ["GEMINI_API_KEY"] = "primary-app-key"
        st.session_state.user_gemini_api_key = "invalid-user-key"

        primary_client = MagicMock()
        primary_client.chat.completions.create.side_effect = Exception(
            "429 Resource has been exhausted"
        )

        fallback_client = MagicMock()
        fallback_client.chat.completions.create.side_effect = Exception("401 API_KEY_INVALID")

        def client_side_effect(base_url, api_key):
            if api_key == "primary-app-key":
                return primary_client
            return fallback_client

        mock_openai_cls.side_effect = client_side_effect

        messages = [{"role": "user", "content": "Hello"}]
        with self.assertRaises(GeminiAuthError):
            execute_chat_completion(messages)

    @patch("backend.ai.client_factory.OpenAI")
    def test_programming_error_does_not_blindly_fallback(self, mock_openai_cls):
        """Phase 6: A 400 Invalid Argument error must NOT trigger fallback or mask code bugs."""
        os.environ["GEMINI_API_KEY"] = "primary-app-key"
        st.session_state.user_gemini_api_key = "user-fallback-key"

        primary_client = MagicMock()
        primary_client.chat.completions.create.side_effect = Exception(
            "400 INVALID_ARGUMENT: Bad json schema"
        )
        mock_openai_cls.return_value = primary_client

        messages = [{"role": "user", "content": "Hello"}]
        with self.assertRaises(GeminiAPIError):
            execute_chat_completion(messages)

        # Mock OpenAI was only called once (no fallback attempt)
        self.assertEqual(mock_openai_cls.call_count, 1)

    @patch("backend.ai.client_factory.AsyncOpenAI")
    def test_streaming_fallback_on_primary_429(self, mock_async_openai_cls):
        """Phase 13 & 22: Async streaming auto-fallback when primary connection fails."""
        os.environ["GEMINI_API_KEY"] = "primary-app-key"
        st.session_state.user_gemini_api_key = "user-fallback-key"

        primary_client = MagicMock()
        primary_client.chat.completions.create = AsyncMock(
            side_effect=Exception("429 Rate limit exceeded")
        )

        async def async_gen():
            chunk1 = MagicMock()
            chunk1.choices = [MagicMock(delta=MagicMock(content="Hello "))]
            chunk2 = MagicMock()
            chunk2.choices = [MagicMock(delta=MagicMock(content="World!"))]
            yield chunk1
            yield chunk2

        fallback_client = MagicMock()
        fallback_client.chat.completions.create = AsyncMock(return_value=async_gen())

        def async_client_side_effect(base_url, api_key):
            if api_key == "primary-app-key":
                return primary_client
            return fallback_client

        mock_async_openai_cls.side_effect = async_client_side_effect

        async def run_stream():
            chunks = []
            async for c in stream_chat_completion([{"role": "user", "content": "Hi"}]):
                chunks.append(c)
            return "".join(chunks)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(run_stream())
        loop.close()

        self.assertEqual(result, "Hello World!")


if __name__ == "__main__":
    unittest.main()
