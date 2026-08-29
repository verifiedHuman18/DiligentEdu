import random
import time
import uuid
from datetime import datetime, timedelta

from backend.curriculum.service import DEFAULT_CURRICULUM_MAPPING
from prisma import Prisma


def get_chapters(class_level, subject):
    key = f"class{class_level}_{subject.lower()}"
    mapping = DEFAULT_CURRICULUM_MAPPING.get(key, {})
    return [info["chapter"] for info in mapping.values()]


def seed_data():
    db = Prisma()

    # Try connecting with retries
    for attempt in range(3):
        try:
            if not db.is_connected():
                db.connect()
            break
        except Exception as e:
            print(f"Connection attempt {attempt + 1} failed: {e}")
            time.sleep(2)

    # Clear existing data first
    print("Clearing existing data...")
    db.questionresponse.delete_many()
    db.quizattempt.delete_many()
    db.teacheractionplan.delete_many()
    db.uploadeddocument.delete_many()
    db.studytwinmatch.delete_many()

    users = db.user.find_many(where={"role": "student"})
    print(f"Found {len(users)} students to seed.")

    all_quizzes = []
    all_action_plans = []
    all_twins = []

    for user in users:
        student_id = user.id
        class_level = user.class_level or 10

        print(f"Preparing data for student {student_id} (Class {class_level})...")

        sci_chapters = get_chapters(class_level, "Science")
        math_chapters = get_chapters(class_level, "Mathematics")

        if not sci_chapters or not math_chapters:
            print(f"Warning: No chapters found for Class {class_level}")
            continue

        num_quizzes = random.randint(15, 30)

        # Prepare Quizzes
        for i in range(num_quizzes):
            subject = random.choice(["Science", "Mathematics"])
            chapter = random.choice(sci_chapters if subject == "Science" else math_chapters)
            score = random.randint(40, 100)
            percentage = float(score)

            all_quizzes.append(
                {
                    "quiz_id": str(uuid.uuid4()),
                    "student_id": student_id,
                    "class_level": class_level,
                    "subject": subject,
                    "chapter": chapter,
                    "chapter_number": random.randint(1, 15),
                    "difficulty": random.choice(["Easy", "Medium", "Hard"]),
                    "score": score,
                    "total_questions": 100,
                    "percentage": percentage,
                    "timestamp": (
                        datetime.now() - timedelta(days=random.randint(0, 30))
                    ).isoformat(),
                }
            )

        # Prepare Teacher Action Plan
        focus_chapter = random.choice(sci_chapters)
        all_action_plans.append(
            {
                "student_id": student_id,
                "class_level": class_level,
                "subject": "Science",
                "plan_data": f'{{"focus_areas": ["{focus_chapter}"]}}',
                "teacher_notes": f"Needs more practice with {focus_chapter}.",
                "updated_at": datetime.now().isoformat(),
            }
        )

        # Prepare Study Twin Match
        all_twins.append(
            {
                "student_id": student_id,
                "twin_student_id": "mock_twin_123",
                "class_level": class_level,
                "subject": "Science",
                "similarity_score": float(random.randint(70, 95)),
                "match_data": "{}",
                "created_at": datetime.now().isoformat(),
            }
        )

    print(f"Bulk inserting {len(all_quizzes)} quizzes...")
    db.quizattempt.create_many(data=all_quizzes)

    print(f"Bulk inserting {len(all_action_plans)} action plans...")
    db.teacheractionplan.create_many(data=all_action_plans)

    print(f"Bulk inserting {len(all_twins)} twins...")
    db.studytwinmatch.create_many(data=all_twins)

    db.disconnect()
    print("Seeding complete!")


if __name__ == "__main__":
    max_retries = 5
    for attempt in range(max_retries):
        try:
            seed_data()
            break
        except Exception as e:
            print(f"Error on attempt {attempt + 1}: {e}")
            import traceback

            traceback.print_exc()
            time.sleep(10)
