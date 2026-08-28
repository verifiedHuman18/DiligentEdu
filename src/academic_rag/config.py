"""Configuration module for DiligentEdu NCERT Academic Science RAG Assistant."""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Ensure environment variables are loaded
load_dotenv()


@dataclass(frozen=True)
class AppConfig:
    """Centralized application configuration."""

    # Project directories
    project_root: Path = field(
        default_factory=lambda: Path(__file__).resolve().parent.parent.parent
    )

    # Storage paths
    @property
    def data_dir(self) -> Path:
        return self.project_root / "data"

    @property
    def storage_dir(self) -> Path:
        return self.data_dir / "storage"

    @property
    def default_db_path(self) -> Path:
        return self.storage_dir / "quiz_history.db"

    @property
    def mapping_file_path(self) -> Path:
        return self.data_dir / "metadata" / "ncert_mapping.json"

    @property
    def class9_sci_dir(self) -> Path:
        return self.data_dir / "class9_sci"

    @property
    def class10_sci_dir(self) -> Path:
        return self.data_dir / "class10_sci"

    @property
    def class9_math_dir(self) -> Path:
        p = self.data_dir / "class9_maths"
        return p if p.exists() else self.data_dir / "class9_math"

    @property
    def class10_math_dir(self) -> Path:
        p = self.data_dir / "class10_maths"
        return p if p.exists() else self.data_dir / "class10_math"

    def get_corpus_dir(self, class_level: int, subject: str = "Science") -> Path:
        """Resolves the authoritative NCERT PDF directory for a (class_level, subject) pair."""
        subj_clean = str(subject).strip().lower()
        cls_int = int(class_level)
        if "math" in subj_clean:
            return self.class9_math_dir if cls_int == 9 else self.class10_math_dir
        return self.class9_sci_dir if cls_int == 9 else self.class10_sci_dir

    @property
    def scholarships_data_dir(self) -> Path:
        return self.data_dir / "scholarships"

    @property
    def scholarships_raw_dir(self) -> Path:
        return self.scholarships_data_dir / "raw"

    @property
    def scholarships_structured_dir(self) -> Path:
        return self.scholarships_data_dir / "structured"

    @property
    def scholarships_sources_file(self) -> Path:
        return self.project_root / "scholarships" / "sources.json"

    @property
    def logs_dir(self) -> Path:
        return self.project_root / "logs"

    # AI & Model configuration
    default_llm_model: str = "gemini-3.5-flash-lite"
    fallback_llm_model: str = "gemini-flash-lite-latest"
    embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    pinecone_index_name: str = os.getenv("PINECONE_INDEX_NAME", "ncert-science")
    gemini_base_url: str = "https://generativelanguage.googleapis.com/v1beta/openai/"

    # Analytics Thresholds
    strong_threshold: float = 70.0
    average_threshold: float = 50.0

    # Study Material Ingestion Configuration
    max_upload_size_bytes: int = 25 * 1024 * 1024  # 25 MB
    pinecone_student_namespace: str = os.getenv("PINECONE_STUDENT_NAMESPACE", "student-materials")
    min_pdf_extracted_chars_per_page: int = 20
    student_chunk_size: int = 700
    student_chunk_overlap: int = 120
    debug_rag: bool = os.getenv("DEBUG_RAG", "false").lower() in ("true", "1", "yes")

    # API Keys resolution
    def get_google_api_key(self, override: Optional[str] = None) -> Optional[str]:
        if override and str(override).strip():
            return str(override).strip()
        try:
            from src.academic_rag.ai.api_config import (
                get_primary_api_key,
                get_user_fallback_api_key,
            )

            return get_primary_api_key() or get_user_fallback_api_key()
        except Exception:
            pass
        return os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")

    def get_pinecone_api_key(self, override: Optional[str] = None) -> Optional[str]:
        if override and str(override).strip():
            return str(override).strip()
        try:
            import streamlit as st

            if hasattr(st, "secrets") and "PINECONE_API_KEY" in st.secrets:
                return str(st.secrets["PINECONE_API_KEY"]).strip()
        except Exception:
            pass
        return os.getenv("PINECONE_API_KEY")


# Global configuration instance
config = AppConfig()

# Export commonly used constants for convenience
PROJECT_ROOT = str(config.project_root)
DATA_DIR = str(config.data_dir)
STORAGE_DIR = str(config.storage_dir)
DEFAULT_DB_PATH = str(config.default_db_path)
MAPPING_FILE = str(config.mapping_file_path)
EMBEDDING_MODEL_NAME = config.embedding_model_name
PINECONE_INDEX_NAME = config.pinecone_index_name
INDEX_NAME = PINECONE_INDEX_NAME
DEFAULT_MODEL = config.default_llm_model
STRONG_THRESHOLD = config.strong_threshold
AVERAGE_THRESHOLD = config.average_threshold
MAX_UPLOAD_SIZE_BYTES = config.max_upload_size_bytes
PINECONE_STUDENT_NAMESPACE = config.pinecone_student_namespace
STUDENT_CHUNK_SIZE = config.student_chunk_size
STUDENT_CHUNK_OVERLAP = config.student_chunk_overlap
DEBUG_RAG = config.debug_rag
