"""Unit tests for Phase 13 (Improved Chapter Statistics) & Phase 14 (Unified SWAT Output)."""

import os
import tempfile
import unittest

from backend.analytics.swat import get_student_swat
from backend.storage.repository import QuizRepository


class TestUnifiedSwatOutput(unittest.TestCase):
    """
    Tests that get_student_swat provides comprehensive chapter statistics
    and a clean, unified schema serving as the single source of truth across all components.
    """

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.db_path = os.path.join(self.temp_dir.name, "test_unified_swat.db")
        self.repo = QuizRepository(db_path=self.db_path)
        self.student_id = "student_p13_p14"

    def tearDown(self):
        try:
            self.temp_dir.cleanup()
        except Exception:
            pass

    def test_chapter_statistics_and_trend(self):
        """
        Phase 13: For every attempted chapter, calculate:
        - Average score (e.g. 40%, 60%, 80% -> 60%)
        - Attempts count (3)
        - Accuracy
        - Recent performance (40% → 60% → 80%)
        - Trend (improving, stable, declining)
        """
        # Quiz 1: Electricity -> 40% (2/5)
        self.repo.record_attempt(
            self.student_id,
            {
                "class_level": 10,
                "chapter": "Electricity",
                "chapter_number": 11,
                "difficulty": "easy",
                "questions": [
                    {"question_id": f"eq1_{i}", "correct_answer": "A"} for i in range(1, 6)
                ],
            },
            {f"q_choice_{i}": "A" if i <= 2 else "B" for i in range(1, 6)},
        )

        # Quiz 2: Electricity -> 60% (3/5)
        self.repo.record_attempt(
            self.student_id,
            {
                "class_level": 10,
                "chapter": "Electricity",
                "chapter_number": 11,
                "difficulty": "medium",
                "questions": [
                    {"question_id": f"eq2_{i}", "correct_answer": "A"} for i in range(1, 6)
                ],
            },
            {f"q_choice_{i}": "A" if i <= 3 else "B" for i in range(1, 6)},
        )

        # Quiz 3: Electricity -> 80% (4/5)
        self.repo.record_attempt(
            self.student_id,
            {
                "class_level": 10,
                "chapter": "Electricity",
                "chapter_number": 11,
                "difficulty": "hard",
                "questions": [
                    {"question_id": f"eq3_{i}", "correct_answer": "A"} for i in range(1, 6)
                ],
            },
            {f"q_choice_{i}": "A" if i <= 4 else "B" for i in range(1, 6)},
        )

        swat = get_student_swat(self.student_id, class_level=10, db_path=self.db_path)
        self.assertTrue(swat["has_data"])

        # Check chapter metrics for Electricity
        ch_stats = swat["chapter_breakdown"]["Electricity"]
        self.assertEqual(ch_stats["score"], 60)  # (40 + 60 + 80) / 3 = 60%
        self.assertEqual(ch_stats["attempts"], 3)
        self.assertEqual(ch_stats["scores"], [40, 60, 80])
        self.assertEqual(ch_stats["accuracy"], 60.0)  # (2 + 3 + 4) / 15 = 9/15 = 60.0%
        self.assertEqual(ch_stats["recent_performance"], "40% → 60% → 80%")
        self.assertEqual(ch_stats["trend"], "improving")
        self.assertEqual(ch_stats["category"], "average")

        # Must be categorized under average
        self.assertEqual(len(swat["average"]), 1)
        self.assertEqual(swat["average"][0]["chapter"], "Electricity")
        self.assertEqual(swat["average"][0]["score"], 60)
        self.assertEqual(swat["average"][0]["attempts"], 3)

    def test_declining_chapter_trend(self):
        """Verify declining chapter scores are correctly identified as 'declining'."""
        # Scores: 80% -> 60% -> 40%
        for score_correct in [4, 3, 2]:
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
                {f"q_choice_{i}": "A" if i <= score_correct else "B" for i in range(1, 6)},
            )

        swat = get_student_swat(self.student_id, class_level=10, db_path=self.db_path)
        lp = swat["chapter_breakdown"]["Life Processes"]
        self.assertEqual(lp["score"], 60)
        self.assertEqual(lp["attempts"], 3)
        self.assertEqual(lp["scores"], [80, 60, 40])
        self.assertEqual(lp["trend"], "declining")
        self.assertEqual(lp["recent_performance"], "80% → 60% → 40%")

    def test_unified_output_schema_and_overall_kpis(self):
        """
        Phase 14: Unified SWAT output structure contains:
        class_level, overall (average, accuracy, attempted_chapters, total_chapters),
        strong, average, weak, unattempted, trend.
        """
        # Record 1 attempt in Chemical Reactions (100%)
        self.repo.record_attempt(
            self.student_id,
            {
                "class_level": 10,
                "chapter": "Chemical Reactions and Equations",
                "chapter_number": 1,
                "difficulty": "medium",
                "questions": [
                    {"question_id": f"cr_{i}", "correct_answer": "A"} for i in range(1, 6)
                ],
            },
            {f"q_choice_{i}": "A" for i in range(1, 6)},
        )

        swat = get_student_swat(self.student_id, class_level=10, db_path=self.db_path)

        # 1. Top-Level Keys
        self.assertEqual(swat["class_level"], 10)
        self.assertTrue(swat["has_data"])
        self.assertIn("overall", swat)
        self.assertIn("strong", swat)
        self.assertIn("average", swat)
        self.assertIn("weak", swat)
        self.assertIn("unattempted", swat)
        self.assertIn("trend", swat)
        self.assertIn("chapter_breakdown", swat)

        # 2. Overall Object
        overall = swat["overall"]
        self.assertEqual(overall["average"], 100)
        self.assertEqual(overall["accuracy"], 100)
        self.assertEqual(overall["attempted_chapters"], 1)
        self.assertEqual(overall["total_chapters"], 13)
        self.assertEqual(overall["quizzes_attempted"], 1)

        # 3. Strong list
        self.assertEqual(len(swat["strong"]), 1)
        self.assertEqual(swat["strong"][0]["chapter"], "Chemical Reactions and Equations")
        self.assertEqual(swat["strong"][0]["score"], 100)
        self.assertEqual(swat["strong"][0]["attempts"], 1)

        # 4. Unattempted list
        self.assertEqual(len(swat["unattempted"]), 12)

        # 5. Trend
        self.assertEqual(swat["trend"]["direction"], "stable")

        # 6. Backward Compatibility Aliases
        self.assertEqual(swat["strengths"], swat["strong"])
        self.assertEqual(swat["average_topics"], swat["average"])
        self.assertEqual(swat["weak_topics"], swat["weak"])
        self.assertEqual(swat["unattempted_topics"], swat["unattempted"])

    def test_configurable_thresholds(self):
        """Verify thresholds remain configurable."""
        # 1 attempt with 75% score
        self.repo.record_attempt(
            self.student_id,
            {
                "class_level": 10,
                "chapter": "Light – Reflection and Refraction",
                "chapter_number": 9,
                "difficulty": "medium",
                "questions": [
                    {"question_id": f"lt_{i}", "correct_answer": "A"} for i in range(1, 5)
                ],
            },
            {"q_choice_1": "A", "q_choice_2": "A", "q_choice_3": "A", "q_choice_4": "B"},
        )  # 3/4 = 75%

        # Default thresholds (>= 70 -> strong)
        swat_def = get_student_swat(self.student_id, class_level=10, db_path=self.db_path)
        self.assertEqual(len(swat_def["strong"]), 1)
        self.assertEqual(len(swat_def["average"]), 0)

        # Custom higher thresholds (>= 80 -> strong, >= 60 -> average)
        swat_custom = get_student_swat(
            self.student_id,
            class_level=10,
            db_path=self.db_path,
            strong_threshold=80.0,
            average_threshold=60.0,
        )
        self.assertEqual(len(swat_custom["strong"]), 0)
        self.assertEqual(len(swat_custom["average"]), 1)
        self.assertEqual(swat_custom["average"][0]["chapter"], "Light – Reflection and Refraction")


if __name__ == "__main__":
    unittest.main()
