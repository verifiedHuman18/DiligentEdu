"""Unit Tests for Student Performance Over Time and Trend Analytics (Phases 1-23)."""

import os
import shutil
import tempfile
import unittest

from backend.analytics.performance_trend import (
    calculate_linear_regression,
    classify_trend_from_scores,
    get_student_performance_trend,
)
from backend.storage.database import init_database
from backend.storage.repository import QuizRepository


class TestPerformanceTrendAnalytics(unittest.TestCase):
    """Tests for linear regression slope, trend classification, and DB integration."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.test_dir, "test_trend.db")
        init_database(self.db_path)
        self.repo = QuizRepository(db_path=self.db_path)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_phase_4_5_increasing_series_classified_as_improving(self):
        """Increasing series (50, 55, 62, 70) is classified as IMPROVING."""
        scores = [50.0, 55.0, 62.0, 70.0]
        res = classify_trend_from_scores(scores)
        self.assertEqual(res["status"], "improving")
        self.assertIn("🟢", res["status_label"])
        self.assertGreater(res["slope"], 2.0)
        self.assertEqual(res["confidence"], "reliable")
        self.assertEqual(res["current_performance"], 70.0)
        self.assertGreater(res["change_pct_points"], 0)

    def test_phase_4_5_decreasing_series_classified_as_declining(self):
        """Decreasing series (80, 73, 65, 55) is classified as DECLINING."""
        scores = [80.0, 73.0, 65.0, 55.0]
        res = classify_trend_from_scores(scores)
        self.assertEqual(res["status"], "declining")
        self.assertIn("🔴", res["status_label"])
        self.assertLess(res["slope"], -2.0)
        self.assertEqual(res["confidence"], "reliable")
        self.assertEqual(res["current_performance"], 55.0)
        self.assertLess(res["change_pct_points"], 0)

    def test_phase_4_5_stable_series_classified_as_stagnant(self):
        """Stable series (70, 71, 69, 70) is classified as STAGNANT."""
        scores = [70.0, 71.0, 69.0, 70.0]
        res = classify_trend_from_scores(scores)
        self.assertEqual(res["status"], "stagnant")
        self.assertIn("🟡", res["status_label"])
        self.assertTrue(-2.0 <= res["slope"] <= 2.0)
        self.assertEqual(res["confidence"], "reliable")

    def test_phase_12_empty_data_insufficient(self):
        """Empty score list returns insufficient_data status."""
        res = classify_trend_from_scores([])
        self.assertEqual(res["status"], "insufficient_data")
        self.assertEqual(res["confidence"], "insufficient")
        self.assertEqual(res["assessment_count"], 0)

    def test_phase_12_single_assessment_insufficient(self):
        """Single assessment returns insufficient_data status."""
        res = classify_trend_from_scores([70.0])
        self.assertEqual(res["status"], "insufficient_data")
        self.assertEqual(res["confidence"], "insufficient")
        self.assertEqual(res["assessment_count"], 1)
        self.assertEqual(res["current_performance"], 70.0)

    def test_phase_12_two_assessments_preliminary(self):
        """2 assessments yield a preliminary trend."""
        scores = [60.0, 80.0]
        res = classify_trend_from_scores(scores)
        self.assertEqual(res["status"], "improving")
        self.assertEqual(res["confidence"], "preliminary")
        self.assertEqual(res["assessment_count"], 2)

    def test_phase_4_linear_regression_math(self):
        """Verify linear regression formula accuracy."""
        # y = 2x + 10 -> for x = 0, 1, 2, 3 -> y = 10, 12, 14, 16
        slope, intercept, r2 = calculate_linear_regression([10.0, 12.0, 14.0, 16.0])
        self.assertAlmostEqual(slope, 2.0, places=2)
        self.assertAlmostEqual(intercept, 10.0, places=2)
        self.assertAlmostEqual(r2, 1.0, places=2)

    def test_phase_2_3_10_end_to_end_student_performance_trend(self):
        """Test full DB retrieval, percentage conversion, and subject isolation."""
        student_id = "student_trend_alice"

        # Record 4 Science quizzes with increasing performance
        quiz_1 = {
            "class_level": 10,
            "subject": "Science",
            "chapter": "Chemical Reactions and Equations",
            "chapter_number": 1,
            "difficulty": "easy",
            "questions": [
                {"question_id": "q1", "question": "Q1", "correct_answer": "A"},
                {"question_id": "q2", "question": "Q2", "correct_answer": "A"},
            ],
        }
        self.repo.record_attempt(
            student_id=student_id,
            quiz_data=quiz_1,
            user_answers={"q_choice_1": "A", "q_choice_2": "B"},  # 1/2 = 50%
            quiz_id="quiz_sci_1",
        )

        quiz_2 = {
            "class_level": 10,
            "subject": "Science",
            "chapter": "Acids, Bases and Salts",
            "chapter_number": 2,
            "difficulty": "medium",
            "questions": [
                {"question_id": "q1", "question": "Q1", "correct_answer": "A"},
                {"question_id": "q2", "question": "Q2", "correct_answer": "A"},
            ],
        }
        self.repo.record_attempt(
            student_id=student_id,
            quiz_data=quiz_2,
            user_answers={"q_choice_1": "A", "q_choice_2": "A"},  # 2/2 = 100%
            quiz_id="quiz_sci_2",
        )

        # Record 1 Mathematics quiz (must NOT mix into Science trend)
        quiz_math = {
            "class_level": 10,
            "subject": "Mathematics",
            "chapter": "Real Numbers",
            "chapter_number": 1,
            "difficulty": "medium",
            "questions": [
                {"question_id": "qm1", "question": "QM1", "correct_answer": "A"},
            ],
        }
        self.repo.record_attempt(
            student_id=student_id,
            quiz_data=quiz_math,
            user_answers={"q_choice_1": "A"},  # 100%
            quiz_id="quiz_math_1",
        )

        # Fetch Science trend
        sci_trend = get_student_performance_trend(
            student_id=student_id,
            class_level=10,
            subject="Science",
            db_path=self.db_path,
        )
        self.assertTrue(sci_trend["has_data"])
        self.assertEqual(len(sci_trend["points"]), 2)
        self.assertEqual(sci_trend["points"][0]["performance"], 50.0)
        self.assertEqual(sci_trend["points"][0]["chapter"], "Chemical Reactions and Equations")
        self.assertEqual(sci_trend["points"][1]["performance"], 100.0)
        self.assertEqual(sci_trend["points"][1]["chapter"], "Acids, Bases and Salts")
        self.assertEqual(sci_trend["trend"]["status"], "improving")

        # Fetch Mathematics trend (should only have 1 quiz -> insufficient_data)
        math_trend = get_student_performance_trend(
            student_id=student_id,
            class_level=10,
            subject="Mathematics",
            db_path=self.db_path,
        )
        self.assertTrue(math_trend["has_data"])
        self.assertEqual(len(math_trend["points"]), 1)
        self.assertEqual(math_trend["trend"]["status"], "insufficient_data")
        self.assertEqual(math_trend["points"][0]["chapter"], "Real Numbers")

    def test_multi_student_isolation(self):
        """Quizzes for Alice must not leak into Bob's performance trend."""
        quiz_data = {
            "class_level": 10,
            "subject": "Science",
            "chapter": "Electricity",
            "questions": [{"question_id": "q1", "correct_answer": "A"}],
        }
        self.repo.record_attempt("student_alice", quiz_data, {"q_choice_1": "A"}, "q_a1")
        self.repo.record_attempt("student_alice", quiz_data, {"q_choice_1": "A"}, "q_a2")

        alice_trend = get_student_performance_trend(
            "student_alice", class_level=10, db_path=self.db_path
        )
        bob_trend = get_student_performance_trend(
            "student_bob", class_level=10, db_path=self.db_path
        )

        self.assertEqual(len(alice_trend["points"]), 2)
        self.assertEqual(len(bob_trend["points"]), 0)
        self.assertFalse(bob_trend["has_data"])


if __name__ == "__main__":
    unittest.main()
