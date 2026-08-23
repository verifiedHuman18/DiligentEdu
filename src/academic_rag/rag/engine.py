"""Direct NCERT RAG Streaming Engine (Zero tool-calling overhead / 1 single request)."""

import logging
from typing import AsyncGenerator, Dict, List, Optional

from src.academic_rag.ai.client_factory import stream_chat_completion
from src.academic_rag.config import config
from src.academic_rag.rag.prompts import NCERT_TUTOR_SYSTEM_PROMPT
from src.academic_rag.rag.retriever import retrieve_ncert_context

logger = logging.getLogger(__name__)


async def stream_ncert_rag_response(
    query: str,
    class_filter: Optional[int] = None,
    grade: Optional[int] = None,
    api_key: Optional[str] = None,
    model_name: Optional[str] = None,
    chat_history: Optional[List[Dict[str, str]]] = None,
    top_k: int = 5,
    **kwargs,
) -> AsyncGenerator[str, None]:
    """
    Direct NCERT RAG streaming engine with centralized Gemini client and automated fallback.
    1. Retrieves top NCERT chunks from Pinecone filtered by Class level.
    2. Invokes Gemini via centralized stream_chat_completion factory.
    3. Streams response token-by-token with grounded textbook explanations & exact page citations.
    """
    effective_class_filter = grade if grade is not None else class_filter
    active_model = model_name or config.default_llm_model

    # 1. Retrieve NCERT Context
    context = retrieve_ncert_context(query, class_filter=effective_class_filter, top_k=top_k)

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

    async for chunk in stream_chat_completion(
        messages=messages,
        model=active_model,
        temperature=0.2,
        override_api_key=api_key,
    ):
        yield chunk
