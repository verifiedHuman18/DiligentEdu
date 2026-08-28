"""Quiz package."""

from backend.quiz.adaptive import get_next_quiz_config
from backend.quiz.evaluator import submit_and_grade_quiz
from backend.quiz.generator import (
    create_student_quiz,
    generate_quiz,
    retrieve_chapter_context_for_quiz,
)
from backend.quiz.socrates import (
    enrich_quiz_with_socrates,
    generate_socrates_hints,
    generate_socrates_misconception,
    stream_socrates_dialogue,
)

__all__ = [
    "generate_quiz",
    "create_student_quiz",
    "retrieve_chapter_context_for_quiz",
    "submit_and_grade_quiz",
    "get_next_quiz_config",
    "generate_socrates_hints",
    "generate_socrates_misconception",
    "stream_socrates_dialogue",
    "enrich_quiz_with_socrates",
]
