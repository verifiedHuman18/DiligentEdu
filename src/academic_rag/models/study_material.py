"""Data models for Student Uploaded Study Material (Phases 1-23)."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class DocumentStatus(str, Enum):
    """Lifecycle status of an uploaded document."""

    PROCESSING = "PROCESSING"
    READY = "READY"
    FAILED = "FAILED"


class UploadedDocument(BaseModel):
    """Represents a student-uploaded study document."""

    document_id: str
    student_id: str
    filename: str
    material_name: str
    class_level: int
    subject: str = "Science"
    chapter: Optional[str] = None
    status: DocumentStatus = DocumentStatus.PROCESSING
    error_message: Optional[str] = None
    page_count: int = 0
    chunk_count: int = 0
    file_size_bytes: int = 0
    uploaded_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


@dataclass
class DocumentChunk:
    """Represents a chunk extracted from an uploaded document with preserved page and source metadata."""

    chunk_id: str
    document_id: str
    student_id: str
    text: str
    page: int
    chunk_index: int
    filename: str
    material_name: str
    class_level: int
    subject: str = "Science"
    chapter: Optional[str] = None
    source_type: str = "user_upload"

    def to_metadata(self) -> Dict[str, Any]:
        """Converts chunk into Pinecone vector metadata dictionary."""
        meta = {
            "chunk_id": self.chunk_id,
            "document_id": self.document_id,
            "student_id": self.student_id,
            "text": self.text,
            "page": int(self.page),
            "chunk_index": int(self.chunk_index),
            "filename": self.filename,
            "material_name": self.material_name,
            "class": int(self.class_level),
            "class_level": int(self.class_level),
            "subject": self.subject,
            "source_type": self.source_type,
        }
        if self.chapter:
            meta["chapter"] = self.chapter
        return meta


@dataclass
class DocumentValidationResult:
    """Result of validating an uploaded file before ingestion."""

    is_valid: bool
    error_message: Optional[str] = None
    file_size_bytes: int = 0
    detected_pages: int = 0
    is_scanned_pdf: bool = False
