"""Data models for Study Twin academic matching system."""

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class StudyTwinProfile:
    """Represents a student's academic profile derived from SWAT and Action Plan."""

    student_id: str
    class_level: int
    subject: str
    current_chapters: List[str] = field(default_factory=list)
    weak_topics: List[str] = field(default_factory=list)
    average_topics: List[str] = field(default_factory=list)
    strong_topics: List[str] = field(default_factory=list)
    unattempted_topics: List[str] = field(default_factory=list)
    topic_mastery: Dict[str, float] = field(default_factory=dict)
    action_plan_priorities: List[str] = field(default_factory=list)
    quizzes_attempted: int = 0
    total_questions: int = 0
    has_sufficient_data: bool = False
    last_activity_timestamp: Optional[str] = None
    last_updated: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class StudyTwinMatch:
    """Represents an anonymous academic match between two students."""

    student_id: str
    twin_student_id: str  # Internal identifier only; never exposed publicly to UI
    class_level: int
    subject: str
    similarity_score: float  # 0.0 to 100.0%
    shared_current_chapters: List[str] = field(default_factory=list)
    shared_weak_topics: List[str] = field(default_factory=list)
    shared_action_goals: List[str] = field(default_factory=list)
    component_scores: Dict[str, float] = field(default_factory=dict)
    explanation: str = ""
    status: str = "active"  # "active", "insufficient_data", "no_strong_match"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
