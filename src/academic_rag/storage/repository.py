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
            raw_concept = q.get("concept_id") or q.get("concept") or q.get("concepts") or ""
            concept_str = json.dumps(raw_concept) if isinstance(raw_concept, list) else str(raw_concept).strip()

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
                    "concept_id": concept_str,
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
                            user_answer, correct_answer, is_correct, source_pages, concept_id
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                            qr["concept_id"],
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
        """Deletes all attempts, question responses, and custom action plans for a student."""
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
                cursor.execute("DELETE FROM teacher_action_plans WHERE student_id = ?", (clean_id,))
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to clear data for {student_id}: {e}")
            raise StorageError(f"Failed to delete student records: {e}")

    def get_all_student_ids(self) -> List[str]:
        """Returns a distinct list of student IDs who have quiz attempt records."""
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT DISTINCT student_id FROM quiz_attempts ORDER BY student_id ASC"
                )
                rows = cursor.fetchall()
                return [r["student_id"] for r in rows if r["student_id"]]
        except Exception:
            return []

    def save_teacher_action_plan(
        self,
        student_id: str,
        class_level: int,
        plan_data: Dict[str, Any],
        teacher_notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Saves or updates a customized teacher action plan for a student and class level.
        """
        clean_id = str(student_id).strip()
        class_int = int(class_level)
        plan_json = json.dumps(plan_data)
        notes = (str(teacher_notes).strip()) if teacher_notes is not None else None
        ts = datetime.now(timezone.utc).isoformat()

        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO teacher_action_plans (student_id, class_level, plan_data, teacher_notes, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(student_id, class_level) DO UPDATE SET
                        plan_data = excluded.plan_data,
                        teacher_notes = excluded.teacher_notes,
                        updated_at = excluded.updated_at
                """,
                    (clean_id, class_int, plan_json, notes, ts),
                )
                conn.commit()
        except Exception as e:
            logger.error(
                f"Failed to save teacher action plan for {student_id} Class {class_level}: {e}"
            )
            raise StorageError(f"Failed to save teacher action plan: {e}")

        return {
            "student_id": clean_id,
            "class_level": class_int,
            "plan_data": plan_data,
            "teacher_notes": notes,
            "updated_at": ts,
        }

    def get_teacher_custom_plan(
        self, student_id: str, class_level: int
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieves active custom teacher action plan for a student and class level if present.
        """
        clean_id = str(student_id).strip()
        class_int = int(class_level)
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT plan_data, teacher_notes, updated_at
                    FROM teacher_action_plans
                    WHERE student_id = ? AND class_level = ?
                """,
                    (clean_id, class_int),
                )
                row = cursor.fetchone()
                if not row:
                    return None

                plan_content = json.loads(row["plan_data"])
                return {
                    "student_id": clean_id,
                    "class_level": class_int,
                    "plan_data": plan_content,
                    "teacher_notes": row["teacher_notes"],
                    "updated_at": row["updated_at"],
                }
        except Exception as e:
            logger.error(
                f"Failed to fetch teacher custom plan for {student_id} Class {class_level}: {e}"
            )
            return None

    def delete_teacher_action_plan(self, student_id: str, class_level: int) -> bool:
        """
        Deletes custom action plan for a student and class level, resetting to default SWAT recommendations.
        """
        clean_id = str(student_id).strip()
        class_int = int(class_level)
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    DELETE FROM teacher_action_plans
                    WHERE student_id = ? AND class_level = ?
                """,
                    (clean_id, class_int),
                )
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(
                f"Failed to delete teacher action plan for {student_id} Class {class_level}: {e}"
            )
            raise StorageError(f"Failed to delete teacher action plan: {e}")


class StudyMaterialRepository:
    """Provides type-safe CRUD operations for student uploaded study documents."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or str(config.default_db_path)

    def save_document_record(
        self,
        document_id: str,
        student_id: str,
        filename: str,
        material_name: str,
        class_level: int,
        subject: str = "Science",
        chapter: Optional[str] = None,
        status: Any = "PROCESSING",
        file_size_bytes: int = 0,
        uploaded_at: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Creates or replaces an uploaded document metadata record."""
        clean_doc_id = str(document_id).strip()
        clean_student_id = str(student_id).strip()
        class_int = int(class_level)
        status_val = status.value if hasattr(status, "value") else str(status)
        ts = uploaded_at or datetime.now(timezone.utc).isoformat()

        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO uploaded_documents (
                        document_id, student_id, filename, material_name, class_level,
                        subject, chapter, status, error_message, page_count, chunk_count,
                        file_size_bytes, uploaded_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        clean_doc_id,
                        clean_student_id,
                        filename,
                        material_name,
                        class_int,
                        subject,
                        chapter,
                        status_val,
                        None,
                        0,
                        0,
                        file_size_bytes,
                        ts,
                    ),
                )
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to save document record {clean_doc_id}: {e}")
            raise StorageError(f"Failed to save document record in database: {e}")

        return {
            "document_id": clean_doc_id,
            "student_id": clean_student_id,
            "filename": filename,
            "material_name": material_name,
            "class_level": class_int,
            "subject": subject,
            "chapter": chapter,
            "status": status_val,
            "file_size_bytes": file_size_bytes,
            "uploaded_at": ts,
            "page_count": 0,
            "chunk_count": 0,
        }

    def update_document_status(
        self,
        document_id: str,
        status: Any,
        error_message: Optional[str] = None,
        page_count: Optional[int] = None,
        chunk_count: Optional[int] = None,
    ) -> bool:
        """Updates the status, counts, and error message of an uploaded document."""
        clean_doc_id = str(document_id).strip()
        status_val = status.value if hasattr(status, "value") else str(status)

        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                updates = ["status = ?"]
                params: List[Any] = [status_val]

                if error_message is not None:
                    updates.append("error_message = ?")
                    params.append(error_message)
                if page_count is not None:
                    updates.append("page_count = ?")
                    params.append(int(page_count))
                if chunk_count is not None:
                    updates.append("chunk_count = ?")
                    params.append(int(chunk_count))

                params.append(clean_doc_id)
                query = f"UPDATE uploaded_documents SET {', '.join(updates)} WHERE document_id = ?"
                cursor.execute(query, tuple(params))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Failed to update status for document {clean_doc_id}: {e}")
            raise StorageError(f"Failed to update document status: {e}")

    def get_student_documents(
        self,
        student_id: str,
        class_level: Optional[int] = None,
        chapter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieves all uploaded documents for a student, optionally filtered by class level and chapter.
        """
        clean_student_id = str(student_id).strip()
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                query = "SELECT * FROM uploaded_documents WHERE student_id = ?"
                params: List[Any] = [clean_student_id]

                if class_level is not None:
                    query += " AND class_level = ?"
                    params.append(int(class_level))

                if chapter is not None and chapter != "All Chapters":
                    query += " AND (chapter = ? OR chapter IS NULL OR chapter = '')"
                    params.append(str(chapter))

                query += " ORDER BY uploaded_at DESC"
                cursor.execute(query, tuple(params))
                rows = cursor.fetchall()
                return [dict(r) for r in rows]
        except Exception as e:
            logger.error(f"Failed to fetch documents for student {clean_student_id}: {e}")
            raise StorageError(f"Failed to fetch uploaded documents: {e}")

    def get_document_by_id(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a single uploaded document record by document_id."""
        clean_doc_id = str(document_id).strip()
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM uploaded_documents WHERE document_id = ?",
                    (clean_doc_id,),
                )
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"Failed to fetch document {clean_doc_id}: {e}")
            return None

    def delete_document_record(
        self, document_id: str, student_id: Optional[str] = None
    ) -> bool:
        """
        Deletes a document record from the registry database.
        Optionally validates student_id ownership.
        """
        clean_doc_id = str(document_id).strip()
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                if student_id is not None:
                    cursor.execute(
                        "DELETE FROM uploaded_documents WHERE document_id = ? AND student_id = ?",
                        (clean_doc_id, str(student_id).strip()),
                    )
                else:
                    cursor.execute(
                        "DELETE FROM uploaded_documents WHERE document_id = ?",
                        (clean_doc_id,),
                    )
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Failed to delete document {clean_doc_id}: {e}")
            raise StorageError(f"Failed to delete document record: {e}")

    def count_student_documents(
        self, student_id: str, class_level: Optional[int] = None
    ) -> int:
        """Returns count of READY uploaded documents for a student."""
        docs = self.get_student_documents(student_id=student_id, class_level=class_level)
        return len([d for d in docs if d.get("status") == "READY"])


# Default repository instances
quiz_repository = QuizRepository()
study_material_repository = StudyMaterialRepository()


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


def get_student_study_materials(
    student_id: str,
    class_level: Optional[int] = None,
    db_path: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Standalone helper for retrieving student study materials."""
    repo = study_material_repository if db_path is None else StudyMaterialRepository(db_path=db_path)
    return repo.get_student_documents(student_id=student_id, class_level=class_level)


def delete_student_study_material(
    document_id: str,
    student_id: Optional[str] = None,
    db_path: Optional[str] = None,
) -> bool:
    """Standalone helper for deleting a student study material record."""
    repo = study_material_repository if db_path is None else StudyMaterialRepository(db_path=db_path)
    return repo.delete_document_record(document_id=document_id, student_id=student_id)
