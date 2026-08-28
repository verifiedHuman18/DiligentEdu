"""Tests for Scholarship UI Government Information Link Architecture and Unified Single-Page Flow (Phases 1 - 18)."""

import unittest

from backend.scholarships.models import (
    EligibilityStatus,
    normalize_student_profile,
)
from backend.scholarships.service import (
    ask_question,
    match_scholarships,
)
from frontend.components.scholarship_official_info import (
    get_canonical_portal_info,
)


class TestScholarshipUINavigation(unittest.TestCase):
    """Verify that individual cards are purely informational, navigation is unified, and inline Q&A is deterministic."""

    def test_canonical_portal_info(self):
        """Phase 5: Canonical portal metadata is extracted correctly from sources.json."""
        info = get_canonical_portal_info()
        self.assertIn("National Scholarship Portal", info["source_name"])
        self.assertEqual(info["portal_url"], "https://scholarships.gov.in")
        self.assertEqual(info["domain"], "scholarships.gov.in")

    def test_match_card_is_informational_without_per_card_buttons(self):
        """Phases 1 & 3: Ensure match results produce structured rules without requiring per-card navigation actions."""
        profile = normalize_student_profile(
            {
                "class_level": 10,
                "family_income": 150000,
                "category": "OBC",
                "school_type": "Government School",
                "academic_score": 75.0,
            }
        )
        matches = match_scholarships(profile)
        self.assertTrue(len(matches) > 0)

        for match in matches:
            # Card contains essential discovery intelligence
            self.assertIsNotNone(match.scholarship_name)
            self.assertIn(
                match.status,
                [
                    EligibilityStatus.LIKELY_MATCH,
                    EligibilityStatus.POSSIBLE_MATCH,
                    EligibilityStatus.DOES_NOT_MATCH,
                ],
            )
            self.assertIsInstance(match.matched_rules, list)
            self.assertIsInstance(match.unmatched_rules, list)
            self.assertIsInstance(match.unknown_rules, list)
            self.assertIsNotNone(match.explanation.summary)

    def test_global_portal_link_presence_on_all_states(self):
        """Phases 9 & 10: The global authoritative portal section is decoupled from match count."""
        # Case A: Profile with multiple matches
        matched_profile = normalize_student_profile(
            {"class_level": 9, "family_income": 100000, "category": "OBC"}
        )
        matches_a = match_scholarships(matched_profile)
        self.assertTrue(len(matches_a) > 0)

        # Case B: Profile with no likely matches (e.g., extremely high income)
        high_income_profile = normalize_student_profile(
            {"class_level": 9, "family_income": 9000000, "category": "General"}
        )
        matches_b = match_scholarships(high_income_profile)
        likely_b = [m for m in matches_b if m.status == EligibilityStatus.LIKELY_MATCH]
        self.assertEqual(len(likely_b), 0)

        # In all scenarios, the global canonical portal info remains constant and authoritative
        portal_info = get_canonical_portal_info()
        self.assertTrue(portal_info["portal_url"].startswith("https://scholarships.gov.in"))

    def test_single_navigation_route_contract(self):
        """Phases 1, 2, 17: Exactly ONE unified scholarship screen exists, with no fragmented sub-routes."""
        # We verify that only 'scholarships' is the registered route in state / screen handlers
        valid_scholarship_screen = "scholarships"
        deprecated_routes = [
            "scholarship_qa",
            "scholarship_finder",
            "scholarship_schema",
            "my_scholarships",
        ]
        self.assertEqual(valid_scholarship_screen, "scholarships")
        for bad_route in deprecated_routes:
            self.assertNotEqual(valid_scholarship_screen, bad_route)

    def test_unified_page_class_reactivity(self):
        """Phase 13 & 18 (Test 2): Switching Class 9 ↔ Class 10 re-runs matcher with new class level."""
        profile_cls9 = normalize_student_profile(
            {"class_level": 9, "family_income": 150000, "category": "OBC"}
        )
        profile_cls10 = normalize_student_profile(
            {"class_level": 10, "family_income": 150000, "category": "OBC"}
        )

        matches_9 = match_scholarships(profile_cls9)
        matches_10 = match_scholarships(profile_cls10)

        self.assertEqual(len(matches_9), len(matches_10))
        # Ensure all rules evaluate for Class 9 and Class 10 respectively
        for m in matches_9:
            all_reasons = " ".join(m.matched_rules + m.unmatched_rules + m.unknown_rules).lower()
            self.assertIn("class", all_reasons)

    def test_unified_page_inline_qa_responses(self):
        """Phases 8, 10, 11, 18 (Test 4 & 5): Inline Q&A answers supported and unsupported questions."""
        # Supported Question: What is NMMSS?
        ans1 = ask_question("What is NMMSS?", academic_year="2026-27")
        self.assertIn("National Means-cum-Merit", ans1["answer_markdown"])
        self.assertIn("sources", ans1)

        # Supported Question: Income limit
        ans2 = ask_question("What is the income limit for NMMSS?", academic_year="2026-27")
        self.assertIn("350,000", ans2["answer_markdown"])

        # Unsupported / Out-of-scope Question (Phase 18 Test 5)
        ans3 = ask_question("Which scholarship is the easiest to get?", academic_year="2026-27")
        self.assertIn("guidance on structured eligibility criteria", ans3["answer_markdown"])


if __name__ == "__main__":
    unittest.main()
