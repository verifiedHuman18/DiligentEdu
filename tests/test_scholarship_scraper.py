"""Tests for NSP Scholarship Scraper and Ingestion Engine (Phase 17)."""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from src.academic_rag.scholarships.models import CatalogueItem, RawScholarshipData
from src.academic_rag.scholarships.scraper import NSPCatalogueScraper
from src.academic_rag.scholarships.storage import ScholarshipStorage


class TestScholarshipScraper(unittest.TestCase):
    """Test suite for NSP catalogue scraper, discovery, and raw text collection."""

    def setUp(self):
        self.storage = ScholarshipStorage()
        self.scraper = NSPCatalogueScraper(storage=self.storage)

    def test_catalogue_discovery(self):
        """Test that the scraper discovers scoped school schemes."""
        schemes = self.scraper.discover_schemes()
        self.assertGreaterEqual(len(schemes), 9)

        # Check discovered fields
        first = schemes[0]
        self.assertIsInstance(first, CatalogueItem)
        self.assertTrue(bool(first.id))
        self.assertTrue(bool(first.name))
        self.assertTrue(bool(first.provider))
        self.assertEqual(first.academic_year, "2026-27")

    def test_urls_and_dates_extracted(self):
        """Test that official URLs and application dates are present on discovered items."""
        schemes = self.scraper.discover_schemes()
        for s in schemes:
            self.assertIsNotNone(s.source_url)
            self.assertTrue(s.source_url.startswith("http"))
            self.assertIsNotNone(s.specification_url)
            self.assertIsNotNone(s.faq_url)
            self.assertIsNotNone(s.application_open)
            self.assertIsNotNone(s.application_close)

    def test_raw_text_harvesting_preservation(self):
        """Test that raw text is properly gathered and stored without premature modification."""
        schemes = self.scraper.discover_schemes()
        nmmss_item = next((s for s in schemes if s.id == "nmmss"), None)
        self.assertIsNotNone(nmmss_item)

        raw_data = self.scraper.harvest_scheme_raw(
            nmmss_item,
            scheme_source_data={
                "ministry": "Ministry of Education",
                "department": "Department of School Education & Literacy",
                "target_classes": ["Class 9", "Class 10"],
                "eligibility_criteria": {"income_ceiling_inr": 350000},
                "financial_assistance": {"amount_per_annum_inr": 12000},
            },
        )

        self.assertIsInstance(raw_data, RawScholarshipData)
        self.assertEqual(raw_data.id, "nmmss")
        self.assertIn("catalogue_text", raw_data.raw)
        self.assertIn("specification_text", raw_data.raw)
        self.assertIn("faq_text", raw_data.raw)
        self.assertTrue(len(raw_data.raw["specification_text"]) > 0)
        self.assertIsNotNone(raw_data.scraped_at)

    def test_isolated_year_execution(self):
        """Phase 16: Test running scraper for a versioned academic year in an isolated directory."""
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            custom_storage = ScholarshipStorage(base_dir=tmp_path)
            custom_scraper = NSPCatalogueScraper(storage=custom_storage)

            result = custom_scraper.run(academic_year="2027-28", force_refresh=True)
            self.assertEqual(result["status"], "success")
            self.assertEqual(result["academic_year"], "2027-28")
            self.assertGreaterEqual(result["total_processed"], 9)

            # Verify structured database exists in isolated year path
            loaded = custom_storage.load_structured_catalogue("2027-28")
            self.assertEqual(len(loaded), result["total_processed"])


if __name__ == "__main__":
    unittest.main()
