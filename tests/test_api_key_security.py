"""Unit tests for Phase 11, 21: API Key Security and Secrecy Audit."""

import os
import unittest
from unittest.mock import MagicMock, patch

import streamlit as st

from backend.ai.api_config import (
    get_api_status,
    get_user_fallback_api_key,
    remove_user_fallback_api_key,
    set_user_fallback_api_key,
)
from backend.ai.client_factory import execute_chat_completion
from frontend.state import init_session_state


class TestApiKeySecurity(unittest.TestCase):
    """Verifies that primary and fallback API keys are never leaked, logged, or persisted to storage."""

    def setUp(self):
        for k in list(st.session_state.keys()):
            del st.session_state[k]

        self.secrets_patcher = patch.object(st, "secrets", {}, create=True)
        self.secrets_patcher.start()

        self.secret_primary_key = "AIzaSySecretPrimaryMasterKey12345"
        self.secret_fallback_key = "AIzaSySecretJudgeFallbackKey67890"

        os.environ["GEMINI_API_KEY"] = self.secret_primary_key

    def tearDown(self):
        self.secrets_patcher.stop()
        if "GEMINI_API_KEY" in os.environ:
            del os.environ["GEMINI_API_KEY"]

    def test_primary_key_never_prefilled_in_session_state(self):
        """Phase 3 & 21: init_session_state must never populate session state with primary API key."""
        init_session_state()

        for key, val in st.session_state.items():
            self.assertNotEqual(
                val,
                self.secret_primary_key,
                f"Security Leak: Primary API key found in session_state['{key}']",
            )
        self.assertIsNone(st.session_state.get("user_gemini_api_key"))

    def test_api_status_does_not_leak_key_string(self):
        """Phase 7, 19, 21: get_api_status returns only booleans and mode strings, never keys."""
        set_user_fallback_api_key(self.secret_fallback_key)
        status = get_api_status()

        status_str = str(status)
        self.assertNotIn(self.secret_primary_key, status_str)
        self.assertNotIn(self.secret_fallback_key, status_str)
        self.assertTrue(status["primary_configured"])
        self.assertTrue(status["fallback_configured"])

    @patch("backend.ai.client_factory.OpenAI")
    def test_logs_never_contain_raw_api_keys(self, mock_openai_cls):
        """Phase 11 & 21: Log statements must only state 'Using primary...' or 'Using session fallback...'."""
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_resp = MagicMock()
        mock_resp.choices = [MagicMock(message=MagicMock(content="Response"))]
        mock_client.chat.completions.create.return_value = mock_resp

        set_user_fallback_api_key(self.secret_fallback_key)

        with self.assertLogs("backend.ai", level="INFO") as log_cm:
            execute_chat_completion([{"role": "user", "content": "test"}])

            log_output = "\n".join(log_cm.output)
            self.assertNotIn(
                self.secret_primary_key,
                log_output,
                "Security Leak: Primary API key found in log output!",
            )
            self.assertNotIn(
                self.secret_fallback_key,
                log_output,
                "Security Leak: Fallback API key found in log output!",
            )
            self.assertIn("Using primary Gemini API", log_output)

    def test_remove_fallback_clears_session_state(self):
        """Phase 18 & 21: Remove button clears user key from session memory."""
        set_user_fallback_api_key(self.secret_fallback_key)
        self.assertEqual(get_user_fallback_api_key(), self.secret_fallback_key)

        remove_user_fallback_api_key()
        self.assertIsNone(get_user_fallback_api_key())
        self.assertNotIn("user_gemini_api_key", st.session_state)


if __name__ == "__main__":
    unittest.main()
