"""Tests for Dynamic Match Sensitivity and Rule Evaluation Integrity (Phases 6, 15, 16, 17, 18)."""

import unittest

from src.academic_rag.scholarships.models import (
    EligibilityStatus,
    StudentScholarshipProfile,
    normalize_student_profile,
)
from src.academic_rag.scholarships.service import match_scholarships


class TestScholarshipDynamicMatching(unittest.TestCase):
    """Phase 15 & 16: Verify that altering individual profile fields dynamically changes match outcomes."""

    def test_income_sensitivity(self):
        """Phase 15 (Test 2): Changing family income alters income-capped scholarships."""
        low_income = normalize_student_profile({
            "class_level": 9,
            "family_income": 100000,
            "category": "OBC",
            "school_type": "Government School",
            "academic_score": 75.0,
        })
        high_income = normalize_student_profile({
            "class_level": 9,
            "family_income": 500000,
            "category": "OBC",
            "school_type": "Government School",
            "academic_score": 75.0,
        })

        low_matches = {m.scholarship_id: m for m in match_scholarships(low_income)}
        high_matches = {m.scholarship_id: m for m in match_scholarships(high_income)}

        # NMMSS has income ceiling <= ₹3,50,000
        self.assertEqual(low_matches["nmmss"].status, EligibilityStatus.LIKELY_MATCH)
        self.assertEqual(high_matches["nmmss"].status, EligibilityStatus.DOES_NOT_MATCH)
        self.assertTrue(any("exceeds" in u for u in high_matches["nmmss"].unmatched_rules))

    def test_category_sensitivity(self):
        """Phase 15 (Test 3): Changing social category alters targeted affirmative action schemes."""
        obc_profile = normalize_student_profile({
            "class_level": 9,
            "family_income": 150000,
            "category": "OBC",
            "school_type": "Government School",
            "academic_score": 70.0,
        })
        sc_profile = normalize_student_profile({
            "class_level": 9,
            "family_income": 150000,
            "category": "SC",
            "school_type": "Government School",
            "academic_score": 70.0,
        })

        obc_matches = {m.scholarship_id: m for m in match_scholarships(obc_profile)}
        sc_matches = {m.scholarship_id: m for m in match_scholarships(sc_profile)}

        # PM-YASASVI targets OBC/EBC/DNT -> Should match for OBC, fail for SC
        self.assertEqual(obc_matches["pm-yasasvi-pre-matric"].status, EligibilityStatus.LIKELY_MATCH)
        self.assertEqual(sc_matches["pm-yasasvi-pre-matric"].status, EligibilityStatus.DOES_NOT_MATCH)

        # Pre-Matric SC -> Should match for SC, fail for OBC
        self.assertEqual(sc_matches["pre-matric-sc"].status, EligibilityStatus.LIKELY_MATCH)
        self.assertEqual(obc_matches["pre-matric-sc"].status, EligibilityStatus.DOES_NOT_MATCH)

    def test_disability_sensitivity(self):
        """Phase 15 (Test 4): Changing disability flag alters disability-specific scheme."""
        no_pwd = normalize_student_profile({
            "class_level": 9,
            "family_income": 150000,
            "category": "General",
            "disability_status": False,
        })
        yes_pwd = normalize_student_profile({
            "class_level": 9,
            "family_income": 150000,
            "category": "General",
            "disability_status": True,
        })

        no_matches = {m.scholarship_id: m for m in match_scholarships(no_pwd)}
        yes_matches = {m.scholarship_id: m for m in match_scholarships(yes_pwd)}

        self.assertEqual(no_matches["pre-matric-disabilities"].status, EligibilityStatus.DOES_NOT_MATCH)
        self.assertEqual(yes_matches["pre-matric-disabilities"].status, EligibilityStatus.LIKELY_MATCH)

    def test_school_type_sensitivity(self):
        """Phase 15 (Test 5): Changing school management type alters institutional verification."""
        govt_profile = normalize_student_profile({
            "class_level": 9,
            "family_income": 150000,
            "school_type": "Government School",
            "academic_score": 75.0,
        })
        pvt_profile = normalize_student_profile({
            "class_level": 9,
            "family_income": 150000,
            "school_type": "Recognized Private School",
            "academic_score": 75.0,
        })

        govt_matches = {m.scholarship_id: m for m in match_scholarships(govt_profile)}
        pvt_matches = {m.scholarship_id: m for m in match_scholarships(pvt_profile)}

        # NMMSS is for Govt / Aided / Local body schools only
        self.assertEqual(govt_matches["nmmss"].status, EligibilityStatus.LIKELY_MATCH)
        self.assertTrue(any("matches" in r for r in govt_matches["nmmss"].matched_rules if "school" in r))
        self.assertTrue(any("not among eligible types" in u for u in pvt_matches["nmmss"].unmatched_rules if "school" in u))

    def test_combination_matrix(self):
        """Phase 16: Multi-field parameter combination testing."""
        combo1 = normalize_student_profile({
            "class_level": 10,
            "category": "OBC",
            "family_income": 150000,
            "school_type": "Government School",
            "disability_status": False,
            "academic_score": 70.0,
        })
        combo2 = normalize_student_profile({
            "class_level": 10,
            "category": "OBC",
            "family_income": 400000,
            "school_type": "Government School",
            "disability_status": False,
            "academic_score": 70.0,
        })
        combo3 = normalize_student_profile({
            "class_level": 10,
            "category": "SC",
            "family_income": 150000,
            "school_type": "Government School",
            "disability_status": False,
            "academic_score": 70.0,
        })

        res1 = match_scholarships(combo1)
        res2 = match_scholarships(combo2)
        res3 = match_scholarships(combo3)

        self.assertNotEqual([m.status for m in res1], [m.status for m in res2])
        self.assertNotEqual([m.status for m in res1], [m.status for m in res3])


if __name__ == "__main__":
    unittest.main()
