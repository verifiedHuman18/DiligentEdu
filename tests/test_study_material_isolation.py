"""Tests for Strict Student and Class Isolation (Phases 1, 7, 19, 20)."""

import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from src.academic_rag.rag.retriever import (
    retrieve_hybrid_academic_context,
    retrieve_student_material_context,
)
from src.academic_rag.storage.database import init_database
from src.academic_rag.storage.repository import StudyMaterialRepository


class TestStudyMaterialIsolation(unittest.TestCase):
    """Test suite ensuring zero cross-tenant leakage between students and grades."""

    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_db.close()
        self.db_path = self.temp_db.name
        init_database(self.db_path)
        self.repo = StudyMaterialRepository(db_path=self.db_path)

        # Seed document records in DB
        self.repo.save_document_record(
            document_id="doc_alice_cls10",
            student_id="student_alice",
            filename="Alice_Physics_Class10.pdf",
            material_name="Alice Physics Reference",
            class_level=10,
            subject="Science",
            chapter="Electricity",
            status="READY",
        )
        self.repo.save_document_record(
            document_id="doc_bob_cls10",
            student_id="student_bob",
            filename="Bob_Chemistry_Class10.pdf",
            material_name="Bob Chemistry Notes",
            class_level=10,
            subject="Science",
            chapter="Chemical Reactions and Equations",
            status="READY",
        )
        self.repo.save_document_record(
            document_id="doc_alice_cls9",
            student_id="student_alice",
            filename="Alice_Biology_Class9.pdf",
            material_name="Alice Class 9 Cells",
            class_level=9,
            subject="Science",
            chapter="The Fundamental Unit of Life",
            status="READY",
        )

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    @patch("src.academic_rag.storage.repository.study_material_repository")
    @patch("src.academic_rag.rag.retriever.get_pinecone_index")
    @patch("src.academic_rag.rag.retriever.get_embeddings")
    def test_student_tenant_isolation(self, mock_get_embeddings, mock_get_pinecone, mock_repo):
        """Verify Student A's retrieval strictly filters by student_id and cannot receive Student B's data."""
        mock_repo.get_student_documents.side_effect = self.repo.get_student_documents
        mock_embeddings = MagicMock()
        mock_embeddings.embed_query.return_value = [0.1] * 384
        mock_get_embeddings.return_value = mock_embeddings

        mock_index = MagicMock()
        # Simulated Pinecone query result for Alice
        mock_index.query.return_value = {
            "matches": [
                {
                    "metadata": {
                        "student_id": "student_alice",
                        "class": 10,
                        "material_name": "Alice Physics Reference",
                        "filename": "Alice_Physics_Class10.pdf",
                        "page": 42,
                        "text": "Ohm's law formula V = IR explained with circuit diagrams.",
                    }
                }
            ]
        }
        mock_get_pinecone.return_value = mock_index

        # 1. Query as Alice
        alice_ctx = retrieve_student_material_context(
            query="Explain Ohm's law",
            student_id="student_alice",
            class_filter=10,
        )

        # Assert filter applied to Pinecone query enforces Alice's student_id
        self.assertTrue(mock_index.query.called)
        query_kwargs = mock_index.query.call_args[1]
        self.assertEqual(query_kwargs["filter"]["student_id"]["$eq"], "student_alice")
        self.assertEqual(query_kwargs["filter"]["class"]["$eq"], 10)
        self.assertEqual(query_kwargs["namespace"], "student-materials")
        self.assertIn("Alice Physics Reference", alice_ctx)
        self.assertIn("PAGE: 42", alice_ctx)

        # 2. Query as Bob
        # If Pinecone hypothetically returned Alice's match by error, our retriever filters it out in-memory as well
        bob_ctx = retrieve_student_material_context(
            query="Explain Ohm's law",
            student_id="student_bob",
            class_filter=10,
        )
        self.assertNotIn("Alice Physics Reference", bob_ctx)

    @patch("src.academic_rag.storage.repository.study_material_repository")
    @patch("src.academic_rag.rag.retriever.get_pinecone_index")
    @patch("src.academic_rag.rag.retriever.get_embeddings")
    def test_class_grade_isolation(self, mock_get_embeddings, mock_get_pinecone, mock_repo):
        """Verify Class 9 queries cannot retrieve Class 10 uploads and vice versa."""
        mock_repo.get_student_documents.side_effect = self.repo.get_student_documents
        mock_embeddings = MagicMock()
        mock_embeddings.embed_query.return_value = [0.1] * 384
        mock_get_embeddings.return_value = mock_embeddings

        mock_index = MagicMock()
        mock_index.query.return_value = {"matches": []}
        mock_get_pinecone.return_value = mock_index

        # Query in Class 9
        retrieve_student_material_context(
            query="Cell structure",
            student_id="student_alice",
            class_filter=9,
        )
        filter_cls9 = mock_index.query.call_args[1]["filter"]
        self.assertEqual(filter_cls9["class"]["$eq"], 9)
        self.assertEqual(filter_cls9["student_id"]["$eq"], "student_alice")

        # Query in Class 10
        retrieve_student_material_context(
            query="Chemical reactions",
            student_id="student_alice",
            class_filter=10,
        )
        filter_cls10 = mock_index.query.call_args[1]["filter"]
        self.assertEqual(filter_cls10["class"]["$eq"], 10)


if __name__ == "__main__":
    unittest.main()
