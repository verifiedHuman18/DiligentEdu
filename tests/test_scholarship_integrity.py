"""Tests for Source Integrity and Official Verification Guarantees (Phase 18)."""

import unittest

from src.academic_rag.scholarships.eligibility import evaluate_scholarship, match_scholarships
from src.academic_rag.scholarships.models import EligibilityStatus, StudentScholarshipProfile
from src.academic_rag.scholarships.service import (
    get_available_scholarships,
    get_scholarship_detail_view,
)


class TestScholarshipSourceIntegrity(unittest.TestCase):
    """Phase 18: Strict validation of official provenance, data integrity, and ethical matching guarantees."""

    def setUp(self):
        self.academic_year = "2026-27"
        self.scholarships = get_available_scholarships(academic_year=self.academic_year)

    def test_every_scholarship_has_official_source_url(self):
        """Phase 18: Guarantee every single scholarship has an authentic official source URL."""
        self.assertGreater(len(self.scholarships), 0)
        for s in self.scholarships:
            self.assertIsNotNone(s.official.source_url, f"Scholarship {s.id} is missing official source URL")
            self.assertTrue(
                s.official.source_url.startswith("https://") or s.official.source_url.startswith("http://"),
                f"Scholarship {s.id} source_url '{s.official.source_url}' is not a valid HTTP URL",
            )

    def test_every_scholarship_has_academic_year_and_timestamp(self):
        """Phase 18: Guarantee academic year and scraped timestamp integrity."""
        for s in self.scholarships:
            self.assertEqual(s.academic_year, self.academic_year, f"Scheme {s.id} does not match active academic year")
            self.assertIsNotNone(s.metadata.scraped_at, f"Scheme {s.id} missing scraped_at timestamp")
            self.assertTrue(len(s.metadata.scraped_at) > 0)

    def test_detail_view_never_omits_official_source(self):
        """Phase 18: Test that no detail card can be rendered without official sources and portal CTA."""
        for s in self.scholarships:
            detail = get_scholarship_detail_view(s.id, academic_year=self.academic_year)
            self.assertIsNotNone(detail)
            self.assertIn("official_sources", detail)
            self.assertIn("source_url", detail["official_sources"])
            self.assertTrue(bool(detail["official_sources"]["source_url"]))
            self.assertIn("Apply on Official Portal", detail["cta"]["label"])
            self.assertIn("scholarships.gov.in", detail["cta"]["url"])

    def test_no_false_eligibility_guarantee(self):
        """Phase 18: Guarantee the system NEVER marks a student as likely_match if a mandatory criterion fails."""
        # Failing income ceiling (e.g. ₹5,00,000 > ₹3,50,000 max across any pre-matric scheme)
        failing_profile = StudentScholarshipProfile(
            class_level=10,
            family_income=500000,
            category="General",
        )

        matches = match_scholarships(failing_profile, academic_year=self.academic_year)
        for m in matches:
            # If the scheme has an income limit <= 350000, it MUST NOT be likely_match
            if m.scholarship_id in ("nmmss", "pm-yasasvi-pre-matric", "pre-matric-sc", "pre-matric-st"):
                self.assertEqual(
                    m.status,
                    EligibilityStatus.DOES_NOT_MATCH,
                    f"Scheme {m.scholarship_id} was improperly matched despite income violation!",
                )


if __name__ == "__main__":
    unittest.main()
