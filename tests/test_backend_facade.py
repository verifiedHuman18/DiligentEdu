"""Unit tests for backend.py Public Facade."""

import os
import tempfile
import unittest

import backend


class TestBackendFacade(unittest.TestCase):
    """Tests the top-level backend facade API functions."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.db_path = os.path.join(self.temp_dir.name, "test_facade.db")
        self.student_id = "test_facade_student"

    def tearDown(self):
        try:
            self.temp_dir.cleanup()
        except Exception:
            pass

    def test_backend_exports_and_calls(self):
        # 1. get_available_chapters
        chapters = backend.get_available_chapters(10, db_path=self.db_path)
        self.assertEqual(len(chapters), 13)

        # 2. submit_quiz
        mock_quiz = {
            "class_level": 10,
            "chapter": "Electricity",
            "chapter_number": 11,
            "difficulty": "medium",
            "questions": [
                {"question_id": "q1", "question": "What is Ohm's law?", "correct_answer": "A"},
                {"question_id": "q2", "question": "What is Joule heating?", "correct_answer": "B"},
            ],
        }
        res = backend.submit_quiz(
            student_id=self.student_id,
            answers={"q_choice_1": "A", "q_choice_2": "B"},
            quiz_data=mock_quiz,
            db_path=self.db_path,
        )
        self.assertEqual(res["score"], 2)
        self.assertEqual(res["percentage"], 100)

        # 3. get_student_swat
        swat = backend.get_student_swat(self.student_id, db_path=self.db_path)
        self.assertTrue(swat["has_data"])
        self.assertEqual(swat["overall"]["average"], 100)

        # 4. get_student_quiz_history
        history = backend.get_student_quiz_history(self.student_id, db_path=self.db_path)
        self.assertEqual(len(history), 1)

        # 5. Teacher APIs
        overview = backend.get_student_overview(self.student_id, db_path=self.db_path)
        self.assertEqual(overview["total_quizzes"], 1)

        chapter_stats = backend.get_student_chapter_stats(self.student_id, db_path=self.db_path)
        self.assertEqual(len(chapter_stats), 1)

        status = backend.get_student_status(self.student_id, db_path=self.db_path)
        self.assertEqual(status["overall_status"], "Performing Well")

        profile = backend.get_teacher_student_profile(self.student_id, db_path=self.db_path)
        self.assertTrue(profile["has_data"])

        # 6. clear_student_data
        backend.clear_student_data(self.student_id, db_path=self.db_path)
        swat_after = backend.get_student_swat(self.student_id, db_path=self.db_path)
        self.assertFalse(swat_after["has_data"])

    def test_quiz_generator_signature_compatibility(self):
        from unittest.mock import patch

        from src.academic_rag.quiz.generator import create_student_quiz

        mock_return = {"quiz_id": "test_123", "questions": []}
        with patch(
            "src.academic_rag.quiz.generator.generate_quiz", return_value=mock_return
        ) as mock_gen:
            # Test create_student_quiz with model_name
            res1 = create_student_quiz(
                student_id="test_student",
                class_level=10,
                chapter="Electricity",
                difficulty="medium",
                num_questions=5,
                api_key="test_key",
                model_name="gemini-2.5-flash",
            )
            self.assertEqual(res1["student_id"], "test_student")
            mock_gen.assert_called_with(
                class_level=10,
                chapter="Electricity",
                difficulty="medium",
                num_questions=5,
                subject="Science",
                student_id="test_student",
                api_key="test_key",
                model="gemini-2.5-flash",
                pinecone_api_key=None,
            )

            # Test backend.generate_student_quiz with model_name
            res2 = backend.generate_student_quiz(
                student_id="test_student",
                class_level=10,
                chapter="Electricity",
                difficulty="medium",
                num_questions=5,
                api_key="test_key",
                model_name="gemini-3.5-flash-lite",
            )
            self.assertEqual(res2["student_id"], "test_student")


if __name__ == "__main__":
    unittest.main()
