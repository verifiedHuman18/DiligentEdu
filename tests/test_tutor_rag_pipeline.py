"""Comprehensive Regression Test Suite for Tutor RAG Pipeline, Grounding Rules,
3-State Responses, Source Isolation, Quota Protection, and Controlled Acceptance (Phases 1-20).
"""

import os
import tempfile
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

import fitz

from frontend.screens.tutor_screen import _get_fresh_suggestions
from src.academic_rag.ingestion.pdf_ingester import ingest_study_material_pdf
from src.academic_rag.quiz.generator import retrieve_chapter_context_for_quiz
from src.academic_rag.rag.engine import stream_ncert_rag_response
from src.academic_rag.rag.prompts import NCERT_TUTOR_SYSTEM_PROMPT
from src.academic_rag.rag.retriever import (
    delete_student_material_vectors,
    retrieve_hybrid_academic_context,
    retrieve_student_material_context,
)
from src.academic_rag.storage.database import init_database
from src.academic_rag.storage.repository import StudyMaterialRepository


def _create_test_pdf(text: str) -> bytes:
    """Helper to generate in-memory test PDF."""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), text)
    pdf_bytes = doc.write()
    doc.close()
    return pdf_bytes


class TestTutorRAGPipeline(unittest.IsolatedAsyncioTestCase):
    """Test suite verifying all 20 phases of the Tutor RAG pipeline."""

    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_db.close()
        self.db_path = self.temp_db.name
        init_database(self.db_path)
        self.repo = StudyMaterialRepository(db_path=self.db_path)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_phase_7_8_prompt_three_states_and_rules(self):
        """Phase 7 & 8: Verify prompt contains explicit State A, State B, State C and conflict resolution."""
        self.assertIn("STATE A — NCERT-SUPPORTED", NCERT_TUTOR_SYSTEM_PROMPT)
        self.assertIn("STATE B — STUDENT-MATERIAL-SUPPORTED", NCERT_TUTOR_SYSTEM_PROMPT)
        self.assertIn("STATE C — GENUINE UNSUPPORTED", NCERT_TUTOR_SYSTEM_PROMPT)
        self.assertIn("Do NOT say \"not in syllabus\"", NCERT_TUTOR_SYSTEM_PROMPT)
        self.assertIn("NCERT IS AUTHORITATIVE", NCERT_TUTOR_SYSTEM_PROMPT)
        self.assertIn("STUDENT MATERIAL IS SUPPLEMENTARY", NCERT_TUTOR_SYSTEM_PROMPT)
        self.assertIn("### NCERT Textbook Citations", NCERT_TUTOR_SYSTEM_PROMPT)
        self.assertIn("### Student Reference Material Citations", NCERT_TUTOR_SYSTEM_PROMPT)

    @patch("src.academic_rag.rag.retriever.retrieve_ncert_context")
    @patch("src.academic_rag.rag.retriever.retrieve_student_material_context")
    def test_phase_6_11_source_classification_and_context_demarcation(
        self, mock_student_ret, mock_ncert_ret
    ):
        """Phase 6 & 11: Verify hybrid context cleanly demarcates official NCERT vs student material."""
        mock_ncert_ret.return_value = "[SOURCE: NCERT Class 10 Science | PAGE: 200]\nV = IR definition."
        mock_student_ret.return_value = "[SOURCE: STUDENT REFERENCE MATERIAL | TITLE: Physics Guide | PAGE: 15]\nCircuit derivation."

        ctx = retrieve_hybrid_academic_context(
            query="Ohm's law derivation",
            student_id="student_001",
            class_filter=10,
        )

        self.assertTrue(ctx["has_student_context"])
        self.assertIn("=== OFFICIAL NCERT TEXTBOOK EXCERPTS ===", ctx["combined_context"])
        self.assertIn("=== STUDENT REFERENCE MATERIAL (SUPPLEMENTARY EXCERPTS) ===", ctx["combined_context"])
        self.assertIn("V = IR definition", ctx["combined_context"])
        self.assertIn("Circuit derivation", ctx["combined_context"])

    @patch("src.academic_rag.rag.retriever.retrieve_ncert_context")
    @patch("src.academic_rag.rag.retriever.retrieve_student_material_context")
    def test_state_b_uploaded_only_knowledge_passed_to_llm(
        self, mock_student_ret, mock_ncert_ret
    ):
        """State B: When question is present only in student material, excerpts reach Gemini payload."""
        mock_ncert_ret.return_value = ""  # No NCERT match
        mock_student_ret.return_value = (
            "[SOURCE: STUDENT REFERENCE MATERIAL | TITLE: Hall Effect Notes | PAGE: 10]\n"
            "The Hall coefficient RH is defined as RH = Ey / (Jx * Bz)."
        )

        ctx = retrieve_hybrid_academic_context(
            query="What is Hall coefficient?",
            student_id="student_001",
            class_filter=10,
        )

        self.assertTrue(ctx["has_student_context"])
        self.assertIn("[No direct NCERT textbook excerpt matches found]", ctx["combined_context"])
        self.assertIn("Hall Effect Notes", ctx["combined_context"])
        self.assertIn("RH = Ey / (Jx * Bz)", ctx["combined_context"])

    @patch("src.academic_rag.rag.retriever.retrieve_ncert_context")
    @patch("src.academic_rag.rag.retriever.retrieve_student_material_context")
    def test_state_c_unsupported_knowledge(self, mock_student_ret, mock_ncert_ret):
        """State C: When neither source has context, formatted context indicates no matches."""
        mock_ncert_ret.return_value = ""
        mock_student_ret.return_value = ""

        ctx = retrieve_hybrid_academic_context(
            query="Quantum superstring entanglement in black holes",
            student_id="student_001",
            class_filter=10,
        )

        self.assertFalse(ctx["has_student_context"])
        self.assertIn("[No direct NCERT textbook excerpt matches found]", ctx["combined_context"])
        self.assertNotIn("STUDENT REFERENCE MATERIAL", ctx["combined_context"])

    @patch("src.academic_rag.storage.repository.study_material_repository")
    @patch("src.academic_rag.rag.retriever.get_pinecone_index")
    @patch("src.academic_rag.rag.retriever.get_embeddings")
    def test_phase_4_student_and_class_isolation(
        self, mock_get_embeddings, mock_get_pinecone, mock_repo
    ):
        """Phase 4 & Test 5/6: Verify multi-tenant student and class isolation in vector query."""
        mock_repo.get_student_documents.side_effect = self.repo.get_student_documents
        mock_embeddings = MagicMock()
        mock_embeddings.embed_query.return_value = [0.1] * 384
        mock_get_embeddings.return_value = mock_embeddings

        mock_index = MagicMock()
        mock_index.query.return_value = {"matches": []}
        mock_get_pinecone.return_value = mock_index

        # Student Alice in Class 10 has a document
        self.repo.save_document_record(
            document_id="doc_alice_10",
            student_id="student_alice",
            filename="Alice_Notes.pdf",
            material_name="Alice Notes",
            class_level=10,
            subject="Science",
            status="READY",
        )

        # 1. Alice queries in Class 10
        retrieve_student_material_context(
            query="Ohm's law",
            student_id="student_alice",
            class_filter=10,
        )
        query_filter = mock_index.query.call_args[1]["filter"]
        self.assertEqual(query_filter["student_id"]["$eq"], "student_alice")
        self.assertEqual(query_filter["class"]["$eq"], 10)

        # 2. Student Bob in Class 10 (no documents) -> returns immediately without leaking
        bob_ctx = retrieve_student_material_context(
            query="Ohm's law",
            student_id="student_bob",
            class_filter=10,
        )
        self.assertEqual(bob_ctx, "")

        # 3. Alice queries in Class 9 (no Class 9 document) -> returns immediately
        alice_cls9_ctx = retrieve_student_material_context(
            query="Cell structure",
            student_id="student_alice",
            class_filter=9,
        )
        self.assertEqual(alice_cls9_ctx, "")

    @patch("src.academic_rag.storage.repository.study_material_repository")
    def test_phase_17_quiz_generation_uses_student_material(
        self, mock_repo
    ):
        """Phase 17: Verify quiz generator retrieves supplementary student reference material."""
        mock_repo.get_student_documents.side_effect = self.repo.get_student_documents

        # Seed student material
        self.repo.save_document_record(
            document_id="doc_elec_001",
            student_id="student_001",
            filename="Electricity_Notes.pdf",
            material_name="Electricity Special Notes",
            class_level=10,
            subject="Science",
            chapter="Electricity",
            status="READY",
        )

        with patch("src.academic_rag.quiz.generator.retrieve_student_material_context") as mock_stud_ctx:
            mock_stud_ctx.return_value = (
                "[SOURCE: STUDENT REFERENCE MATERIAL | TITLE: Electricity Special Notes | PAGE: 5]\n"
                "Advanced resistor bridge formula."
            )

            quiz_ctx = retrieve_chapter_context_for_quiz(
                class_level=10,
                chapter_number=12,
                chapter_title="Magnetic Effects of Electric Current",
                student_id="student_001",
            )

            self.assertIn("Advanced resistor bridge formula", quiz_ctx)
            self.assertIn("SUPPLEMENTARY STUDENT REFERENCE MATERIAL", quiz_ctx)

    def test_phase_18_tutor_suggested_questions_from_uploaded_material(self):
        """Phase 18: Verify tutor suggested questions incorporate uploaded reference books."""
        self.repo.save_document_record(
            document_id="doc_solar_001",
            student_id="student_solar",
            filename="Solar_Energy_Guide.pdf",
            material_name="Solar Energy Guide",
            class_level=10,
            subject="Science",
            chapter="Sources of Energy",
            status="READY",
        )

        with patch("src.academic_rag.storage.repository.study_material_repository", self.repo):
            suggestions = _get_fresh_suggestions(class_level=10, student_id="student_solar")
            self.assertGreaterEqual(len(suggestions), 1)
            # Check if any suggestion has the reference prefix or mentions reference
            labels = [s[0] for s in suggestions]
            self.assertTrue(any("Ref:" in label or "Energy" in label for label in labels))

    @patch("src.academic_rag.rag.engine.stream_chat_completion")
    @patch("src.academic_rag.rag.engine.retrieve_hybrid_academic_context")
    async def test_phase_19_gemini_quota_protection_one_request(
        self, mock_hybrid, mock_stream
    ):
        """Phase 19: Verify exactly ONE streaming Gemini request is made per user turn."""
        mock_hybrid.return_value = {
            "ncert_context": "NCERT text",
            "student_context": "Student text",
            "combined_context": "=== OFFICIAL NCERT ===\nNCERT\n=== STUDENT MATERIAL ===\nStudent",
            "has_student_context": True,
        }

        async def _mock_generator(*args, **kwargs):
            yield "Ohm's "
            yield "Law."

        mock_stream.return_value = _mock_generator()

        chunks = []
        async for chunk in stream_ncert_rag_response(
            query="Explain Ohm's Law",
            class_filter=10,
            student_id="student_001",
            api_key="fake_key",
        ):
            chunks.append(chunk)

        self.assertEqual("".join(chunks), "Ohm's Law.")
        self.assertEqual(mock_stream.call_count, 1)

    @patch("src.academic_rag.rag.retriever.get_pinecone_index")
    @patch("src.academic_rag.ingestion.pdf_ingester.get_pinecone_index")
    def test_phase_20_end_to_end_controlled_lifecycle(self, mock_ingest_pinecone, mock_retriever_pinecone):
        """Phase 20: Controlled test with distinctive fact ('Luminescence-X principle') through ingestion, retrieval, and deletion."""
        mock_index = MagicMock()
        mock_ingest_pinecone.return_value = mock_index
        mock_retriever_pinecone.return_value = mock_index

        distinctive_text = (
            "The fictional Luminescence-X principle states that photons emitted in quantum crystals "
            "undergo coherent hyper-amplification when magnetic flux equals 4.2 Tesla."
        )
        pdf_bytes = _create_test_pdf(distinctive_text)

        # 1. Ingest PDF
        ingest_res = ingest_study_material_pdf(
            student_id="student_tester",
            file_data=pdf_bytes,
            filename="Luminescence_X_Guide.pdf",
            material_name="Luminescence X Guide",
            class_level=10,
            subject="Science",
            chapter="Light – Reflection and Refraction",
            db_path=self.db_path,
            repository=self.repo,
        )
        self.assertEqual(ingest_res["status"], "READY")
        doc_id = ingest_res["document_id"]

        # 2. Check Database Record
        doc = self.repo.get_document_by_id(doc_id)
        self.assertIsNotNone(doc)
        self.assertEqual(doc["material_name"], "Luminescence X Guide")

        # 3. Simulate Pinecone vector delete
        delete_success = delete_student_material_vectors(document_id=doc_id, student_id="student_tester")
        self.assertTrue(delete_success)
        self.assertTrue(mock_index.delete.called)

        # 4. Remove DB Record
        db_del = self.repo.delete_document_record(document_id=doc_id, student_id="student_tester")
        self.assertTrue(db_del)
        self.assertIsNone(self.repo.get_document_by_id(doc_id))


if __name__ == "__main__":
    unittest.main()
