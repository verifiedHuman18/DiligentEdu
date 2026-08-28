"""Tests for Action Plan Linkage and SWAT Invariance (Phases 16-17)."""

import os
import tempfile
import unittest
from unittest.mock import patch

from src.academic_rag.analytics.action_plan import generate_action_plan
from src.academic_rag.analytics.swat import get_student_swat
from src.academic_rag.storage.database import init_database
from src.academic_rag.storage.repository import QuizRepository, StudyMaterialRepository


class TestStudyMaterialActionPlan(unittest.TestCase):
    """Test suite ensuring SWAT score invariance and Action Plan resource integration."""

    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_db.close()
        self.db_path = self.temp_db.name
        init_database(self.db_path)
        self.quiz_repo = QuizRepository(db_path=self.db_path)
        self.doc_repo = StudyMaterialRepository(db_path=self.db_path)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_swat_score_invariant_to_document_uploads(self):
        """Verify that uploading a study material does NOT alter a student's SWAT mastery score."""
        # 1. Record a quiz attempt for student_001 in Electricity (score 40% -> WEAK)
        quiz_data = {
            "class_level": 10,
            "chapter": "Electricity",
            "chapter_number": 12,
            "difficulty": "medium",
            "questions": [
                {"question": "Q1", "correct_answer": "A"},
                {"question": "Q2", "correct_answer": "A"},
                {"question": "Q3", "correct_answer": "A"},
                {"question": "Q4", "correct_answer": "A"},
                {"question": "Q5", "correct_answer": "A"},
            ],
        }
        # Student gets 2/5 right (40%)
        user_answers = {"q_choice_1": "A", "q_choice_2": "A", "q_choice_3": "B", "q_choice_4": "B", "q_choice_5": "B"}
        self.quiz_repo.record_attempt("student_001", quiz_data, user_answers)

        swat_before = get_student_swat("student_001", class_level=10, db_path=self.db_path)
        self.assertEqual(swat_before["overall"]["average"], 40)
        self.assertEqual(len(swat_before["weak"]), 1)
        self.assertEqual(swat_before["weak"][0]["chapter"], "Electricity")

        # 2. Upload a 500-page Reference Book for Electricity
        self.doc_repo.save_document_record(
            document_id="doc_elec_ref",
            student_id="student_001",
            filename="Comprehensive_Electricity.pdf",
            material_name="Comprehensive Electricity Guide",
            class_level=10,
            subject="Science",
            chapter="Electricity",
            status="READY",
        )

        # 3. Check SWAT after upload - MUST REMAIN 40% (no artificial score inflation)
        swat_after = get_student_swat("student_001", class_level=10, db_path=self.db_path)
        self.assertEqual(swat_after["overall"]["average"], 40)
        self.assertEqual(swat_after["weak"][0]["score"], 40)
        self.assertEqual(swat_after["uploaded_materials_count"], 1)

    @patch("src.academic_rag.storage.repository.study_material_repository")
    def test_action_plan_recommends_uploaded_resources(self, mock_doc_repo):
        """Verify Action Plan suggests student's uploaded material for weak/unattempted topics."""
        mock_doc_repo.get_student_documents.side_effect = self.doc_repo.get_student_documents

        # Record weak quiz in Electricity
        quiz_data = {
            "class_level": 10,
            "chapter": "Electricity",
            "chapter_number": 12,
            "difficulty": "medium",
            "questions": [{"question": "Q1", "correct_answer": "A"}],
        }
        self.quiz_repo.record_attempt("student_001", quiz_data, {"q_choice_1": "B"})

        # Upload reference material for Electricity
        self.doc_repo.save_document_record(
            document_id="doc_elec_notes",
            student_id="student_001",
            filename="Physics_Notes.pdf",
            material_name="Physics Notes Ch 12",
            class_level=10,
            subject="Science",
            chapter="Electricity",
            status="READY",
        )

        # Generate Action Plan
        plan = generate_action_plan("student_001", class_level=10, db_path=self.db_path)
        self.assertGreater(len(plan["actions"]), 0)

        # First action should be weak chapter Electricity, recommending the uploaded notes
        top_action = plan["actions"][0]
        self.assertEqual(top_action["chapter"], "Electricity")
        self.assertIn("Physics Notes Ch 12", top_action["reason"])
        self.assertEqual(len(top_action["recommended_resources"]), 1)
        self.assertEqual(top_action["recommended_resources"][0]["material_name"], "Physics Notes Ch 12")


if __name__ == "__main__":
    unittest.main()
