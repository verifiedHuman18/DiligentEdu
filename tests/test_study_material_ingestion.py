"""Tests for Study Material Ingestion Pipeline, Chunking, and Embedding (Phases 4-8, 20-21)."""

import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

import fitz

from backend.models.study_material import DocumentStatus
from backend.storage.database import init_database
from backend.storage.repository import StudyMaterialRepository
from src.academic_rag.ingestion.chunker import chunk_document_pages
from src.academic_rag.ingestion.document_processor import extract_pages_from_pdf
from src.academic_rag.ingestion.pdf_ingester import ingest_study_material_pdf


def _create_multi_page_pdf(pages_text: list[str]) -> bytes:
    """Helper to create a multi-page PDF."""
    doc = fitz.open()
    for text in pages_text:
        page = doc.new_page()
        page.insert_text((50, 50), text)
    pdf_bytes = doc.write()
    doc.close()
    return pdf_bytes


class TestStudyMaterialIngestion(unittest.TestCase):
    """Test suite for PDF ingestion, chunking, and local embedding pipeline."""

    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_db.close()
        self.db_path = self.temp_db.name
        init_database(self.db_path)
        self.repo = StudyMaterialRepository(db_path=self.db_path)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_document_processor_page_extraction(self):
        """Test that extract_pages_from_pdf preserves 1-indexed page numbering."""
        p1 = "Page one content with definitions and basic laws of physics."
        p2 = "Page two content with numerical examples and circuit diagrams."
        pdf_bytes = _create_multi_page_pdf([p1, p2])

        extracted = extract_pages_from_pdf(pdf_bytes)
        self.assertEqual(len(extracted), 2)
        self.assertEqual(extracted[0][0], 1)
        self.assertIn("Page one", extracted[0][1])
        self.assertEqual(extracted[1][0], 2)
        self.assertIn("Page two", extracted[1][1])

    def test_chunker_metadata_preservation(self):
        """Test that chunks retain rich metadata and correct page references."""
        pages = [
            (1, "Ohm's law states that V = IR. Resistance depends on length and area."),
            (2, "In series circuits, R_eq = R1 + R2. In parallel circuits, 1/R_eq = 1/R1 + 1/R2."),
        ]

        chunks = chunk_document_pages(
            pages=pages,
            document_id="doc_test_123",
            student_id="student_alice",
            filename="Physics_Reference.pdf",
            material_name="Physics Reference",
            class_level=10,
            subject="Science",
            chapter="Electricity",
            chunk_size=100,
            chunk_overlap=20,
        )

        self.assertGreaterEqual(len(chunks), 2)
        c0 = chunks[0]
        self.assertEqual(c0.student_id, "student_alice")
        self.assertEqual(c0.document_id, "doc_test_123")
        self.assertEqual(c0.class_level, 10)
        self.assertEqual(c0.chapter, "Electricity")
        self.assertEqual(c0.source_type, "user_upload")
        self.assertEqual(c0.page, 1)

        meta = c0.to_metadata()
        self.assertEqual(meta["class"], 10)
        self.assertEqual(meta["student_id"], "student_alice")
        self.assertEqual(meta["source_type"], "user_upload")

    @patch("src.academic_rag.ingestion.pdf_ingester.get_pinecone_index")
    def test_end_to_end_ingestion_zero_gemini(self, mock_get_pinecone):
        """Test full ingestion pipeline without invoking any Gemini API calls."""
        mock_index = MagicMock()
        mock_get_pinecone.return_value = mock_index

        page1_text = (
            "Chapter 10: Light Reflection and Refraction. Spherical mirrors have a pole, "
            "center of curvature, and principal axis. The mirror formula is 1/f = 1/v + 1/u."
        )
        pdf_bytes = _create_multi_page_pdf([page1_text])

        # Execute Ingestion
        result = ingest_study_material_pdf(
            student_id="student_001",
            file_data=pdf_bytes,
            filename="Light_Ref_Notes.pdf",
            material_name="Light Reference Notes",
            class_level=10,
            subject="Science",
            chapter="Light – Reflection and Refraction",
            db_path=self.db_path,
            repository=self.repo,
        )

        self.assertEqual(result["status"], DocumentStatus.READY.value)
        self.assertEqual(result["page_count"], 1)
        self.assertGreater(result["chunk_count"], 0)
        self.assertEqual(result["material_name"], "Light Reference Notes")

        # Verify Pinecone upsert was called under namespace 'student-materials'
        self.assertTrue(mock_index.upsert.called)
        call_kwargs = mock_index.upsert.call_args[1]
        self.assertEqual(call_kwargs.get("namespace"), "student-materials")
        upserted_vectors = call_kwargs.get("vectors")
        self.assertGreater(len(upserted_vectors), 0)

        # Verify SQLite DB record
        docs = self.repo.get_student_documents("student_001", class_level=10)
        self.assertEqual(len(docs), 1)
        self.assertEqual(docs[0]["status"], "READY")
        self.assertEqual(docs[0]["filename"], "Light_Ref_Notes.pdf")


if __name__ == "__main__":
    unittest.main()
