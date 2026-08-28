"""Comprehensive Automated Test Suite for Mathematics (Class 9 & Class 10) Support & Cross-Subject Isolation."""

import os
import sqlite3
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from src.academic_rag.analytics.action_plan import generate_action_plan
from src.academic_rag.analytics.knowledge_graph import (
    calculate_student_concept_telemetry,
    get_available_knowledge_map_chapters,
    get_chapter_knowledge_graph,
)
from src.academic_rag.analytics.swat import (
    get_attempted_chapters,
    get_available_chapters,
    get_student_swat,
    get_unattempted_chapters,
)
from src.academic_rag.analytics.teacher import (
    get_teacher_chapter_statistics,
    get_teacher_student_overview,
    get_teacher_student_profile,
)
from src.academic_rag.config import config
from src.academic_rag.curriculum.concepts import (
    get_all_registered_chapters,
    get_chapter_concept_metadata,
)
from src.academic_rag.curriculum.service import curriculum_service, get_ncert_curriculum
from src.academic_rag.rag.retriever import retrieve_hybrid_academic_context, retrieve_ncert_context
from src.academic_rag.storage.database import init_database
from src.academic_rag.storage.repository import QuizRepository, StudyMaterialRepository


class TestMathematicsCurriculumAndMetadata(unittest.TestCase):
    """Verifies Curriculum and Chapter Mapping Registry for Mathematics."""

    def test_class10_mathematics_chapters_count(self):
        """Class 10 Mathematics must contain exactly 14 official NCERT chapters."""
        math_chapters = curriculum_service.get_chapters_for_grade(10, subject="Mathematics")
        self.assertEqual(len(math_chapters), 14)
        ch_names = [ch.chapter_title for ch in math_chapters]
        self.assertIn("Real Numbers", ch_names)
        self.assertIn("Introduction to Trigonometry", ch_names)
        self.assertIn("Probability", ch_names)

    def test_class9_mathematics_chapters_count(self):
        """Class 9 Mathematics must contain exactly 8 Ganita Manjari chapters."""
        math_chapters = curriculum_service.get_chapters_for_grade(9, subject="Mathematics")
        self.assertEqual(len(math_chapters), 8)
        ch_names = [ch.chapter_title for ch in math_chapters]
        self.assertIn("The World of Numbers", ch_names)
        self.assertIn("Exploring Algebraic Identities", ch_names)

    def test_science_chapters_backward_compatibility(self):
        """Default subject must remain Science (13 chapters for Class 9 and 10)."""
        c10_sci = curriculum_service.get_chapters_for_grade(10)
        c9_sci = curriculum_service.get_chapters_for_grade(9)
        self.assertEqual(len(c10_sci), 13)
        self.assertEqual(len(c9_sci), 13)

    def test_resolve_chapter_math(self):
        """Resolving chapters in Mathematics."""
        num, title = curriculum_service.resolve_chapter(10, "Trigonometry", subject="Mathematics")
        self.assertEqual(num, 8)
        self.assertEqual(title, "Introduction to Trigonometry")

        num9, title9 = curriculum_service.resolve_chapter(9, "Coordinates", subject="Mathematics")
        self.assertEqual(num9, 1)
        self.assertEqual(title9, "Orienting Yourself: The Use of Coordinates")


class TestMathematicsConceptGraphs(unittest.TestCase):
    """Verifies Concept Knowledge Mapping for Mathematics chapters."""

    def test_class10_math_concept_metadata(self):
        """Class 10 Math chapters have registered concept nodes and dependency edges."""
        real_num_meta = get_chapter_concept_metadata("Real Numbers", class_level=10, subject="Mathematics")
        self.assertIsNotNone(real_num_meta)
        self.assertTrue(len(real_num_meta["nodes"]) >= 2)
        self.assertTrue(len(real_num_meta["edges"]) >= 1)

        trig_meta = get_chapter_concept_metadata("Introduction to Trigonometry", class_level=10, subject="Mathematics")
        self.assertIsNotNone(trig_meta)
        node_names = [n["name"] for n in trig_meta["nodes"]]
        self.assertTrue(any("Trigonometric Ratios" in n for n in node_names))
        self.assertTrue(any("Trigonometric Identities" in n for n in node_names))

    def test_class9_math_concept_metadata(self):
        """Class 9 Math chapters have registered concept nodes and dependency edges."""
        num_meta = get_chapter_concept_metadata("The World of Numbers", class_level=9, subject="Mathematics")
        self.assertIsNotNone(num_meta)
        self.assertTrue(len(num_meta["nodes"]) >= 2)

    def test_available_knowledge_map_chapters_by_subject(self):
        """Available knowledge map chapters should reflect active subject."""
        math_km = get_available_knowledge_map_chapters(10, subject="Mathematics")
        sci_km = get_available_knowledge_map_chapters(10, subject="Science")
        self.assertEqual(len(math_km), 14)
        self.assertEqual(len(sci_km), 13)


class TestMathematicsStorageAndSWAT(unittest.TestCase):
    """Verifies SQLite persistence and SWAT analytics isolation for Mathematics."""

    def setUp(self):
        self.temp_db_fd, self.temp_db_path = tempfile.mkstemp(suffix=".db")
        init_database(self.temp_db_path)
        self.repo = QuizRepository(db_path=self.temp_db_path)

    def tearDown(self):
        try:
            os.close(self.temp_db_fd)
            if os.path.exists(self.temp_db_path):
                os.remove(self.temp_db_path)
        except Exception:
            pass

    def test_record_attempt_and_subject_isolation(self):
        """Quiz attempts in Mathematics must be isolated from Science SWAT."""
        student_id = "math_student_001"

        # Record a Class 10 Mathematics attempt
        math_quiz_data = {
            "class_level": 10,
            "subject": "Mathematics",
            "chapter": "Real Numbers",
            "chapter_number": 1,
            "difficulty": "medium",
            "total_questions": 5,
            "questions": [
                {
                    "question_id": "q1",
                    "question": "What is the HCF of 12 and 18?",
                    "options": ["A) 2", "B) 3", "C) 6", "D) 12"],
                    "correct_answer": "C",
                    "concept_id": "c10_m01_fund_thm",
                }
            ],
        }
        math_answers = {"q1": "C"}
        self.repo.record_attempt(
            student_id=student_id,
            quiz_data=math_quiz_data,
            user_answers=math_answers,
            quiz_id="math_quiz_101",
        )

        # Record a Class 10 Science attempt
        sci_quiz_data = {
            "class_level": 10,
            "subject": "Science",
            "chapter": "Chemical Reactions and Equations",
            "chapter_number": 1,
            "difficulty": "medium",
            "total_questions": 5,
            "questions": [
                {
                    "question_id": "q2",
                    "question": "What is the product of Mg + O2?",
                    "options": ["A) MgO", "B) MgO2", "C) Mg2O", "D) None"],
                    "correct_answer": "A",
                    "concept_id": "c10_s01_chemical_eq",
                }
            ],
        }
        sci_answers = {"q2": "A"}
        self.repo.record_attempt(
            student_id=student_id,
            quiz_data=sci_quiz_data,
            user_answers=sci_answers,
            quiz_id="sci_quiz_101",
        )

        # Verify Math SWAT only contains Math chapters (14 total) and 1 attempt
        math_swat = get_student_swat(student_id, class_level=10, subject="Mathematics", db_path=self.temp_db_path)
        self.assertEqual(math_swat["overall"]["quizzes_attempted"], 1)
        self.assertEqual(math_swat["overall"]["total_chapters"], 14)
        self.assertIn("Real Numbers", math_swat["chapter_breakdown"])
        self.assertNotIn("Chemical Reactions and Equations", math_swat["chapter_breakdown"])

        # Verify Science SWAT only contains Science chapters (13 total) and 1 attempt
        sci_swat = get_student_swat(student_id, class_level=10, subject="Science", db_path=self.temp_db_path)
        self.assertEqual(sci_swat["overall"]["quizzes_attempted"], 1)
        self.assertEqual(sci_swat["overall"]["total_chapters"], 13)
        self.assertIn("Chemical Reactions and Equations", sci_swat["chapter_breakdown"])
        self.assertNotIn("Real Numbers", sci_swat["chapter_breakdown"])

    def test_action_plan_subject_awareness(self):
        """Action plan must recommend Mathematics unattempted/weak chapters when subject is Mathematics."""
        student_id = "math_student_002"
        math_plan = generate_action_plan(student_id, class_level=10, subject="Mathematics", db_path=self.temp_db_path)
        self.assertEqual(math_plan["subject"], "Mathematics")
        top_act_chapter = math_plan["actions"][0]["chapter"]
        math_chapters = [c.chapter_title for c in curriculum_service.get_chapters_for_grade(10, subject="Mathematics")]
        self.assertIn(top_act_chapter, math_chapters)

    def test_knowledge_graph_concept_telemetry_isolation(self):
        """Concept telemetry must isolate scores to Mathematics attempts."""
        student_id = "math_student_003"
        quiz_data = {
            "class_level": 10,
            "subject": "Mathematics",
            "chapter": "Real Numbers",
            "chapter_number": 1,
            "difficulty": "medium",
            "total_questions": 1,
            "questions": [
                {
                    "question_id": "q1",
                    "question": "State the Fundamental Theorem of Arithmetic.",
                    "options": ["A) Prime factorization is unique", "B) False"],
                    "correct_answer": "A",
                    "concept_id": "c10_m01_fund_thm",
                }
            ],
        }
        self.repo.record_attempt(student_id, quiz_data, {"q1": "A"}, quiz_id="q_math_001")

        telemetry = calculate_student_concept_telemetry(
            student_id, class_level=10, chapter_name="Real Numbers", subject="Mathematics", db_path=self.temp_db_path
        )
        self.assertIn("c10_m01_fund_thm", telemetry)
        self.assertEqual(telemetry["c10_m01_fund_thm"]["attempts"], 1)
        self.assertEqual(telemetry["c10_m01_fund_thm"]["correct"], 1)


class TestMathematicsRAGRetrievalFilter(unittest.TestCase):
    """Verifies that RAG Retrieval applies metadata filtering for Mathematics."""

    @patch("src.academic_rag.rag.retriever.get_pinecone_index")
    @patch("src.academic_rag.rag.retriever.get_embeddings")
    def test_retrieve_ncert_context_mathematics_filter(self, mock_get_embeddings, mock_get_index):
        mock_emb = MagicMock()
        mock_emb.embed_query.return_value = [0.1] * 384
        mock_get_embeddings.return_value = mock_emb

        mock_idx = MagicMock()
        mock_idx.query.return_value = {
            "matches": [
                {
                    "id": "ncert_c10_math_ch01_p001_ck001",
                    "metadata": {
                        "class": 10,
                        "subject": "Mathematics",
                        "chapter_number": 1,
                        "chapter": "Real Numbers",
                        "page": 1,
                        "text": "Every composite number can be expressed uniquely as a product of primes.",
                    },
                }
            ]
        }
        mock_get_index.return_value = mock_idx

        ctx = retrieve_ncert_context(
            query="Fundamental Theorem of Arithmetic",
            class_filter=10,
            chapter_filter=1,
            subject_filter="Mathematics",
        )
        self.assertIn("NCERT Class 10 Mathematics", ctx)
        self.assertIn("Real Numbers", ctx)

        # Verify Pinecone query was filtered by subject: Mathematics
        called_kwargs = mock_idx.query.call_args[1]
        filter_applied = called_kwargs.get("filter", {})
        self.assertEqual(filter_applied.get("subject"), {"$eq": "Mathematics"})
        self.assertEqual(filter_applied.get("class"), {"$eq": 10})


if __name__ == "__main__":
    unittest.main()
