"""SQLite Database initialization and connection management."""

import logging
import os
import sqlite3
from contextlib import contextmanager
from typing import Generator

from backend.config import config
from backend.exceptions import StorageError

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
                subject TEXT DEFAULT 'Science',
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

        # Migrations: ensure concept_id and subject exist in existing databases
        try:
            cursor.execute("ALTER TABLE question_responses ADD COLUMN concept_id TEXT")
        except sqlite3.OperationalError:
            pass  # Column already exists

        try:
            cursor.execute("ALTER TABLE quiz_attempts ADD COLUMN subject TEXT DEFAULT 'Science'")
        except sqlite3.OperationalError:
            pass  # Column already exists

        # Backfill any null/empty subjects to Science
        cursor.execute(
            "UPDATE quiz_attempts SET subject = 'Science' WHERE subject IS NULL OR subject = ''"
        )

        # Teacher custom action plans table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS teacher_action_plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT NOT NULL,
                class_level INTEGER NOT NULL,
                subject TEXT DEFAULT 'Science',
                plan_data TEXT NOT NULL,
                teacher_notes TEXT,
                updated_at TEXT NOT NULL,
                UNIQUE(student_id, class_level, subject)
            )
        """)

        try:
            cursor.execute(
                "ALTER TABLE teacher_action_plans ADD COLUMN subject TEXT DEFAULT 'Science'"
            )
        except sqlite3.OperationalError:
            pass  # Column already exists

        cursor.execute(
            "UPDATE teacher_action_plans SET subject = 'Science' WHERE subject IS NULL OR subject = ''"
        )

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

        # Study Twin matches registry table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS study_twin_matches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT NOT NULL,
                twin_student_id TEXT NOT NULL,
                class_level INTEGER NOT NULL,
                subject TEXT NOT NULL,
                similarity_score REAL NOT NULL,
                match_data TEXT NOT NULL,
                created_at TEXT NOT NULL,
                UNIQUE(student_id, class_level, subject)
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
            "CREATE INDEX IF NOT EXISTS idx_attempts_student_class_subject ON quiz_attempts(student_id, class_level, subject)"
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
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_twin_matches_student ON study_twin_matches(student_id, class_level, subject)"
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
