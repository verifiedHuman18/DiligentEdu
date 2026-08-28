"""Storage package."""

from src.academic_rag.storage.database import (
    get_db_connection,
    init_database,
)
from src.academic_rag.storage.repository import (
    QuizRepository,
    StudyMaterialRepository,
    delete_student_study_material,
    get_student_class_history,
    get_student_study_materials,
    quiz_repository,
    study_material_repository,
)

__all__ = [
    "init_database",
    "get_db_connection",
    "QuizRepository",
    "quiz_repository",
    "get_student_class_history",
    "StudyMaterialRepository",
    "study_material_repository",
    "get_student_study_materials",
    "delete_student_study_material",
]
