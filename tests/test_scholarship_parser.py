"""Tests for Scholarship Parser and Normalization Utilities (Phase 17)."""

import unittest

from src.academic_rag.scholarships.models import RawScholarshipData, StructuredScholarship
from src.academic_rag.scholarships.parser import (
    extract_clean_text,
    parse_categories,
    parse_classes,
    parse_disability_requirement,
    parse_gender,
    parse_income_ceiling,
    parse_scholarship_amount,
    raw_to_structured,
)


class TestScholarshipParser(unittest.TestCase):
    """Test suite for parsing raw text and HTML into structured models."""

    def test_html_tag_stripping(self):
        """Test that HTML tags, scripts, and whitespace are cleaned."""
        raw_html = "<div><h2>Eligibility</h2><p>Class 9 and 10 students.</p><script>alert('test');</script></div>"
        cleaned = extract_clean_text(raw_html)
        self.assertIn("Eligibility", cleaned)
        self.assertIn("Class 9 and 10 students.", cleaned)
        self.assertNotIn("alert", cleaned)
        self.assertNotIn("<script>", cleaned)

    def test_class_extraction(self):
        """Test extraction of class numbers from natural language."""
        self.assertEqual(parse_classes("Scheme for Class IX and Class X students."), [9, 10])
        self.assertEqual(parse_classes("Pre-Matric scholarship for 9th standard."), [9, 10])
        self.assertEqual(parse_classes("Class 9 to 12 top class education"), [9, 10, 11, 12])

    def test_income_ceiling_extraction(self):
        """Test extraction of income limits in various currency notations."""
        self.assertEqual(
            parse_income_ceiling("Annual family income must not exceed Rs. 3.5 Lakh"), 350000
        )
        self.assertEqual(parse_income_ceiling("Income ceiling: ₹2.50 lakh per annum"), 250000)
        self.assertEqual(parse_income_ceiling("Parental income up to Rs 1,00,000 / year"), 100000)
        self.assertEqual(
            parse_income_ceiling("Monthly income limit of Rs. 10000 per month"), 120000
        )

    def test_missing_income_null_safety(self):
        """Test that schemes without income cap return None rather than inventing a number."""
        text_without_income = "Pre-Matric Scholarship for children of parents in hazardous occupations. No income ceiling applicable."
        self.assertIsNone(parse_income_ceiling(text_without_income))

    def test_category_extraction(self):
        """Test extraction of reservation and community categories."""
        cats = parse_categories("Available for SC/ST and OBC students", scheme_id="pm-yasasvi")
        self.assertIn("SC", cats)
        self.assertIn("ST", cats)
        self.assertIn("OBC", cats)

        # Open scheme returns empty list (all categories allowed)
        open_cats = parse_categories(
            "Means cum merit for all meritorious students", scheme_id="nmmss"
        )
        self.assertEqual(open_cats, [])

    def test_disability_and_gender_parsing(self):
        """Test disability threshold and gender detection."""
        self.assertEqual(
            parse_disability_requirement("Requires minimum 40% disability certificate with UDID"),
            "REQUIRED_MIN_40_PERCENT",
        )
        self.assertEqual(parse_disability_requirement("Open for all eligible students"), "ANY")
        self.assertEqual(parse_gender("Applicable for girl student only"), "FEMALE")
        self.assertEqual(parse_gender("Open for all genders"), "ANY")

    def test_amount_extraction(self):
        """Test extraction of annual scholarship amounts."""
        self.assertEqual(
            parse_scholarship_amount("Students receive ₹12,000 per annum (₹1,000 per month)"), 12000
        )
        self.assertEqual(parse_scholarship_amount("Assistance up to Rs. 75,000 per year"), 75000)
        self.assertEqual(parse_scholarship_amount("Allowance of Rs 4000"), 4000)

    def test_raw_to_structured_transformation(self):
        """Test end-to-end transformation of RawScholarshipData to StructuredScholarship."""
        raw = RawScholarshipData(
            id="test-pre-matric",
            name="Pre-Matric Scholarship Scheme for SC Students",
            academic_year="2026-27",
            provider="Ministry of Social Justice & Empowerment",
            source_url="https://scholarships.gov.in",
            raw={
                "specification_text": "Class 9 and 10 SC students. Income ceiling Rs. 2.5 Lakh. Amount Rs. 4000 per annum.",
            },
        )

        structured = raw_to_structured(raw)
        self.assertIsInstance(structured, StructuredScholarship)
        self.assertEqual(structured.id, "test-pre-matric")
        self.assertEqual(structured.eligibility.classes, [9, 10])
        self.assertEqual(structured.eligibility.income_max, 250000)
        self.assertIn("SC", structured.eligibility.categories)
        self.assertIsNotNone(structured.financial_assistance)
        self.assertEqual(structured.financial_assistance.amount_per_annum, 4000)


if __name__ == "__main__":
    unittest.main()
