"""Tests for Dual-Source Hybrid Retrieval and Tutor Prompts (Phases 10-12)."""

import unittest
from unittest.mock import patch

from backend.rag.prompts import NCERT_TUTOR_SYSTEM_PROMPT
from backend.rag.retriever import retrieve_hybrid_academic_context


class TestStudyMaterialRetrieval(unittest.TestCase):
    """Test suite for multi-source hybrid retrieval and prompt formatting."""

    @patch("backend.rag.retriever.retrieve_student_material_context")
    @patch("backend.rag.retriever.retrieve_ncert_context")
    def test_hybrid_retrieval_combines_ncert_and_student_material(self, mock_ncert, mock_student):
        """Test that hybrid context cleanly segregates official NCERT and student material."""
        mock_ncert.return_value = (
            "[SOURCE: NCERT Class 10 Science | CHAPTER 12: Electricity | PAGE: 199]\n"
            "The potential difference V across ends of a metallic wire is directly proportional to current I."
        )
        mock_student.return_value = (
            "[SOURCE: STUDENT REFERENCE MATERIAL | TITLE: HC Verma Notes | PAGE: 48]\n"
            "Circuit diagram and numerical derivation for parallel resistors."
        )

        result = retrieve_hybrid_academic_context(
            query="Explain Ohm's law with circuit",
            student_id="student_001",
            class_filter=10,
        )

        self.assertTrue(result["has_student_context"])
        self.assertIn("OFFICIAL NCERT TEXTBOOK EXCERPTS", result["combined_context"])
        self.assertIn(
            "STUDENT REFERENCE MATERIAL (SUPPLEMENTARY EXCERPTS)", result["combined_context"]
        )
        self.assertIn("Electricity | PAGE: 199", result["combined_context"])
        self.assertIn("HC Verma Notes | PAGE: 48", result["combined_context"])

    def test_tutor_system_prompt_enforces_authoritative_hierarchy(self):
        """Verify the tutor system prompt explicitly mandates NCERT as authoritative ground truth."""
        self.assertIn("NCERT IS AUTHORITATIVE", NCERT_TUTOR_SYSTEM_PROMPT)
        self.assertIn("STUDENT MATERIAL IS SUPPLEMENTARY", NCERT_TUTOR_SYSTEM_PROMPT)
        self.assertIn("NCERT Textbook Citations", NCERT_TUTOR_SYSTEM_PROMPT)
        self.assertIn("Student Reference Material Citations", NCERT_TUTOR_SYSTEM_PROMPT)


if __name__ == "__main__":
    unittest.main()
