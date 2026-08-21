"""RAG package."""

from src.academic_rag.rag.engine import stream_ncert_rag_response
from src.academic_rag.rag.prompts import (
    NCERT_TUTOR_SYSTEM_PROMPT,
    QUIZ_GENERATOR_SYSTEM_PROMPT_TEMPLATE,
)
from src.academic_rag.rag.retriever import (
    get_embeddings,
    get_pinecone_index,
    retrieve_ncert_context,
)

__all__ = [
    "get_embeddings",
    "get_pinecone_index",
    "retrieve_ncert_context",
    "stream_ncert_rag_response",
    "NCERT_TUTOR_SYSTEM_PROMPT",
    "QUIZ_GENERATOR_SYSTEM_PROMPT_TEMPLATE",
]
