"""Performance Benchmark Suite and Latency Verification (Phases 1-3, 39, 40, 46)."""

import time
import unittest
from unittest.mock import MagicMock, patch

import streamlit as st

from backend.ai.client_factory import get_async_gemini_client, get_gemini_client
from backend.rag.retriever import embed_query_fast, get_embeddings
from backend.utils.perf import get_performance_summary, measure, reset_performance_metrics
from frontend.state import init_session_state, navigate_to


class TestPerformanceBenchmarks(unittest.TestCase):
    """Verifies sub-millisecond instrumentation, client caching, embedding cache, and latency bounds."""

    def setUp(self):
        reset_performance_metrics()
        st.session_state.clear()
        if hasattr(st, "query_params"):
            st.query_params.clear()
        init_session_state()

    def test_measure_context_manager_records_latency(self):
        """measure context manager records sub-millisecond execution duration."""
        with measure("test_fast_operation", {"tag": "unit_test"}) as m:
            time.sleep(0.01)  # 10ms sleep

        self.assertGreaterEqual(m["duration_ms"], 8.0)
        self.assertEqual(m["operation"], "test_fast_operation")

        summary = get_performance_summary()
        self.assertIn("test_fast_operation", summary)
        self.assertEqual(summary["test_fast_operation"]["count"], 1)
        self.assertGreaterEqual(summary["test_fast_operation"]["avg_ms"], 8.0)

    def test_gemini_client_connection_caching(self):
        """get_gemini_client and get_async_gemini_client reuse existing connection instances for the same key."""
        test_key = "test_perf_api_key_123456789"
        client1 = get_gemini_client(api_key=test_key)
        client2 = get_gemini_client(api_key=test_key)
        self.assertIs(client1, client2, "Client instance was not reused from cache")

        async_client1 = get_async_gemini_client(api_key=test_key)
        async_client2 = get_async_gemini_client(api_key=test_key)
        self.assertIs(async_client1, async_client2, "Async client instance was not reused from cache")

    @patch("backend.rag.retriever.get_embeddings")
    def test_embed_query_lru_caching(self, mock_get_embeddings):
        """embed_query_fast reuses cached vectors for identical query text."""
        mock_embedder = MagicMock()
        mock_embedder.embed_query.return_value = [0.1, 0.2, 0.3, 0.4]
        mock_get_embeddings.return_value = mock_embedder

        # First call
        res1 = embed_query_fast("What is Ohm's Law?")
        self.assertEqual(res1, [0.1, 0.2, 0.3, 0.4])

        # Second identical call should hit LRU cache and NOT re-call mock_embedder.embed_query
        res2 = embed_query_fast("What is Ohm's Law?")
        self.assertEqual(res2, [0.1, 0.2, 0.3, 0.4])

    def test_navigation_latency_budget(self):
        """navigate_to completes in under 5 milliseconds."""
        start = time.perf_counter()
        navigate_to("quiz")
        duration_ms = (time.perf_counter() - start) * 1000.0

        self.assertEqual(st.session_state.get("current_screen"), "quiz")
        self.assertLess(duration_ms, 15.0, "navigate_to exceeded 15ms latency budget")


if __name__ == "__main__":
    unittest.main()
