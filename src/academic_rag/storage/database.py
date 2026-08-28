"""SQLite Database initialization and connection management."""

import logging
import os
import sqlite3
from contextlib import contextmanager
from typing import Generator

from src.academic_rag.config import config
from src.academic_rag.exceptions import StorageError

logger = logging.getLogger(__name__)


def init_database(db_path: str = None) -> None:
    """Initializes tables and indexes in SQLite database."""
    target_path = db_path or str(config.default_db_path)
    os.makedirs(os.path.dirname(os.path.abspath(target_path)), exist_ok=True)

    conn = sqlite3.connect(target_path)
    try:
        cursor = conn.cursor()

        # Quiz attempts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quiz_attempts (
                quiz_id TEXT PRIMARY KEY,
                student_id TEXT NOT NULL,
                class_level INTEGER NOT NULL,
                chapter TEXT NOT NULL,
                chapter_number INTEGER,
                difficulty TEXT NOT NULL,
                score INTEGER NOT NULL,
                total_questions INTEGER NOT NULL,
                percentage REAL NOT NULL,
                timestamp TEXT NOT NULL
            )
        """)

        # Question responses table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS question_responses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                quiz_id TEXT NOT NULL,
                question_id TEXT NOT NULL,
                question_text TEXT,
                chapter TEXT NOT NULL,
                difficulty TEXT NOT NULL,
                user_answer TEXT,
                correct_answer TEXT,
                is_correct INTEGER NOT NULL,
                source_pages TEXT,
                concept_id TEXT,
                FOREIGN KEY (quiz_id) REFERENCES quiz_attempts(quiz_id) ON DELETE CASCADE
            )
        """)

        # Migration: ensure concept_id exists in existing databases
        try:
            cursor.execute("ALTER TABLE question_responses ADD COLUMN concept_id TEXT")
        except sqlite3.OperationalError:
            pass  # Column already exists

        # Teacher custom action plans table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS teacher_action_plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT NOT NULL,
                class_level INTEGER NOT NULL,
                plan_data TEXT NOT NULL,
                teacher_notes TEXT,
                updated_at TEXT NOT NULL,
                UNIQUE(student_id, class_level)
            )
        """)

        # Student uploaded study materials registry table (Phases 1-9)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS uploaded_documents (
                document_id TEXT PRIMARY KEY,
                student_id TEXT NOT NULL,
                filename TEXT NOT NULL,
                material_name TEXT NOT NULL,
                class_level INTEGER NOT NULL,
                subject TEXT NOT NULL,
                chapter TEXT,
                status TEXT NOT NULL,
                error_message TEXT,
                page_count INTEGER DEFAULT 0,
                chunk_count INTEGER DEFAULT 0,
                file_size_bytes INTEGER DEFAULT 0,
                uploaded_at TEXT NOT NULL
            )
        """)

        # Indexes for performance
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_attempts_student ON quiz_attempts(student_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_attempts_student_class ON quiz_attempts(student_id, class_level)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_attempts_chapter ON quiz_attempts(student_id, chapter)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_responses_quiz ON question_responses(quiz_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_responses_chapter ON question_responses(chapter)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_teacher_plans_student ON teacher_action_plans(student_id, class_level)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_docs_student ON uploaded_documents(student_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_docs_student_class ON uploaded_documents(student_id, class_level)"
        )

        conn.commit()
    except Exception as e:
        logger.error(f"Failed to initialize SQLite database at {target_path}: {e}")
        raise StorageError(f"Database initialization failed: {e}")
    finally:
        conn.close()


@contextmanager
def get_db_connection(db_path: str = None) -> Generator[sqlite3.Connection, None, None]:
    """Context manager yielding SQLite connection with Row factory enabled."""
    target_path = db_path or str(config.default_db_path)
    init_database(target_path)
    conn = sqlite3.connect(target_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()
