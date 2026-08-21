"""Unit tests for Student SWAT Engine."""

import os
import tempfile
import unittest

from src.academic_rag.analytics.swat import (
    format_swat_report,
    get_available_chapters,
    get_student_swat,
)
from src.academic_rag.storage.repository import QuizRepository


class TestStudentSWAT(unittest.TestCase):
    """Tests SWAT profile generation, chapter categorization, and trend calculation."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.db_path = os.path.join(self.temp_dir.name, "test_swat.db")
        self.repo = QuizRepository(db_path=self.db_path)
        self.student_id = "test_student_swat"

    def tearDown(self):
        try:
            self.temp_dir.cleanup()
        except Exception:
            pass

    def test_swat_empty_history(self):
        swat = get_student_swat("non_existent_student", db_path=self.db_path)
        self.assertFalse(swat["has_data"])
        self.assertEqual(swat["overall"]["average"], 0)
        self.assertEqual(len(swat["strengths"]), 0)

    def test_swat_categorization_and_trend(self):
        # 1. Chemical Reactions: 100% -> Strong
        self.repo.record_attempt(
            self.student_id,
            {
                "class_level": 10,
                "chapter": "Chemical Reactions and Equations",
                "difficulty": "medium",
                "questions": [
                    {"question_id": f"c_{i}", "correct_answer": "A"} for i in range(1, 6)
                ],
            },
            {f"q_choice_{i}": "A" for i in range(1, 6)},
        )

        # 2. Electricity: 60% -> Average
        self.repo.record_attempt(
            self.student_id,
            {
                "class_level": 10,
                "chapter": "Electricity",
                "difficulty": "medium",
                "questions": [
                    {"question_id": f"e_{i}", "correct_answer": "A"} for i in range(1, 6)
                ],
            },
            {f"q_choice_{i}": "A" if i <= 3 else "B" for i in range(1, 6)},
        )

        # 3. Magnetic Effects: 40% -> Weak
        self.repo.record_attempt(
            self.student_id,
            {
                "class_level": 10,
                "chapter": "Magnetic Effects of Electric Current",
                "difficulty": "hard",
                "questions": [
                    {"question_id": f"m_{i}", "correct_answer": "A"} for i in range(1, 6)
                ],
            },
            {f"q_choice_{i}": "A" if i <= 2 else "B" for i in range(1, 6)},
        )

        swat = get_student_swat(self.student_id, db_path=self.db_path)
        self.assertTrue(swat["has_data"])
        self.assertEqual(swat["overall"]["quizzes_attempted"], 3)
        self.assertEqual(swat["overall"]["total_questions"], 15)
        self.assertEqual(swat["overall"]["total_correct"], 5 + 3 + 2)  # 10

        strength_names = [s["chapter"] for s in swat["strengths"]]
        avg_names = [a["chapter"] for a in swat["average_topics"]]
        weak_names = [w["chapter"] for w in swat["weak_topics"]]

        self.assertIn("Chemical Reactions and Equations", strength_names)
        self.assertIn("Electricity", avg_names)
        self.assertIn("Magnetic Effects of Electric Current", weak_names)

        # Test ASCII report formatting
        report = format_swat_report(swat)
        self.assertIn("STUDENT SWAT", report)
        self.assertIn("STRONG", report)

        # Test get_available_chapters with SWAT overlay
        available = get_available_chapters(10, student_id=self.student_id, db_path=self.db_path)
        self.assertEqual(len(available), 13)
        chem_item = next(ch for ch in available if ch["chapter_number"] == 1)
        self.assertEqual(chem_item["status"], "strong")
        self.assertEqual(chem_item["score"], 100)


if __name__ == "__main__":
    unittest.main()
