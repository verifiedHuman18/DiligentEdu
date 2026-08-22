#!/usr/bin/env python3
"""
Retrieval & Metadata Filtering Verification Script
Tests similarity search and metadata filtering against the Pinecone `ncert-science` index.
"""

import os
import sys

from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
from pinecone import Pinecone

# Reconfigure stdout for UTF-8
sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "ncert-science")
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


def test_retrieval():
    print("=" * 60)
    print(f"Testing Retrieval from Pinecone Index: {INDEX_NAME}")
    print("=" * 60)

    if not PINECONE_API_KEY:
        print("❌ Error: PINECONE_API_KEY not found in environment.")
        return False

    pc = Pinecone(api_key=PINECONE_API_KEY)
    index = pc.Index(INDEX_NAME)

    print(f"🧠 Loading embedding model: {MODEL_NAME}...")
    embeddings = HuggingFaceEmbeddings(model_name=MODEL_NAME)

    test_cases = [
        {
            "query": "What is covalent bonding and why does carbon form four bonds?",
            "filter": {"class": {"$eq": 10}, "chapter_number": {"$eq": 4}},
            "description": "Class 10 - Chapter 4 (Carbon and its Compounds)",
        },
        {
            "query": "What is the function of the plasma membrane in a cell?",
            "filter": {"class": {"$eq": 9}, "chapter_number": {"$eq": 2}},
            "description": "Class 9 - Chapter 2 (Cell: The Building Block of Life)",
        },
        {
            "query": "How do sound waves propagate through a medium?",
            "filter": {"class": {"$eq": 9}},
            "description": "Class 9 - Any chapter (Sound/Physics)",
        },
    ]

    for tc in test_cases:
        print(f'\n🔎 Test Query: "{tc["query"]}"')
        print(f"   Filter: {tc['filter']} ({tc['description']})")

        # Generate query vector
        query_vector = embeddings.embed_query(tc["query"])

        # Query Pinecone
        results = index.query(
            vector=query_vector,
            top_k=2,
            include_metadata=True,
            filter=tc["filter"],
        )

        matches = results.get("matches", [])
        if not matches:
            print("   ⚠️ No matching documents returned.")
            continue

        for idx, match in enumerate(matches, 1):
            score = match.get("score", 0.0)
            meta = match.get("metadata", {})
            text_preview = meta.get("text", "")[:150].replace("\n", " ")
            print(f"   Match {idx} [Score: {score:.4f}]:")
            print(
                f"     Class: {meta.get('class')} | Ch {meta.get('chapter_number')}: {meta.get('chapter')} | Page {meta.get('page')}"
            )
            print(f"     Snippet: {text_preview}...")

    print("\n" + "=" * 60)
    print("✅ Retrieval and metadata filtering test complete!")
    print("=" * 60)
    return True


if __name__ == "__main__":
    test_retrieval()
