"""Tests for Scholarship Details View and Contextual Queries (Phases 14, 15, 16, 19)."""

import unittest

from backend.scholarships.models import StudentScholarshipProfile
from backend.scholarships.service import (
    ask_question,
    get_scholarship_detail_view,
)


class TestScholarshipDetails(unittest.TestCase):
    """Test suite for scholarship detail card synthesis and contextual questions."""

    def test_nmmss_detail_view_fields(self):
        """Phase 15: Verify all required detail card sections for NMMSS."""
        detail = get_scholarship_detail_view("nmmss", academic_year="2026-27")
        self.assertIsNotNone(detail)

        self.assertEqual(detail["id"], "nmmss")
        self.assertEqual(detail["academic_year"], "2026-27")
        self.assertEqual(detail["provider"], "Department of School Education & Literacy")
        self.assertEqual(detail["amount_per_annum"], 12000)
        self.assertIn("Monthly", detail["disbursement_frequency"])

        # Sections
        self.assertTrue(len(detail["why_it_matches"]) > 0)
        self.assertTrue(len(detail["potentially_required"]) > 0)
        self.assertIn("01 Jun 2026", detail["application_window"])

        # Official sources & CTA
        self.assertIn("source_url", detail["official_sources"])
        self.assertTrue(detail["official_sources"]["source_url"].startswith("http"))
        self.assertIn("specification_url", detail["official_sources"])
        self.assertIn("faq_url", detail["official_sources"])
        self.assertEqual(detail["cta"]["label"], "Apply on Official Portal")
        self.assertIn("scholarships.gov.in", detail["cta"]["url"])

    def test_contextual_ask_about_this_scholarship(self):
        """Phase 16: Verify asking question with current_scheme_id binds context."""
        # On NMMSS details page, asking "What is the income limit?" should resolve without naming NMMSS in the text
        res = ask_question("What is the income limit?", current_scheme_id="nmmss")
        self.assertEqual(res["intent"], "INCOME")
        self.assertIsNotNone(res["target_scholarship"])
        self.assertEqual(res["target_scholarship"]["id"], "nmmss")
        self.assertIn("350,000", res["answer_markdown"])

    def test_detail_view_with_student_profile(self):
        """Phase 15: Verify personalized why_it_matches bullets when student profile is supplied."""
        profile = StudentScholarshipProfile(
            class_level=9,
            family_income=150000,
            category="OBC",
            school_type="Government School",
            academic_score=75.0,
        )

        detail = get_scholarship_detail_view("pm-yasasvi-pre-matric", student_profile=profile)
        self.assertIsNotNone(detail)
        self.assertEqual(detail["status"], "likely_match")
        self.assertEqual(detail["status_icon"], "🟢")
        self.assertTrue(any("income" in b.lower() for b in detail["why_it_matches"]))
        self.assertTrue(any("class" in b.lower() for b in detail["why_it_matches"]))


if __name__ == "__main__":
    unittest.main()
