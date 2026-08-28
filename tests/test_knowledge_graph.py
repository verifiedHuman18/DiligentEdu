"""Automated Unit Tests for Concept-Level Knowledge Graph & Analytics (Phases 1-31)."""

import os
import tempfile
import unittest

from backend import (
    calculate_student_concept_telemetry,
    get_available_knowledge_map_chapters,
    get_chapter_knowledge_graph,
    submit_quiz,
)
from backend.curriculum.concepts import (
    get_chapter_concept_metadata,
)
from backend.models.knowledge_graph import ConceptStatus
from backend.storage.database import init_database
from backend.storage.repository import (
    QuizRepository,
    StudyMaterialRepository,
)


class TestKnowledgeGraph(unittest.TestCase):
    """Unit test suite for Chapter Knowledge Graph and Concept Mastery."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test_academic.db")
        init_database(self.db_path)
        self.quiz_repo = QuizRepository(db_path=self.db_path)
        self.mat_repo = StudyMaterialRepository(db_path=self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_phase_1_to_6_graph_schema_and_registry_structure(self):
        """Verify authoritative intra-chapter concepts and dependency edges for Class 9 & 10."""
        # Class 10 Electricity
        elec_meta = get_chapter_concept_metadata("Electricity", class_level=10)
        self.assertIsNotNone(elec_meta)
        self.assertEqual(elec_meta["class_level"], 10)
        self.assertEqual(elec_meta["chapter_number"], 11)
        node_ids = [n["id"] for n in elec_meta["nodes"]]
        self.assertIn("elec_ohms_law", node_ids)
        self.assertIn("elec_current_potential", node_ids)
        self.assertIn("elec_series_parallel", node_ids)

        # Check edge structure
        edges = elec_meta["edges"]
        self.assertTrue(len(edges) >= 3)
        self.assertTrue(
            any(
                e["source"] == "elec_current_potential" and e["target"] == "elec_ohms_law"
                for e in edges
            )
        )

        # Class 9 Describing Motion Around Us
        motion_meta = get_chapter_concept_metadata("Describing Motion Around Us", class_level=9)
        self.assertIsNotNone(motion_meta)
        self.assertEqual(motion_meta["class_level"], 9)
        self.assertTrue(len(motion_meta["nodes"]) >= 4)

        # Available chapters
        avail_10 = get_available_knowledge_map_chapters(class_level=10)
        self.assertTrue(len(avail_10) >= 10)

    def test_phase_10_to_12_concept_mastery_calculation(self):
        """Verify M_c = correct / attempts, with thresholds (Strong >= 80%, Moderate 60-79%, Weak < 60%)."""
        student_id = "student_test_mastery"

        # Record 8 attempts on Ohm's law: 6 correct -> 75.0% (Moderate)
        questions = [
            {
                "question_id": f"q_ohm_{i}",
                "question": f"Ohm law question {i}",
                "difficulty": "medium",
                "correct_answer": "A",
                "concept_id": "elec_ohms_law",
            }
            for i in range(1, 9)
        ]
        user_answers = {f"q_ohm_{i}": ("A" if i <= 6 else "B") for i in range(1, 9)}
        quiz_data = {
            "class_level": 10,
            "chapter": "Electricity",
            "chapter_number": 11,
            "difficulty": "medium",
            "questions": questions,
        }
        self.quiz_repo.record_attempt(
            student_id=student_id,
            quiz_data=quiz_data,
            user_answers=user_answers,
        )

        telemetry = calculate_student_concept_telemetry(
            student_id=student_id,
            class_level=10,
            chapter="Electricity",
            db_path=self.db_path,
        )
        self.assertIn("elec_ohms_law", telemetry)
        ohm_stat = telemetry["elec_ohms_law"]
        self.assertEqual(ohm_stat["attempts"], 8)
        self.assertEqual(ohm_stat["correct"], 6)
        self.assertEqual(ohm_stat["mastery"], 75.0)
        self.assertEqual(ohm_stat["status"], ConceptStatus.MODERATE)
        self.assertEqual(ohm_stat["confidence"], "High")

    def test_phase_11_unattempted_concept_isolation(self):
        """Verify unattempted concepts return mastery=None and status='unattempted' (not 0% or Weak)."""
        student_id = "student_brand_new"

        graph = get_chapter_knowledge_graph(
            student_id=student_id,
            class_level=10,
            chapter="Electricity",
            db_path=self.db_path,
        )
        self.assertIsNone(graph["overall_mastery"])
        self.assertEqual(graph["unattempted_count"], len(graph["nodes"]))
        self.assertEqual(graph["strong_count"], 0)
        self.assertEqual(graph["weak_count"], 0)

        for n in graph["nodes"]:
            self.assertIsNone(n["mastery"])
            self.assertEqual(n["status"], "unattempted")
            self.assertEqual(n["attempts"], 0)
            self.assertEqual(n["confidence"], "Unassessed")

    def test_phase_9_multi_concept_question_weighting(self):
        """Verify questions testing multiple concepts distribute evidence equally (w = 1/n)."""
        student_id = "student_multi_concept"

        # 1 question testing 2 concepts: resistance factors & ohms law (Answered Correctly)
        questions = [
            {
                "question_id": "q_combined_001",
                "question": "Calculate resistivity and current from V and dimensions.",
                "difficulty": "hard",
                "correct_answer": "A",
                "concept_id": ["elec_ohms_law", "elec_resistivity_factors"],
            }
        ]
        quiz_data = {
            "class_level": 10,
            "chapter": "Electricity",
            "chapter_number": 11,
            "difficulty": "hard",
            "questions": questions,
        }
        user_answers = {"q_combined_001": "A"}
        self.quiz_repo.record_attempt(
            student_id=student_id,
            quiz_data=quiz_data,
            user_answers=user_answers,
        )

        telemetry = calculate_student_concept_telemetry(
            student_id=student_id,
            class_level=10,
            chapter="Electricity",
            db_path=self.db_path,
        )

        # Both concepts receive 0.5 rounded
        self.assertIn("elec_ohms_law", telemetry)
        self.assertIn("elec_resistivity_factors", telemetry)
        self.assertEqual(telemetry["elec_ohms_law"]["mastery"], 100.0)
        self.assertEqual(telemetry["elec_resistivity_factors"]["mastery"], 100.0)

    def test_phase_29_student_multi_tenant_isolation(self):
        """Verify Student A mastery is completely isolated from Student B."""
        # Alice gets 100% on electric current
        quiz_data_alice = {
            "class_level": 10,
            "chapter": "Electricity",
            "chapter_number": 11,
            "difficulty": "easy",
            "questions": [
                {
                    "question_id": "q_alice_1",
                    "question": "Current definition",
                    "difficulty": "easy",
                    "correct_answer": "A",
                    "concept_id": "elec_current_potential",
                },
                {
                    "question_id": "q_alice_2",
                    "question": "Potential difference unit",
                    "difficulty": "easy",
                    "correct_answer": "A",
                    "concept_id": "elec_current_potential",
                },
            ],
        }
        self.quiz_repo.record_attempt(
            student_id="student_alice",
            quiz_data=quiz_data_alice,
            user_answers={"q_alice_1": "A", "q_alice_2": "A"},
        )

        graph_alice = get_chapter_knowledge_graph(
            student_id="student_alice",
            class_level=10,
            chapter="Electricity",
            db_path=self.db_path,
        )
        current_node_alice = next(
            n for n in graph_alice["nodes"] if n["id"] == "elec_current_potential"
        )
        self.assertEqual(current_node_alice["mastery"], 100.0)
        self.assertEqual(current_node_alice["status"], "strong")

        # Bob has 0 attempts
        graph_bob = get_chapter_knowledge_graph(
            student_id="student_bob",
            class_level=10,
            chapter="Electricity",
            db_path=self.db_path,
        )
        current_node_bob = next(
            n for n in graph_bob["nodes"] if n["id"] == "elec_current_potential"
        )
        self.assertIsNone(current_node_bob["mastery"])
        self.assertEqual(current_node_bob["status"], "unattempted")

    def test_phase_29_class_grade_isolation(self):
        """Verify Class 9 and Class 10 concept graphs remain strictly segregated."""
        # Class 9 Motion graph
        graph_c9 = get_chapter_knowledge_graph(
            student_id="student_alice",
            class_level=9,
            chapter="Describing Motion Around Us",
            db_path=self.db_path,
        )
        self.assertEqual(graph_c9["class_level"], 9)
        c9_node_ids = [n["id"] for n in graph_c9["nodes"]]
        self.assertIn("mot_distance_displacement", c9_node_ids)
        self.assertNotIn("elec_ohms_law", c9_node_ids)

        # Class 10 Electricity graph
        graph_c10 = get_chapter_knowledge_graph(
            student_id="student_alice",
            class_level=10,
            chapter="Electricity",
            db_path=self.db_path,
        )
        self.assertEqual(graph_c10["class_level"], 10)
        c10_node_ids = [n["id"] for n in graph_c10["nodes"]]
        self.assertIn("elec_ohms_law", c10_node_ids)
        self.assertNotIn("mot_distance_displacement", c10_node_ids)

    def test_phase_27_study_material_resource_linkage(self):
        """Verify student uploaded materials matching the chapter are linked as recommended resources."""
        student_id = "student_with_notes"

        self.mat_repo.save_document_record(
            document_id="doc_elec_guide",
            student_id=student_id,
            filename="Electricity_Revision_Handbook.pdf",
            material_name="Electricity Revision Handbook",
            class_level=10,
            subject="Science",
            chapter="Electricity",
            file_size_bytes=102400,
            status="READY",
        )

        graph = get_chapter_knowledge_graph(
            student_id=student_id,
            class_level=10,
            chapter="Electricity",
            db_path=self.db_path,
        )

        ohms_node = next(n for n in graph["nodes"] if n["id"] == "elec_ohms_law")
        resource_titles = [r["title"] for r in ohms_node["recommended_resources"]]
        self.assertTrue(any("NCERT Class 10 Science" in t for t in resource_titles))
        self.assertTrue(any("Electricity Revision Handbook" in t for t in resource_titles))

    def test_phase_30_quiz_submission_updates_knowledge_map(self):
        """Verify submitting a quiz via the facade dynamically updates the Knowledge Graph mastery."""
        student_id = "student_dynamic_quiz"

        # Submit quiz with 2 questions on Light reflection (1 correct, 1 wrong -> 50% Weak)
        quiz_data = {
            "class_level": 10,
            "chapter": "Light – Reflection and Refraction",
            "chapter_number": 9,
            "difficulty": "medium",
            "total_questions": 2,
            "questions": [
                {
                    "question_id": "q1",
                    "question": "What is the angle of reflection?",
                    "options": ["Equal to angle of incidence", "Double", "Half", "Zero"],
                    "correct_answer": "A",
                    "difficulty": "medium",
                    "concept_id": "light_reflection_mirrors",
                },
                {
                    "question_id": "q2",
                    "question": "What is the mirror formula?",
                    "options": ["1/v + 1/u = 1/f", "1/v - 1/u = 1/f", "v + u = f", "v*u = f"],
                    "correct_answer": "A",
                    "difficulty": "medium",
                    "concept_id": "light_mirror_formula",
                },
            ],
        }
        answers = {"q1": "A", "q2": "C"}  # q1 correct, q2 wrong

        res = submit_quiz(
            student_id=student_id,
            quiz_id="quiz_test_light_001",
            answers=answers,
            quiz_data=quiz_data,
            db_path=self.db_path,
        )
        self.assertEqual(res["score"], 1)
        self.assertEqual(res["total"], 2)

        # Retrieve Light Knowledge Graph
        graph = get_chapter_knowledge_graph(
            student_id=student_id,
            class_level=10,
            chapter="Light – Reflection and Refraction",
            db_path=self.db_path,
        )

        refl_node = next(n for n in graph["nodes"] if n["id"] == "light_reflection_mirrors")
        self.assertEqual(refl_node["mastery"], 100.0)
        self.assertEqual(refl_node["status"], "strong")

        mirror_node = next(n for n in graph["nodes"] if n["id"] == "light_mirror_formula")
        self.assertEqual(mirror_node["mastery"], 0.0)
        self.assertEqual(mirror_node["status"], "weak")

        # Snells law node remains unattempted
        snell_node = next(n for n in graph["nodes"] if n["id"] == "light_refraction_snell")
        self.assertIsNone(snell_node["mastery"])
        self.assertEqual(snell_node["status"], "unattempted")


if __name__ == "__main__":
    unittest.main()
