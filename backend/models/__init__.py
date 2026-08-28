"""Domain models package."""

from backend.models.analytics import (
    EarlyWarningAlert,
    OverallMetrics,
    StudentSWATReport,
    SWATTopicItem,
    TeacherStudentStatus,
    TrendInfo,
)
from backend.models.curriculum import (
    ChapterInfo,
    ChapterSummaryStatus,
)
from backend.models.quiz import (
    QuestionFeedback,
    QuizData,
    QuizQuestion,
    QuizSubmissionResult,
)
from src.academic_rag.models.knowledge_graph import (
    ChapterKnowledgeGraph,
    ConceptEdge,
    ConceptNode,
    ConceptStatus,
    EdgeRelationship,
)
from src.academic_rag.models.study_material import (
    DocumentChunk,
    DocumentStatus,
    DocumentValidationResult,
    UploadedDocument,
)

__all__ = [
    "ChapterInfo",
    "ChapterSummaryStatus",
    "QuizQuestion",
    "QuizData",
    "QuestionFeedback",
    "QuizSubmissionResult",
    "SWATTopicItem",
    "TrendInfo",
    "OverallMetrics",
    "StudentSWATReport",
    "EarlyWarningAlert",
    "TeacherStudentStatus",
    "UploadedDocument",
    "DocumentChunk",
    "DocumentStatus",
    "DocumentValidationResult",
    "ConceptNode",
    "ConceptEdge",
    "ChapterKnowledgeGraph",
    "ConceptStatus",
    "EdgeRelationship",
]
