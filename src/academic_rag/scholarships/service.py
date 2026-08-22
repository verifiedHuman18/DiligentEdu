"""Scholarship Discovery Service Layer (Phase 15 & 19).

Provides a clean, unified interface for frontend and backend consumers.
Encapsulates all scraping, local caching, deterministic matching, ranking,
and detail page synthesis.
"""

import logging
from typing import Any, Dict, List, Optional, Union

from src.academic_rag.scholarships.eligibility import (
    evaluate_scholarship,
    match_scholarships as run_match_scholarships,
)
from src.academic_rag.scholarships.models import (
    EligibilityStatus,
    MatchExplanation,
    MatchResult,
    StructuredScholarship,
    StudentScholarshipProfile,
    get_scholarship_primary_url,
)
from src.academic_rag.scholarships.scraper import NSPCatalogueScraper
from src.academic_rag.scholarships.storage import ScholarshipStorage

from src.academic_rag.scholarships.qa import ask_scholarship_question as run_ask_question
from src.academic_rag.scholarships.search import search_scholarships as run_search_scholarships

logger = logging.getLogger(__name__)

# Shared default storage instance
_default_storage = ScholarshipStorage()


def search_scholarships(
    query: str,
    class_level: Optional[int] = None,
    field: Optional[str] = None,
    academic_year: str = "2026-27",
    storage: Optional[ScholarshipStorage] = None,
) -> List[StructuredScholarship]:
    """Search scholarships across fields."""
    store = storage or _default_storage
    from src.academic_rag.scholarships.search import ScholarshipSearchEngine
    engine = ScholarshipSearchEngine(storage=store)
    return run_search_scholarships(
        query=query,
        class_level=class_level,
        field=field,
        academic_year=academic_year,
        engine=engine,
    )


def ask_question(
    question: str,
    student_profile: Optional[Union[StudentScholarshipProfile, Dict[str, Any]]] = None,
    current_scheme_id: Optional[str] = None,
    academic_year: str = "2026-27",
    storage: Optional[ScholarshipStorage] = None,
) -> Dict[str, Any]:
    """Ask a question about scholarships."""
    store = storage or _default_storage
    from src.academic_rag.scholarships.qa import ScholarshipQAEngine
    engine = ScholarshipQAEngine(storage=store)
    return run_ask_question(
        question=question,
        student_profile=student_profile,
        current_scheme_id=current_scheme_id,
        academic_year=academic_year,
        engine=engine,
    )


def get_available_scholarships(
    academic_year: str = "2026-27",
    storage: Optional[ScholarshipStorage] = None,
) -> List[StructuredScholarship]:
    """Retrieve all structured scholarships available in the local database for a given academic year."""
    store = storage or _default_storage
    schemes = store.load_structured_catalogue(academic_year=academic_year)
    if not schemes:
        logger.info(f"No schemes found in cache for {academic_year}. Refreshing from catalogue...")
        refresh_scholarships(academic_year=academic_year, storage=store)
        schemes = store.load_structured_catalogue(academic_year=academic_year)
    return schemes


def get_scholarship(
    scholarship_id: str,
    academic_year: str = "2026-27",
    storage: Optional[ScholarshipStorage] = None,
) -> Optional[StructuredScholarship]:
    """Retrieve a single scholarship by ID."""
    store = storage or _default_storage
    return store.get_scholarship_by_id(scholarship_id, academic_year=academic_year)


def match_scholarships(
    student_profile: Union[StudentScholarshipProfile, Dict[str, Any]],
    scholarships: Optional[List[StructuredScholarship]] = None,
    academic_year: str = "2026-27",
    storage: Optional[ScholarshipStorage] = None,
) -> List[MatchResult]:
    """Match and rank all scholarships for a given student profile against the local database."""
    store = storage or _default_storage
    return run_match_scholarships(
        student_profile=student_profile,
        scholarships=scholarships,
        academic_year=academic_year,
        storage=store,
    )


def get_scholarship_explanation(
    scholarship_id: str,
    student_profile: Union[StudentScholarshipProfile, Dict[str, Any]],
    academic_year: str = "2026-27",
    storage: Optional[ScholarshipStorage] = None,
) -> Optional[MatchExplanation]:
    """Generate deterministic template-based explanation for why a specific scholarship matches or fails."""
    scheme = get_scholarship(scholarship_id, academic_year=academic_year, storage=storage)
    if not scheme:
        return None

    if isinstance(student_profile, dict):
        profile = StudentScholarshipProfile.from_dict(student_profile)
    else:
        profile = student_profile

    result = evaluate_scholarship(scheme, profile)
    return result.explanation


def get_scholarship_detail_view(
    scholarship_id: str,
    student_profile: Optional[Union[StudentScholarshipProfile, Dict[str, Any]]] = None,
    academic_year: str = "2026-27",
    storage: Optional[ScholarshipStorage] = None,
) -> Optional[Dict[str, Any]]:
    """Phase 15: Generate a structured detail view card for a scholarship.

    Includes:
    - Scholarship Name, Provider, Academic Year
    - Why it matches (Class, Income, Category)
    - Potentially required / verification needed
    - Application window
    - Official sources (Specifications, FAQ, Guidelines)
    - Direct portal CTA (Apply on Official Portal)
    """
    scheme = get_scholarship(scholarship_id, academic_year=academic_year, storage=storage)
    if not scheme:
        return None

    why_it_matches = []
    potentially_required = []
    match_status = "unverified"
    status_icon = "ℹ️"

    if student_profile:
        if isinstance(student_profile, dict):
            profile = StudentScholarshipProfile.from_dict(student_profile)
        else:
            profile = student_profile

        match_res = evaluate_scholarship(scheme, profile)
        match_status = match_res.status
        status_icon = match_res.status_icon
        why_it_matches = match_res.explanation.reasons_matched
        potentially_required = match_res.explanation.verification_needed

    # If no profile was provided or matched list is empty, construct general criteria bullets
    if not why_it_matches:
        if scheme.eligibility.classes:
            why_it_matches.append(f"✓ Target Classes: {', '.join([f'Class {c}' for c in scheme.eligibility.classes])}")
        if scheme.eligibility.income_max:
            why_it_matches.append(f"✓ Income Ceiling: Annual family income ≤ ₹{scheme.eligibility.income_max:,}")
        if scheme.eligibility.categories:
            why_it_matches.append(f"✓ Eligible Categories: {', '.join(scheme.eligibility.categories)}")
        else:
            why_it_matches.append("✓ Open to students of all categories (General, OBC, SC, ST, Minorities)")

    if not potentially_required:
        if scheme.merit_requirements.required:
            potentially_required.append(
                f"⚠ Academic requirement: {scheme.merit_requirements.details or 'Merit progression/exam'}"
            )
        if scheme.institution_requirements:
            potentially_required.append(
                f"⚠ Institution requirement: Must study in a recognized {', '.join(scheme.institution_requirements)} school"
            )
        potentially_required.append("⚠ Valid One Time Registration (OTR) on National Scholarship Portal")

    # Application window definition for AY 2026-27
    application_window = "01 Jun 2026 – 31 Aug 2026"

    # Source Integrity check: Guarantee official source URL exists
    source_url = scheme.official.source_url or "https://scholarships.gov.in"
    spec_url = scheme.official.specification_url or f"https://scholarships.gov.in/public/schemeGuidelines/{scheme.id}_guidelines.pdf"
    faq_url = scheme.official.faq_url or f"https://scholarships.gov.in/public/faq/{scheme.id}_faq.html"

    return {
        "id": scheme.id,
        "name": scheme.name,
        "provider": scheme.provider,
        "academic_year": scheme.academic_year,
        "status": match_status,
        "status_icon": status_icon,
        "amount_per_annum": scheme.financial_assistance.amount_per_annum if scheme.financial_assistance else None,
        "disbursement_frequency": scheme.financial_assistance.disbursement_frequency if scheme.financial_assistance else "Annual",
        "why_it_matches": why_it_matches,
        "potentially_required": potentially_required,
        "application_window": application_window,
        "official_sources": {
            "source_url": source_url,
            "specification_url": spec_url,
            "faq_url": faq_url,
            "guidelines_url": scheme.official.guidelines_url,
            "portal_name": "National Scholarship Portal (scholarships.gov.in)",
        },
        "cta": {
            "label": "Apply on Official Portal",
            "url": source_url,
            "notice": "Official applications and document verification are processed strictly on scholarships.gov.in.",
        },
        "metadata": {
            "scraped_at": scheme.metadata.scraped_at,
            "verified_at": scheme.metadata.verified_at,
            "version": scheme.metadata.version,
        },
    }


def refresh_scholarships(
    academic_year: str = "2026-27",
    force: bool = False,
    storage: Optional[ScholarshipStorage] = None,
) -> Dict[str, Any]:
    """Phase 16: Trigger refresh and versioning for a specified academic year."""
    store = storage or _default_storage
    scraper = NSPCatalogueScraper(storage=store)
    return scraper.run(academic_year=academic_year, force_refresh=force)


def list_available_academic_years(storage: Optional[ScholarshipStorage] = None) -> List[str]:
    """Phase 16: List all loaded academic years."""
    store = storage or _default_storage
    return store.list_available_years()
