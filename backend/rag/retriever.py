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
    subject_filter: Optional[str] = "Science",
    top_k: int = 4,
    api_key: Optional[str] = None,
) -> str:
    """
    Retrieves representative, rich NCERT textbook chunks from Pinecone.
    Preserves exact class, subject, chapter name, chapter number, and page number metadata.
    """
    try:
        embeddings = get_embeddings()
        index = get_pinecone_index(api_key=api_key)

        filter_dict: Dict[str, Any] = {}
        if class_filter is not None:
            filter_dict["class"] = {"$eq": int(class_filter)}
        if chapter_filter is not None:
            filter_dict["chapter_number"] = {"$eq": int(chapter_filter)}
        if subject_filter is not None:
            subj_val = "Mathematics" if "math" in str(subject_filter).lower() else "Science"
            filter_dict["subject"] = {"$eq": subj_val}

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
            subj_name = meta.get("subject", "Science")
            ch_name = meta.get("chapter", subj_name)
            page_num = int(meta.get("page", 0))
            text = meta.get("text", "").strip()

            chunk_header = f"[SOURCE: NCERT Class {cls_num} {subj_name} | CHAPTER {ch_num}: {ch_name} | PAGE: {page_num}]"
            formatted_chunks.append(f"{chunk_header}\n{text}")

        return "\n\n---\n\n".join(formatted_chunks)

    except Exception as e:
        logger.error(f"Error retrieving NCERT context: {e}")
        raise RetrievalError(f"Vector search retrieval failed: {e}")


def retrieve_student_material_context(
    query: str,
    student_id: str,
    class_filter: Optional[int] = None,
    chapter_filter: Optional[str] = None,
    subject_filter: Optional[str] = None,
    top_k: int = 3,
    api_key: Optional[str] = None,
) -> str:
    """
    Retrieves student-uploaded reference material chunks from Pinecone.
    Strictly isolates vectors by student_id, class level, and subject.
    """
    clean_student_id = str(student_id).strip()
    if not clean_student_id:
        return ""

    try:
        from src.academic_rag.config import DEBUG_RAG, PINECONE_STUDENT_NAMESPACE
        from src.academic_rag.storage.repository import study_material_repository

        # Quick check: does student have any READY uploaded materials?
        ready_docs = study_material_repository.get_student_documents(
            student_id=clean_student_id, class_level=class_filter, subject=subject_filter
        )
        ready_docs = [d for d in ready_docs if d.get("status") == "READY"]
        if not ready_docs:
            if DEBUG_RAG:
                logger.info(
                    f"[DEBUG_RAG] No READY documents found for student '{clean_student_id}' in class {class_filter}"
                )
            return ""

        embeddings = get_embeddings()
        index = get_pinecone_index(api_key=api_key)

        filter_dict: Dict[str, Any] = {
            "student_id": {"$eq": clean_student_id},
        }
        if class_filter is not None:
            filter_dict["class"] = {"$eq": int(class_filter)}
        if subject_filter is not None:
            subj_val = "Mathematics" if "math" in str(subject_filter).lower() else "Science"
            filter_dict["subject"] = {"$eq": subj_val}

        # Semantic retrieval is primary; chapter filter is applied loosely if available
        query_vector = embeddings.embed_query(query)
        results = index.query(
            vector=query_vector,
            top_k=top_k,
            include_metadata=True,
            filter=filter_dict,
            namespace=PINECONE_STUDENT_NAMESPACE,
        )

        matches = results.get("matches", [])
        if not matches:
            if DEBUG_RAG:
                logger.info(
                    f"[DEBUG_RAG] 0 matches returned from Pinecone student namespace for query='{query}'"
                )
            return ""

        formatted_chunks = []
        matched_docs_info = []

        for match in matches:
            meta = match.get("metadata", {})
            score = match.get("score")
            # Verify student_id and class match to guarantee isolation
            if meta.get("student_id") != clean_student_id:
                continue
            if class_filter is not None and int(
                meta.get("class", meta.get("class_level", 0))
            ) != int(class_filter):
                continue
            if subject_filter is not None:
                meta_subj = str(meta.get("subject", "")).lower()
                target_subj = "mathematics" if "math" in str(subject_filter).lower() else "science"
                if meta_subj and meta_subj != target_subj:
                    continue

            mat_name = meta.get("material_name") or meta.get("filename", "Reference Material")
            filename = meta.get("filename", "")
            page_num = int(meta.get("page", 0))
            text = meta.get("text", "").strip()

            chunk_header = f"[SOURCE: STUDENT REFERENCE MATERIAL | TITLE: {mat_name} ({filename}) | PAGE: {page_num}]"
            formatted_chunks.append(f"{chunk_header}\n{text}")
            matched_docs_info.append(
                f"{mat_name} (p.{page_num}, score={score:.3f})"
                if score is not None
                else f"{mat_name} (p.{page_num})"
            )

        if DEBUG_RAG:
            logger.info(
                f"[DEBUG_RAG] Student Material Matches ({len(formatted_chunks)}): {', '.join(matched_docs_info)}"
            )

        return "\n\n---\n\n".join(formatted_chunks)

    except Exception as e:
        logger.warning(f"Failed to retrieve student material context: {e}")
        return ""


def retrieve_hybrid_academic_context(
    query: str,
    student_id: Optional[str] = None,
    class_filter: Optional[int] = None,
    subject_filter: Optional[str] = "Science",
    chapter_filter: Optional[Any] = None,
    ncert_top_k: int = 4,
    student_top_k: int = 3,
    api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Retrieves both authoritative NCERT context and supplementary student reference context.
    Returns structured dictionary with segregated context and merged formatted block.
    """
    from src.academic_rag.config import DEBUG_RAG

    # 1. Retrieve NCERT context (authoritative)
    ch_num = chapter_filter if isinstance(chapter_filter, int) else None
    ncert_ctx = retrieve_ncert_context(
        query=query,
        class_filter=class_filter,
        chapter_filter=ch_num,
        subject_filter=subject_filter,
        top_k=ncert_top_k,
        api_key=api_key,
    )

    # 2. Retrieve Student Material context (supplementary)
    student_ctx = ""
    if student_id:
        student_ctx = retrieve_student_material_context(
            query=query,
            student_id=student_id,
            class_filter=class_filter,
            subject_filter=subject_filter,
            top_k=student_top_k,
            api_key=api_key,
        )

    # 3. Format Combined Context with explicit source demarcation
    has_student = bool(student_ctx and student_ctx.strip())
    has_ncert = bool(ncert_ctx and ncert_ctx.strip())

    combined_parts = []
    if has_ncert:
        combined_parts.append(f"=== OFFICIAL NCERT TEXTBOOK EXCERPTS ===\n{ncert_ctx}")
    else:
        combined_parts.append(
            "=== OFFICIAL NCERT TEXTBOOK EXCERPTS ===\n[No direct NCERT textbook excerpt matches found]"
        )

    if has_student:
        combined_parts.append(
            f"=== STUDENT REFERENCE MATERIAL (SUPPLEMENTARY EXCERPTS) ===\n{student_ctx}"
        )

    combined_text = "\n\n========================================\n\n".join(combined_parts)

    if DEBUG_RAG:
        logger.info(
            f"[DEBUG_RAG] Hybrid Retrieval Complete:\n"
            f"  Query: '{query}'\n"
            f"  Class Filter: {class_filter} | Student: '{student_id}'\n"
            f"  NCERT Excerpt Size: {len(ncert_ctx)} chars\n"
            f"  Student Excerpt Size: {len(student_ctx)} chars\n"
            f"  Has Student Context: {has_student}"
        )

    return {
        "ncert_context": ncert_ctx,
        "student_context": student_ctx,
        "combined_context": combined_text,
        "has_student_context": has_student,
    }


def delete_student_material_vectors(
    document_id: str,
    student_id: Optional[str] = None,
    api_key: Optional[str] = None,
) -> bool:
    """
    Deletes all Pinecone vector embeddings associated with document_id from the student namespace.
    """
    clean_doc_id = str(document_id).strip()
    if not clean_doc_id:
        return False

    try:
        from src.academic_rag.config import PINECONE_STUDENT_NAMESPACE

        index = get_pinecone_index(api_key=api_key)
        filter_dict = {"document_id": {"$eq": clean_doc_id}}
        if student_id:
            filter_dict["student_id"] = {"$eq": str(student_id).strip()}

        index.delete(filter=filter_dict, namespace=PINECONE_STUDENT_NAMESPACE)
        logger.info(
            f"Successfully deleted vectors for document {clean_doc_id} in namespace '{PINECONE_STUDENT_NAMESPACE}'"
        )
        return True
    except Exception as e:
        logger.error(f"Failed to delete vectors for document {clean_doc_id}: {e}")
        return False
