"""Scholarship Field-Level Search Engine (Phases 3 & 4).

Enables deterministic, zero-LLM keyword and field-level searching across:
- Name and Provider
- Description & Scheme Type
- Eligibility (Classes, Categories, Gender, Disability)
- Income criteria & ceilings
- Benefits & financial assistance
- Document requirements
- Selection and Examination criteria
- Application timelines and dates
"""

import logging
import re
from typing import Dict, List, Optional

from backend.scholarships.models import StructuredScholarship
from backend.scholarships.storage import ScholarshipStorage

logger = logging.getLogger(__name__)


class ScholarshipSearchEngine:
    """Field-level search engine for locally cached scholarships."""

    def __init__(self, storage: Optional[ScholarshipStorage] = None) -> None:
        self.storage = storage or ScholarshipStorage()

    def _get_scheme_search_document(self, s: StructuredScholarship) -> Dict[str, str]:
        """Construct field-specific text representations for a scholarship."""
        classes_str = " ".join([f"class {c} grade {c} {c}th" for c in s.eligibility.classes])
        cats_str = " ".join(s.eligibility.categories)
        income_str = (
            f"income ceiling ₹{s.eligibility.income_max:,} limit {s.eligibility.income_max}"
            if s.eligibility.income_max
            else "no income limit"
        )
        benefit_str = (
            f"financial assistance ₹{s.financial_assistance.amount_per_annum:,} {s.financial_assistance.disbursement_frequency} {s.financial_assistance.details}"
            if s.financial_assistance
            else ""
        )
        merit_str = (
            f"merit {s.merit_requirements.min_percentage}% exam {s.merit_requirements.details}"
            if s.merit_requirements.required
            else "direct admission"
        )
        inst_str = " ".join(s.institution_requirements)

        # Standard document requirements based on scheme type
        docs = [
            "Aadhaar",
            "One Time Registration (OTR)",
            "Previous Year Marksheet",
            "Bank Account Details (Aadhaar linked)",
        ]
        if s.eligibility.income_max:
            docs.append("Income Certificate (Tehsildar/Revenue Authority)")
        if s.eligibility.categories:
            docs.append("Caste / Community Certificate")
        if s.eligibility.disability != "ANY":
            docs.append("Disability Certificate / UDID Card (≥40% disability)")
        if "beedi" in s.id or "mine" in s.id:
            docs.append("Worker Identity Card / Mine Welfare Passbook")
        if "hazardous" in s.id:
            docs.append("Occupational Certificate from Local Body / Municipal Authority")

        docs_str = " ".join(docs)
        dates_str = "01 June 2026 to 31 August 2026 opening June closing August deadline"

        return {
            "all": f"{s.name} {s.provider} {s.scheme_type} {classes_str} {cats_str} {income_str} {benefit_str} {merit_str} {inst_str} {docs_str} {dates_str}".lower(),
            "name": s.name.lower(),
            "provider": s.provider.lower(),
            "income": income_str.lower(),
            "class": classes_str.lower(),
            "category": cats_str.lower(),
            "benefits": benefit_str.lower(),
            "documents": docs_str.lower(),
            "selection": merit_str.lower(),
            "institution": inst_str.lower(),
            "dates": dates_str.lower(),
        }

    def search(
        self,
        query: str,
        class_level: Optional[int] = None,
        field: Optional[str] = None,
        academic_year: str = "2026-27",
    ) -> List[StructuredScholarship]:
        """Search scholarships across all fields or a targeted field."""
        all_schemes = self.storage.load_structured_catalogue(academic_year=academic_year)
        if not query and class_level is None:
            return all_schemes

        query_tokens = [t.strip().lower() for t in re.split(r"\s+", query) if len(t.strip()) > 1]
        results: List[StructuredScholarship] = []

        for s in all_schemes:
            # Class filter if specified
            if class_level is not None and s.eligibility.classes:
                if class_level not in s.eligibility.classes:
                    continue

            if not query_tokens:
                results.append(s)
                continue

            doc_fields = self._get_scheme_search_document(s)
            target_text = (
                doc_fields.get(field.lower(), doc_fields["all"]) if field else doc_fields["all"]
            )

            # Match tokens
            score = 0
            for token in query_tokens:
                if token in target_text:
                    score += 1
                if token in doc_fields["name"]:
                    score += 2  # Higher weight for name match

            if score > 0:
                results.append(s)

        return results

    def find_scheme_by_alias(
        self,
        text: str,
        academic_year: str = "2026-27",
    ) -> Optional[StructuredScholarship]:
        """Resolve common scheme abbreviations and titles to a single StructuredScholarship."""
        normalized = text.lower().strip()
        all_schemes = self.storage.load_structured_catalogue(academic_year=academic_year)

        # Direct ID or alias matching
        alias_map = {
            "nmmss": "nmmss",
            "nmms": "nmmss",
            "means cum merit": "nmmss",
            "national means": "nmmss",
            "yasasvi": "pm-yasasvi-pre-matric",
            "pm-yasasvi": "pm-yasasvi-pre-matric",
            "pm yasasvi": "pm-yasasvi-pre-matric",
            "top class": "pm-yasasvi-top-class-schools",
            "top class school": "pm-yasasvi-top-class-schools",
            "disabilit": "pre-matric-disabilities",
            "pwd": "pre-matric-disabilities",
            "handicap": "pre-matric-disabilities",
            "divyang": "pre-matric-disabilities",
            "sc scholarship": "pre-matric-sc",
            "scheduled caste": "pre-matric-sc",
            "st scholarship": "pre-matric-st",
            "scheduled tribe": "pre-matric-st",
            "tribal": "pre-matric-st",
            "minority": "pre-matric-minorities",
            "minorities": "pre-matric-minorities",
            "muslim": "pre-matric-minorities",
            "beedi": "pre-matric-beedi-cine-workers",
            "cine": "pre-matric-beedi-cine-workers",
            "mine worker": "pre-matric-beedi-cine-workers",
            "hazardous": "pre-matric-hazardous-occupations",
            "sanitation": "pre-matric-hazardous-occupations",
            "scavenger": "pre-matric-hazardous-occupations",
        }

        for alias, scheme_id in alias_map.items():
            if alias in normalized:
                for s in all_schemes:
                    if s.id == scheme_id:
                        return s

        # Substring in scheme name
        for s in all_schemes:
            if s.id in normalized or s.name.lower() in normalized:
                return s

        return None


# Helper instance function
_default_search_engine = ScholarshipSearchEngine()


def search_scholarships(
    query: str,
    class_level: Optional[int] = None,
    field: Optional[str] = None,
    academic_year: str = "2026-27",
    engine: Optional[ScholarshipSearchEngine] = None,
) -> List[StructuredScholarship]:
    """Public helper for searching scholarships."""
    searcher = engine or _default_search_engine
    return searcher.search(
        query=query,
        class_level=class_level,
        field=field,
        academic_year=academic_year,
    )
