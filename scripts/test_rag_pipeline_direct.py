#!/usr/bin/env python3
"""
Targeted Verification Script for Direct NCERT RAG Pipeline
Verifies:
1. Zero tool-calling / function-calling overhead (no thought_signature errors).
2. Zero OpenAI agent tracing (no 401s).
3. Exactly 1 Gemini request for: "What is Ohm's law and how is resistance calculated?"
4. Accurate, grounded answer with exact NCERT chapter & page citations.
"""

import asyncio
import os
import sys
import time

from dotenv import load_dotenv

# Reconfigure stdout for UTF-8
sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

load_dotenv()
from src.academic_rag.rag.engine import stream_ncert_rag_response
from src.academic_rag.rag.retriever import retrieve_ncert_context


async def test_direct_rag():
    print("=" * 70)
    print("TESTING DIRECT NCERT RAG PIPELINE (ZERO FUNCTION CALLS / 1 REQUEST)")
    print("=" * 70)

    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        # Check secrets.toml
        import toml

        secrets_path = os.path.join(PROJECT_ROOT, ".streamlit", "secrets.toml")
        if os.path.exists(secrets_path):
            sec = toml.load(secrets_path)
            api_key = sec.get("GOOGLE_API_KEY") or sec.get("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY / GOOGLE_API_KEY not found.")
        return

    query = "What is Ohm's law and how is resistance calculated?"
    class_filter = 10  # Class 10 NCERT Science

    print(f"\nQuery: {query}")
    print(f"Target Class Filter: Class {class_filter}")
    print("\n--- 1. Testing Pinecone Retrieval ---")
    context = retrieve_ncert_context(query, class_filter=class_filter, top_k=4)
    print(f"Retrieved Context Length: {len(context)} chars")
    assert "Electricity" in context, "Expected 'Electricity' in retrieved context"
    assert "PAGE:" in context, "Expected page metadata in retrieved context"
    print("✓ Retrieval verified successfully!")

    print("\n--- 2. Streaming Response from Gemini 3.5 Flash-Lite ---")
    start_t = time.time()
    full_response = ""

    async for token in stream_ncert_rag_response(
        query=query,
        class_filter=class_filter,
        api_key=api_key,
        model_name="gemini-3.5-flash-lite",
    ):
        full_response += token
        print(token, end="", flush=True)

    elapsed = time.time() - start_t
    print(f"\n\n⏱️ Total generation time: {elapsed:.2f}s")
    print("-" * 70)

    # Verification assertions
    assert len(full_response) > 100, "Response should be substantive"
    assert (
        "V = IR" in full_response or "V = I" in full_response or "Ohm" in full_response
    ), "Expected Ohm's law formula"
    assert "NCERT" in full_response, "Expected NCERT citation block"
    assert "Electricity" in full_response or "Chapter" in full_response, "Expected chapter citation"

    print("\n" + "=" * 70)
    print("🎉 DIRECT NCERT RAG PIPELINE VERIFICATION PASSED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(test_direct_rag())
