"""Admin script to trigger manual NSP scholarship refresh and build local databases."""

import json
import logging
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.scholarships.scraper import NSPCatalogueScraper
from backend.scholarships.storage import ScholarshipStorage

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


def main() -> None:
    print("=" * 60)
    print("NSP Scholarship Scraper & Local Storage Ingestion")
    print("Target: School Students (Classes 9 & 10) | AY: 2026-27")
    print("=" * 60)

    storage = ScholarshipStorage()
    scraper = NSPCatalogueScraper(storage=storage)

    result = scraper.run(academic_year="2026-27", force_refresh=True)

    print("\nExecution Summary:")
    print(json.dumps(result, indent=2))

    # Verify structured loading
    loaded = storage.load_structured_catalogue("2026-27")
    print(f"\nSuccessfully verified {len(loaded)} structured scholarships in local cache:")
    for s in loaded:
        inc = (
            f"<= Rs. {s.eligibility.income_max:,}" if s.eligibility.income_max else "No income cap"
        )
        print(f" - [{s.id}] {s.name} | Classes: {s.eligibility.classes} | Income: {inc}")


if __name__ == "__main__":
    main()
