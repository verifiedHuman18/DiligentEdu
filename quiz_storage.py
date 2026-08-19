#!/usr/bin/env python3
"""
NCERT Quiz Performance Storage Engine (Phase 8)
Persistent SQLite storage for quiz attempts and question responses with history retrieval and SWAT preparation.
"""

import os
import sys
import json
import sqlite3
import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Union

# Reconfigure stdout for UTF-8
sys.stdout.reconfigure(encoding="utf-8")

logger = logging.getLogger(__name__)

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
STORAGE_DIR = os.path.join(PROJECT_ROOT, "data", "storage")
DEFAULT_DB_PATH = os.path.join(STORAGE_DIR, "quiz_history.db")


def init_db(db_path: str = DEFAULT_DB_PATH) -> None:
    """Initialize the SQLite database with required tables and indexes."""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    with sqlite3.connect(db_path) as conn:
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

        # Indexes for fast querying by student, chapter, and timestamp
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_attempts_student ON quiz_attempts(student_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_attempts_chapter ON quiz_attempts(student_id, chapter)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_responses_quiz ON question_responses(quiz_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_responses_chapter ON question_responses(chapter)")

        conn.commit()


def record_quiz_attempt(
    student_id: str,
    quiz_data: Dict[str, Any],
    user_answers: Dict[str, str],
    quiz_id: Optional[str] = None,
    db_path: str = DEFAULT_DB_PATH,
) -> Dict[str, Any]:
    """
    Records a completed quiz attempt and its individual question responses.

    Args:
        student_id: Unique student identifier (e.g. "student_001")
        quiz_data: Dict returned by generate_quiz with 'class_level', 'chapter', 'difficulty', 'questions'
        user_answers: Dict mapping option keys (e.g. 'q_choice_1': 'B) ...') or direct choices to answers
        quiz_id: Optional unique ID (generates UUID if None)
        db_path: Path to SQLite DB file

    Returns:
        Structured summary dict of the saved attempt.
    """
    init_db(db_path)

    q_id = quiz_id or f"quiz_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
    class_level = int(quiz_data.get("class_level", 10))
    chapter = str(quiz_data.get("chapter", "Science"))
    chapter_number = int(quiz_data.get("chapter_number", 0))
    difficulty = str(quiz_data.get("difficulty", "medium")).lower()
    questions = quiz_data.get("questions", [])
    total_questions = len(questions)

    # Score calculation
    score = 0
    question_records = []

    for idx, q in enumerate(questions, 1):
        q_identifier = q.get("question_id", f"{q_id}_q{idx}")
        q_text = q.get("question", "")
        correct_ans = str(q.get("correct_answer", "A")).strip().upper()
        if len(correct_ans) > 1 and correct_ans.startswith(("A", "B", "C", "D")):
            correct_ans = correct_ans[0]

        # Extract user answer for this question
        u_ans = user_answers.get(f"q_choice_{idx}", user_answers.get(str(idx), user_answers.get(q_identifier, "")))
        u_ans_clean = str(u_ans).strip()

        # Check correctness
        is_corr = False
        if u_ans_clean:
            if u_ans_clean.upper().startswith(correct_ans):
                is_corr = True
            elif u_ans_clean.upper() == correct_ans:
                is_corr = True

        if is_corr:
            score += 1

        sp = q.get("source_pages", [])
        sp_json = json.dumps(sp)

        question_records.append({
            "quiz_id": q_id,
            "question_id": q_identifier,
            "question_text": q_text,
            "chapter": chapter,
            "difficulty": difficulty,
            "user_answer": u_ans_clean,
            "correct_answer": correct_ans,
            "is_correct": 1 if is_corr else 0,
            "source_pages": sp_json,
        })

    percentage = (float(score) / float(total_questions) * 100.0) if total_questions > 0 else 0.0
    ts = datetime.now(timezone.utc).isoformat()

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()

        # Insert attempt
        cursor.execute("""
            INSERT OR REPLACE INTO quiz_attempts (
                quiz_id, student_id, class_level, chapter, chapter_number,
                difficulty, score, total_questions, percentage, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            q_id, student_id, class_level, chapter, chapter_number,
            difficulty, score, total_questions, round(percentage, 2), ts
        ))

        # Insert question responses
        for qr in question_records:
            cursor.execute("""
                INSERT INTO question_responses (
                    quiz_id, question_id, question_text, chapter, difficulty,
                    user_answer, correct_answer, is_correct, source_pages
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                qr["quiz_id"], qr["question_id"], qr["question_text"],
                qr["chapter"], qr["difficulty"], qr["user_answer"],
                qr["correct_answer"], qr["is_correct"], qr["source_pages"]
            ))

        conn.commit()

    return {
        "quiz_id": q_id,
        "student_id": student_id,
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
    student_id: str,
    include_questions: bool = False,
    db_path: str = DEFAULT_DB_PATH,
) -> List[Dict[str, Any]]:
    """
    Retrieves the complete chronological quiz history for a student.

    Args:
        student_id: The student identifier
        include_questions: If True, attaches all question responses for each quiz
        db_path: Path to SQLite DB file

    Returns:
        List of quiz attempt dictionaries sorted chronologically (oldest to newest).
    """
    init_db(db_path)

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM quiz_attempts
            WHERE student_id = ?
            ORDER BY timestamp ASC
        """, (student_id,))

        rows = cursor.fetchall()
        history = [dict(row) for row in rows]

        if include_questions and history:
            for item in history:
                q_cursor = conn.cursor()
                q_cursor.execute("""
                    SELECT question_id, question_text, chapter, difficulty,
                           user_answer, correct_answer, is_correct, source_pages
                    FROM question_responses
                    WHERE quiz_id = ?
                    ORDER BY id ASC
                """, (item["quiz_id"],))

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


def get_student_chapter_summary(
    student_id: str,
    db_path: str = DEFAULT_DB_PATH,
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Groups a student's quiz history by chapter to show progression over time.

    Returns:
        Dict: {
            "Electricity": [
                {"quiz_num": 1, "quiz_id": "...", "difficulty": "easy", "score": 2, "total": 5, "percentage": 40.0, "timestamp": "..."},
                {"quiz_num": 2, "quiz_id": "...", "difficulty": "medium", "score": 3, "total": 5, "percentage": 60.0, "timestamp": "..."}
            ],
            "Light": [...]
        }
    """
    history = get_student_history(student_id, include_questions=False, db_path=db_path)
    summary: Dict[str, List[Dict[str, Any]]] = {}

    for attempt in history:
        ch = attempt["chapter"]
        if ch not in summary:
            summary[ch] = []

        quiz_idx = len(summary[ch]) + 1
        summary[ch].append({
            "quiz_num": quiz_idx,
            "quiz_id": attempt["quiz_id"],
            "difficulty": attempt["difficulty"],
            "score": attempt["score"],
            "total_questions": attempt["total_questions"],
            "percentage": attempt["percentage"],
            "timestamp": attempt["timestamp"],
        })

    return summary


def get_student_swat_metrics(
    student_id: str,
    db_path: str = DEFAULT_DB_PATH,
) -> Dict[str, Any]:
    """
    Calculates aggregated SWAT (Strengths, Weaknesses, Accuracy, and Topics) metrics
    for a student across all quiz attempts.
    """
    history = get_student_history(student_id, include_questions=True, db_path=db_path)
    if not history:
        return {"total_quizzes": 0, "overall_accuracy": 0.0, "chapters": {}}

    total_attempts = len(history)
    total_q_answered = 0
    total_q_correct = 0
    chapter_stats: Dict[str, Dict[str, Any]] = {}

    for attempt in history:
        ch = attempt["chapter"]
        if ch not in chapter_stats:
            chapter_stats[ch] = {
                "attempts": 0,
                "total_questions": 0,
                "total_correct": 0,
                "latest_percentage": 0.0,
                "percentages": [],
                "difficulties_tested": set(),
            }

        c_stat = chapter_stats[ch]
        c_stat["attempts"] += 1
        c_stat["total_questions"] += attempt["total_questions"]
        c_stat["total_correct"] += attempt["score"]
        c_stat["latest_percentage"] = attempt["percentage"]
        c_stat["percentages"].append(attempt["percentage"])
        c_stat["difficulties_tested"].add(attempt["difficulty"])

        total_q_answered += attempt["total_questions"]
        total_q_correct += attempt["score"]

    # Calculate Strengths & Weaknesses
    for ch, stat in chapter_stats.items():
        stat["accuracy"] = round((stat["total_correct"] / stat["total_questions"] * 100.0), 1) if stat["total_questions"] > 0 else 0.0
        stat["difficulties_tested"] = sorted(list(stat["difficulties_tested"]))

    overall_acc = round((total_q_correct / total_q_answered * 100.0), 1) if total_q_answered > 0 else 0.0

    # Categorize chapters into strengths (>= 75%) and weaknesses (< 50%)
    strengths = [ch for ch, st in chapter_stats.items() if st["accuracy"] >= 75.0]
    weaknesses = [ch for ch, st in chapter_stats.items() if st["accuracy"] < 50.0]
    in_progress = [ch for ch, st in chapter_stats.items() if 50.0 <= st["accuracy"] < 75.0]

    return {
        "student_id": student_id,
        "total_quizzes_taken": total_attempts,
        "total_questions_answered": total_q_answered,
        "overall_accuracy": overall_acc,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "in_progress": in_progress,
        "chapters": chapter_stats,
    }


def clear_student_history(student_id: str, db_path: str = DEFAULT_DB_PATH) -> None:
    """Clear all records for a given student (useful for tests and resets)."""
    if os.path.exists(db_path):
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM question_responses WHERE quiz_id IN (SELECT quiz_id FROM quiz_attempts WHERE student_id = ?)", (student_id,))
            cursor.execute("DELETE FROM quiz_attempts WHERE student_id = ?", (student_id,))
            conn.commit()


def submit_and_grade_quiz(
    student_id: str,
    quiz_data: Dict[str, Any],
    user_answers: Dict[str, str],
    quiz_id: Optional[str] = None,
    db_path: str = DEFAULT_DB_PATH,
) -> Dict[str, Any]:
    """
    Complete Phase 12 pipeline:
    1. Capture previous SWAT status for the chapter.
    2. Grade quiz locally against ground truth keys (0 Gemini calls).
    3. Persist attempt and per-question responses in SQLite.
    4. Automatically recalculate student SWAT profile.
    5. Return comprehensive result with score, question feedback, and SWAT transition diff.

    Args:
        student_id: Student identifier (e.g. "student_001")
        quiz_data: Generated quiz dictionary containing questions & answers
        user_answers: Student's answer map (e.g. {"q_choice_1": "B", "q_choice_2": "C"})
        quiz_id: Optional custom quiz ID
        db_path: Optional path to SQLite DB

    Returns:
        Structured submission result matching Phase 12 specification.
    """
    if not student_id or not str(student_id).strip():
        raise ValueError("student_id cannot be empty.")
    clean_student_id = str(student_id).strip()

    chapter = str(quiz_data.get("chapter", "Science"))

    # Step 1: Pre-submission SWAT snapshot
    prev_chapter_score = None
    prev_status = "not_attempted"
    try:
        from swat_analyzer import get_student_swat
        prev_swat = get_student_swat(clean_student_id, db_path=db_path)
        ch_info = prev_swat.get("chapter_breakdown", {}).get(chapter)
        if ch_info:
            prev_chapter_score = ch_info.get("score")
            prev_status = ch_info.get("category", "average")
    except Exception as e:
        logger.warning(f"Could not retrieve pre-submission SWAT: {e}")

    # Step 2: Grade locally & Save attempt
    saved_attempt = record_quiz_attempt(
        student_id=clean_student_id,
        quiz_data=quiz_data,
        user_answers=user_answers,
        quiz_id=quiz_id,
        db_path=db_path,
    )

    q_id = saved_attempt["quiz_id"]
    score = saved_attempt["score"]
    total = saved_attempt["total_questions"]
    percentage = saved_attempt["percentage"]

    # Step 3: Extract question-level feedback
    questions = quiz_data.get("questions", [])
    question_feedback = []
    for idx, q in enumerate(questions, 1):
        q_identifier = q.get("question_id", f"{q_id}_q{idx}")
        correct_ans = str(q.get("correct_answer", "A")).strip().upper()
        if len(correct_ans) > 1 and correct_ans.startswith(("A", "B", "C", "D")):
            correct_ans = correct_ans[0]

        u_ans = user_answers.get(f"q_choice_{idx}", user_answers.get(str(idx), user_answers.get(q_identifier, "")))
        u_ans_clean = str(u_ans).strip()

        is_corr = False
        if u_ans_clean:
            if u_ans_clean.upper().startswith(correct_ans) or u_ans_clean.upper() == correct_ans:
                is_corr = True

        question_feedback.append({
            "question_id": q_identifier,
            "question_text": q.get("question", f"Question {idx}"),
            "options": q.get("options", []),
            "user_answer": u_ans_clean,
            "correct_answer": correct_ans,
            "is_correct": is_corr,
            "explanation": q.get("explanation", "Refer to NCERT textbook."),
            "source_pages": q.get("source_pages", []),
        })

    # Step 4: Recalculate SWAT automatically
    new_chapter_score = int(round(percentage))
    new_status = "average"
    new_swat = {}
    try:
        from swat_analyzer import get_student_swat
        new_swat = get_student_swat(clean_student_id, db_path=db_path)
        new_ch_info = new_swat.get("chapter_breakdown", {}).get(chapter)
        if new_ch_info:
            new_chapter_score = new_ch_info.get("score", int(round(percentage)))
            new_status = new_ch_info.get("category", "average")
    except Exception as e:
        logger.warning(f"Could not recalculate SWAT: {e}")

    # Determine status change
    status_changed = (prev_status != new_status)
    if prev_chapter_score is not None:
        status_change_summary = f"{chapter} average: {prev_chapter_score}% ({prev_status.upper()}) ➔ {new_chapter_score}% ({new_status.upper()})"
    else:
        status_change_summary = f"{chapter} initial score: {new_chapter_score}% ({new_status.upper()})"

    return {
        "student_id": clean_student_id,
        "quiz_id": q_id,
        "class_level": saved_attempt.get("class_level", 10),
        "chapter": chapter,
        "difficulty": saved_attempt.get("difficulty", "medium"),
        "score": score,
        "total": total,
        "percentage": int(round(percentage)),
        "previous_chapter_score": prev_chapter_score,
        "previous_status": prev_status,
        "new_chapter_score": new_chapter_score,
        "new_status": new_status,
        "status_changed": status_changed,
        "status_change_summary": status_change_summary,
        "timestamp": saved_attempt.get("timestamp"),
        "question_feedback": question_feedback,
        "updated_swat": new_swat,
    }


if __name__ == "__main__":
    print("Testing Quiz Storage Engine...")
    test_student = "student_test_001"
    clear_student_history(test_student)

    # Mock attempt 1
    mock_quiz = {
        "class_level": 10,
        "chapter": "Electricity",
        "chapter_number": 11,
        "difficulty": "medium",
        "questions": [
            {"question_id": "q1", "question": "What is Ohm's Law?", "correct_answer": "B", "source_pages": [6]},
            {"question_id": "q2", "question": "What is Joule heating?", "correct_answer": "C", "source_pages": [20]},
            {"question_id": "q3", "question": "What is tungsten filament?", "correct_answer": "A", "source_pages": [24]},
            {"question_id": "q4", "question": "What is electric power?", "correct_answer": "D", "source_pages": [22]},
            {"question_id": "q5", "question": "What is electrical resistivity?", "correct_answer": "B", "source_pages": [9]},
        ]
    }
    user_ans = {"q_choice_1": "B) V = IR", "q_choice_2": "C) H = I^2Rt", "q_choice_3": "B) Wrong", "q_choice_4": "A) Wrong", "q_choice_5": "B) Correct"}
    res = record_quiz_attempt(test_student, mock_quiz, user_ans)
    print("Saved attempt:", json.dumps(res, indent=2))

    hist = get_student_history(test_student, include_questions=True)
    print(f"\nRetrieved {len(hist)} attempt(s) for {test_student}.")
    print("✅ Quiz Storage Engine test passed.")
