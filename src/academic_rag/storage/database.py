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
                FOREIGN KEY (quiz_id) REFERENCES quiz_attempts(quiz_id) ON DELETE CASCADE
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
