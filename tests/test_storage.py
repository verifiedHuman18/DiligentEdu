"""Unit tests for QuizRepository and SQLite Storage."""

import os
import tempfile
import unittest

from src.academic_rag.storage.repository import QuizRepository


class TestQuizRepository(unittest.TestCase):
    """Tests SQLite repository CRUD operations and question persistence."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.db_path = os.path.join(self.temp_dir.name, "test_quiz.db")
        self.repo = QuizRepository(db_path=self.db_path)
        self.student_id = "test_student_unit"

    def tearDown(self):
        try:
            self.temp_dir.cleanup()
        except Exception:
            pass

    def test_record_and_retrieve_attempt(self):
        quiz_data = {
            "class_level": 10,
            "chapter": "Electricity",
            "chapter_number": 11,
            "difficulty": "medium",
            "questions": [
                {
                    "question_id": "q1",
                    "question": "What is Ohm's law?",
                    "correct_answer": "B",
                    "source_pages": [6],
                },
                {
                    "question_id": "q2",
                    "question": "What is Joule heating?",
                    "correct_answer": "C",
                    "source_pages": [20],
                },
            ],
        }
        user_answers = {"q_choice_1": "B", "q_choice_2": "A"}

        result = self.repo.record_attempt(self.student_id, quiz_data, user_answers)
        self.assertEqual(result["score"], 1)
        self.assertEqual(result["total_questions"], 2)
        self.assertEqual(result["percentage"], 50.0)

        # Retrieve history
        history = self.repo.get_student_history(self.student_id, include_questions=True)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["chapter"], "Electricity")
        self.assertEqual(len(history[0]["questions"]), 2)
        self.assertTrue(history[0]["questions"][0]["is_correct"])
        self.assertFalse(history[0]["questions"][1]["is_correct"])

    def test_clear_student_data(self):
        quiz_data = {
            "class_level": 10,
            "chapter": "Electricity",
            "questions": [{"question_id": "q1", "correct_answer": "A"}],
        }
        self.repo.record_attempt(self.student_id, quiz_data, {"q_choice_1": "A"})
        history = self.repo.get_student_history(self.student_id)
        self.assertEqual(len(history), 1)

        self.repo.clear_student_data(self.student_id)
        history_after = self.repo.get_student_history(self.student_id)
        self.assertEqual(len(history_after), 0)


if __name__ == "__main__":
    unittest.main()
