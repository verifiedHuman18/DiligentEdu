"""DiligentEdu - NCERT Academic Science RAG Assistant & Intelligent Tutor package."""

__version__ = "0.1.0"

import io
import logging
from typing import Any, Dict, List, Optional, Union

from backend.analytics.action_plan import (
    generate_action_plan,
    get_teacher_action_plan,
    reset_teacher_action_plan,
    save_teacher_action_plan,
)
from backend.analytics.knowledge_graph import (
    get_available_knowledge_map_chapters,
    get_chapter_knowledge_graph,
)
from backend.analytics.swat import (
    format_swat_report,
    get_attempted_chapters,
    get_available_chapters,
    get_student_swat,
    get_unattempted_chapters,
)
from backend.analytics.teacher import (
    get_student_status,
    get_teacher_chapter_statistics,
    get_teacher_quiz_history,
    get_teacher_student_overview,
    get_teacher_student_profile,
)
from backend.config import config
from backend.curriculum.service import (
    curriculum_service,
    get_chapter_pdf,
    get_ncert_curriculum,
)
from backend.quiz.adaptive import get_next_quiz_config
from backend.quiz.evaluator import submit_and_grade_quiz
from backend.quiz.generator import (
    create_student_quiz,
    generate_quiz,
)
from backend.rag.engine import stream_ncert_rag_response
from backend.rag.retriever import retrieve_ncert_context
from backend.storage.repository import (
    count_student_study_materials,
    delete_student_study_material,
    get_student_class_history,
    get_student_study_materials,
    quiz_repository,
    study_material_repository,
)

logger = logging.getLogger(__name__)


def upload_study_material(
    student_id: str,
    file_data: Union[bytes, io.BytesIO],
    filename: str,
    material_name: Optional[str] = None,
    class_level: int = 10,
    subject: str = "Science",
    chapter: Optional[str] = None,
    pinecone_api_key: Optional[str] = None,
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Ingests, chunks, embeds, and indexes uploaded study material for a specific student, class, and subject."""
    from src.academic_rag.ingestion.pdf_ingester import ingest_study_material_pdf

    return ingest_study_material_pdf(
        student_id=student_id,
        file_data=file_data,
        filename=filename,
        material_name=material_name,
        class_level=class_level,
        subject=subject,
        chapter=chapter,
        pinecone_api_key=pinecone_api_key,
        db_path=db_path,
    )


def delete_study_material(
    document_id: str,
    student_id: Optional[str] = None,
    db_path: Optional[str] = None,
    pinecone_api_key: Optional[str] = None,
) -> bool:
    """Deletes a student study material record from SQLite and its vectors from Pinecone."""
    from backend.rag.retriever import get_pinecone_index

    # 1. Delete SQLite record
    success = delete_student_study_material(
        document_id=document_id, student_id=student_id, db_path=db_path
    )

    # 2. Delete Pinecone vectors under namespace 'student-materials'
    try:
        index = get_pinecone_index(api_key=pinecone_api_key)
        index.delete(
            namespace="student-materials",
            filter={"document_id": {"$eq": document_id}},
        )
    except Exception as e:
        logger.warning(f"Could not delete Pinecone vectors for {document_id}: {e}")

    return success


# Aliases for unified contracts
get_student_action_plan = generate_action_plan
get_chapters_with_status = get_available_chapters
get_teacher_swat = get_student_swat
upload_student_study_material = upload_study_material
delete_student_study_material_record = delete_study_material

__all__ = [
    "config",
    "curriculum_service",
    "get_ncert_curriculum",
    "get_chapter_pdf",
    "quiz_repository",
    "study_material_repository",
    "get_student_class_history",
    "get_student_study_materials",
    "count_student_study_materials",
    "upload_study_material",
    "delete_study_material",
    "delete_student_study_material",
    "retrieve_ncert_context",
    "stream_ncert_rag_response",
    "generate_quiz",
    "create_student_quiz",
    "submit_and_grade_quiz",
    "get_next_quiz_config",
    "get_student_swat",
    "get_student_action_plan",
    "get_chapters_with_status",
    "get_available_chapters",
    "get_attempted_chapters",
    "get_unattempted_chapters",
    "generate_action_plan",
    "format_swat_report",
    "get_teacher_student_overview",
    "get_teacher_swat",
    "get_teacher_action_plan",
    "save_teacher_action_plan",
    "reset_teacher_action_plan",
    "get_teacher_chapter_statistics",
    "get_teacher_quiz_history",
    "get_student_status",
    "get_teacher_student_profile",
    "get_chapter_knowledge_graph",
    "get_available_knowledge_map_chapters",
]

