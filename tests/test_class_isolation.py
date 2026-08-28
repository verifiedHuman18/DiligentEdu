"""Unit and Integration Tests for Phase 10: Strict Class Isolation."""

import os
import tempfile
import unittest

import backend
from backend.analytics.swat import get_available_chapters, get_student_swat
from backend.analytics.teacher import (
    get_student_status,
    get_teacher_chapter_statistics,
    get_teacher_student_overview,
    get_teacher_student_profile,
)
from backend.quiz.evaluator import submit_and_grade_quiz
from backend.storage.repository import (
    QuizRepository,
    get_student_class_history,
)


class TestClassIsolation(unittest.TestCase):
    """
    Tests that a student's Class 9 data NEVER pollutes Class 10 SWAT/analytics/action plans,
    and vice versa, with strict database query-level filtering.
    """

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.db_path = os.path.join(self.temp_dir.name, "test_isolation.db")
        self.repo = QuizRepository(db_path=self.db_path)
        self.student_id = "student_001"

        # Populate Class 9 attempts for student_001
        # 1. Class 9: Exploration: Entering the World of Secondary Science -> 100%
        self.repo.record_attempt(
            self.student_id,
            {
                "class_level": 9,
                "chapter": "Exploration: Entering the World of Secondary Science",
                "chapter_number": 1,
                "difficulty": "easy",
                "questions": [
                    {"question_id": f"c9_1_{i}", "correct_answer": "A"} for i in range(1, 6)
                ],
            },
            {f"q_choice_{i}": "A" for i in range(1, 6)},
        )

        # 2. Class 9: Describing Motion Around Us -> 80% (4/5)
        self.repo.record_attempt(
            self.student_id,
            {
                "class_level": 9,
                "chapter": "Describing Motion Around Us",
                "chapter_number": 4,
                "difficulty": "medium",
                "questions": [
                    {"question_id": f"c9_2_{i}", "correct_answer": "A"} for i in range(1, 6)
                ],
            },
            {f"q_choice_{i}": "A" if i <= 4 else "B" for i in range(1, 6)},
        )

        # Populate Class 10 attempts for student_001
        # 3. Class 10: Chemical Reactions and Equations -> 60% (3/5)
        self.repo.record_attempt(
            self.student_id,
            {
                "class_level": 10,
                "chapter": "Chemical Reactions and Equations",
                "chapter_number": 1,
                "difficulty": "medium",
                "questions": [
                    {"question_id": f"c10_1_{i}", "correct_answer": "A"} for i in range(1, 6)
                ],
            },
            {f"q_choice_{i}": "A" if i <= 3 else "B" for i in range(1, 6)},
        )

        # 4. Class 10: Electricity -> 40% (2/5)
        self.repo.record_attempt(
            self.student_id,
            {
                "class_level": 10,
                "chapter": "Electricity",
                "chapter_number": 11,
                "difficulty": "hard",
                "questions": [
                    {"question_id": f"c10_2_{i}", "correct_answer": "A"} for i in range(1, 6)
                ],
            },
            {f"q_choice_{i}": "A" if i <= 2 else "B" for i in range(1, 6)},
        )

    def tearDown(self):
        try:
            self.temp_dir.cleanup()
        except Exception:
            pass

    def test_repository_get_student_class_history(self):
        """Verify get_student_class_history strictly retrieves only the requested class."""
        c9_history = self.repo.get_student_class_history(self.student_id, class_level=9)
        self.assertEqual(len(c9_history), 2)
        for att in c9_history:
            self.assertEqual(att["class_level"], 9)
            self.assertIn(
                att["chapter"],
                [
                    "Exploration: Entering the World of Secondary Science",
                    "Describing Motion Around Us",
                ],
            )

        c10_history = self.repo.get_student_class_history(self.student_id, class_level=10)
        self.assertEqual(len(c10_history), 2)
        for att in c10_history:
            self.assertEqual(att["class_level"], 10)
            self.assertIn(att["chapter"], ["Chemical Reactions and Equations", "Electricity"])

        # Test standalone helper
        helper_c9 = get_student_class_history(self.student_id, class_level=9, db_path=self.db_path)
        self.assertEqual(len(helper_c9), 2)

    def test_swat_class_isolation(self):
        """Verify SWAT calculations are 100% isolated between Class 9 and Class 10."""
        # Class 9 SWAT
        swat_c9 = get_student_swat(self.student_id, class_level=9, db_path=self.db_path)
        self.assertTrue(swat_c9["has_data"])
        self.assertEqual(swat_c9["overall"]["quizzes_attempted"], 2)
        self.assertEqual(swat_c9["overall"]["total_questions"], 10)
        self.assertEqual(swat_c9["overall"]["total_correct"], 9)  # 5 + 4
        self.assertEqual(swat_c9["overall"]["average"], 90)
        self.assertEqual(swat_c9["overall"]["accuracy"], 90)

        c9_breakdown = swat_c9["chapter_breakdown"]
        self.assertIn("Exploration: Entering the World of Secondary Science", c9_breakdown)
        self.assertIn("Describing Motion Around Us", c9_breakdown)
        self.assertNotIn("Electricity", c9_breakdown)
        self.assertNotIn("Chemical Reactions and Equations", c9_breakdown)

        # Class 10 SWAT
        swat_c10 = get_student_swat(self.student_id, class_level=10, db_path=self.db_path)
        self.assertTrue(swat_c10["has_data"])
        self.assertEqual(swat_c10["overall"]["quizzes_attempted"], 2)
        self.assertEqual(swat_c10["overall"]["total_questions"], 10)
        self.assertEqual(swat_c10["overall"]["total_correct"], 5)  # 3 + 2
        self.assertEqual(swat_c10["overall"]["average"], 50)
        self.assertEqual(swat_c10["overall"]["accuracy"], 50)

        c10_breakdown = swat_c10["chapter_breakdown"]
        self.assertIn("Chemical Reactions and Equations", c10_breakdown)
        self.assertIn("Electricity", c10_breakdown)
        self.assertNotIn("Exploration: Entering the World of Secondary Science", c10_breakdown)
        self.assertNotIn("Describing Motion Around Us", c10_breakdown)

        # Weak topics in Class 10 should not affect Class 9
        weak_c10 = [w["chapter"] for w in swat_c10["weak_topics"]]
        self.assertIn("Electricity", weak_c10)
        self.assertEqual(len(swat_c9["weak_topics"]), 0)

    def test_available_chapters_overlay_isolation(self):
        """Verify chapter list status overlay only reflects attempts in that grade."""
        chs_9 = get_available_chapters(9, student_id=self.student_id, db_path=self.db_path)
        ch1_9 = next(c for c in chs_9 if c["chapter_number"] == 1)
        self.assertEqual(ch1_9["chapter"], "Exploration: Entering the World of Secondary Science")
        self.assertEqual(ch1_9["status"], "strong")
        self.assertEqual(ch1_9["score"], 100)

        ch4_9 = next(c for c in chs_9 if c["chapter_number"] == 4)
        self.assertEqual(ch4_9["chapter"], "Describing Motion Around Us")
        self.assertEqual(ch4_9["status"], "strong")
        self.assertEqual(ch4_9["score"], 80)

        chs_10 = get_available_chapters(10, student_id=self.student_id, db_path=self.db_path)
        ch1_10 = next(c for c in chs_10 if c["chapter_number"] == 1)
        self.assertEqual(ch1_10["chapter"], "Chemical Reactions and Equations")
        self.assertEqual(ch1_10["status"], "average")
        self.assertEqual(ch1_10["score"], 60)

        ch11_10 = next(c for c in chs_10 if c["chapter_number"] == 11)
        self.assertEqual(ch11_10["chapter"], "Electricity")
        self.assertEqual(ch11_10["status"], "weak")
        self.assertEqual(ch11_10["score"], 40)

    def test_teacher_analytics_class_isolation(self):
        """Verify teacher diagnostics and master profiles respect class isolation."""
        # Class 9 Overview
        t_overview_9 = get_teacher_student_overview(
            self.student_id, class_level=9, db_path=self.db_path
        )
        self.assertEqual(t_overview_9["overall_average"], 90)
        self.assertEqual(t_overview_9["total_quizzes"], 2)

        # Class 10 Overview
        t_overview_10 = get_teacher_student_overview(
            self.student_id, class_level=10, db_path=self.db_path
        )
        self.assertEqual(t_overview_10["overall_average"], 50)
        self.assertEqual(t_overview_10["total_quizzes"], 2)

        # Class 9 Chapter stats
        stats_9 = get_teacher_chapter_statistics(
            self.student_id, class_level=9, db_path=self.db_path
        )
        self.assertEqual(len(stats_9), 2)
        stat_names_9 = [s["chapter"] for s in stats_9]
        self.assertIn("Exploration: Entering the World of Secondary Science", stat_names_9)
        self.assertIn("Describing Motion Around Us", stat_names_9)
        self.assertNotIn("Electricity", stat_names_9)

        # Class 10 Status (should trigger weak topic alert for Electricity)
        status_10 = get_student_status(self.student_id, class_level=10, db_path=self.db_path)
        self.assertEqual(status_10["overall_status"], "Monitor")
        self.assertIn("Electricity", status_10["weak_topics"])

        # Class 9 Status (should be Performing Well with 0 weak topics)
        status_9 = get_student_status(self.student_id, class_level=9, db_path=self.db_path)
        self.assertEqual(status_9["overall_status"], "Performing Well")
        self.assertEqual(len(status_9["weak_topics"]), 0)

        # Master profile
        prof_9 = get_teacher_student_profile(self.student_id, class_level=9, db_path=self.db_path)
        self.assertEqual(prof_9["overview"]["overall_average"], 90)
        self.assertEqual(len(prof_9["chapter_statistics"]), 2)

        prof_10 = get_teacher_student_profile(self.student_id, class_level=10, db_path=self.db_path)
        self.assertEqual(prof_10["overview"]["overall_average"], 50)
        self.assertEqual(len(prof_10["chapter_statistics"]), 2)

    def test_backend_facade_class_isolation(self):
        """Verify backend facade methods isolate by class_level."""
        c9_hist = backend.get_student_class_history(
            self.student_id, class_level=9, db_path=self.db_path
        )
        self.assertEqual(len(c9_hist), 2)

        c10_swat = backend.get_student_swat(self.student_id, class_level=10, db_path=self.db_path)
        self.assertEqual(c10_swat["overall"]["average"], 50)

        c9_swat = backend.get_student_swat(self.student_id, class_level=9, db_path=self.db_path)
        self.assertEqual(c9_swat["overall"]["average"], 90)

    def test_quiz_evaluator_isolated_swat_transition(self):
        """Verify submitting a Class 9 quiz calculates transition using Class 9 history only."""
        new_quiz = {
            "class_level": 9,
            "chapter": "Describing Motion Around Us",
            "difficulty": "medium",
            "questions": [
                {"question_id": "m_new_1", "correct_answer": "A"},
                {"question_id": "m_new_2", "correct_answer": "A"},
            ],
        }
        res = submit_and_grade_quiz(
            student_id=self.student_id,
            quiz_data=new_quiz,
            user_answers={"q_choice_1": "A", "q_choice_2": "A"},
            db_path=self.db_path,
        )
        self.assertEqual(res["score"], 2)
        self.assertEqual(res["percentage"], 100)
        self.assertEqual(res["class_level"], 9)
        # Previous score for Describing Motion Around Us in Class 9 was 80%
        self.assertEqual(res["previous_chapter_score"], 80)
        # New score for Describing Motion Around Us in Class 9 is mean of [80%, 100%] = 90%
        self.assertEqual(res["new_chapter_score"], 90)


if __name__ == "__main__":
    unittest.main()
