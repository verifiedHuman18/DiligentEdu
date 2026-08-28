"""Scholarship Discovery and Ingestion Package."""

from backend.scholarships.eligibility import (
    build_rules_for_scholarship,
    evaluate_rule,
    evaluate_scholarship,
    generate_template_explanation,
    get_dynamic_questionnaire,
    match_scholarships,
    rank_matches,
)
from backend.scholarships.models import (
    CatalogueItem,
    EligibilityCriteria,
    EligibilityRule,
    EligibilityStatus,
    FinancialAssistance,
    MatchExplanation,
    MatchResult,
    MeritRequirements,
    OfficialLinks,
    QuestionDefinition,
    RawScholarshipData,
    ScholarshipMetadata,
    StructuredScholarship,
    StudentScholarshipProfile,
    compute_profile_signature,
    get_scholarship_primary_url,
    normalize_student_profile,
)
from backend.scholarships.parser import (
    extract_clean_text,
    parse_categories,
    parse_classes,
    parse_income_ceiling,
    raw_to_structured,
)
from backend.scholarships.qa import (
    ScholarshipQAEngine,
    ask_scholarship_question,
)
from backend.scholarships.scraper import NSPCatalogueScraper
from backend.scholarships.search import (
    ScholarshipSearchEngine,
    search_scholarships,
)
from backend.scholarships.service import (
    ask_question,
    get_available_scholarships,
    get_scholarship,
    get_scholarship_detail_view,
    get_scholarship_explanation,
    list_available_academic_years,
    refresh_scholarships,
)
from backend.scholarships.storage import ScholarshipStorage

__all__ = [
    # Models
    "CatalogueItem",
    "EligibilityCriteria",
    "EligibilityRule",
    "EligibilityStatus",
    "FinancialAssistance",
    "MatchExplanation",
    "MatchResult",
    "MeritRequirements",
    "OfficialLinks",
    "QuestionDefinition",
    "RawScholarshipData",
    "ScholarshipMetadata",
    "StructuredScholarship",
    "StudentScholarshipProfile",
    "compute_profile_signature",
    "get_scholarship_primary_url",
    "normalize_student_profile",
    # Core Scraper & Storage
    "NSPCatalogueScraper",
    "ScholarshipStorage",
    # Parser Utilities
    "extract_clean_text",
    "parse_classes",
    "parse_income_ceiling",
    "parse_categories",
    "raw_to_structured",
    # Eligibility & Rules
    "build_rules_for_scholarship",
    "evaluate_rule",
    "evaluate_scholarship",
    "generate_template_explanation",
    "get_dynamic_questionnaire",
    "match_scholarships",
    "rank_matches",
    # Search Engine (Phases 3 & 4)
    "ScholarshipSearchEngine",
    "search_scholarships",
    # Q&A Engine (Phases 5 - 12)
    "ScholarshipQAEngine",
    "ask_scholarship_question",
    # Service Layer (Phases 15, 19)
    "ask_question",
    "get_available_scholarships",
    "get_scholarship",
    "get_scholarship_detail_view",
    "get_scholarship_explanation",
    "refresh_scholarships",
    "list_available_academic_years",
]
