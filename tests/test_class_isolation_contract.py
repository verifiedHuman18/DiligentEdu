"""Automated Test Suite for Phase 21 (Clean Backend Contracts) and Phase 22 (Strict Class Isolation)."""

import os
import tempfile
import unittest

import backend
from src.academic_rag.storage.repository import QuizRepository


class TestClassIsolationContracts(unittest.TestCase):
    """
    Automated verification of strict Class 9 vs Class 10 isolation across:
    - get_student_swat
    - get_student_action_plan
    - get_chapters_with_status
    - get_teacher_swat
    - get_teacher_action_plan
    """

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.db_path = os.path.join(self.temp_dir.name, "test_class_isolation_contract.db")
        self.repo = QuizRepository(db_path=self.db_path)
        self.student_id = "student_001"

        # Setup Class 9 test data:
        # 1. Motion -> 80% (4/5)
        self.repo.record_attempt(
            self.student_id,
            {
                "class_level": 9,
                "chapter": "Describing Motion Around Us",
                "chapter_number": 4,
                "difficulty": "medium",
                "questions": [
                    {"question_id": f"c9_mot_{i}", "correct_answer": "A"} for i in range(1, 6)
                ],
            },
            {f"q_choice_{i}": "A" if i <= 4 else "B" for i in range(1, 6)},
        )

        # 2. Force -> 40% (2/5)
        self.repo.record_attempt(
            self.student_id,
            {
                "class_level": 9,
                "chapter": "How Forces Affect Motion",
                "chapter_number": 6,
                "difficulty": "medium",
                "questions": [
                    {"question_id": f"c9_frc_{i}", "correct_answer": "A"} for i in range(1, 6)
                ],
            },
            {f"q_choice_{i}": "A" if i <= 2 else "B" for i in range(1, 6)},
        )

        # Setup Class 10 test data:
        # 3. Electricity -> 30% (3/10)
        self.repo.record_attempt(
            self.student_id,
            {
                "class_level": 10,
                "chapter": "Electricity",
                "chapter_number": 11,
                "difficulty": "hard",
                "questions": [
                    {"question_id": f"c10_elec_{i}", "correct_answer": "A"} for i in range(1, 11)
                ],
            },
            {f"q_choice_{i}": "A" if i <= 3 else "B" for i in range(1, 11)},
        )

        # 4. Light -> 90% (9/10)
        self.repo.record_attempt(
            self.student_id,
            {
                "class_level": 10,
                "chapter": "Light – Reflection and Refraction",
                "chapter_number": 9,
                "difficulty": "medium",
                "questions": [
                    {"question_id": f"c10_lgt_{i}", "correct_answer": "A"} for i in range(1, 11)
                ],
            },
            {f"q_choice_{i}": "A" if i <= 9 else "B" for i in range(1, 11)},
        )

    def tearDown(self):
        try:
            self.temp_dir.cleanup()
        except Exception:
            pass

    def test_student_swat_class_isolation(self):
        """
        get_student_swat('student_001', 9) must show:
          Motion -> 80%, Force -> 40% (0 Class 10 chapters).
        get_student_swat('student_001', 10) must show:
          Electricity -> 30%, Light -> 90% (0 Class 9 chapters).
        """
        # 1. Class 9 SWAT
        swat_9 = backend.get_student_swat(self.student_id, class_level=9, db_path=self.db_path)
        self.assertEqual(swat_9["class_level"], 9)
        self.assertEqual(swat_9["overall"]["attempted_chapters"], 2)
        self.assertEqual(swat_9["overall"]["total_chapters"], 13)

        # Strengths & Weaknesses in Class 9
        strong_9 = [s["chapter"] for s in swat_9["strong"]]
        weak_9 = [w["chapter"] for w in swat_9["weak"]]
        self.assertIn("Describing Motion Around Us", strong_9)
        self.assertIn("How Forces Affect Motion", weak_9)

        # Zero Class 10 chapters in Class 9
        all_ch_9 = list(swat_9["chapter_breakdown"].keys())
        self.assertNotIn("Electricity", all_ch_9)
        self.assertNotIn("Light – Reflection and Refraction", all_ch_9)

        # 2. Class 10 SWAT
        swat_10 = backend.get_student_swat(self.student_id, class_level=10, db_path=self.db_path)
        self.assertEqual(swat_10["class_level"], 10)
        self.assertEqual(swat_10["overall"]["attempted_chapters"], 2)
        self.assertEqual(swat_10["overall"]["total_chapters"], 13)

        # Strengths & Weaknesses in Class 10
        strong_10 = [s["chapter"] for s in swat_10["strong"]]
        weak_10 = [w["chapter"] for w in swat_10["weak"]]
        self.assertIn("Light – Reflection and Refraction", strong_10)
        self.assertIn("Electricity", weak_10)

        # Zero Class 9 chapters in Class 10
        all_ch_10 = list(swat_10["chapter_breakdown"].keys())
        self.assertNotIn("Describing Motion Around Us", all_ch_10)
        self.assertNotIn("How Forces Affect Motion", all_ch_10)

    def test_student_and_teacher_action_plan_isolation(self):
        """
        Class 9 action plan -> Priority 1: Force (40%)
        Class 10 action plan -> Priority 1: Electricity (30%)
        """
        # Student Action Plans
        plan_9 = backend.get_student_action_plan(self.student_id, class_level=9, db_path=self.db_path)
        self.assertEqual(plan_9["actions"][0]["chapter"], "How Forces Affect Motion")
        self.assertEqual(plan_9["actions"][0]["status"], "weak")
        self.assertEqual(plan_9["actions"][0]["score"], 40)

        plan_10 = backend.get_student_action_plan(self.student_id, class_level=10, db_path=self.db_path)
        self.assertEqual(plan_10["actions"][0]["chapter"], "Electricity")
        self.assertEqual(plan_10["actions"][0]["status"], "weak")
        self.assertEqual(plan_10["actions"][0]["score"], 30)

        # Teacher Action Plans (shares the same engine)
        t_plan_9 = backend.get_teacher_action_plan(self.student_id, class_level=9, db_path=self.db_path)
        self.assertEqual(t_plan_9["actions"][0]["chapter"], "How Forces Affect Motion")

        t_plan_10 = backend.get_teacher_action_plan(self.student_id, class_level=10, db_path=self.db_path)
        self.assertEqual(t_plan_10["actions"][0]["chapter"], "Electricity")

    def test_teacher_swat_shares_student_engine(self):
        """get_teacher_swat uses the exact same calculation engine without duplication."""
        t_swat_10 = backend.get_teacher_swat(self.student_id, class_level=10, db_path=self.db_path)
        s_swat_10 = backend.get_student_swat(self.student_id, class_level=10, db_path=self.db_path)

        self.assertEqual(t_swat_10["overall"]["average"], s_swat_10["overall"]["average"])
        self.assertEqual(t_swat_10["strong"], s_swat_10["strong"])
        self.assertEqual(t_swat_10["weak"], s_swat_10["weak"])
        self.assertEqual(t_swat_10["unattempted"], s_swat_10["unattempted"])

    def test_get_chapters_with_status_contract(self):
        """Verify get_chapters_with_status returns accurate class-scoped chapter list."""
        chs_9 = backend.get_chapters_with_status(self.student_id, class_level=9, db_path=self.db_path)
        self.assertEqual(len(chs_9), 13)
        chs_9_dict = {c["chapter"]: c for c in chs_9}
        self.assertEqual(chs_9_dict["Describing Motion Around Us"]["status"], "strong")
        self.assertEqual(chs_9_dict["How Forces Affect Motion"]["status"], "weak")

        chs_10 = backend.get_chapters_with_status(self.student_id, class_level=10, db_path=self.db_path)
        self.assertEqual(len(chs_10), 13)
        chs_10_dict = {c["chapter"]: c for c in chs_10}
        self.assertEqual(chs_10_dict["Electricity"]["status"], "weak")
        self.assertEqual(chs_10_dict["Light – Reflection and Refraction"]["status"], "strong")


if __name__ == "__main__":
    unittest.main()
