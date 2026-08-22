"""Tests for Scholarship Eligibility Engine, Ranking, and Service Layer (Phases 15, 17, 19)."""

import unittest

from src.academic_rag.scholarships.eligibility import (
    evaluate_scholarship,
    get_dynamic_questionnaire,
    match_scholarships,
    rank_matches,
)
from src.academic_rag.scholarships.models import (
    EligibilityCriteria,
    EligibilityStatus,
    FinancialAssistance,
    MeritRequirements,
    OfficialLinks,
    StructuredScholarship,
    StudentScholarshipProfile,
)
from src.academic_rag.scholarships.service import (
    get_available_scholarships,
    get_scholarship,
    get_scholarship_detail_view,
    get_scholarship_explanation,
)


class TestScholarshipEligibility(unittest.TestCase):
    """Test suite for eligibility evaluation, questionnaire, ranking, and service endpoints."""

    def setUp(self):
        self.sample_scheme = StructuredScholarship(
            id="test-nmmss",
            name="National Means-cum-Merit Scholarship Scheme",
            academic_year="2026-27",
            provider="Department of School Education & Literacy",
            scheme_type="merit_cum_means",
            eligibility=EligibilityCriteria(
                classes=[9, 10],
                states=["ALL"],
                categories=[],
                income_max=350000,
                gender="ANY",
                disability="ANY",
            ),
            merit_requirements=MeritRequirements(
                required=True,
                min_percentage=55.0,
                exam_required=True,
                details="State-level selection examination (MAT/SAT)",
            ),
            institution_requirements=["Government", "Government-aided", "Local Body"],
            financial_assistance=FinancialAssistance(
                amount_per_annum=12000,
                disbursement_frequency="Monthly",
                details="₹1,000 per month via DBT",
            ),
            official=OfficialLinks(
                source_url="https://scholarships.gov.in",
                specification_url="https://scholarships.gov.in/public/schemeGuidelines/nmmss_guidelines.pdf",
                faq_url="https://scholarships.gov.in/public/faq/nmmss_faq.html",
            ),
        )

    def test_class10_matching_income_likely_match(self):
        """Phase 17: Class 10 + matching income -> likely match."""
        profile = StudentScholarshipProfile(
            class_level=10,
            family_income=200000,
            category="General",
            school_type="Government School",
            academic_score=70.0,
            disability_status=False,
        )

        result = evaluate_scholarship(self.sample_scheme, profile)
        self.assertEqual(result.status, EligibilityStatus.LIKELY_MATCH)
        self.assertEqual(result.status_icon, "🟢")
        self.assertGreater(len(result.matched_rules), 0)
        self.assertEqual(len(result.unmatched_rules), 0)

    def test_class_mismatch_does_not_match(self):
        """Phase 17: Class mismatch -> does not match."""
        profile = StudentScholarshipProfile(
            class_level=12,  # Scheme is only for [9, 10]
            family_income=200000,
            category="General",
            school_type="Government School",
        )

        result = evaluate_scholarship(self.sample_scheme, profile)
        self.assertEqual(result.status, EligibilityStatus.DOES_NOT_MATCH)
        self.assertEqual(result.status_icon, "🔴")
        self.assertTrue(any("class" in r.lower() for r in result.unmatched_rules))

    def test_income_mismatch_does_not_match(self):
        """Phase 17: Income exceeding limit -> does not match."""
        profile = StudentScholarshipProfile(
            class_level=10,
            family_income=450000,  # Exceeds 350,000 limit
            category="General",
            school_type="Government School",
        )

        result = evaluate_scholarship(self.sample_scheme, profile)
        self.assertEqual(result.status, EligibilityStatus.DOES_NOT_MATCH)
        self.assertEqual(result.status_icon, "🔴")
        self.assertTrue(any("income" in r.lower() for r in result.unmatched_rules))

    def test_unknown_requirement_possible_match(self):
        """Phase 17: Missing / unknown requirements -> possible match."""
        profile = StudentScholarshipProfile(
            class_level=10,
            family_income=200000,
            # category, school_type, academic_score are unknown
        )

        result = evaluate_scholarship(self.sample_scheme, profile)
        self.assertEqual(result.status, EligibilityStatus.POSSIBLE_MATCH)
        self.assertEqual(result.status_icon, "🟡")
        self.assertGreater(len(result.unknown_rules), 0)

    def test_detail_view_synthesis(self):
        """Phase 15: Detail card synthesis with all standard sections."""
        profile = StudentScholarshipProfile(
            class_level=9,
            family_income=180000,
            category="General",
            school_type="Government School",
            academic_score=65.0,
        )

        detail = get_scholarship_detail_view("nmmss", student_profile=profile)
        self.assertIsNotNone(detail)
        self.assertEqual(detail["id"], "nmmss")
        self.assertIn("National Means-cum-Merit", detail["name"])
        self.assertIn("why_it_matches", detail)
        self.assertIn("potentially_required", detail)
        self.assertIn("application_window", detail)
        self.assertIn("official_sources", detail)
        self.assertIn("source_url", detail["official_sources"])
        self.assertIn("cta", detail)
        self.assertIn("Apply on Official Portal", detail["cta"]["label"])

    def test_service_layer_endpoints(self):
        """Phase 19: Test unified service functions."""
        schemes = get_available_scholarships("2026-27")
        self.assertGreaterEqual(len(schemes), 9)

        scheme = get_scholarship("nmmss", "2026-27")
        self.assertIsNotNone(scheme)
        self.assertEqual(scheme.id, "nmmss")

        explanation = get_scholarship_explanation("nmmss", {"class_level": 9, "family_income": 150000})
        self.assertIsNotNone(explanation)
        self.assertTrue(len(explanation.reasons_matched) > 0)


if __name__ == "__main__":
    unittest.main()
