"""Repository for quiz attempts, question responses, and student history persistence."""

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from src.academic_rag.config import config
from src.academic_rag.exceptions import StorageError
from src.academic_rag.storage.database import get_db_connection

logger = logging.getLogger(__name__)


class QuizRepository:
    """Provides type-safe CRUD operations for student quiz data."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or str(config.default_db_path)

    def record_attempt(
        self,
        student_id: str,
        quiz_data: Dict[str, Any],
        user_answers: Dict[str, str],
        quiz_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Persists a completed quiz attempt and each question's response record.
        """
        clean_student_id = str(student_id).strip()
        q_id = (
            quiz_id
            or f"quiz_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
        )
        class_level = int(quiz_data.get("class_level", 10))
        chapter = str(quiz_data.get("chapter", "Science"))
        chapter_number = int(quiz_data.get("chapter_number", 0))
        difficulty = str(quiz_data.get("difficulty", "medium")).lower()
        questions = quiz_data.get("questions", [])
        total_questions = len(questions)

        score = 0
        question_records = []

        for idx, q in enumerate(questions, 1):
            q_identifier = q.get("question_id", f"{q_id}_q{idx}")
            q_text = q.get("question", "")
            correct_ans = str(q.get("correct_answer", "A")).strip().upper()
            if len(correct_ans) > 1 and correct_ans.startswith(("A", "B", "C", "D")):
                correct_ans = correct_ans[0]

            u_ans = user_answers.get(
                f"q_choice_{idx}",
                user_answers.get(str(idx), user_answers.get(q_identifier, "")),
            )
            u_ans_clean = str(u_ans).strip()

            is_corr = False
            if u_ans_clean:
                if (
                    u_ans_clean.upper().startswith(correct_ans)
                    or u_ans_clean.upper() == correct_ans
                ):
                    is_corr = True

            if is_corr:
                score += 1

            sp = q.get("source_pages", [])
            sp_json = json.dumps(sp)

            question_records.append(
                {
                    "quiz_id": q_id,
                    "question_id": q_identifier,
                    "question_text": q_text,
                    "chapter": chapter,
                    "difficulty": difficulty,
                    "user_answer": u_ans_clean,
                    "correct_answer": correct_ans,
                    "is_correct": 1 if is_corr else 0,
                    "source_pages": sp_json,
                }
            )

        percentage = (float(score) / float(total_questions) * 100.0) if total_questions > 0 else 0.0
        ts = datetime.now(timezone.utc).isoformat()

        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    INSERT OR REPLACE INTO quiz_attempts (
                        quiz_id, student_id, class_level, chapter, chapter_number,
                        difficulty, score, total_questions, percentage, timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        q_id,
                        clean_student_id,
                        class_level,
                        chapter,
                        chapter_number,
                        difficulty,
                        score,
                        total_questions,
                        round(percentage, 2),
                        ts,
                    ),
                )

                for qr in question_records:
                    cursor.execute(
                        """
                        INSERT INTO question_responses (
                            quiz_id, question_id, question_text, chapter, difficulty,
                            user_answer, correct_answer, is_correct, source_pages
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            qr["quiz_id"],
                            qr["question_id"],
                            qr["question_text"],
                            qr["chapter"],
                            qr["difficulty"],
                            qr["user_answer"],
                            qr["correct_answer"],
                            qr["is_correct"],
                            qr["source_pages"],
                        ),
                    )

                conn.commit()
        except Exception as e:
            logger.error(f"Failed to record quiz attempt: {e}")
            raise StorageError(f"Failed to record quiz attempt in database: {e}")

        return {
            "quiz_id": q_id,
            "student_id": clean_student_id,
            "class_level": class_level,
            "chapter": chapter,
            "chapter_number": chapter_number,
            "difficulty": difficulty,
            "score": score,
            "total_questions": total_questions,
            "percentage": round(percentage, 2),
            "timestamp": ts,
            "question_count": len(question_records),
        }

    def get_student_history(
        self,
        student_id: str,
        class_level: Optional[int] = None,
        include_questions: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Retrieves chronological quiz attempts for a student, optionally filtered by class_level.
        Directly filters by class_level at the query level when specified.
        """
        clean_id = str(student_id).strip()
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                if class_level is not None:
                    try:
                        class_int = int(class_level)
                    except (ValueError, TypeError):
                        raise ValueError(f"Invalid class_level: {class_level}")
                    cursor.execute(
                        """
                        SELECT * FROM quiz_attempts
                        WHERE student_id = ? AND class_level = ?
                        ORDER BY timestamp ASC
                    """,
                        (clean_id, class_int),
                    )
                else:
                    cursor.execute(
                        """
                        SELECT * FROM quiz_attempts
                        WHERE student_id = ?
                        ORDER BY timestamp ASC
                    """,
                        (clean_id,),
                    )

                rows = cursor.fetchall()
                history = [dict(row) for row in rows]

                if include_questions and history:
                    for item in history:
                        q_cursor = conn.cursor()
                        q_cursor.execute(
                            """
                            SELECT question_id, question_text, chapter, difficulty,
                                   user_answer, correct_answer, is_correct, source_pages
                            FROM question_responses
                            WHERE quiz_id = ?
                            ORDER BY id ASC
                        """,
                            (item["quiz_id"],),
                        )

                        q_rows = q_cursor.fetchall()
                        q_list = []
                        for qr in q_rows:
                            qd = dict(qr)
                            try:
                                qd["source_pages"] = json.loads(qd["source_pages"])
                            except Exception:
                                qd["source_pages"] = []
                            qd["is_correct"] = bool(qd["is_correct"])
                            q_list.append(qd)
                        item["questions"] = q_list

                return history
        except Exception as e:
            logger.error(f"Failed to fetch student history for {student_id}: {e}")
            raise StorageError(f"Database query failed: {e}")

    def get_student_class_history(
        self,
        student_id: str,
        class_level: int,
        include_questions: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Dedicated class-scoped retrieval function.
        Guarantees that attempts outside the requested class_level are never fetched.
        """
        if class_level is None:
            raise ValueError("class_level is required for get_student_class_history")
        return self.get_student_history(
            student_id=student_id,
            class_level=int(class_level),
            include_questions=include_questions,
        )

    def clear_student_data(self, student_id: str) -> None:
        """Deletes all attempts and question responses for a student."""
        clean_id = str(student_id).strip()
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    DELETE FROM question_responses
                    WHERE quiz_id IN (SELECT quiz_id FROM quiz_attempts WHERE student_id = ?)
                """,
                    (clean_id,),
                )
                cursor.execute("DELETE FROM quiz_attempts WHERE student_id = ?", (clean_id,))
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to clear data for {student_id}: {e}")
            raise StorageError(f"Failed to delete student records: {e}")


# Default repository instance
quiz_repository = QuizRepository()


def get_student_class_history(
    student_id: str,
    class_level: int,
    include_questions: bool = False,
    db_path: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Standalone helper for class-scoped student history retrieval."""
    repo = quiz_repository if db_path is None else QuizRepository(db_path=db_path)
    return repo.get_student_class_history(
        student_id=student_id,
        class_level=class_level,
        include_questions=include_questions,
    )

