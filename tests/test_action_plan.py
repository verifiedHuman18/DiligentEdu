"""Unit tests for Phases 15, 16 & 17: Action-Plan Recommendation Engine."""

import os
import tempfile
import unittest

import backend
from src.academic_rag.analytics.action_plan import generate_action_plan
from src.academic_rag.storage.repository import QuizRepository


class TestActionPlanRecommendationEngine(unittest.TestCase):
    """
    Tests deterministic action plan generation, priority ranking:
    Weak (Priority 1) -> Unattempted (Priority 2) -> Average (Priority 3) -> Strong (Priority 4),
    and actionable metadata (action, button_text, difficulty, reason).
    """

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.db_path = os.path.join(self.temp_dir.name, "test_action_plan.db")
        self.repo = QuizRepository(db_path=self.db_path)
        self.student_id = "student_plan_test"

    def tearDown(self):
        try:
            self.temp_dir.cleanup()
        except Exception:
            pass

    def test_priority_hierarchy(self):
        """
        Tests that recommendations follow strict priority order:
        Weak -> Unattempted -> Average -> Strong.
        """
        # 1. Weak Topic: Electricity -> 40% (2/5)
        self.repo.record_attempt(
            self.student_id,
            {
                "class_level": 10,
                "chapter": "Electricity",
                "chapter_number": 11,
                "difficulty": "hard",
                "questions": [
                    {"question_id": f"e_{i}", "correct_answer": "A"} for i in range(1, 6)
                ],
            },
            {f"q_choice_{i}": "A" if i <= 2 else "B" for i in range(1, 6)},
        )

        # 2. Average Topic: Life Processes -> 60% (3/5)
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
            {f"q_choice_{i}": "A" if i <= 3 else "B" for i in range(1, 6)},
        )

        # 3. Strong Topic: Chemical Reactions -> 100% (5/5)
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

        plan = generate_action_plan(self.student_id, class_level=10, db_path=self.db_path)

        self.assertEqual(plan["class_level"], 10)
        self.assertEqual(plan["priority"], "high")
        self.assertIn("High priority", plan["summary"])

        actions = plan["actions"]
        self.assertEqual(len(actions), 13)

        # 1st Action: Weak chapter Electricity (Priority 1)
        act1 = actions[0]
        self.assertEqual(act1["chapter"], "Electricity")
        self.assertEqual(act1["status"], "weak")
        self.assertEqual(act1["score"], 40)
        self.assertEqual(act1["action"], "practice")
        self.assertEqual(act1["button_text"], "Practice Electricity")
        self.assertEqual(act1["difficulty"], "medium")
        self.assertEqual(act1["priority_rank"], 1)
        self.assertIn("below target", act1["reason"])

        # 2nd through 11th Actions: Unattempted chapters (Priority 2)
        unatt_actions = [a for a in actions if a["status"] == "unattempted"]
        self.assertEqual(len(unatt_actions), 10)
        for u in unatt_actions:
            self.assertEqual(u["priority_rank"], 2)
            self.assertEqual(u["action"], "diagnostic")
            self.assertEqual(u["button_text"], "Take Diagnostic Quiz")
            self.assertEqual(u["difficulty"], "easy")
            self.assertIsNone(u["score"])

        # Next Action: Average chapter Life Processes (Priority 3)
        avg_actions = [a for a in actions if a["status"] == "average"]
        self.assertEqual(len(avg_actions), 1)
        self.assertEqual(avg_actions[0]["chapter"], "Life Processes")
        self.assertEqual(avg_actions[0]["priority_rank"], 3)
        self.assertEqual(avg_actions[0]["difficulty"], "medium")

        # Last Action: Strong chapter Chemical Reactions (Priority 4)
        strong_actions = [a for a in actions if a["status"] == "strong"]
        self.assertEqual(len(strong_actions), 1)
        self.assertEqual(strong_actions[0]["chapter"], "Chemical Reactions and Equations")
        self.assertEqual(strong_actions[0]["priority_rank"], 4)
        self.assertEqual(strong_actions[0]["action"], "mastery")
        self.assertEqual(strong_actions[0]["difficulty"], "hard")

    def test_fresh_student_action_plan(self):
        """A student with 0 attempts should receive diagnostic actions for all chapters."""
        plan = generate_action_plan("fresh_student_999", class_level=10, db_path=self.db_path)
        self.assertEqual(plan["priority"], "medium")
        self.assertEqual(len(plan["actions"]), 13)
        for act in plan["actions"]:
            self.assertEqual(act["status"], "unattempted")
            self.assertEqual(act["action"], "diagnostic")
            self.assertEqual(act["difficulty"], "easy")
            self.assertIsNone(act["score"])

    def test_class_isolation_in_action_plan(self):
        """Action plan for Class 9 must strictly contain Class 9 chapters only."""
        # Add Class 9 attempt
        self.repo.record_attempt(
            self.student_id,
            {
                "class_level": 9,
                "chapter": "Describing Motion Around Us",
                "chapter_number": 4,
                "difficulty": "medium",
                "questions": [
                    {"question_id": f"c9_{i}", "correct_answer": "A"} for i in range(1, 6)
                ],
            },
            {f"q_choice_{i}": "A" if i <= 2 else "B" for i in range(1, 6)},
        )

        plan_9 = generate_action_plan(self.student_id, class_level=9, db_path=self.db_path)
        self.assertEqual(plan_9["class_level"], 9)
        self.assertEqual(len(plan_9["actions"]), 13)
        self.assertEqual(plan_9["actions"][0]["chapter"], "Describing Motion Around Us")
        self.assertEqual(plan_9["actions"][0]["status"], "weak")

        # Class 10 must NOT contain Describing Motion Around Us
        plan_10 = generate_action_plan(self.student_id, class_level=10, db_path=self.db_path)
        ch_names_10 = [a["chapter"] for a in plan_10["actions"]]
        self.assertNotIn("Describing Motion Around Us", ch_names_10)

    def test_backend_facade_generate_action_plan(self):
        """Verify backend facade exposes generate_action_plan."""
        plan = backend.generate_action_plan(self.student_id, class_level=10, db_path=self.db_path)
        self.assertIn("actions", plan)
        self.assertIn("priority", plan)


if __name__ == "__main__":
    unittest.main()
