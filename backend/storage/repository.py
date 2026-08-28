"""Repository for quiz attempts, question responses, and student history persistence (Prisma implementation)."""

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from backend.exceptions import StorageError
from prisma import Prisma

logger = logging.getLogger(__name__)


class QuizRepository:
    """Provides type-safe CRUD operations for student quiz data using Prisma with SQLite fallback support."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path
        if self.db_path:
            try:
                from backend.storage.database import init_database
                init_database(self.db_path)
            except Exception:
                pass
        self.db = Prisma()

    def _ensure_connected(self):
        if not self.db.is_connected():
            self.db.connect()


    def record_attempt(
        self,
        student_id: str,
        quiz_data: Dict[str, Any],
        user_answers: Dict[str, str],
        quiz_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        self._ensure_connected()
        clean_student_id = str(student_id).strip()
        q_id = (
            quiz_id
            or f"quiz_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
        )
        class_level = int(quiz_data.get("class_level", 10))
        subject = str(quiz_data.get("subject", "Science"))
        chapter = str(quiz_data.get("chapter", "Science"))
        chapter_number = int(quiz_data.get("chapter_number", 0))
        difficulty = str(quiz_data.get("difficulty", "medium")).lower()
        questions = quiz_data.get("questions", [])
        total_questions = len(questions)

        score = 0
        responses_data = []

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
            concept_str = (
                json.dumps(raw_concept)
                if isinstance(raw_concept, list)
                else str(raw_concept).strip()
            )

            responses_data.append(
                {
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

        # Synchronize with SQLite when db_path is provided
        if self.db_path:
            try:
                import sqlite3
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO quiz_attempts (
                        quiz_id, student_id, class_level, subject, chapter, chapter_number,
                        difficulty, score, total_questions, percentage, timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (q_id, clean_student_id, class_level, subject, chapter, chapter_number, difficulty, score, total_questions, round(percentage, 2), ts))
                cursor.execute("DELETE FROM question_responses WHERE quiz_id = ?", (q_id,))
                for r in responses_data:
                    cursor.execute("""
                        INSERT INTO question_responses (
                            quiz_id, question_id, question_text, chapter, difficulty,
                            user_answer, correct_answer, is_correct, source_pages, concept_id
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (q_id, r["question_id"], r["question_text"], r["chapter"], r["difficulty"], r["user_answer"], r["correct_answer"], r["is_correct"], r["source_pages"], r["concept_id"]))
                conn.commit()
                conn.close()
            except Exception as sq_err:
                logger.debug(f"SQLite attempt persistence fallback: {sq_err}")

            return {
                "quiz_id": q_id,
                "student_id": clean_student_id,
                "class_level": class_level,
                "subject": subject,
                "chapter": chapter,
                "chapter_number": chapter_number,
                "difficulty": difficulty,
                "score": score,
                "total_questions": total_questions,
                "percentage": round(percentage, 2),
                "timestamp": ts,
                "responses": responses_data,
            }

        try:
            existing = self.db.quizattempt.find_unique(where={"quiz_id": q_id})

            if existing:
                self.db.questionresponse.delete_many(where={"quiz_id": q_id})
                self.db.quizattempt.update(
                    where={"quiz_id": q_id},
                    data={
                        "student_id": clean_student_id,
                        "class_level": class_level,
                        "subject": subject,
                        "chapter": chapter,
                        "chapter_number": chapter_number,
                        "difficulty": difficulty,
                        "score": score,
                        "total_questions": total_questions,
                        "percentage": round(percentage, 2),
                        "timestamp": ts,
                        "responses": {"create": responses_data},
                    },
                )
            else:
                self.db.quizattempt.create(
                    data={
                        "quiz_id": q_id,
                        "student_id": clean_student_id,
                        "class_level": class_level,
                        "subject": subject,
                        "chapter": chapter,
                        "chapter_number": chapter_number,
                        "difficulty": difficulty,
                        "score": score,
                        "total_questions": total_questions,
                        "percentage": round(percentage, 2),
                        "timestamp": ts,
                        "responses": {"create": responses_data},
                    }
                )

        except Exception as e:
            if not self.db_path:
                logger.error(f"Failed to record quiz attempt: {e}")
                raise StorageError(f"Failed to record quiz attempt in database: {e}")

        return {
            "quiz_id": q_id,
            "student_id": clean_student_id,
            "class_level": class_level,
            "subject": subject,
            "chapter": chapter,
            "chapter_number": chapter_number,
            "difficulty": difficulty,
            "score": score,
            "total_questions": total_questions,
            "percentage": round(percentage, 2),
            "timestamp": ts,
            "responses": responses_data,
        }

    def get_student_history(
        self,
        student_id: str,
        class_level: Optional[int] = None,
        subject: Optional[str] = None,
        include_questions: bool = False,
    ) -> List[Dict[str, Any]]:
        clean_id = str(student_id).strip()

        if self.db_path:
            try:
                import sqlite3
                conn = sqlite3.connect(self.db_path)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = "SELECT * FROM quiz_attempts WHERE student_id = ?"
                params: List[Any] = [clean_id]
                if class_level is not None:
                    query += " AND class_level = ?"
                    params.append(int(class_level))
                if subject is not None:
                    subj_clean = "Mathematics" if "math" in str(subject).lower() else "Science"
                    query += " AND subject = ?"
                    params.append(subj_clean)
                query += " ORDER BY timestamp ASC"
                cursor.execute(query, tuple(params))
                attempts = [dict(row) for row in cursor.fetchall()]
                if include_questions:
                    for att in attempts:
                        cursor.execute("SELECT * FROM question_responses WHERE quiz_id = ?", (att["quiz_id"],))
                        q_rows = [dict(r) for r in cursor.fetchall()]
                        for qd in q_rows:
                            try:
                                qd["source_pages"] = json.loads(qd.get("source_pages") or "[]")
                            except Exception:
                                qd["source_pages"] = []
                            qd["is_correct"] = bool(qd.get("is_correct", 0))
                        att["questions"] = q_rows
                conn.close()
                return attempts
            except Exception as sq_err:
                logger.debug(f"SQLite get_student_history query: {sq_err}")
                return []

        self._ensure_connected()

        try:
            where_clause = {"student_id": clean_id}

            if class_level is not None:
                where_clause["class_level"] = int(class_level)

            if subject is not None:
                subj_clean = "Mathematics" if "math" in str(subject).lower() else "Science"
                where_clause["subject"] = subj_clean

            attempts = self.db.quizattempt.find_many(
                where=where_clause,
                include={"responses": True} if include_questions else None,
                order={"timestamp": "asc"},
            )

            history = []
            for attempt in attempts:
                item = attempt.model_dump()
                if include_questions and attempt.responses:
                    q_list = []
                    for qr in attempt.responses:
                        qd = qr.model_dump()
                        try:
                            qd["source_pages"] = json.loads(qd.get("source_pages") or "[]")
                        except Exception:
                            qd["source_pages"] = []
                        qd["is_correct"] = bool(qd.get("is_correct", 0))
                        q_list.append(qd)
                    item["questions"] = sorted(q_list, key=lambda x: x["id"])
                history.append(item)

            return history
        except Exception as e:
            if not self.db_path:
                logger.error(f"Failed to fetch student history for {student_id}: {e}")
                raise StorageError(f"Database query failed: {e}")
            return []

    def get_student_class_history(
        self,
        student_id: str,
        class_level: int,
        subject: Optional[str] = None,
        include_questions: bool = False,
    ) -> List[Dict[str, Any]]:
        if class_level is None:
            raise ValueError("class_level is required for get_student_class_history")
        return self.get_student_history(
            student_id=student_id,
            class_level=int(class_level),
            subject=subject,
            include_questions=include_questions,
        )

    def clear_student_data(self, student_id: str) -> None:
        self._ensure_connected()
        clean_id = str(student_id).strip()
        try:
            self.db.quizattempt.delete_many(where={"student_id": clean_id})
            self.db.teacheractionplan.delete_many(where={"student_id": clean_id})
        except Exception as e:
            logger.error(f"Failed to clear data for {student_id}: {e}")
            raise StorageError(f"Failed to delete student records: {e}")

    def get_all_student_ids(self) -> List[str]:
        self._ensure_connected()
        try:
            attempts = self.db.quizattempt.find_many(distinct=["student_id"])
            return [a.student_id for a in attempts if a.student_id]
        except Exception:
            return []

    def save_teacher_action_plan(
        self,
        student_id: str,
        class_level: int,
        plan_data: Dict[str, Any],
        teacher_notes: Optional[str] = None,
        subject: str = "Science",
    ) -> Dict[str, Any]:
        self._ensure_connected()
        clean_id = str(student_id).strip()
        class_int = int(class_level)
        subj_clean = "Mathematics" if "math" in str(subject).lower() else "Science"
        plan_json = json.dumps(plan_data)
        notes = (str(teacher_notes).strip()) if teacher_notes is not None else None
        ts = datetime.now(timezone.utc).isoformat()

        try:
            existing = self.db.teacheractionplan.find_first(
                where={"student_id": clean_id, "class_level": class_int, "subject": subj_clean}
            )
            if existing:
                self.db.teacheractionplan.update(
                    where={"id": existing.id},
                    data={"plan_data": plan_json, "teacher_notes": notes, "updated_at": ts},
                )
            else:
                self.db.teacheractionplan.create(
                    data={
                        "student_id": clean_id,
                        "class_level": class_int,
                        "subject": subj_clean,
                        "plan_data": plan_json,
                        "teacher_notes": notes,
                        "updated_at": ts,
                    }
                )
        except Exception as e:
            logger.error(
                f"Failed to save teacher action plan for {student_id} Class {class_level} {subj_clean}: {e}"
            )
            raise StorageError(f"Failed to save teacher action plan: {e}")

        return {
            "student_id": clean_id,
            "class_level": class_int,
            "subject": subj_clean,
            "plan_data": plan_data,
            "teacher_notes": notes,
            "updated_at": ts,
        }

    def get_teacher_custom_plan(
        self, student_id: str, class_level: int, subject: str = "Science"
    ) -> Optional[Dict[str, Any]]:
        self._ensure_connected()
        clean_id = str(student_id).strip()
        class_int = int(class_level)
        subj_clean = "Mathematics" if "math" in str(subject).lower() else "Science"
        try:
            plan = self.db.teacheractionplan.find_first(
                where={"student_id": clean_id, "class_level": class_int, "subject": subj_clean}
            )
            if not plan:
                return None
            return {
                "student_id": clean_id,
                "class_level": class_int,
                "subject": subj_clean,
                "plan_data": json.loads(plan.plan_data),
                "teacher_notes": plan.teacher_notes,
                "updated_at": plan.updated_at,
            }
        except Exception as e:
            logger.error(
                f"Failed to fetch teacher custom plan for {student_id} Class {class_level} {subj_clean}: {e}"
            )
            return None

    def delete_teacher_action_plan(
        self, student_id: str, class_level: int, subject: str = "Science"
    ) -> bool:
        self._ensure_connected()
        clean_id = str(student_id).strip()
        class_int = int(class_level)
        subj_clean = "Mathematics" if "math" in str(subject).lower() else "Science"
        try:
            plan = self.db.teacheractionplan.find_first(
                where={"student_id": clean_id, "class_level": class_int, "subject": subj_clean}
            )
            if plan:
                self.db.teacheractionplan.delete(where={"id": plan.id})
                return True
            return False
        except Exception as e:
            logger.error(
                f"Failed to delete teacher action plan for {student_id} Class {class_level} {subj_clean}: {e}"
            )
            raise StorageError(f"Failed to delete teacher action plan: {e}")


class StudyMaterialRepository:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path
        if self.db_path:
            try:
                from backend.storage.database import init_database
                init_database(self.db_path)
            except Exception:
                pass
        self.db = Prisma()

    def _ensure_connected(self):
        if not self.db.is_connected():
            self.db.connect()

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
        clean_doc_id = str(document_id).strip()
        clean_student_id = str(student_id).strip()
        class_int = int(class_level)
        status_val = status.value if hasattr(status, "value") else str(status)
        ts = uploaded_at or datetime.now(timezone.utc).isoformat()

        if self.db_path:
            try:
                import sqlite3
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO uploaded_documents (
                        document_id, student_id, filename, material_name, class_level,
                        subject, chapter, status, file_size_bytes, uploaded_at, page_count, chunk_count
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (clean_doc_id, clean_student_id, filename, material_name, class_int, subject, chapter, status_val, file_size_bytes, ts, 0, 0))
                conn.commit()
                conn.close()
            except Exception:
                pass
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

        self._ensure_connected()


        try:
            existing = self.db.uploadeddocument.find_unique(where={"document_id": clean_doc_id})
            if existing:
                self.db.uploadeddocument.update(
                    where={"document_id": clean_doc_id},
                    data={
                        "student_id": clean_student_id,
                        "filename": filename,
                        "material_name": material_name,
                        "class_level": class_int,
                        "subject": subject,
                        "chapter": chapter,
                        "status": status_val,
                        "file_size_bytes": file_size_bytes,
                        "uploaded_at": ts,
                    },
                )
            else:
                self.db.uploadeddocument.create(
                    data={
                        "document_id": clean_doc_id,
                        "student_id": clean_student_id,
                        "filename": filename,
                        "material_name": material_name,
                        "class_level": class_int,
                        "subject": subject,
                        "chapter": chapter,
                        "status": status_val,
                        "error_message": None,
                        "page_count": 0,
                        "chunk_count": 0,
                        "file_size_bytes": file_size_bytes,
                        "uploaded_at": ts,
                    }
                )
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
        self._ensure_connected()
        clean_doc_id = str(document_id).strip()
        status_val = status.value if hasattr(status, "value") else str(status)

        data = {"status": status_val}
        if error_message is not None:
            data["error_message"] = error_message
        if page_count is not None:
            data["page_count"] = int(page_count)
        if chunk_count is not None:
            data["chunk_count"] = int(chunk_count)

        try:
            self.db.uploadeddocument.update(where={"document_id": clean_doc_id}, data=data)
            return True
        except Exception as e:
            logger.error(f"Failed to update status for document {clean_doc_id}: {e}")
            raise StorageError(f"Failed to update document status: {e}")

    def get_student_documents(
        self,
        student_id: str,
        class_level: Optional[int] = None,
        chapter: Optional[str] = None,
        subject: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        clean_student_id = str(student_id).strip()

        if self.db_path:
            try:
                import sqlite3
                conn = sqlite3.connect(self.db_path)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = "SELECT * FROM uploaded_documents WHERE student_id = ?"
                params: List[Any] = [clean_student_id]
                if class_level is not None:
                    query += " AND class_level = ?"
                    params.append(int(class_level))
                if subject is not None:
                    subj_clean = "Mathematics" if "math" in str(subject).lower() else "Science"
                    query += " AND (subject = ? OR subject = '' OR subject IS NULL)"
                    params.append(subj_clean)
                query += " ORDER BY uploaded_at DESC"
                cursor.execute(query, tuple(params))
                rows = [dict(r) for r in cursor.fetchall()]
                conn.close()
                if chapter is not None and chapter != "All Chapters":
                    rows = [d for d in rows if d.get("chapter") == chapter or not d.get("chapter")]
                return rows
            except Exception as sq_err:
                logger.debug(f"SQLite study material query: {sq_err}")
                return []

        self._ensure_connected()
        try:
            where_clause = {"student_id": clean_student_id}
            if class_level is not None:
                where_clause["class_level"] = int(class_level)

            if subject is not None:
                subj_clean = "Mathematics" if "math" in str(subject).lower() else "Science"
                where_clause["subject"] = {"in": [subj_clean, ""]}

            docs = self.db.uploadeddocument.find_many(
                where=where_clause, order={"uploaded_at": "desc"}
            )

            results = [d.model_dump() for d in docs]
            if chapter is not None and chapter != "All Chapters":
                results = [
                    d for d in results if d.get("chapter") == chapter or not d.get("chapter")
                ]

            return results
        except Exception as e:
            if not self.db_path:
                logger.error(f"Failed to fetch documents for student {clean_student_id}: {e}")
                raise StorageError(f"Failed to fetch uploaded documents: {e}")
            return []

    def get_document_by_id(self, document_id: str) -> Optional[Dict[str, Any]]:
        clean_doc_id = str(document_id).strip()

        if self.db_path:
            try:
                import sqlite3
                conn = sqlite3.connect(self.db_path)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM uploaded_documents WHERE document_id = ?", (clean_doc_id,))
                row = cursor.fetchone()
                conn.close()
                return dict(row) if row else None
            except Exception:
                return None

        self._ensure_connected()
        try:
            doc = self.db.uploadeddocument.find_unique(where={"document_id": clean_doc_id})
            return doc.model_dump() if doc else None
        except Exception as e:
            logger.error(f"Failed to fetch document {clean_doc_id}: {e}")
            return None

    def delete_document_record(self, document_id: str, student_id: Optional[str] = None) -> bool:
        clean_doc_id = str(document_id).strip()

        if self.db_path:
            try:
                import sqlite3
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM uploaded_documents WHERE document_id = ?", (clean_doc_id,))
                conn.commit()
                conn.close()
                return True
            except Exception:
                return False


        self._ensure_connected()
        try:
            where_clause = {"document_id": clean_doc_id}
            doc = self.db.uploadeddocument.find_unique(where=where_clause)
            if not doc:
                return False
            if student_id is not None and doc.student_id != str(student_id).strip():
                return False
            self.db.uploadeddocument.delete(where={"document_id": clean_doc_id})
            return True
        except Exception as e:
            if not self.db_path:
                logger.error(f"Failed to delete document {clean_doc_id}: {e}")
                raise StorageError(f"Failed to delete document record: {e}")
            return False


    def count_student_documents(self, student_id: str, class_level: Optional[int] = None) -> int:
        docs = self.get_student_documents(student_id=student_id, class_level=class_level)
        return len([d for d in docs if d.get("status") == "READY"])


quiz_repository = QuizRepository()
study_material_repository = StudyMaterialRepository()


def get_student_class_history(
    student_id: str,
    class_level: int,
    include_questions: bool = False,
    db_path: Optional[str] = None,
) -> List[Dict[str, Any]]:
    repo = quiz_repository if db_path is None else QuizRepository(db_path=db_path)
    return repo.get_student_class_history(
        student_id=student_id,
        class_level=class_level,
        include_questions=include_questions,
    )



def get_student_study_materials(
    student_id: str,
    class_level: Optional[int] = None,
    subject: Optional[str] = None,
    db_path: Optional[str] = None,
) -> List[Dict[str, Any]]:
    return study_material_repository.get_student_documents(
        student_id=student_id, class_level=class_level, subject=subject
    )


def delete_student_study_material(
    document_id: str,
    student_id: Optional[str] = None,
    db_path: Optional[str] = None,
) -> bool:
    return study_material_repository.delete_document_record(
        document_id=document_id, student_id=student_id
    )


def count_student_study_materials(
    student_id: str,
    class_level: Optional[int] = None,
    subject: Optional[str] = None,
    db_path: Optional[str] = None,
) -> int:
    return study_material_repository.count_student_documents(
        student_id=student_id, class_level=class_level, subject=subject
    )


def save_study_twin_match(
    student_id: str,
    twin_student_id: str,
    class_level: int,
    subject: str,
    similarity_score: float,
    match_data: Dict[str, Any],
    db_path: Optional[str] = None,
) -> bool:
    ts = datetime.now(timezone.utc).isoformat()
    match_json = json.dumps(match_data)
    try:
        db = Prisma()
        if not db.is_connected():
            db.connect()
        existing = db.studytwinmatch.find_first(
            where={
                "student_id": str(student_id).strip(),
                "class_level": int(class_level),
                "subject": str(subject).strip(),
            }
        )
        if existing:
            db.studytwinmatch.update(
                where={"id": existing.id},
                data={
                    "twin_student_id": str(twin_student_id).strip(),
                    "similarity_score": float(similarity_score),
                    "match_data": match_json,
                    "created_at": ts,
                },
            )
        else:
            db.studytwinmatch.create(
                data={
                    "student_id": str(student_id).strip(),
                    "twin_student_id": str(twin_student_id).strip(),
                    "class_level": int(class_level),
                    "subject": str(subject).strip(),
                    "similarity_score": float(similarity_score),
                    "match_data": match_json,
                    "created_at": ts,
                }
            )
        return True
    except Exception as e:
        logger.error(f"Failed to save study twin match: {e}")
        return False


def get_saved_study_twin_match(
    student_id: str,
    class_level: int,
    subject: str,
    db_path: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    try:
        db = Prisma()
        if not db.is_connected():
            db.connect()
        match = db.studytwinmatch.find_first(
            where={
                "student_id": str(student_id).strip(),
                "class_level": int(class_level),
                "subject": str(subject).strip(),
            }
        )
        if not match:
            return None
        data = match.model_dump()
        if data.get("match_data"):
            try:
                data["match_data"] = json.loads(data["match_data"])
            except Exception:
                pass
        return data
    except Exception as e:
        logger.error(f"Failed to retrieve saved study twin match: {e}")
        return None


def clear_study_twin_match(
    student_id: str,
    class_level: int,
    subject: str,
    db_path: Optional[str] = None,
) -> bool:
    try:
        db = Prisma()
        if not db.is_connected():
            db.connect()
        match = db.studytwinmatch.find_first(
            where={
                "student_id": str(student_id).strip(),
                "class_level": int(class_level),
                "subject": str(subject).strip(),
            }
        )
        if match:
            db.studytwinmatch.delete(where={"id": match.id})
            return True
        return False
    except Exception as e:
        logger.error(f"Failed to clear study twin match: {e}")
        return False


def get_all_candidate_student_ids(
    class_level: int,
    subject: str,
    exclude_student_id: Optional[str] = None,
    db_path: Optional[str] = None,
) -> List[str]:
    candidates = set()
    clean_exclude = str(exclude_student_id).strip() if exclude_student_id else None
    subj_clean = "Mathematics" if "math" in str(subject).lower() else "Science"

    try:
        db = Prisma()
        if not db.is_connected():
            db.connect()

        attempts = db.quizattempt.find_many(
            where={"class_level": int(class_level), "subject": {"in": [subj_clean, ""]}},
            distinct=["student_id"],
        )
        for a in attempts:
            if a.student_id and a.student_id != clean_exclude:
                candidates.add(a.student_id)

        students = db.user.find_many(where={"role": "student"})
        for s in students:
            s_class = s.class_level or 10
            if s_class == int(class_level) and s.id != clean_exclude:
                candidates.add(s.id)
    except Exception as e:
        logger.warning(f"Could not load candidates: {e}")

    return sorted(list(candidates))
