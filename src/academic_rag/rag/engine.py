"""Direct NCERT RAG Streaming Engine (Zero tool-calling overhead / 1 single request)."""

import logging
from typing import Optional, List, Dict, AsyncGenerator
from openai import AsyncOpenAI

from src.academic_rag.config import config
from src.academic_rag.exceptions import AuthenticationError
from src.academic_rag.rag.prompts import NCERT_TUTOR_SYSTEM_PROMPT
from src.academic_rag.rag.retriever import retrieve_ncert_context

logger = logging.getLogger(__name__)


async def stream_ncert_rag_response(
    query: str,
    class_filter: Optional[int],
    api_key: Optional[str] = None,
    model_name: Optional[str] = None,
    chat_history: Optional[List[Dict[str, str]]] = None,
    top_k: int = 5,
) -> AsyncGenerator[str, None]:
    """
    Direct NCERT RAG streaming engine.
    1. Retrieves top NCERT chunks from Pinecone filtered by Class level.
    2. Directly invokes Gemini via OpenAI-compatible endpoint.
    3. Streams response token-by-token with grounded textbook explanations & exact page citations.
    """
    active_key = config.get_google_api_key(override=api_key)
    if not active_key:
        raise AuthenticationError("Google Gemini API key is required.")

    active_model = model_name or config.default_llm_model

    # 1. Retrieve NCERT Context
    context = retrieve_ncert_context(query, class_filter=class_filter, top_k=top_k)

    # 2. Build Messages
    messages = [{"role": "system", "content": NCERT_TUTOR_SYSTEM_PROMPT}]

    if chat_history:
        for msg in chat_history[-4:]:
            if msg.get("content"):
                messages.append({"role": msg["role"], "content": msg["content"]})

    user_content = f"""NCERT TEXTBOOK EXCERPTS:
{context}

STUDENT QUESTION:
{query}

Please provide a thorough, pedagogically structured explanation with step-by-step reasoning followed by the exact NCERT citation:"""

    messages.append({"role": "user", "content": user_content})

    client = AsyncOpenAI(
        base_url=config.gemini_base_url,
        api_key=active_key,
    )

    response_stream = await client.chat.completions.create(
        model=active_model,
        messages=messages,
        stream=True,
        temperature=0.2,
    )

    async for chunk in response_stream:
        if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content
