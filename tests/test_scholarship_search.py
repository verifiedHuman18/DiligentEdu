"""Tests for Scholarship Search Engine and Field-Level Matching (Phases 3, 4, 19)."""

import unittest

from src.academic_rag.scholarships.search import ScholarshipSearchEngine, search_scholarships


class TestScholarshipSearch(unittest.TestCase):
    """Test suite for keyword, field-level, and alias search."""

    def setUp(self):
        self.search_engine = ScholarshipSearchEngine()

    def test_search_by_scheme_alias(self):
        """Phase 19: Test 'What is NMMSS?' alias resolution."""
        scheme = self.search_engine.find_scheme_by_alias("NMMSS")
        self.assertIsNotNone(scheme)
        self.assertEqual(scheme.id, "nmmss")

        scheme_yasasvi = self.search_engine.find_scheme_by_alias("PM-YASASVI")
        self.assertIsNotNone(scheme_yasasvi)
        self.assertIn("pm-yasasvi", scheme_yasasvi.id)

    def test_search_by_income_field(self):
        """Phase 19: Search across income criteria."""
        results = search_scholarships(query="income limit", field="income")
        self.assertGreater(len(results), 0)
        self.assertTrue(any(s.id == "nmmss" for s in results))

    def test_search_by_documents_field(self):
        """Phase 19: Search across document requirements."""
        results = search_scholarships(query="UDID disability certificate", field="documents")
        self.assertGreater(len(results), 0)
        self.assertTrue(any(s.id == "pre-matric-disabilities" for s in results))

    def test_class_isolation_search(self):
        """Phase 19: Test class isolation filtering in search."""
        class9_results = search_scholarships(query="", class_level=9)
        self.assertGreaterEqual(len(class9_results), 8)

        class10_results = search_scholarships(query="", class_level=10)
        self.assertGreaterEqual(len(class10_results), 8)

        # Every result must contain the requested class
        for s in class9_results:
            self.assertIn(9, s.eligibility.classes)
        for s in class10_results:
            self.assertIn(10, s.eligibility.classes)


if __name__ == "__main__":
    unittest.main()
