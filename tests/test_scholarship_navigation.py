"""Tests for Scholarship Official URL Resolution and Navigation (Phases 1, 2, 3, 6, 9, 10, 14, 15)."""

import unittest

from src.academic_rag.scholarships.models import (
    OfficialLinks,
    StudentScholarshipProfile,
    get_scholarship_primary_url,
    normalize_student_profile,
)
from src.academic_rag.scholarships.service import (
    get_available_scholarships,
    get_scholarship,
    match_scholarships,
)


class TestScholarshipNavigation(unittest.TestCase):
    """Verify that every scholarship accurately resolves to its verified official scheme page."""

    def test_primary_url_priority(self):
        """Phase 14 (Test 1): Primary URL takes top precedence when explicitly present."""
        sample = {
            "official": {
                "primary_url": "https://scholarships.gov.in/public/schemeGuidelines/nmmss_guidelines.pdf",
                "specification_url": "https://scholarships.gov.in/public/schemeGuidelines/fallback.pdf",
                "source_url": "https://scholarships.gov.in",
            }
        }
        self.assertEqual(
            get_scholarship_primary_url(sample),
            "https://scholarships.gov.in/public/schemeGuidelines/nmmss_guidelines.pdf",
        )

    def test_specification_url_fallback(self):
        """Phase 14 (Test 2): Fallback to specification_url when primary_url is missing."""
        sample = {
            "official": {
                "primary_url": None,
                "specification_url": "https://scholarships.gov.in/public/schemeGuidelines/pm-yasasvi-pre-matric_guidelines.pdf",
                "source_url": "https://scholarships.gov.in",
            }
        }
        self.assertEqual(
            get_scholarship_primary_url(sample),
            "https://scholarships.gov.in/public/schemeGuidelines/pm-yasasvi-pre-matric_guidelines.pdf",
        )

    def test_faq_and_source_url_fallback(self):
        """Phase 14 (Test 2): Fallback hierarchy down to faq_url and source_url."""
        sample_faq = {
            "official": {
                "primary_url": None,
                "specification_url": None,
                "faq_url": "https://scholarships.gov.in/public/faq/nmmss_faq.html",
                "source_url": "https://scholarships.gov.in",
            }
        }
        self.assertEqual(
            get_scholarship_primary_url(sample_faq),
            "https://scholarships.gov.in/public/faq/nmmss_faq.html",
        )

        sample_portal = {
            "official": {
                "primary_url": None,
                "specification_url": None,
                "faq_url": None,
                "source_url": "https://scholarships.gov.in/All-Scholarships",
            }
        }
        self.assertEqual(
            get_scholarship_primary_url(sample_portal),
            "https://scholarships.gov.in/All-Scholarships",
        )

    def test_invalid_and_null_safety(self):
        """Phase 9 & 14 (Test 3): Null, empty, '#', or JavaScript URLs return None to prevent broken links."""
        self.assertIsNone(get_scholarship_primary_url(None))
        self.assertIsNone(get_scholarship_primary_url({}))
        self.assertIsNone(get_scholarship_primary_url({"official": {"primary_url": "#"}}))
        self.assertIsNone(get_scholarship_primary_url({"official": {"primary_url": "javascript:void(0)"}}))
        self.assertIsNone(get_scholarship_primary_url({"official": {"primary_url": "about:blank"}}))
        self.assertIsNone(get_scholarship_primary_url({"official": {"primary_url": ""}}))

    def test_all_prototype_schemes_have_exact_urls(self):
        """Phase 10 & 15: Every curated prototype scholarship must resolve to an exact scheme-specific page."""
        expected_schemes = [
            "nmmss",
            "pm-yasasvi-pre-matric",
            "pm-yasasvi-top-class-schools",
            "pre-matric-disabilities",
            "pre-matric-sc",
            "pre-matric-st",
            "pre-matric-beedi-cine-workers",
            "pre-matric-minorities",
            "pre-matric-hazardous-occupations",
        ]

        all_schemes = get_available_scholarships("2026-27")
        self.assertEqual(len(all_schemes), len(expected_schemes))

        for scheme in all_schemes:
            url = get_scholarship_primary_url(scheme)
            self.assertIsNotNone(url, f"Scheme {scheme.id} must have a valid official primary URL")
            self.assertTrue(
                url.startswith("https://") or url.startswith("http://"),
                f"Scheme {scheme.id} URL must use valid HTTP/HTTPS protocol: {url}",
            )
            # Guarantee it is a scheme-specific path and not just generic homepage
            self.assertTrue(
                scheme.id in url or "guidelines" in url or "schemeGuidelines" in url,
                f"Scheme {scheme.id} URL must point to specific scheme page/guideline: {url}",
            )

    def test_match_result_navigation_integration(self):
        """Phase 17: Matched scholarship results directly expose the correct official URL."""
        profile = normalize_student_profile({
            "class_level": 9,
            "family_income": 120000,
            "category": "OBC",
            "school_type": "Government School",
            "academic_score": 75.0,
        })
        matches = match_scholarships(profile, academic_year="2026-27")

        for match in matches:
            resolved_url = get_scholarship_primary_url(match)
            self.assertIsNotNone(resolved_url)
            self.assertTrue(resolved_url.startswith("https://"))


if __name__ == "__main__":
    unittest.main()
