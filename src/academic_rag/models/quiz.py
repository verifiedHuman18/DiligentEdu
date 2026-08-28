"""Quiz and Question data models."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class QuizQuestion:
    """Individual MCQ Question with answer key and NCERT citations."""

    question: str
    options: List[str]
    correct_answer: str  # 'A', 'B', 'C', or 'D'
    explanation: str
    difficulty: str
    chapter: str
    source_pages: List[int] = field(default_factory=list)
    question_id: Optional[str] = None
    concept_id: Optional[str] = None
    concepts: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        data = {
            "question": self.question,
            "options": self.options,
            "correct_answer": self.correct_answer,
            "explanation": self.explanation,
            "difficulty": self.difficulty,
            "chapter": self.chapter,
            "source_pages": self.source_pages,
        }
        if self.question_id:
            data["question_id"] = self.question_id
        if self.concept_id:
            data["concept_id"] = self.concept_id
        if self.concepts:
            data["concepts"] = self.concepts
        return data


@dataclass
class QuizData:
    """Complete structured quiz specification."""

    class_level: int
    chapter: str
    chapter_number: int
    difficulty: str
    total_questions: int
    questions: List[QuizQuestion]
    student_id: Optional[str] = None
    quiz_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        data = {
            "class_level": self.class_level,
            "chapter": self.chapter,
            "chapter_number": self.chapter_number,
            "difficulty": self.difficulty,
            "total_questions": self.total_questions,
            "questions": [q.to_dict() for q in self.questions],
        }
        if self.student_id:
            data["student_id"] = self.student_id
        if self.quiz_id:
            data["quiz_id"] = self.quiz_id
        return data


@dataclass
class QuestionFeedback:
    """Question-level evaluation result for student review."""

    question_id: str
    question_text: str
    options: List[str]
    user_answer: str
    correct_answer: str
    is_correct: bool
    explanation: str
    source_pages: List[int] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "question_id": self.question_id,
            "question_text": self.question_text,
            "options": self.options,
            "user_answer": self.user_answer,
            "correct_answer": self.correct_answer,
            "is_correct": self.is_correct,
            "explanation": self.explanation,
            "source_pages": self.source_pages,
        }


@dataclass
class QuizSubmissionResult:
    """Complete evaluation and SWAT delta summary after quiz submission."""

    student_id: str
    quiz_id: str
    class_level: int
    chapter: str
    difficulty: str
    score: int
    total: int
    percentage: int
    previous_chapter_score: Optional[int]
    previous_status: str
    new_chapter_score: int
    new_status: str
    status_changed: bool
    status_change_summary: str
    timestamp: str
    question_feedback: List[QuestionFeedback]
    updated_swat: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "student_id": self.student_id,
            "quiz_id": self.quiz_id,
            "class_level": self.class_level,
            "chapter": self.chapter,
            "difficulty": self.difficulty,
            "score": self.score,
            "total": self.total,
            "percentage": self.percentage,
            "previous_chapter_score": self.previous_chapter_score,
            "previous_status": self.previous_status,
            "new_chapter_score": self.new_chapter_score,
            "new_status": self.new_status,
            "status_changed": self.status_changed,
            "status_change_summary": self.status_change_summary,
            "timestamp": self.timestamp,
            "question_feedback": [qf.to_dict() for qf in self.question_feedback],
            "updated_swat": self.updated_swat,
        }
