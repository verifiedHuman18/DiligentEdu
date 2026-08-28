#!/usr/bin/env python3
"""
Integration test for NCERT Science RAG & Citations
Tests the end-to-end flow: Question -> Direct RAG -> Pinecone -> Gemini -> Answer + Citation
"""

import asyncio
import os
import sys

from dotenv import load_dotenv

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.config import config
from backend.rag.engine import stream_ncert_rag_response

# Reconfigure stdout for UTF-8
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()
GOOGLE_API_KEY = config.get_google_api_key()


async def run_test():
    print("=" * 70)
    print("Testing End-to-End Direct RAG with NCERT Citations")
    print("=" * 70)

    if not GOOGLE_API_KEY:
        print("❌ Error: GOOGLE_API_KEY missing.")
        return

    test_queries = [
        {
            "query": "What is Ohm's law and what is the formula?",
            "class_filter": 10,
        },
        {
            "query": "What is the cell membrane and how does it function?",
            "class_filter": 9,
        },
    ]

    for tc in test_queries:
        print(f'\n💬 Query: "{tc["query"]}" (Class Filter: {tc["class_filter"]})')
        print("-" * 50)

        full_resp = ""
        async for chunk in stream_ncert_rag_response(
            query=tc["query"],
            class_filter=tc["class_filter"],
            api_key=GOOGLE_API_KEY,
            model_name=config.default_llm_model,
        ):
            full_resp += chunk

        print("🤖 Response:")
        print(full_resp)
        print("=" * 70)


if __name__ == "__main__":
    asyncio.run(run_test())
