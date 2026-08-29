import json
import random
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from backend.curriculum.service import DEFAULT_CURRICULUM_MAPPING
from prisma import Prisma


def get_subject_chapters(class_level: int, subject: str) -> List[str]:
    """Return only the valid chapter titles for a specific class + subject pair."""
    class_level = int(class_level)
    subject_key = str(subject).strip().lower()
    subject_name = "Mathematics" if "math" in subject_key else "Science"
    mapping_key = (
        f"class{class_level}_{'mathematics' if subject_name == 'Mathematics' else 'science'}"
    )
    mapping = DEFAULT_CURRICULUM_MAPPING.get(mapping_key, {})
    if not mapping and subject_name == "Science":
        mapping = DEFAULT_CURRICULUM_MAPPING.get(f"class{class_level}", {})
    if not mapping:
        return []
    return [info["chapter"] for info in mapping.values() if "chapter" in info]


def get_chapter_number(class_level: int, subject: str, chapter: str) -> int:
    class_level = int(class_level)
    chapters = get_subject_chapters(class_level, subject)
    if chapter not in chapters:
        return 1
    mapping_key = (
        f"class{class_level}_{'mathematics' if 'math' in str(subject).lower() else 'science'}"
    )
    mapping = DEFAULT_CURRICULUM_MAPPING.get(mapping_key, {})
    for chapter_number, info in (
        (int(value.get("chapter_number", 1)), value)
        for value in mapping.values()
        if isinstance(value, dict)
    ):
        if info.get("chapter") == chapter:
            return chapter_number
    return 1


def build_question_response(
    quiz_id: str, question_index: int, chapter: str, difficulty: str, correct_answer: str
) -> Dict[str, Any]:
    options = ["A", "B", "C", "D"]
    user_answer = (
        correct_answer
        if question_index % 3 == 0
        else random.choice([opt for opt in options if opt != correct_answer])
    )
    return {
        "question_id": f"{quiz_id}_q{question_index}",
        "question_text": f"Apply the key idea from {chapter} to choose the correct option.",
        "chapter": chapter,
        "difficulty": difficulty,
        "user_answer": user_answer,
        "correct_answer": correct_answer,
        "is_correct": 1 if user_answer == correct_answer else 0,
        "source_pages": json.dumps([random.randint(10, 80), random.randint(81, 160)]),
        "concept_id": f"concept_{random.randint(1, 200)}",
    }


def generate_student_seed_payload(
    student_id: str,
    class_level: int,
    rng: Optional[random.Random] = None,
    candidate_twin_ids: Optional[List[str]] = None,
) -> Dict[str, Any]:
    rng = rng or random.Random()
    class_level = int(class_level)
    subjects = ["Science", "Mathematics"]
    total_quizzes = rng.randint(15, 30)
    science_quizzes = max(7, total_quizzes // 2)
    math_quizzes = total_quizzes - science_quizzes
    if math_quizzes < 6:
        science_quizzes = total_quizzes - 6
        math_quizzes = 6

    quizzes: List[Dict[str, Any]] = []
    action_plans: List[Dict[str, Any]] = []
    study_twins: List[Dict[str, Any]] = []
    twin_pool = candidate_twin_ids or []

    for subject in subjects:
        chapters = get_subject_chapters(class_level, subject)
        if not chapters:
            continue
        subject_quiz_count = science_quizzes if subject == "Science" else math_quizzes
        for _ in range(subject_quiz_count):
            chapter = rng.choice(chapters)
            chapter_number = get_chapter_number(class_level, subject, chapter)
            difficulty = rng.choices(["Easy", "Medium", "Hard"], weights=[45, 35, 20], k=1)[0]
            total_questions = rng.randint(5, 8)
            correct_answers = rng.randint(max(2, total_questions // 2), total_questions)
            score = min(correct_answers, total_questions)
            percentage = round((score / total_questions) * 100, 2)
            quiz_id = str(uuid.uuid4())
            timestamp = (
                datetime.now(timezone.utc)
                - timedelta(days=rng.randint(0, 180), hours=rng.randint(0, 23))
            ).isoformat()
            correct_answer = rng.choice(["A", "B", "C", "D"])
            responses = []
            for idx in range(total_questions):
                responses.append(
                    build_question_response(
                        quiz_id=quiz_id,
                        question_index=idx + 1,
                        chapter=chapter,
                        difficulty=difficulty,
                        correct_answer=correct_answer,
                    )
                )
            quiz = {
                "quiz_id": quiz_id,
                "student_id": student_id,
                "class_level": class_level,
                "subject": subject,
                "chapter": chapter,
                "chapter_number": chapter_number,
                "difficulty": difficulty,
                "score": score,
                "total_questions": total_questions,
                "percentage": percentage,
                "timestamp": timestamp,
                "responses": responses,
            }
            quizzes.append(quiz)

        focus_chapter = rng.choice(chapters)
        action_plans.append(
            {
                "student_id": student_id,
                "class_level": class_level,
                "subject": subject,
                "focus_chapter": focus_chapter,
                "plan_data": json.dumps(
                    {
                        "focus_areas": [focus_chapter],
                        "priority": "high" if subject == "Science" else "medium",
                        "recommended_topics": [focus_chapter, rng.choice(chapters)],
                        "next_steps": [
                            "Complete a timed revision set",
                            "Review textbook examples",
                            "Retake a mixed practice quiz",
                        ],
                    }
                ),
                "teacher_notes": (
                    f"{subject} revision plan: revisit {focus_chapter}, then practice two short mixed quizzes before the next assessment."
                ),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
        )

        twin_candidates = [candidate for candidate in twin_pool if candidate != student_id]
        twin_student_id = (
            rng.choice(twin_candidates)
            if twin_candidates
            else f"student_{class_level}_{subject.lower()}_peer_{rng.randint(1000, 9999)}"
        )
        study_twins.append(
            {
                "student_id": student_id,
                "twin_student_id": twin_student_id,
                "class_level": class_level,
                "subject": subject,
                "similarity_score": float(rng.randint(74, 96)),
                "match_data": json.dumps(
                    {
                        "shared_strengths": [rng.choice(chapters)],
                        "shared_goals": ["Improve fluency", "Target weak chapters"],
                        "study_window": "Evening review",
                    }
                ),
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        )

    return {
        "student_id": student_id,
        "class_level": class_level,
        "quizzes": quizzes,
        "action_plans": action_plans,
        "study_twins": study_twins,
    }


def seed_data():
    db = Prisma()

    for attempt in range(4):
        try:
            if not db.is_connected():
                db.connect()
            break
        except Exception as exc:
            print(f"Connection attempt {attempt + 1} failed: {exc}")
            time.sleep(2)

    print("Clearing existing seed data...")
    db.questionresponse.delete_many()
    db.quizattempt.delete_many()
    db.teacheractionplan.delete_many()
    db.uploadeddocument.delete_many()
    db.studytwinmatch.delete_many()

    users = db.user.find_many(where={"role": "student"})
    print(f"Found {len(users)} students to seed.")

    for user in users:
        class_level = int(user.class_level or 10)
        candidates = [
            other.id
            for other in users
            if other.id != user.id and int(other.class_level or 10) == class_level
        ]
        payload = generate_student_seed_payload(
            student_id=user.id,
            class_level=class_level,
            rng=random.Random(f"{user.id}:{class_level}"),
            candidate_twin_ids=candidates,
        )

        print(
            f"Seeding {len(payload['quizzes'])} quizzes and 2 subject plans for student {user.id} (Class {class_level})"
        )

        for quiz in payload["quizzes"]:
            db.quizattempt.create(
                data={
                    "quiz_id": quiz["quiz_id"],
                    "student_id": quiz["student_id"],
                    "class_level": quiz["class_level"],
                    "subject": quiz["subject"],
                    "chapter": quiz["chapter"],
                    "chapter_number": quiz["chapter_number"],
                    "difficulty": quiz["difficulty"],
                    "score": quiz["score"],
                    "total_questions": quiz["total_questions"],
                    "percentage": quiz["percentage"],
                    "timestamp": quiz["timestamp"],
                    "responses": {"create": quiz["responses"]},
                }
            )

        for plan in payload["action_plans"]:
            existing = db.teacheractionplan.find_first(
                where={
                    "student_id": plan["student_id"],
                    "class_level": plan["class_level"],
                    "subject": plan["subject"],
                }
            )
            if existing:
                db.teacheractionplan.update(
                    where={"id": existing.id},
                    data={
                        "plan_data": plan["plan_data"],
                        "teacher_notes": plan["teacher_notes"],
                        "updated_at": plan["updated_at"],
                    },
                )
            else:
                db.teacheractionplan.create(
                    data={
                        "student_id": plan["student_id"],
                        "class_level": plan["class_level"],
                        "subject": plan["subject"],
                        "plan_data": plan["plan_data"],
                        "teacher_notes": plan["teacher_notes"],
                        "updated_at": plan["updated_at"],
                    }
                )

        for twin in payload["study_twins"]:
            existing = db.studytwinmatch.find_first(
                where={
                    "student_id": twin["student_id"],
                    "class_level": twin["class_level"],
                    "subject": twin["subject"],
                }
            )
            if existing:
                db.studytwinmatch.update(
                    where={"id": existing.id},
                    data={
                        "twin_student_id": twin["twin_student_id"],
                        "similarity_score": twin["similarity_score"],
                        "match_data": twin["match_data"],
                        "created_at": twin["created_at"],
                    },
                )
            else:
                db.studytwinmatch.create(
                    data={
                        "student_id": twin["student_id"],
                        "twin_student_id": twin["twin_student_id"],
                        "class_level": twin["class_level"],
                        "subject": twin["subject"],
                        "similarity_score": twin["similarity_score"],
                        "match_data": twin["match_data"],
                        "created_at": twin["created_at"],
                    }
                )

    db.disconnect()
    print("Production-style mock seeding complete.")


if __name__ == "__main__":
    max_retries = 5
    for attempt in range(max_retries):
        try:
            seed_data()
            break
        except Exception as exc:
            print(f"Error on attempt {attempt + 1}: {exc}")
            import traceback

            traceback.print_exc()
            time.sleep(10)
