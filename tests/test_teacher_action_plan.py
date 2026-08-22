"""Unit tests for Phase 19 (Teacher Action-Plan Statistics) & Phase 20 (Class-Scoped Teacher Analytics)."""

import os
import tempfile
import unittest

from src.academic_rag.analytics.teacher import get_teacher_student_profile
from src.academic_rag.storage.repository import QuizRepository


class TestTeacherActionPlanAndClassScoping(unittest.TestCase):
    """
    Verifies that Teacher master profiles include rich action plan statistics (Phase 19)
    and strictly scope all metrics, SWAT, and recommendations to the selected grade (Phase 20).
    """

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.db_path = os.path.join(self.temp_dir.name, "test_teacher_action_plan.db")
        self.repo = QuizRepository(db_path=self.db_path)
        self.student_id = "student_teacher_scope_test"

        # Populate Class 9 attempts:
        # 1. Describing Motion Around Us (60%)
        self.repo.record_attempt(
            self.student_id,
            {
                "class_level": 9,
                "chapter": "Describing Motion Around Us",
                "chapter_number": 4,
                "difficulty": "medium",
                "questions": [
                    {"question_id": f"c9_m_{i}", "correct_answer": "A"} for i in range(1, 6)
                ],
            },
            {f"q_choice_{i}": "A" if i <= 3 else "B" for i in range(1, 6)},
        )

        # 2. Exploration (80%)
        self.repo.record_attempt(
            self.student_id,
            {
                "class_level": 9,
                "chapter": "Exploration: Entering the World of Secondary Science",
                "chapter_number": 1,
                "difficulty": "easy",
                "questions": [
                    {"question_id": f"c9_e_{i}", "correct_answer": "A"} for i in range(1, 6)
                ],
            },
            {f"q_choice_{i}": "A" if i <= 4 else "B" for i in range(1, 6)},
        )

        # Populate Class 10 attempts:
        # 3. Electricity (attempt 1: 40%, attempt 2: 60%, attempt 3: 40%) -> weak (46.7%)
        for score_corr in [2, 3, 2]:
            self.repo.record_attempt(
                self.student_id,
                {
                    "class_level": 10,
                    "chapter": "Electricity",
                    "chapter_number": 11,
                    "difficulty": "medium",
                    "questions": [
                        {"question_id": f"c10_el_{i}", "correct_answer": "A"} for i in range(1, 6)
                    ],
                },
                {f"q_choice_{i}": "A" if i <= score_corr else "B" for i in range(1, 6)},
            )

        # 4. Chemical Reactions (100%)
        self.repo.record_attempt(
            self.student_id,
            {
                "class_level": 10,
                "chapter": "Chemical Reactions and Equations",
                "chapter_number": 1,
                "difficulty": "medium",
                "questions": [
                    {"question_id": f"c10_cr_{i}", "correct_answer": "A"} for i in range(1, 6)
                ],
            },
            {f"q_choice_{i}": "A" for i in range(1, 6)},
        )

    def tearDown(self):
        try:
            self.temp_dir.cleanup()
        except Exception:
            pass

    def test_teacher_profile_contains_action_plan_statistics(self):
        """Phase 19: Verify action plan in teacher profile has supporting stats & reasoning."""
        prof_10 = get_teacher_student_profile(self.student_id, class_level=10, db_path=self.db_path)
        self.assertTrue(prof_10["has_data"])
        self.assertIn("action_plan", prof_10)

        plan = prof_10["action_plan"]
        self.assertEqual(plan["class_level"], 10)
        self.assertEqual(plan["priority"], "high")

        # Electricity should be Priority 1
        actions = plan["actions"]
        act1 = actions[0]
        self.assertEqual(act1["chapter"], "Electricity")
        self.assertEqual(act1["status"], "weak")
        self.assertEqual(act1["priority_rank"], 1)
        self.assertEqual(act1["attempts"], 3)
        self.assertEqual(act1["recent_performance"], "40% → 60% → 40%")
        self.assertIn("below target", act1["reason"])

    def test_strict_class_scoping_class_9(self):
        """
        Phase 20: When Teacher views Class 9, ALL analytics, SWAT, chapter stats,
        and recommendations must come from Class 9. Zero Class 10 chapters (like Electricity) allowed.
        """
        prof_9 = get_teacher_student_profile(self.student_id, class_level=9, db_path=self.db_path)
        self.assertTrue(prof_9["has_data"])
        self.assertEqual(prof_9["overview"]["class"], 9)
        self.assertEqual(prof_9["overview"]["total_quizzes"], 2)

        # Verify chapter statistics only have Class 9 chapters
        ch_names_9 = [c["chapter"] for c in prof_9["chapter_statistics"]]
        self.assertIn("Describing Motion Around Us", ch_names_9)
        self.assertIn("Exploration: Entering the World of Secondary Science", ch_names_9)
        self.assertNotIn("Electricity", ch_names_9)
        self.assertNotIn("Chemical Reactions and Equations", ch_names_9)

        # Verify action plan only contains Class 9 chapters
        plan_ch_names_9 = [a["chapter"] for a in prof_9["action_plan"]["actions"]]
        self.assertIn("Describing Motion Around Us", plan_ch_names_9)
        self.assertNotIn("Electricity", plan_ch_names_9)
        self.assertNotIn("Chemical Reactions and Equations", plan_ch_names_9)

    def test_strict_class_scoping_class_10(self):
        """
        Phase 20: When Teacher views Class 10, ALL analytics, SWAT, chapter stats,
        and recommendations must come from Class 10. Zero Class 9 chapters allowed.
        """
        prof_10 = get_teacher_student_profile(self.student_id, class_level=10, db_path=self.db_path)
        self.assertTrue(prof_10["has_data"])
        self.assertEqual(prof_10["overview"]["class"], 10)
        self.assertEqual(prof_10["overview"]["total_quizzes"], 4)  # 3 on Electricity + 1 on Chem

        # Verify chapter statistics only have Class 10 chapters
        ch_names_10 = [c["chapter"] for c in prof_10["chapter_statistics"]]
        self.assertIn("Electricity", ch_names_10)
        self.assertIn("Chemical Reactions and Equations", ch_names_10)
        self.assertNotIn("Describing Motion Around Us", ch_names_10)
        self.assertNotIn("Exploration: Entering the World of Secondary Science", ch_names_10)

        # Verify action plan only contains Class 10 chapters
        plan_ch_names_10 = [a["chapter"] for a in prof_10["action_plan"]["actions"]]
        self.assertIn("Electricity", plan_ch_names_10)
        self.assertIn("Chemical Reactions and Equations", plan_ch_names_10)
        self.assertNotIn("Describing Motion Around Us", plan_ch_names_10)


if __name__ == "__main__":
    unittest.main()
