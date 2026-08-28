"""Local storage manager for raw and structured scholarship databases."""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.config import config
from backend.scholarships.models import RawScholarshipData, StructuredScholarship

logger = logging.getLogger(__name__)


class ScholarshipStorage:
    """Manages offline-first persistent JSON storage for raw and structured scholarship data."""

    def __init__(
        self,
        base_dir: Optional[Path] = None,
        raw_dir: Optional[Path] = None,
        structured_dir: Optional[Path] = None,
    ) -> None:
        self.base_dir = base_dir or config.scholarships_data_dir
        self.raw_dir = raw_dir or config.scholarships_raw_dir
        self.structured_dir = structured_dir or config.scholarships_structured_dir

        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.structured_dir.mkdir(parents=True, exist_ok=True)

    def _get_raw_year_dir(self, academic_year: str) -> Path:
        sanitized_year = academic_year.replace("/", "-")
        # Support both data/scholarships/raw/{year} and data/scholarships/{year}/raw
        year_dir = self.raw_dir / sanitized_year
        year_dir.mkdir(parents=True, exist_ok=True)
        return year_dir

    def _get_structured_file_path(self, academic_year: str) -> Path:
        sanitized_year = academic_year.replace("/", "-")
        return self.structured_dir / f"{sanitized_year}.json"

    def list_available_years(self) -> List[str]:
        """List all versioned academic years available in local storage."""
        years = set()

        # Check structured directory
        if self.structured_dir.exists():
            for f in self.structured_dir.glob("*.json"):
                years.add(f.stem)

        # Check raw year directories
        if self.raw_dir.exists():
            for d in self.raw_dir.iterdir():
                if d.is_dir():
                    years.add(d.name)

        # Check root year directories
        if self.base_dir.exists():
            for d in self.base_dir.iterdir():
                if d.is_dir() and d.name not in ("raw", "structured"):
                    years.add(d.name)

        return sorted(list(years)) if years else ["2026-27"]

    def save_raw(self, raw_data: RawScholarshipData) -> Path:
        """Save an individual raw scholarship record into data/scholarships/raw/{academic_year}/{id}.json."""
        year_dir = self._get_raw_year_dir(raw_data.academic_year)
        file_path = year_dir / f"{raw_data.id}.json"

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(raw_data.to_dict(), f, indent=2, ensure_ascii=False)

        logger.debug(f"Saved raw scholarship to {file_path}")
        return file_path

    def load_raw(
        self, scheme_id: str, academic_year: str = "2026-27"
    ) -> Optional[RawScholarshipData]:
        """Load a single raw scholarship record by ID."""
        year_dir = self._get_raw_year_dir(academic_year)
        file_path = year_dir / f"{scheme_id}.json"

        if not file_path.exists():
            return None

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return RawScholarshipData.from_dict(data)
        except Exception as e:
            logger.error(f"Error loading raw scholarship {scheme_id}: {e}")
            return None

    def list_raw(self, academic_year: str = "2026-27") -> List[RawScholarshipData]:
        """List all raw scholarship records for the given academic year."""
        year_dir = self._get_raw_year_dir(academic_year)
        records = []

        for file_path in year_dir.glob("*.json"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                records.append(RawScholarshipData.from_dict(data))
            except Exception as e:
                logger.error(f"Error reading {file_path}: {e}")

        return records

    def save_structured_catalogue(
        self,
        scholarships: List[StructuredScholarship],
        academic_year: str = "2026-27",
    ) -> Path:
        """Save the structured scholarship database to data/scholarships/structured/{academic_year}.json."""
        file_path = self._get_structured_file_path(academic_year)

        payload: Dict[str, Any] = {
            "academic_year": academic_year,
            "total_count": len(scholarships),
            "source": "National Scholarship Portal",
            "scholarships": [s.to_dict() for s in scholarships],
        }

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved {len(scholarships)} structured scholarships to {file_path}")
        return file_path

    def load_structured_catalogue(
        self, academic_year: str = "2026-27"
    ) -> List[StructuredScholarship]:
        """Load structured scholarships from local database without making any external requests."""
        file_path = self._get_structured_file_path(academic_year)

        if not file_path.exists():
            logger.warning(f"Structured database not found at {file_path}")
            return []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            items = data.get("scholarships", [])
            return [StructuredScholarship.from_dict(item) for item in items]
        except Exception as e:
            logger.error(f"Error reading structured database {file_path}: {e}")
            return []

    def get_scholarship_by_id(
        self,
        scheme_id: str,
        academic_year: str = "2026-27",
    ) -> Optional[StructuredScholarship]:
        """Retrieve a specific structured scholarship by ID from local cache."""
        all_schemes = self.load_structured_catalogue(academic_year)
        for scheme in all_schemes:
            if scheme.id == scheme_id:
                return scheme
        return None

    def search_scholarships(
        self,
        query: Optional[str] = None,
        class_level: Optional[int] = None,
        annual_income: Optional[int] = None,
        category: Optional[str] = None,
        is_disabled: Optional[bool] = None,
        academic_year: str = "2026-27",
    ) -> List[StructuredScholarship]:
        """Deterministic local filtering over the structured database."""
        all_schemes = self.load_structured_catalogue(academic_year)
        results = []

        for s in all_schemes:
            # Filter by class
            if class_level is not None and s.eligibility.classes:
                if class_level not in s.eligibility.classes:
                    continue

            # Filter by annual family income
            if annual_income is not None and s.eligibility.income_max is not None:
                if annual_income > s.eligibility.income_max:
                    continue

            # Filter by category
            if category and s.eligibility.categories:
                cat_upper = category.strip().upper()
                scheme_cats = [c.upper() for c in s.eligibility.categories]
                if (
                    cat_upper not in scheme_cats
                    and "ALL" not in scheme_cats
                    and "GENERAL" not in scheme_cats
                ):
                    continue

            # Filter by disability
            if is_disabled is False and s.eligibility.disability in (
                "REQUIRED",
                "REQUIRED_MIN_40_PERCENT",
            ):
                continue

            # Text query matching
            if query:
                q = query.lower().strip()
                matched = (
                    q in s.name.lower()
                    or q in s.provider.lower()
                    or q in s.scheme_type.lower()
                    or (
                        s.financial_assistance
                        and s.financial_assistance.details
                        and q in s.financial_assistance.details.lower()
                    )
                )
                if not matched:
                    continue

            results.append(s)

        return results
