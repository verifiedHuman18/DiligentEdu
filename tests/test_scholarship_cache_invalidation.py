"""Tests for Matcher Purity and Cache Invalidation (Phases 5, 9, 10, 11, 17)."""

import unittest

from backend.scholarships.models import (
    compute_profile_signature,
    normalize_student_profile,
)
from backend.scholarships.service import match_scholarships


class TestScholarshipCacheInvalidation(unittest.TestCase):
    """Verify that match results are pure, signature-deterministic, and free of stale caches."""

    def test_matcher_purity(self):
        """Phase 5: Guarantee pure execution without side-effects or mutations."""
        profile = normalize_student_profile(
            {
                "class_level": 10,
                "family_income": 180000,
                "category": "OBC",
                "school_type": "Government School",
                "academic_score": 75.0,
            }
        )

        run1 = match_scholarships(profile)
        run2 = match_scholarships(profile)

        self.assertEqual(len(run1), len(run2))
        for m1, m2 in zip(run1, run2):
            self.assertEqual(m1.scholarship_id, m2.scholarship_id)
            self.assertEqual(m1.status, m2.status)
            self.assertEqual(m1.score, m2.score)
            self.assertEqual(m1.matched_rules, m2.matched_rules)

    def test_immediate_invalidation_on_profile_change(self):
        """Phase 9 & 10: Changing profile invalidates old signature and produces fresh result set."""
        profile_a = normalize_student_profile(
            {"class_level": 9, "family_income": 120000, "category": "SC"}
        )
        profile_b = normalize_student_profile(
            {"class_level": 9, "family_income": 500000, "category": "SC"}
        )

        sig_a = compute_profile_signature(profile_a)
        sig_b = compute_profile_signature(profile_b)
        self.assertNotEqual(sig_a, sig_b)

        res_a = match_scholarships(profile_a)
        res_b = match_scholarships(profile_b)

        # In res_a, pre-matric-sc should be likely_match
        # In res_b, pre-matric-sc should be does_not_match (income limit is 2.5 Lakh)
        sc_a = next(m for m in res_a if m.scholarship_id == "pre-matric-sc")
        sc_b = next(m for m in res_b if m.scholarship_id == "pre-matric-sc")

        self.assertEqual(sc_a.status, "likely_match")
        self.assertEqual(sc_b.status, "does_not_match")


if __name__ == "__main__":
    unittest.main()
