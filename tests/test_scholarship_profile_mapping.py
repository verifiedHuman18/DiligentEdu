"""Tests for Canonical Student Profile Mapping and Normalization (Phases 2, 3, 4, 17)."""

import unittest

from src.academic_rag.scholarships.models import (
    StudentScholarshipProfile,
    compute_profile_signature,
    normalize_student_profile,
)


class TestScholarshipProfileMapping(unittest.TestCase):
    """Verify that all UI and raw dictionary fields normalize to the canonical profile schema."""

    def test_class_normalization(self):
        """Phase 4: Test class string to int normalization."""
        p1 = normalize_student_profile({"class_level": "Class 10"})
        self.assertEqual(p1.class_level, 10)

        p2 = normalize_student_profile({"selected_class": "Class 9"})
        self.assertEqual(p2.class_level, 9)

        p3 = normalize_student_profile({}, default_class_level=9)
        self.assertEqual(p3.class_level, 9)

    def test_income_normalization_variations(self):
        """Phase 4: Test diverse income notations (numbers, lakh strings, formatted rupee strings)."""
        # Exact integer
        p1 = normalize_student_profile({"family_income": 180000})
        self.assertEqual(p1.family_income, 180000)

        # String representation of integer
        p2 = normalize_student_profile({"family_income": "250000"})
        self.assertEqual(p2.family_income, 250000)

        # Lakh notation
        p3 = normalize_student_profile({"income": "₹1.5 Lakh"})
        self.assertEqual(p3.family_income, 150000)

        p4 = normalize_student_profile({"income": "3.50 lakh per annum"})
        self.assertEqual(p4.family_income, 350000)

        # None / unspecified
        p5 = normalize_student_profile({"family_income": None})
        self.assertIsNone(p5.family_income)

    def test_category_normalization(self):
        """Phase 4: Test category cleanup from dropdown display text."""
        p1 = normalize_student_profile({"category": "Minorities (Muslim/Christian/Sikh/Jain/Buddhist/Parsi)"})
        self.assertEqual(p1.category, "Minorities")

        p2 = normalize_student_profile({"category": "OBC"})
        self.assertEqual(p2.category, "OBC")

    def test_disability_normalization(self):
        """Phase 4: Test boolean conversion for disability."""
        self.assertTrue(normalize_student_profile({"disability_status": "Yes"}).disability_status)
        self.assertFalse(normalize_student_profile({"disability_status": "No"}).disability_status)
        self.assertTrue(normalize_student_profile({"disability": True}).disability_status)
        self.assertFalse(normalize_student_profile({"disability": False}).disability_status)

    def test_academic_score_normalization(self):
        """Phase 4: Test percentage string / float parsing."""
        p1 = normalize_student_profile({"academic_score": "75.5%"})
        self.assertEqual(p1.academic_score, 75.5)

        p2 = normalize_student_profile({"score": 80})
        self.assertEqual(p2.academic_score, 80.0)

    def test_profile_signature_determinism(self):
        """Phase 10: Verify profile signature hashing and sensitivity."""
        p_a = normalize_student_profile({"class_level": 10, "family_income": 180000, "category": "OBC"})
        p_b = normalize_student_profile({"class_level": 10, "family_income": 180000, "category": "OBC"})
        p_c = normalize_student_profile({"class_level": 10, "family_income": 500000, "category": "OBC"})

        sig_a = compute_profile_signature(p_a)
        sig_b = compute_profile_signature(p_b)
        sig_c = compute_profile_signature(p_c)

        self.assertEqual(sig_a, sig_b, "Identical profiles must produce identical signatures")
        self.assertNotEqual(sig_a, sig_c, "Altered income must change the profile signature")


if __name__ == "__main__":
    unittest.main()
