import random
import uuid
from datetime import datetime, timedelta

from prisma import Prisma


def seed_data():
    db = Prisma()
    db.connect()

    users = db.user.find_many(where={"role": "student"})
    print(f"Found {len(users)} students.")

    chapters = [
        "Chemical Reactions and Equations",
        "Acids, Bases and Salts",
        "Metals and Non-metals",
        "Carbon and its Compounds",
        "Life Processes",
    ]
    difficulties = ["Easy", "Medium", "Hard"]

    for user in users:
        print(f"Seeding data for {user.email}")
        class_level = user.class_level if user.class_level else 10

        # Generate some QuizAttempts
        for _ in range(random.randint(3, 8)):
            quiz_id = str(uuid.uuid4())
            chapter = random.choice(chapters)
            diff = random.choice(difficulties)
            total_q = 10
            score = random.randint(4, 10)
            percentage = (score / total_q) * 100

            days_ago = random.randint(1, 30)
            timestamp = (datetime.now() - timedelta(days=days_ago)).isoformat()

            db.quizattempt.create(
                data={
                    "quiz_id": quiz_id,
                    "student_id": user.id,
                    "class_level": class_level,
                    "subject": "Science",
                    "chapter": chapter,
                    "chapter_number": chapters.index(chapter) + 1,
                    "difficulty": diff,
                    "score": score,
                    "total_questions": total_q,
                    "percentage": percentage,
                    "timestamp": timestamp,
                }
            )

            for i in range(total_q):
                is_correct = 1 if i < score else 0
                db.questionresponse.create(
                    data={
                        "quiz_id": quiz_id,
                        "question_id": f"q_{i}",
                        "question_text": f"Sample question on {chapter}?",
                        "chapter": chapter,
                        "difficulty": diff,
                        "user_answer": "Option A",
                        "correct_answer": "Option A" if is_correct else "Option B",
                        "is_correct": is_correct,
                        "source_pages": "12,13",
                        "concept_id": f"concept_{random.randint(1, 100)}",
                    }
                )

        # Generate Uploaded Documents
        for _ in range(random.randint(1, 4)):
            doc_id = str(uuid.uuid4())
            db.uploadeddocument.create(
                data={
                    "document_id": doc_id,
                    "student_id": user.id,
                    "filename": f"Notes_{random.choice(chapters).replace(' ', '_')}.pdf",
                    "material_name": "Study Notes",
                    "class_level": class_level,
                    "subject": "Science",
                    "status": "PROCESSED",
                    "page_count": random.randint(5, 20),
                    "chunk_count": random.randint(10, 50),
                    "file_size_bytes": random.randint(100000, 5000000),
                    "uploaded_at": (
                        datetime.now() - timedelta(days=random.randint(1, 30))
                    ).isoformat(),
                }
            )

    db.disconnect()
    print("Done seeding")


if __name__ == "__main__":
    seed_data()
