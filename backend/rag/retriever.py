"""Vector Store Retriever for NCERT Science textbook content in Pinecone."""

import logging
from typing import Any, Dict, Optional

from langchain_huggingface import HuggingFaceEmbeddings
from pinecone import Pinecone

from backend.config import config
from backend.exceptions import AuthenticationError, RetrievalError

logger = logging.getLogger(__name__)

_cached_embeddings = None
_cached_pinecone_index = None


def get_embeddings() -> HuggingFaceEmbeddings:
    """Returns cached or newly initialized HuggingFace embeddings model."""
    global _cached_embeddings
    if _cached_embeddings is None:
        logger.info(f"Initializing embedding model: {config.embedding_model_name}")
        _cached_embeddings = HuggingFaceEmbeddings(model_name=config.embedding_model_name)
    return _cached_embeddings


def get_pinecone_index(api_key: Optional[str] = None):
    """Returns cached or newly initialized Pinecone Index connection."""
    global _cached_pinecone_index
    # Guard against mistakenly passing a Google API key to Pinecone
    clean_override = api_key if (api_key and not str(api_key).startswith("AIza")) else None
    if clean_override is not None:
        active_key = config.get_pinecone_api_key(override=clean_override)
        if not active_key:
            raise AuthenticationError("PINECONE_API_KEY is not set.")
        logger.info(f"Connecting to Pinecone index: {config.pinecone_index_name}")
        pc = Pinecone(api_key=active_key)
        return pc.Index(config.pinecone_index_name)

    if _cached_pinecone_index is None:
        active_key = config.get_pinecone_api_key()
        if not active_key:
            raise AuthenticationError("PINECONE_API_KEY is not set.")
        logger.info(f"Connecting to Pinecone index: {config.pinecone_index_name}")
        pc = Pinecone(api_key=active_key)
        _cached_pinecone_index = pc.Index(config.pinecone_index_name)
    return _cached_pinecone_index


def retrieve_ncert_context(
    query: str,
    class_filter: Optional[int] = None,
    chapter_filter: Optional[int] = None,
    top_k: int = 4,
    api_key: Optional[str] = None,
) -> str:
    """
    Retrieves representative, rich NCERT textbook chunks from Pinecone.
    Preserves exact class, chapter name, chapter number, and page number metadata.
    """
    try:
        embeddings = get_embeddings()
        index = get_pinecone_index(api_key=api_key)

        filter_dict: Dict[str, Any] = {}
        if class_filter is not None:
            filter_dict["class"] = {"$eq": int(class_filter)}
        if chapter_filter is not None:
            filter_dict["chapter_number"] = {"$eq": int(chapter_filter)}

        query_vector = embeddings.embed_query(query)

        query_kwargs = {
            "vector": query_vector,
            "top_k": top_k,
            "include_metadata": True,
        }
        if filter_dict:
            query_kwargs["filter"] = filter_dict

        results = index.query(**query_kwargs)
        matches = results.get("matches", [])

        if not matches:
            return "No matching NCERT textbook content found for this query."

        formatted_chunks = []
        for match in matches:
            meta = match.get("metadata", {})
            cls_num = int(meta.get("class", class_filter or 0))
            ch_num = int(meta.get("chapter_number", chapter_filter or 0))
            ch_name = meta.get("chapter", "Science")
            page_num = int(meta.get("page", 0))
            text = meta.get("text", "").strip()

            chunk_header = f"[SOURCE: NCERT Class {cls_num} Science | CHAPTER {ch_num}: {ch_name} | PAGE: {page_num}]"
            formatted_chunks.append(f"{chunk_header}\n{text}")

        return "\n\n---\n\n".join(formatted_chunks)

    except Exception as e:
        logger.error(f"Error retrieving NCERT context: {e}")
        raise RetrievalError(f"Vector search retrieval failed: {e}")
