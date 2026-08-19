#!/usr/bin/env python3
"""
Integration test for NCERT Science Agent & Citations
Tests the end-to-end flow: Question -> Agent -> Tool -> Pinecone -> Gemini -> Answer + Citation
"""

import os
import sys
import asyncio
from dotenv import load_dotenv
from openai import AsyncOpenAI
from agents import Agent, OpenAIChatCompletionsModel, Runner, SQLiteSession
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app import create_function_tools, agent_initialization

# Reconfigure stdout for UTF-8
sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")


async def run_test():
    print("=" * 70)
    print("Testing End-to-End Agent RAG with NCERT Citations")
    print("=" * 70)

    if not GOOGLE_API_KEY:
        print("❌ Error: GOOGLE_API_KEY missing.")
        return

    test_queries = [
        {
            "query": "What is Ohm's law and what is the formula?",
            "class_focus": "Class 10",
        },
        {
            "query": "What is the cell membrane and how does it function?",
            "class_focus": "Class 9",
        },
    ]

    for tc in test_queries:
        print(f"\n💬 Query: \"{tc['query']}\" (Focus: {tc['class_focus']})")
        print("-" * 50)
        
        agent = agent_initialization("gemini-2.5-flash", GOOGLE_API_KEY, tc["class_focus"])
        session = SQLiteSession("test_session")

        result = await Runner.run(agent, tc["query"], session=session)
        print("🤖 Response:")
        print(result.final_output)
        print("=" * 70)


if __name__ == "__main__":
    asyncio.run(run_test())
