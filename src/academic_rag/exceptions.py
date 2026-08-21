"""Domain-specific exceptions for the Academic RAG Assistant."""


class AcademicRAGError(Exception):
    """Base exception for all Academic RAG errors."""

    pass


class ConfigurationError(AcademicRAGError):
    """Raised when configuration or required credentials are missing/invalid."""

    pass


class AuthenticationError(AcademicRAGError):
    """Raised when API keys or authentication credentials fail."""

    pass


class CurriculumError(AcademicRAGError):
    """Raised when syllabus or chapter resolution fails."""

    pass


class ChapterNotFoundError(CurriculumError):
    """Raised when a specific chapter cannot be located in the curriculum."""

    pass


class RetrievalError(AcademicRAGError):
    """Raised when vector retrieval from Pinecone fails."""

    pass


class QuizGenerationError(AcademicRAGError):
    """Raised when LLM quiz generation or schema parsing fails."""

    pass


class StorageError(AcademicRAGError):
    """Raised when database operations encounter errors."""

    pass
