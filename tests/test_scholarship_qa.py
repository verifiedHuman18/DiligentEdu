"""Tests for Scholarship Q&A Engine, Intent Detection, and Attribution (Phases 5-12, 19)."""

import unittest

from src.academic_rag.scholarships.models import StudentScholarshipProfile
from src.academic_rag.scholarships.qa import ScholarshipQAEngine, ask_scholarship_question


class TestScholarshipQA(unittest.TestCase):
    """Test suite for intent classification, structured Q&A, and unknown handling."""

    def setUp(self):
        self.qa_engine = ScholarshipQAEngine()

    def test_intent_detection(self):
        """Phase 5 & 6: Test intent detection."""
        self.assertEqual(self.qa_engine.detect_intent("What is NMMSS?"), "WHAT_IS")
        self.assertEqual(self.qa_engine.detect_intent("What is the income limit?"), "INCOME")
        self.assertEqual(self.qa_engine.detect_intent("Who can apply for PM-YASASVI?"), "ELIGIBILITY")
        self.assertEqual(self.qa_engine.detect_intent("What benefits are provided?"), "BENEFIT")
        self.assertEqual(self.qa_engine.detect_intent("What documents are required?"), "DOCUMENTS")
        self.assertEqual(self.qa_engine.detect_intent("When is the application deadline?"), "DEADLINE")
        self.assertEqual(self.qa_engine.detect_intent("What is the selection process?"), "SELECTION")
        self.assertEqual(self.qa_engine.detect_intent("What scholarships are available for Class 10?"), "CLASS")
        self.assertEqual(self.qa_engine.detect_intent("Why does PM-YASASVI match for me?"), "WHY_MATCH")

    def test_what_is_nmmss(self):
        """Phase 19: Test 'What is NMMSS?'."""
        res = ask_scholarship_question("What is NMMSS?")
        self.assertEqual(res["intent"], "WHAT_IS")
        self.assertIsNotNone(res["target_scholarship"])
        self.assertEqual(res["target_scholarship"]["id"], "nmmss")
        self.assertIn("National Means-cum-Merit", res["answer_markdown"])
        self.assertIn("National Scholarship Portal", res["sources"]["portal_name"])

    def test_income_limit_query(self):
        """Phase 19: Test 'What is the income limit for NMMSS?'."""
        res = ask_scholarship_question("What is the income limit for NMMSS?")
        self.assertEqual(res["intent"], "INCOME")
        self.assertIn("350,000", res["answer_markdown"])
        self.assertIn("National Scholarship Portal", res["answer_markdown"])

    def test_documents_required_query(self):
        """Phase 19: Test 'What documents are required for NMMSS?'."""
        res = ask_scholarship_question("What documents are required for NMMSS?")
        self.assertEqual(res["intent"], "DOCUMENTS")
        self.assertIn("Aadhaar", res["answer_markdown"])
        self.assertIn("OTR", res["answer_markdown"])
        self.assertIn("Income Certificate", res["answer_markdown"])

    def test_class10_available_scholarships(self):
        """Phase 19: Test 'What scholarships are available for Class 10?'."""
        res = ask_scholarship_question("What scholarships are available for Class 10?")
        self.assertIn("Class 10", res["answer_markdown"])
        self.assertGreaterEqual(len(res["relevant_scholarships"]), 8)

    def test_unsupported_speculative_question_graceful_handling(self):
        """Phase 10 & 19: Test unsupported questions return verified unavailability message."""
        res = ask_scholarship_question(
            "Can I apply if my father works abroad and is a foreign worker?",
            current_scheme_id="nmmss",
        )
        self.assertEqual(res["intent"], "UNKNOWN_CONDITION")
        self.assertIn("couldn't find verified information", res["answer_markdown"])
        self.assertIn("Official Specifications", res["answer_markdown"])

    def test_personalized_why_match_query(self):
        """Phase 12: Test 'Why does this scholarship appear for me?' with active profile."""
        profile = StudentScholarshipProfile(
            class_level=9,
            family_income=180000,
            category="OBC",
            school_type="Government School",
        )
        res = ask_scholarship_question(
            "Why does PM-YASASVI appear for me?",
            student_profile=profile,
            current_scheme_id="pm-yasasvi-pre-matric",
        )
        self.assertEqual(res["intent"], "WHY_MATCH")
        self.assertIn("Why", res["answer_markdown"])
        self.assertIn("class", res["answer_markdown"].lower())


if __name__ == "__main__":
    unittest.main()
