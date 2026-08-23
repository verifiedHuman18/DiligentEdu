"""Unit tests for Teacher Action-Plan Customization, Persistence, and Student Integration."""

import os
import tempfile
import unittest

import backend
from src.academic_rag.analytics.action_plan import (
    generate_action_plan,
    reset_teacher_action_plan,
    save_teacher_action_plan,
)
from src.academic_rag.storage.repository import QuizRepository


class TestTeacherActionPlanCustomization(unittest.TestCase):
    """
    Verifies that teachers can customize, save, inspect, and reset student action plans,
    ensuring proper SQLite persistence, metadata enrichment, and strict class isolation.
    """

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.db_path = os.path.join(self.temp_dir.name, "test_teacher_custom_plan.db")
        self.repo = QuizRepository(db_path=self.db_path)
        self.student_id = "student_cust_test_001"

        # Record sample attempts for Class 10
        # 1. Electricity (40% - weak)
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
            {f"q_choice_{i}": "A" if i <= 2 else "B" for i in range(1, 6)},
        )

        # 2. Chemical Reactions (100% - strong)
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

    def tearDown(self):
        try:
            self.temp_dir.cleanup()
        except Exception:
            pass

    def test_default_action_plan_is_uncustomized(self):
        """Initially, action plan is automatically generated from SWAT with is_customized=False."""
        plan = generate_action_plan(self.student_id, class_level=10, db_path=self.db_path)
        self.assertFalse(plan["is_customized"])
        self.assertIsNone(plan["teacher_notes"])
        self.assertEqual(plan["actions"][0]["chapter"], "Electricity")
        self.assertEqual(plan["actions"][0]["status"], "weak")

    def test_save_and_retrieve_custom_action_plan(self):
        """Teacher assigns a custom action plan prioritizing Chemical Reactions (Hard) and Light (Easy)."""
        custom_actions = [
            {
                "chapter": "Chemical Reactions and Equations",
                "difficulty": "hard",
                "action": "mastery",
                "reason": "Master stoichiometry before Monday's test.",
                "teacher_note": "Focus on balancing equations.",
            },
            {
                "chapter": "Light – Reflection and Refraction",
                "difficulty": "easy",
                "action": "diagnostic",
                "reason": "Establish baseline on ray optics.",
                "teacher_note": "Practice concave mirror diagrams.",
            },
        ]
        global_note = "Complete these 2 modules before Friday review."

        saved_plan = save_teacher_action_plan(
            student_id=self.student_id,
            class_level=10,
            actions=custom_actions,
            teacher_notes=global_note,
            db_path=self.db_path,
        )

        self.assertTrue(saved_plan["is_customized"])
        self.assertEqual(saved_plan["customized_by"], "teacher")
        self.assertEqual(saved_plan["teacher_notes"], global_note)

        actions = saved_plan["actions"]
        # Total recommendations should cover all NCERT Class 10 chapters (13)
        self.assertEqual(len(actions), 13)

        # Priority 1: Chemical Reactions (assigned hard difficulty by teacher)
        act1 = actions[0]
        self.assertEqual(act1["chapter"], "Chemical Reactions and Equations")
        self.assertEqual(act1["difficulty"], "hard")
        self.assertEqual(act1["action"], "mastery")
        self.assertEqual(act1["priority_rank"], 1)
        self.assertTrue(act1["is_teacher_assigned"])
        self.assertEqual(act1["teacher_note"], "Focus on balancing equations.")
        self.assertEqual(act1["score"], 100)  # enriched with real SWAT score

        # Priority 2: Light (assigned easy difficulty by teacher)
        act2 = actions[1]
        self.assertEqual(act2["chapter"], "Light – Reflection and Refraction")
        self.assertEqual(act2["difficulty"], "easy")
        self.assertEqual(act2["priority_rank"], 2)
        self.assertTrue(act2["is_teacher_assigned"])

        # Remaining chapters follow contiguous ranking
        for idx, act in enumerate(actions[2:], 3):
            self.assertEqual(act["priority_rank"], idx)
            self.assertFalse(act["is_teacher_assigned"])

    def test_student_and_teacher_action_plan_facades(self):
        """Backend facades get_student_action_plan and get_teacher_action_plan return identical customized plans."""
        custom_actions = [
            {
                "chapter": "Acids, Bases and Salts",
                "difficulty": "medium",
                "action": "practice",
                "reason": "Revise pH scale.",
            }
        ]
        backend.save_teacher_action_plan(
            student_id=self.student_id,
            class_level=10,
            actions=custom_actions,
            teacher_notes="Study guide Chapter 2",
            db_path=self.db_path,
        )

        student_plan = backend.get_student_action_plan(
            self.student_id, class_level=10, db_path=self.db_path
        )
        teacher_plan = backend.get_teacher_action_plan(
            self.student_id, class_level=10, db_path=self.db_path
        )

        self.assertTrue(student_plan["is_customized"])
        self.assertTrue(teacher_plan["is_customized"])
        self.assertEqual(student_plan["actions"][0]["chapter"], "Acids, Bases and Salts")
        self.assertEqual(teacher_plan["actions"][0]["chapter"], "Acids, Bases and Salts")
        self.assertEqual(student_plan["teacher_notes"], "Study guide Chapter 2")

    def test_reset_custom_action_plan(self):
        """Teacher resetting the action plan deletes customizations and reverts to automated SWAT recommendations."""
        custom_actions = [
            {
                "chapter": "Magnetic Effects of Electric Current",
                "difficulty": "hard",
                "action": "practice",
            }
        ]
        save_teacher_action_plan(
            student_id=self.student_id,
            class_level=10,
            actions=custom_actions,
            db_path=self.db_path,
        )

        # Confirm customized
        plan_before = generate_action_plan(self.student_id, class_level=10, db_path=self.db_path)
        self.assertTrue(plan_before["is_customized"])

        # Reset plan
        success = reset_teacher_action_plan(self.student_id, class_level=10, db_path=self.db_path)
        self.assertTrue(success)

        # Plan after reset should be standard SWAT plan (Electricity is Priority 1 weak topic)
        plan_after = generate_action_plan(self.student_id, class_level=10, db_path=self.db_path)
        self.assertFalse(plan_after["is_customized"])
        self.assertIsNone(plan_after["teacher_notes"])
        self.assertEqual(plan_after["actions"][0]["chapter"], "Electricity")
        self.assertEqual(plan_after["actions"][0]["status"], "weak")

    def test_strict_class_isolation_for_custom_plans(self):
        """Custom plan for Class 9 does not affect Class 10, and vice versa."""
        # Custom plan for Class 9
        custom_c9 = [
            {
                "chapter": "Describing Motion Around Us",
                "difficulty": "medium",
                "action": "practice",
                "reason": "Class 9 kinematics focus.",
            }
        ]
        save_teacher_action_plan(
            student_id=self.student_id,
            class_level=9,
            actions=custom_c9,
            teacher_notes="Class 9 Physics Focus",
            db_path=self.db_path,
        )

        plan_9 = generate_action_plan(self.student_id, class_level=9, db_path=self.db_path)
        plan_10 = generate_action_plan(self.student_id, class_level=10, db_path=self.db_path)

        # Class 9 is customized with Describing Motion Around Us
        self.assertTrue(plan_9["is_customized"])
        self.assertEqual(plan_9["actions"][0]["chapter"], "Describing Motion Around Us")
        self.assertEqual(plan_9["teacher_notes"], "Class 9 Physics Focus")

        # Class 10 is NOT customized and has automated SWAT plan
        self.assertFalse(plan_10["is_customized"])
        self.assertEqual(plan_10["actions"][0]["chapter"], "Electricity")
        self.assertIsNone(plan_10["teacher_notes"])

    def test_clear_student_data_purges_custom_plans(self):
        """Clearing student data purges quiz attempts AND custom teacher action plans."""
        save_teacher_action_plan(
            student_id=self.student_id,
            class_level=10,
            actions=[{"chapter": "Electricity", "difficulty": "hard"}],
            teacher_notes="Test note",
            db_path=self.db_path,
        )

        self.repo.clear_student_data(self.student_id)

        custom = self.repo.get_teacher_custom_plan(self.student_id, class_level=10)
        self.assertIsNone(custom)

        plan = generate_action_plan(self.student_id, class_level=10, db_path=self.db_path)
        self.assertFalse(plan["is_customized"])


if __name__ == "__main__":
    unittest.main()
