"""Tests for Document Deletion and Cleanup (Phases 9, 20)."""

import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from backend import delete_study_material
from src.academic_rag.storage.database import init_database
from src.academic_rag.storage.repository import StudyMaterialRepository


class TestStudyMaterialDeletion(unittest.TestCase):
    """Test suite for document removal and vector cleanup."""

    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_db.close()
        self.db_path = self.temp_db.name
        init_database(self.db_path)
        self.repo = StudyMaterialRepository(db_path=self.db_path)

        # Seed document
        self.repo.save_document_record(
            document_id="doc_to_delete_001",
            student_id="student_alice",
            filename="Obsolete_Notes.pdf",
            material_name="Obsolete Physics Notes",
            class_level=10,
            subject="Science",
            chapter="Electricity",
            status="READY",
        )

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    @patch("src.academic_rag.rag.retriever.get_pinecone_index")
    def test_delete_document_removes_db_and_vectors(self, mock_get_pinecone):
        """Verify deletion removes SQLite record and triggers Pinecone vector deletion by document_id."""
        mock_index = MagicMock()
        mock_get_pinecone.return_value = mock_index

        # Verify doc exists before deletion
        doc_before = self.repo.get_document_by_id("doc_to_delete_001")
        self.assertIsNotNone(doc_before)

        # Delete document via backend facade
        success = delete_study_material(
            document_id="doc_to_delete_001",
            student_id="student_alice",
            db_path=self.db_path,
        )
        self.assertTrue(success)

        # Verify SQLite record is gone
        doc_after = self.repo.get_document_by_id("doc_to_delete_001")
        self.assertIsNone(doc_after)
        self.assertEqual(len(self.repo.get_student_documents("student_alice")), 0)

        # Verify Pinecone vector delete was called with document_id filter
        self.assertTrue(mock_index.delete.called)
        del_kwargs = mock_index.delete.call_args[1]
        self.assertEqual(del_kwargs["namespace"], "student-materials")
        self.assertEqual(del_kwargs["filter"]["document_id"]["$eq"], "doc_to_delete_001")


if __name__ == "__main__":
    unittest.main()
