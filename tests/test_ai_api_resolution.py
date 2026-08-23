"""Unit tests for Phase 2, 3, 4, 5, 10, 18, 19: AI API Key Resolution and Modes."""

import os
import unittest
from unittest.mock import MagicMock, patch

import streamlit as st

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


class TestAIApiResolution(unittest.TestCase):
    """Verifies that API keys are resolved with the correct precedence and secrecy."""

    def setUp(self):
        # Clear Streamlit session state
        for k in list(st.session_state.keys()):
            del st.session_state[k]

        # Backup environment
        self.orig_env_gemini = os.environ.get("GEMINI_API_KEY")
        self.orig_env_google = os.environ.get("GOOGLE_API_KEY")

        if "GEMINI_API_KEY" in os.environ:
            del os.environ["GEMINI_API_KEY"]
        if "GOOGLE_API_KEY" in os.environ:
            del os.environ["GOOGLE_API_KEY"]

    def tearDown(self):
        # Restore environment
        if self.orig_env_gemini is not None:
            os.environ["GEMINI_API_KEY"] = self.orig_env_gemini
        elif "GEMINI_API_KEY" in os.environ:
            del os.environ["GEMINI_API_KEY"]

        if self.orig_env_google is not None:
            os.environ["GOOGLE_API_KEY"] = self.orig_env_google
        elif "GOOGLE_API_KEY" in os.environ:
            del os.environ["GOOGLE_API_KEY"]

    def test_primary_key_resolution_from_env(self):
        """Phase 2: Primary API key is retrieved from GEMINI_API_KEY / GOOGLE_API_KEY env vars."""
        with patch.object(st, "secrets", {}, create=True):
            os.environ["GEMINI_API_KEY"] = "test-env-gemini-key-123"
            self.assertEqual(get_primary_api_key(), "test-env-gemini-key-123")
            self.assertTrue(has_primary_api_key())

    def test_primary_key_resolution_from_st_secrets(self):
        """Phase 3: Primary API key is retrieved from Streamlit secrets without leaking to state."""
        mock_secrets = {"GEMINI_API_KEY": "secret-vault-key-xyz"}
        with patch.object(st, "secrets", mock_secrets, create=True):
            self.assertEqual(get_primary_api_key(), "secret-vault-key-xyz")
            self.assertTrue(has_primary_api_key())

    def test_user_fallback_key_lifecycle(self):
        """Phase 10 & 18: Fallback key stores in session state and is removable."""
        with patch.object(st, "secrets", {}, create=True):
            self.assertFalse(has_user_fallback_api_key())
            self.assertIsNone(get_user_fallback_api_key())

            # Set user fallback key
            set_user_fallback_api_key("user-fallback-test-key-456")
            self.assertTrue(has_user_fallback_api_key())
            self.assertEqual(get_user_fallback_api_key(), "user-fallback-test-key-456")

            # Remove user fallback key
            remove_user_fallback_api_key()
            self.assertFalse(has_user_fallback_api_key())
            self.assertIsNone(get_user_fallback_api_key())

    def test_active_mode_and_status(self):
        """Phase 19: Mode indicator reports 'primary', 'fallback', or 'none' without exposing key."""
        with patch.object(st, "secrets", {}, create=True):
            # 1. Neither configured
            self.assertEqual(get_active_api_mode(), "none")
            status = get_api_status()
            self.assertFalse(status["primary_configured"])
            self.assertFalse(status["fallback_configured"])
            self.assertEqual(status["active_mode"], "none")

            # 2. Only fallback configured
            set_user_fallback_api_key("user-key-789")
            self.assertEqual(get_active_api_mode(), "fallback")
            status = get_api_status()
            self.assertFalse(status["primary_configured"])
            self.assertTrue(status["fallback_configured"])
            self.assertEqual(status["active_mode"], "fallback")

            # 3. Primary configured
            os.environ["GOOGLE_API_KEY"] = "primary-app-key-001"
            self.assertEqual(get_active_api_mode(), "primary")
            status = get_api_status()
            self.assertTrue(status["primary_configured"])
            self.assertTrue(status["fallback_configured"])
            self.assertEqual(status["active_mode"], "primary")

    @patch("src.academic_rag.ai.api_config.OpenAI")
    def test_test_gemini_api_key_success(self, mock_openai):
        """Phase 14: Save & Test makes 1 lightweight call and returns success."""
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_client.chat.completions.create.return_value = MagicMock()

        is_valid, msg = test_gemini_api_key("test-key-12345")
        self.assertTrue(is_valid)
        self.assertIn("verified", msg.lower())

        # Verify minimal request parameters
        mock_client.chat.completions.create.assert_called_once()
        kwargs = mock_client.chat.completions.create.call_args[1]
        self.assertEqual(kwargs["max_tokens"], 1)

    @patch("src.academic_rag.ai.api_config.OpenAI")
    def test_test_gemini_api_key_quota_error(self, mock_openai):
        """Phase 14 & 20: Save & Test handles quota errors with actionable message."""
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception(
            "HTTP 429: Resource has been exhausted (e.g. check quota)"
        )

        is_valid, msg = test_gemini_api_key("test-exhausted-key")
        self.assertFalse(is_valid)
        self.assertIn("quota", msg.lower())


if __name__ == "__main__":
    unittest.main()
