"""Unit tests for NSP Scholarship Scraper, Storage, Generic Rules, and Eligibility Engine."""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from src.academic_rag.scholarships.eligibility import (
    build_rules_for_scholarship,
    evaluate_rule,
    evaluate_scholarship,
    generate_template_explanation,
    get_dynamic_questionnaire,
    match_scholarships,
    rank_matches,
)
from src.academic_rag.scholarships.models import (
    CatalogueItem,
    EligibilityCriteria,
    EligibilityRule,
    EligibilityStatus,
    FinancialAssistance,
    RawScholarshipData,
    StructuredScholarship,
    StudentScholarshipProfile,
)
from src.academic_rag.scholarships.parser import (
    extract_clean_text,
    parse_categories,
    parse_classes,
    parse_income_ceiling,
    raw_to_structured,
)
from src.academic_rag.scholarships.storage import ScholarshipStorage


class TestScholarshipModule(unittest.TestCase):
    """Test suite for scholarship discovery, scraping, parsing, storage, and eligibility matching."""

    def test_clean_html_text_extraction(self):
        html_content = "<p>National Means-cum-Merit Scholarship Scheme for <b>Class 9</b> students.</p><script>var x = 1;</script>"
        text = extract_clean_text(html_content)
        self.assertIn("National Means-cum-Merit Scholarship Scheme", text)
        self.assertIn("Class 9", text)
        self.assertNotIn("var x = 1", text)

    def test_parse_helpers(self):
        sample_text = "Eligibility: Class 9 and Class 10 SC/ST students with annual family income not exceeding Rs. 3.5 Lakh (Rs 350,000)."
        classes = parse_classes(sample_text)
        income = parse_income_ceiling(sample_text)
        categories = parse_categories(sample_text)

        self.assertIn(9, classes)
        self.assertIn(10, classes)
        self.assertEqual(income, 350000)
        self.assertIn("SC", categories)
        self.assertIn("ST", categories)

    def test_null_income_safety(self):
        sample_text = "Pre-Matric Scholarship for vulnerable sanitation workers with no income restriction."
        income = parse_income_ceiling(sample_text)
        self.assertIsNone(income)

    def test_scholarship_storage_lifecycle(self):
        with TemporaryDirectory() as tmp_dir:
            base_path = Path(tmp_dir)
            raw_path = base_path / "raw"
            struct_path = base_path / "structured"

            storage = ScholarshipStorage(
                base_dir=base_path,
                raw_dir=raw_path,
                structured_dir=struct_path,
            )

            raw_item = RawScholarshipData(
                id="test-nmmss",
                name="Test National Means Cum Merit",
                academic_year="2026-27",
                provider="Dept of School Education",
                source_url="https://scholarships.gov.in",
                raw={"catalogue_text": "Sample catalogue raw text", "specification_text": "Income limit Rs. 350000"},
            )

            saved_file = storage.save_raw(raw_item)
            self.assertTrue(saved_file.exists())

            loaded_raw = storage.load_raw("test-nmmss", academic_year="2026-27")
            self.assertIsNotNone(loaded_raw)
            self.assertEqual(loaded_raw.id, "test-nmmss")
            self.assertEqual(loaded_raw.name, "Test National Means Cum Merit")

            # Structured conversion and persistence
            structured_item = raw_to_structured(raw_item)
            storage.save_structured_catalogue([structured_item], academic_year="2026-27")

            loaded_catalogue = storage.load_structured_catalogue(academic_year="2026-27")
            self.assertEqual(len(loaded_catalogue), 1)
            self.assertEqual(loaded_catalogue[0].id, "test-nmmss")
            self.assertEqual(loaded_catalogue[0].eligibility.income_max, 350000)

    def test_generic_rule_evaluation(self):
        """Phase 7: Test generic rule evaluation engine."""
        profile = StudentScholarshipProfile(
            class_level=10,
            family_income=180000,
            category="OBC",
            academic_score=78.5,
        )

        rule_class = EligibilityRule(field="class_level", operator="in", value=[9, 10], mandatory=True)
        status, msg = evaluate_rule(rule_class, profile)
        self.assertEqual(status, "matched")

        rule_income = EligibilityRule(field="family_income", operator="<=", value=250000, mandatory=True)
        status, msg = evaluate_rule(rule_income, profile)
        self.assertEqual(status, "matched")

        rule_income_fail = EligibilityRule(field="family_income", operator="<=", value=100000, mandatory=True)
        status, msg = evaluate_rule(rule_income_fail, profile)
        self.assertEqual(status, "unmatched")

        rule_unknown = EligibilityRule(field="school_type", operator="in", value=["Government"], mandatory=True)
        status, msg = evaluate_rule(rule_unknown, profile)
        self.assertEqual(status, "unknown")

    def test_three_eligibility_states(self):
        """Phase 9: Test Likely Match, Possible Match, and Does Not Match."""
        # 1. Profile matching NMMSS
        profile_likely = StudentScholarshipProfile(
            class_level=9,
            family_income=200000,
            category="General",
            school_type="Government School",
            academic_score=68.0,
            disability_status=False,
        )

        results = match_scholarships(profile_likely, academic_year="2026-27")
        nmmss_result = next((r for r in results if r.scholarship_id == "nmmss"), None)
        self.assertIsNotNone(nmmss_result)
        self.assertEqual(nmmss_result.status, EligibilityStatus.LIKELY_MATCH)
        self.assertEqual(nmmss_result.status_icon, "🟢")

        # 2. Profile with high income failing threshold
        profile_failing = StudentScholarshipProfile(
            class_level=9,
            family_income=500000,  # Exceeds NMMSS Rs 3.5 Lakh
            category="General",
            school_type="Government School",
        )
        failing_results = match_scholarships(profile_failing, academic_year="2026-27")
        nmmss_failing = next((r for r in failing_results if r.scholarship_id == "nmmss"), None)
        self.assertIsNotNone(nmmss_failing)
        self.assertEqual(nmmss_failing.status, EligibilityStatus.DOES_NOT_MATCH)
        self.assertEqual(nmmss_failing.status_icon, "🔴")

        # 3. Incomplete profile yielding Possible Match
        profile_incomplete = StudentScholarshipProfile(
            class_level=9,
            family_income=150000,
            # category, school_type, score not provided
        )
        incomplete_results = match_scholarships(profile_incomplete, academic_year="2026-27")
        self.assertTrue(any(r.status == EligibilityStatus.POSSIBLE_MATCH for r in incomplete_results))

    def test_dynamic_questionnaire_prioritization(self):
        """Phase 11: Dynamic questionnaire asks only missing fields."""
        # Profile has only class_level
        profile_partial = StudentScholarshipProfile(class_level=10)
        questions = get_dynamic_questionnaire(profile_partial)

        field_names = [q.field_name for q in questions]
        self.assertNotIn("class_level", field_names)  # Already known!
        self.assertIn("family_income", field_names)   # Missing core
        self.assertIn("category", field_names)        # Missing core

        # Check priority order
        priorities = [q.priority for q in questions]
        self.assertEqual(priorities, sorted(priorities))

    def test_ranking_and_explanation(self):
        """Phase 12 & 13: Test multi-tier ranking and template explanation generation."""
        profile = StudentScholarshipProfile(
            class_level=10,
            family_income=180000,
            category="OBC",
            school_type="Government School",
            disability_status=False,
        )

        ranked = match_scholarships(profile, academic_year="2026-27")
        self.assertGreater(len(ranked), 0)

        # First items must be likely_match or possible_match before does_not_match
        statuses = [r.status for r in ranked]
        if EligibilityStatus.DOES_NOT_MATCH in statuses:
            first_fail_idx = statuses.index(EligibilityStatus.DOES_NOT_MATCH)
            for s in statuses[:first_fail_idx]:
                self.assertIn(s, [EligibilityStatus.LIKELY_MATCH, EligibilityStatus.POSSIBLE_MATCH])

        # Test explanation structure
        first_match = ranked[0]
        self.assertIsInstance(first_match.explanation.summary, str)
        self.assertTrue(len(first_match.explanation.reasons_matched) > 0 or len(first_match.explanation.verification_needed) > 0)
        self.assertIn("https://scholarships.gov.in", first_match.explanation.action_guidance)


if __name__ == "__main__":
    unittest.main()
