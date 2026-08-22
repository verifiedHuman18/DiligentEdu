"""Unit tests for Phase 12: SWAT Unattempted Chapters Integration."""

import os
import tempfile
import unittest

import backend
from src.academic_rag.analytics.swat import (
    format_swat_report,
    get_attempted_chapters,
    get_student_swat,
    get_unattempted_chapters,
)
from src.academic_rag.storage.repository import QuizRepository


class TestSwatUnattemptedChapters(unittest.TestCase):
    """
    Verifies that SWAT categorizes chapters into 4 distinct groups:
    Strong, Average, Weak, and Unattempted.
    Ensures unattempted chapters NEVER receive an artificial 0% score.
    """

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.db_path = os.path.join(self.temp_dir.name, "test_unattempted_swat.db")
        self.repo = QuizRepository(db_path=self.db_path)
        self.student_id = "student_test_p12"

    def tearDown(self):
        try:
            self.temp_dir.cleanup()
        except Exception:
            pass

    def test_fresh_student_all_chapters_unattempted(self):
        """A student with 0 attempts should have all 13 Class 10 chapters in unattempted with score=None."""
        swat = get_student_swat(self.student_id, class_level=10, db_path=self.db_path)
        self.assertFalse(swat["has_data"])
        self.assertEqual(len(swat["strengths"]), 0)
        self.assertEqual(len(swat["average_topics"]), 0)
        self.assertEqual(len(swat["weak_topics"]), 0)

        unattempted = swat["unattempted_topics"]
        self.assertEqual(len(unattempted), 13)

        # Verify NO chapter receives artificial 0%
        for item in unattempted:
            self.assertIsNone(item["score"], f"Chapter {item['chapter']} received artificial score!")
            self.assertIsNone(item["accuracy"])
            self.assertEqual(item["attempts"], 0)
            self.assertEqual(item["category"], "unattempted")

        # Verify helper
        unatt_helper = get_unattempted_chapters(self.student_id, class_level=10, db_path=self.db_path)
        self.assertEqual(len(unatt_helper), 13)
        attempted_helper = get_attempted_chapters(self.student_id, class_level=10, db_path=self.db_path)
        self.assertEqual(len(attempted_helper), 0)

    def test_partial_attempts_four_categories(self):
        """Student with 2 attempts should have 2 scored chapters and 11 unattempted chapters."""
        # 1. Strong Chapter: Chemical Reactions (100%)
        self.repo.record_attempt(
            self.student_id,
            {
                "class_level": 10,
                "chapter": "Chemical Reactions and Equations",
                "chapter_number": 1,
                "difficulty": "medium",
                "questions": [
                    {"question_id": f"c10_q_{i}", "correct_answer": "A"} for i in range(1, 6)
                ],
            },
            {f"q_choice_{i}": "A" for i in range(1, 6)},
        )

        # 2. Weak Chapter: Electricity (40%)
        self.repo.record_attempt(
            self.student_id,
            {
                "class_level": 10,
                "chapter": "Electricity",
                "chapter_number": 11,
                "difficulty": "hard",
                "questions": [
                    {"question_id": f"c10_e_{i}", "correct_answer": "A"} for i in range(1, 6)
                ],
            },
            {f"q_choice_{i}": "A" if i <= 2 else "B" for i in range(1, 6)},
        )

        swat = get_student_swat(self.student_id, class_level=10, db_path=self.db_path)
        self.assertTrue(swat["has_data"])

        # Strengths: 1 chapter (Chemical Reactions)
        self.assertEqual(len(swat["strengths"]), 1)
        self.assertEqual(swat["strengths"][0]["chapter"], "Chemical Reactions and Equations")
        self.assertEqual(swat["strengths"][0]["score"], 100)

        # Average: 0 chapters
        self.assertEqual(len(swat["average_topics"]), 0)

        # Weak: 1 chapter (Electricity)
        self.assertEqual(len(swat["weak_topics"]), 1)
        self.assertEqual(swat["weak_topics"][0]["chapter"], "Electricity")
        self.assertEqual(swat["weak_topics"][0]["score"], 40)

        # Unattempted: 11 chapters (13 - 2)
        unattempted = swat["unattempted_topics"]
        self.assertEqual(len(unattempted), 11)
        unatt_names = [u["chapter"] for u in unattempted]
        self.assertNotIn("Chemical Reactions and Equations", unatt_names)
        self.assertNotIn("Electricity", unatt_names)
        self.assertIn("Magnetic Effects of Electric Current", unatt_names)
        self.assertIn("Life Processes", unatt_names)

        for u in unattempted:
            self.assertIsNone(u["score"])
            self.assertEqual(u["attempts"], 0)
            self.assertEqual(u["category"], "unattempted")

        # Check helpers
        attempted = get_attempted_chapters(self.student_id, class_level=10, db_path=self.db_path)
        self.assertEqual(len(attempted), 2)
        self.assertIn("Chemical Reactions and Equations", attempted)
        self.assertIn("Electricity", attempted)

    def test_zero_percent_is_not_unattempted(self):
        """A score of 0% on an attempted quiz is WEAK (<50%), NOT 'Not Attempted'."""
        self.repo.record_attempt(
            self.student_id,
            {
                "class_level": 10,
                "chapter": "Life Processes",
                "chapter_number": 5,
                "difficulty": "medium",
                "questions": [
                    {"question_id": f"lp_{i}", "correct_answer": "A"} for i in range(1, 6)
                ],
            },
            {f"q_choice_{i}": "B" for i in range(1, 6)},  # All wrong -> 0%
        )

        swat = get_student_swat(self.student_id, class_level=10, db_path=self.db_path)
        self.assertTrue(swat["has_data"])

        # Life Processes must be in weak_topics with score 0
        weak_names = [w["chapter"] for w in swat["weak_topics"]]
        self.assertIn("Life Processes", weak_names)
        lp_weak = next(w for w in swat["weak_topics"] if w["chapter"] == "Life Processes")
        self.assertEqual(lp_weak["score"], 0)
        self.assertEqual(lp_weak["attempts"], 1)

        # Life Processes must NOT be in unattempted_topics
        unatt_names = [u["chapter"] for u in swat["unattempted_topics"]]
        self.assertNotIn("Life Processes", unatt_names)

    def test_formatted_swat_report_includes_unattempted_section(self):
        """Verify format_swat_report includes '⚪ NOT ATTEMPTED' section."""
        self.repo.record_attempt(
            self.student_id,
            {
                "class_level": 10,
                "chapter": "Light – Reflection and Refraction",
                "chapter_number": 9,
                "difficulty": "medium",
                "questions": [
                    {"question_id": f"l_{i}", "correct_answer": "A"} for i in range(1, 6)
                ],
            },
            {f"q_choice_{i}": "A" for i in range(1, 6)},
        )

        swat = get_student_swat(self.student_id, class_level=10, db_path=self.db_path)
        report = format_swat_report(swat)

        self.assertIn("🟢 STRONG (≥ 70%)", report)
        self.assertIn("Light – Reflection and Refraction", report)
        self.assertIn("⚪ NOT ATTEMPTED", report)
        self.assertIn("Electricity", report)
        self.assertIn("Chemical Reactions and Equations", report)

    def test_backend_facade_unattempted_apis(self):
        """Verify backend facade exposes get_attempted_chapters and get_unattempted_chapters."""
        self.repo.record_attempt(
            self.student_id,
            {
                "class_level": 10,
                "chapter": "Electricity",
                "chapter_number": 11,
                "difficulty": "medium",
                "questions": [
                    {"question_id": f"e_{i}", "correct_answer": "A"} for i in range(1, 6)
                ],
            },
            {f"q_choice_{i}": "A" for i in range(1, 6)},
        )

        attempted = backend.get_attempted_chapters(
            self.student_id, class_level=10, db_path=self.db_path
        )
        self.assertEqual(attempted, ["Electricity"])

        unattempted = backend.get_unattempted_chapters(
            self.student_id, class_level=10, db_path=self.db_path
        )
        self.assertEqual(len(unattempted), 12)
        self.assertNotIn("Electricity", [u["chapter"] for u in unattempted])


if __name__ == "__main__":
    unittest.main()
