"""Unit tests for Teacher Analytics & Early-Warning Engine."""

import os
import tempfile
import unittest

from src.academic_rag.analytics.teacher import (
    get_student_status,
    get_teacher_chapter_statistics,
    get_teacher_quiz_history,
    get_teacher_student_overview,
    get_teacher_student_profile,
)
from src.academic_rag.storage.repository import QuizRepository


class TestTeacherEngine(unittest.TestCase):
    """Tests teacher overview KPIs, chapter statistics, history formatting, and early warnings."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.db_path = os.path.join(self.temp_dir.name, "test_teacher.db")
        self.repo = QuizRepository(db_path=self.db_path)
        self.student_id = "test_student_teacher"

    def tearDown(self):
        try:
            self.temp_dir.cleanup()
        except Exception:
            pass

    def test_teacher_overview_and_early_warning(self):
        # 1. First quiz: 80% on Electricity
        self.repo.record_attempt(
            self.student_id,
            {
                "class_level": 10,
                "chapter": "Electricity",
                "difficulty": "medium",
                "questions": [
                    {"question_id": f"e1_{i}", "correct_answer": "A"} for i in range(1, 6)
                ],
            },
            {f"q_choice_{i}": "A" if i <= 4 else "B" for i in range(1, 6)},
        )

        # 2. Second quiz: 40% on Electricity (Declining)
        self.repo.record_attempt(
            self.student_id,
            {
                "class_level": 10,
                "chapter": "Electricity",
                "difficulty": "hard",
                "questions": [
                    {"question_id": f"e2_{i}", "correct_answer": "A"} for i in range(1, 6)
                ],
            },
            {f"q_choice_{i}": "A" if i <= 2 else "B" for i in range(1, 6)},
        )

        overview = get_teacher_student_overview(self.student_id, db_path=self.db_path)
        self.assertTrue(overview["has_data"])
        self.assertEqual(overview["total_quizzes"], 2)
        self.assertEqual(overview["overall_average"], 60)

        chapter_stats = get_teacher_chapter_statistics(self.student_id, db_path=self.db_path)
        self.assertEqual(len(chapter_stats), 1)
        self.assertEqual(chapter_stats[0]["chapter"], "Electricity")
        self.assertEqual(chapter_stats[0]["average"], 60)

        quiz_history = get_teacher_quiz_history(self.student_id, db_path=self.db_path)
        self.assertEqual(len(quiz_history), 2)

        # Early Warning Status
        status = get_student_status(self.student_id, db_path=self.db_path)
        self.assertTrue(status["has_data"])
        self.assertEqual(status["overall_status"], "Monitor")
        self.assertEqual(status["trend"]["direction"], "declining")
        self.assertTrue(status["trend"]["alert"])

        # Master profile
        master = get_teacher_student_profile(self.student_id, db_path=self.db_path)
        self.assertTrue(master["has_data"])
        self.assertIn("overview", master)
        self.assertIn("status", master)


if __name__ == "__main__":
    unittest.main()
