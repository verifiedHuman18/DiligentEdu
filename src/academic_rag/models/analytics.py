"""Analytics, SWAT and Teacher Diagnostics models."""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class SWATTopicItem:
    """A chapter item in a SWAT category (Strong, Average, Weak)."""

    chapter: str
    score: int
    accuracy: float
    attempts: int
    questions: int
    correct: int
    category: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chapter": self.chapter,
            "score": self.score,
            "accuracy": self.accuracy,
            "attempts": self.attempts,
            "questions": self.questions,
            "correct": self.correct,
            "category": self.category,
        }


@dataclass
class TrendInfo:
    """Performance trend details."""

    direction: str  # 'improving', 'declining', 'stable', 'no_data'
    recent_average: int
    earlier_average: int
    summary: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "direction": self.direction,
            "recent_average": self.recent_average,
            "earlier_average": self.earlier_average,
            "summary": self.summary,
        }


@dataclass
class OverallMetrics:
    """Overall lifetime student performance metrics."""

    average: int
    accuracy: int
    quizzes_attempted: int
    total_questions: int
    total_correct: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "average": self.average,
            "accuracy": self.accuracy,
            "quizzes_attempted": self.quizzes_attempted,
            "total_questions": self.total_questions,
            "total_correct": self.total_correct,
        }


@dataclass
class StudentSWATReport:
    """Complete student SWAT performance profile."""

    student_id: str
    has_data: bool
    overall: OverallMetrics
    strengths: List[SWATTopicItem]
    average_topics: List[SWATTopicItem]
    weak_topics: List[SWATTopicItem]
    chapter_breakdown: Dict[str, Dict[str, Any]]
    trend: TrendInfo

    def to_dict(self) -> Dict[str, Any]:
        return {
            "student_id": self.student_id,
            "has_data": self.has_data,
            "overall": self.overall.to_dict(),
            "strengths": [s.to_dict() for s in self.strengths],
            "average_topics": [a.to_dict() for a in self.average_topics],
            "weak_topics": [w.to_dict() for w in self.weak_topics],
            "chapter_breakdown": self.chapter_breakdown,
            "trend": self.trend.to_dict(),
        }


@dataclass
class EarlyWarningAlert:
    """Teacher early-warning alert message."""

    type: str  # 'weak_topic', 'declining_trend'
    message: str
    chapter: Optional[str] = None
    score: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        d = {"type": self.type, "message": self.message}
        if self.chapter:
            d["chapter"] = self.chapter
        if self.score is not None:
            d["score"] = self.score
        return d


@dataclass
class TeacherStudentStatus:
    """Student standing evaluation with early-warning alerts for teachers."""

    student_id: str
    has_data: bool
    overall_status: str
    status_code: str
    status_icon: str
    overall_average: int
    total_quizzes: int
    trend: Dict[str, Any]
    alerts: List[EarlyWarningAlert]
    weak_topics: List[str]
    positive_notes: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "student_id": self.student_id,
            "has_data": self.has_data,
            "overall_status": self.overall_status,
            "status_code": self.status_code,
            "status_icon": self.status_icon,
            "overall_average": self.overall_average,
            "total_quizzes": self.total_quizzes,
            "trend": self.trend,
            "alerts": [a.to_dict() for a in self.alerts],
            "weak_topics": self.weak_topics,
            "positive_notes": self.positive_notes,
        }
