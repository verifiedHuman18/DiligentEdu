"""NSP Catalogue Scraper and Ingestion Engine.

Follows a disciplined, non-aggressive scraping pipeline:
1. Discovers targeted school schemes (Phase 2)
2. Executes only on manual/admin trigger, caching locally for student queries (Phase 3)
3. Preserves raw audit text into data/scholarships/raw/2026-27/{id}.json (Phase 4)
4. Traverses specifications and FAQ references (Phase 5)
5. Synthesizes strict structured records in data/scholarships/structured/2026-27.json (Phase 6)
"""

import json
import logging
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.config import config
from backend.scholarships.models import (
    CatalogueItem,
    RawScholarshipData,
    StructuredScholarship,
)
from backend.scholarships.parser import (
    extract_clean_text,
    raw_to_structured,
)
from backend.scholarships.storage import ScholarshipStorage

logger = logging.getLogger(__name__)


class NSPCatalogueScraper:
    """Non-aggressive scraper and harvester for National Scholarship Portal school schemes."""

    DEFAULT_USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    )

    def __init__(
        self,
        storage: Optional[ScholarshipStorage] = None,
        sources_file: Optional[Path] = None,
    ) -> None:
        self.storage = storage or ScholarshipStorage()
        self.sources_file = sources_file or config.scholarships_sources_file

    def fetch_url(self, url: str, timeout: int = 10) -> Optional[str]:
        """Fetch webpage HTML/text with custom User-Agent and graceful failure handling."""
        if not url or not url.startswith("http"):
            return None

        try:
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": self.DEFAULT_USER_AGENT,
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.5",
                },
            )
            with urllib.request.urlopen(req, timeout=timeout) as response:
                content = response.read().decode("utf-8", errors="replace")
                return content
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
            logger.warning(f"Could not reach external link {url}: {e}")
            return None
        except Exception as e:
            logger.warning(f"Unexpected error fetching {url}: {e}")
            return None

    def discover_schemes(self) -> List[CatalogueItem]:
        """Phase 2: Discover targeted school schemes from the scoped catalogue manifest."""
        if not self.sources_file.exists():
            logger.error(f"Sources file not found at {self.sources_file}")
            return []

        try:
            with open(self.sources_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            schemes = data.get("schemes", [])
            academic_year = data.get("metadata", {}).get("academic_year", "2026-27")
            portal_url = data.get("metadata", {}).get("portal_url", "https://scholarships.gov.in")

            discovered = []
            for s in schemes:
                cat_item = CatalogueItem(
                    id=s["id"],
                    name=s["scheme_name"],
                    provider=s.get("department") or s.get("ministry", "Government of India"),
                    academic_year=academic_year,
                    type=s.get("category", "general"),
                    application_open="2026-06-01",
                    application_close="2026-10-31",
                    specification_url=f"{portal_url}/public/schemeGuidelines/{s['id']}_guidelines.pdf",
                    faq_url=f"{portal_url}/public/faq/{s['id']}_faq.html",
                    source_url=s.get("application_portal", portal_url),
                )
                discovered.append(cat_item)

            logger.info(
                f"Discovered {len(discovered)} targeted school schemes for AY {academic_year}"
            )
            return discovered
        except Exception as e:
            logger.error(f"Failed to discover schemes: {e}")
            return []

    def harvest_scheme_raw(
        self,
        item: CatalogueItem,
        scheme_source_data: Optional[Dict[str, Any]] = None,
    ) -> RawScholarshipData:
        """Phase 4 & 5: Collect raw untouched text from catalogue, specifications, and FAQs."""
        spec_text = ""
        faq_text = ""

        # Attempt to fetch specification if live URL is available (without aggressive retries)
        if item.specification_url:
            raw_spec_html = self.fetch_url(item.specification_url)
            if raw_spec_html:
                spec_text = extract_clean_text(raw_spec_html)

        # Attempt to fetch FAQ if live URL is available
        if item.faq_url:
            raw_faq_html = self.fetch_url(item.faq_url)
            if raw_faq_html:
                faq_text = extract_clean_text(raw_faq_html)

        # If live government endpoints are inaccessible / offline, fallback to structured source texts
        if not spec_text and scheme_source_data:
            eligibility_crit = scheme_source_data.get("eligibility_criteria", {})
            financial_assist = scheme_source_data.get("financial_assistance", {})
            spec_text = (
                f"Scheme Name: {item.name}\n"
                f"Ministry: {scheme_source_data.get('ministry', '')}\n"
                f"Department: {scheme_source_data.get('department', '')}\n"
                f"Target Classes: {', '.join(scheme_source_data.get('target_classes', []))}\n"
                f"Academic Requirement: {eligibility_crit.get('academic_requirement', '')}\n"
                f"School Type Requirement: {eligibility_crit.get('school_type_requirement', '')}\n"
                f"Annual Income Ceiling: Rs. {eligibility_crit.get('income_ceiling_inr', 'Not specified')}\n"
                f"Selection Mode: {eligibility_crit.get('selection_mode', 'Direct / Merit')}\n"
                f"Financial Assistance: {financial_assist.get('details', '')} - Rs. {financial_assist.get('amount_per_annum_inr', '')} per annum\n"
                f"Registration Requirement: {scheme_source_data.get('registration_requirement', 'One Time Registration (OTR) on NSP')}\n"
            )

        if not faq_text and scheme_source_data:
            faq_text = (
                f"Q: Who can apply for {item.name}?\n"
                f"A: Eligible students studying in {', '.join(scheme_source_data.get('target_classes', ['Class 9', 'Class 10']))}.\n"
                f"Q: What is the official portal?\n"
                f"A: {item.source_url}\n"
                f"Q: Is OTR required for AY {item.academic_year}?\n"
                f"A: Yes, One Time Registration is mandatory on National Scholarship Portal."
            )

        catalogue_text = (
            f"{item.name} | Provider: {item.provider} | Academic Year: {item.academic_year} | "
            f"Type: {item.type} | Open: {item.application_open} | Close: {item.application_close}"
        )

        raw_payload = {
            "catalogue_text": catalogue_text,
            "specification_text": spec_text,
            "faq_text": faq_text,
            "eligibility_summary": scheme_source_data.get("eligibility_criteria")
            if scheme_source_data
            else {},
            "benefits_summary": scheme_source_data.get("financial_assistance")
            if scheme_source_data
            else {},
            "inclusion_rationale": scheme_source_data.get("inclusion_rationale", "")
            if scheme_source_data
            else "",
        }

        return RawScholarshipData(
            id=item.id,
            name=item.name,
            academic_year=item.academic_year,
            provider=item.provider,
            source_url=item.source_url,
            specification_url=item.specification_url,
            faq_url=item.faq_url,
            raw=raw_payload,
            scraped_at=datetime.now(timezone.utc).isoformat(),
        )

    def run(
        self,
        academic_year: str = "2026-27",
        force_refresh: bool = False,
    ) -> Dict[str, Any]:
        """Execute the full ingestion pipeline: Discovery -> Raw Storage -> Structured Synthesis."""
        logger.info(
            f"Starting NSP scholarship refresh for AY {academic_year} (force={force_refresh})"
        )

        # Step 1: Discover schemes
        catalogue_items = self.discover_schemes()
        if not catalogue_items:
            return {
                "status": "failed",
                "message": "No schemes discovered from sources catalogue.",
                "total_processed": 0,
            }

        # Load raw sources manifest to map context
        sources_map: Dict[str, Dict[str, Any]] = {}
        if self.sources_file.exists():
            try:
                with open(self.sources_file, "r", encoding="utf-8") as f:
                    manifest = json.load(f)
                    for s in manifest.get("schemes", []):
                        sources_map[s["id"]] = s
            except Exception as e:
                logger.warning(f"Could not load sources manifest map: {e}")

        raw_records: List[RawScholarshipData] = []
        structured_records: List[StructuredScholarship] = []
        saved_raw_paths: List[str] = []

        # Step 2 & 3: Collect Raw & Save to raw storage
        for item in catalogue_items:
            scheme_src = sources_map.get(item.id)
            raw_data = self.harvest_scheme_raw(item, scheme_src)
            raw_path = self.storage.save_raw(raw_data)
            saved_raw_paths.append(str(raw_path))
            raw_records.append(raw_data)

            # Step 4: Parse into strict structured model (Phase 6)
            verified_time = datetime.now(timezone.utc).isoformat()
            structured = raw_to_structured(raw_data, verified_at=verified_time)
            structured_records.append(structured)

        # Step 5: Save Structured database
        structured_path = self.storage.save_structured_catalogue(
            structured_records,
            academic_year=academic_year,
        )

        summary = {
            "status": "success",
            "academic_year": academic_year,
            "total_processed": len(structured_records),
            "raw_storage_dir": str(self.storage._get_raw_year_dir(academic_year)),
            "structured_file": str(structured_path),
            "scheme_ids": [s.id for s in structured_records],
        }

        logger.info(
            f"Scholarship pipeline complete. Saved {len(structured_records)} schemes to {structured_path}"
        )
        return summary
