"""Quiz Submission and Evaluation Engine (Zero LLM calls)."""

import logging
from typing import Any, Dict, Optional

from src.academic_rag.analytics.swat import get_student_swat
from src.academic_rag.storage.repository import quiz_repository

logger = logging.getLogger(__name__)


def submit_and_grade_quiz(
    student_id: str,
    quiz_data: Dict[str, Any],
    user_answers: Dict[str, str],
    quiz_id: Optional[str] = None,
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Submits, grades, records attempt in SQLite, and computes SWAT transitions.
    0 LLM calls; instantaneous deterministic evaluation.
    """
    if not student_id or not str(student_id).strip():
        raise ValueError("student_id cannot be empty.")
    clean_student_id = str(student_id).strip()

    chapter = str(quiz_data.get("chapter", "Science"))

    # Step 1: Pre-submission SWAT snapshot
    prev_chapter_score = None
    prev_status = "not_attempted"
    try:
        prev_swat = get_student_swat(clean_student_id, db_path=db_path)
        ch_info = prev_swat.get("chapter_breakdown", {}).get(chapter)
        if ch_info:
            prev_chapter_score = ch_info.get("score")
            prev_status = ch_info.get("category", "average")
    except Exception as e:
        logger.warning(f"Could not retrieve pre-submission SWAT: {e}")

    # Step 2: Record attempt & grade locally
    repo = quiz_repository if db_path is None else type(quiz_repository)(db_path=db_path)
    saved_attempt = repo.record_attempt(
        student_id=clean_student_id,
        quiz_data=quiz_data,
        user_answers=user_answers,
        quiz_id=quiz_id,
    )

    q_id = saved_attempt["quiz_id"]
    score = saved_attempt["score"]
    total = saved_attempt["total_questions"]
    percentage = saved_attempt["percentage"]

    # Step 3: Question feedback list
    questions = quiz_data.get("questions", [])
    question_feedback = []
    for idx, q in enumerate(questions, 1):
        q_identifier = q.get("question_id", f"{q_id}_q{idx}")
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
            if u_ans_clean.upper().startswith(correct_ans) or u_ans_clean.upper() == correct_ans:
                is_corr = True

        question_feedback.append(
            {
                "question_id": q_identifier,
                "question_text": q.get("question", f"Question {idx}"),
                "options": q.get("options", []),
                "user_answer": u_ans_clean,
                "correct_answer": correct_ans,
                "is_correct": is_corr,
                "explanation": q.get("explanation", "Refer to NCERT textbook."),
                "source_pages": q.get("source_pages", []),
            }
        )

    # Step 4: Recalculate SWAT automatically
    new_chapter_score = int(round(percentage))
    new_status = "average"
    new_swat = {}
    try:
        new_swat = get_student_swat(clean_student_id, db_path=db_path)
        new_ch_info = new_swat.get("chapter_breakdown", {}).get(chapter)
        if new_ch_info:
            new_chapter_score = new_ch_info.get("score", int(round(percentage)))
            new_status = new_ch_info.get("category", "average")
    except Exception as e:
        logger.warning(f"Could not recalculate SWAT: {e}")

    # Determine status change
    status_changed = prev_status != new_status
    if prev_chapter_score is not None:
        status_change_summary = f"{chapter} average: {prev_chapter_score}% ({prev_status.upper()}) ➔ {new_chapter_score}% ({new_status.upper()})"
    else:
        status_change_summary = (
            f"{chapter} initial score: {new_chapter_score}% ({new_status.upper()})"
        )

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
