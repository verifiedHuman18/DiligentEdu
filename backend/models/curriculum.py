"""Curriculum and chapter models."""

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class ChapterInfo:
    """Represents an individual textbook chapter."""

    chapter_number: int
    chapter_title: str
    filename: str
    class_level: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chapter_number": self.chapter_number,
            "chapter": self.chapter_title,
            "filename": self.filename,
            "class_level": self.class_level,
        }


@dataclass
class ChapterSummaryStatus:
    """Chapter with student SWAT overlay for selection views."""

    chapter_number: int
    chapter_title: str
    filename: str
    status: str  # 'strong', 'average', 'weak', 'not_attempted'
    score: Optional[int]
    attempts: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chapter_number": self.chapter_number,
            "chapter": self.chapter_title,
            "filename": self.filename,
            "status": self.status,
            "score": self.score,
            "attempts": self.attempts,
        }
