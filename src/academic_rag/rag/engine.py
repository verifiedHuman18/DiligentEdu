"""Direct NCERT RAG Streaming Engine (Zero tool-calling overhead / 1 single request)."""

import logging
from typing import AsyncGenerator, Dict, List, Optional

from src.academic_rag.ai.client_factory import stream_chat_completion
from src.academic_rag.config import config
from src.academic_rag.rag.prompts import NCERT_TUTOR_SYSTEM_PROMPT
from src.academic_rag.rag.retriever import retrieve_hybrid_academic_context

logger = logging.getLogger(__name__)


async def stream_ncert_rag_response(
    query: str,
    class_filter: Optional[int] = None,
    grade: Optional[int] = None,
    student_id: Optional[str] = None,
    api_key: Optional[str] = None,
    model_name: Optional[str] = None,
    chat_history: Optional[List[Dict[str, str]]] = None,
    top_k: int = 5,
    **kwargs,
) -> AsyncGenerator[str, None]:
    """
    Direct NCERT + Student Study Material RAG streaming engine.
    1. Retrieves authoritative NCERT chunks and supplementary student material chunks.
    2. Invokes Gemini via centralized stream_chat_completion factory.
    3. Streams response token-by-token with dual-source citations.
    """
    effective_class_filter = grade if grade is not None else class_filter
    active_model = model_name or config.default_llm_model

    # 1. Retrieve Hybrid Context (NCERT + Student Reference Material)
    hybrid_result = retrieve_hybrid_academic_context(
        query=query,
        student_id=student_id,
        class_filter=effective_class_filter,
        ncert_top_k=top_k,
        student_top_k=3,
        api_key=api_key,
    )
    context_text = hybrid_result["combined_context"]

    # 2. Build Messages
    messages = [{"role": "system", "content": NCERT_TUTOR_SYSTEM_PROMPT}]

    if chat_history:
        for msg in chat_history[-4:]:
            if msg.get("content"):
                messages.append({"role": msg["role"], "content": msg["content"]})

    user_content = f"""{context_text}

STUDENT QUESTION:
{query}

Please provide a thorough, pedagogically structured explanation with step-by-step reasoning followed by exact citations:"""

    messages.append({"role": "user", "content": user_content})

    from src.academic_rag.config import DEBUG_RAG

    if DEBUG_RAG:
        logger.info(
            f"[DEBUG_RAG] Streaming LLM Request (Model: {active_model}):\n"
            f"  System Prompt Length: {len(NCERT_TUTOR_SYSTEM_PROMPT)} chars\n"
            f"  History Messages: {len(messages) - 2}\n"
            f"  User Prompt Length: {len(user_content)} chars\n"
            f"  User Payload Snippet:\n{user_content[:400]}..."
        )

    async for chunk in stream_chat_completion(
        messages=messages,
        model=active_model,
        temperature=0.2,
        override_api_key=api_key,
    ):
        yield chunk
