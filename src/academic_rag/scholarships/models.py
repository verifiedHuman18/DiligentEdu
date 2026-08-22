"""Data models for Scholarship Scraper and Storage."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union


@dataclass
class CatalogueItem:
    """Discovered scholarship item from the NSP catalogue."""

    id: str
    name: str
    provider: str
    academic_year: str = "2026-27"
    type: str = "general"
    application_open: Optional[str] = None
    application_close: Optional[str] = None
    specification_url: Optional[str] = None
    faq_url: Optional[str] = None
    source_url: str = "https://scholarships.gov.in/All-Scholarships"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "provider": self.provider,
            "academic_year": self.academic_year,
            "type": self.type,
            "application_open": self.application_open,
            "application_close": self.application_close,
            "specification_url": self.specification_url,
            "faq_url": self.faq_url,
            "source_url": self.source_url,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CatalogueItem":
        return cls(
            id=data["id"],
            name=data["name"],
            provider=data.get("provider", "Unknown Provider"),
            academic_year=data.get("academic_year", "2026-27"),
            type=data.get("type", "general"),
            application_open=data.get("application_open"),
            application_close=data.get("application_close"),
            specification_url=data.get("specification_url"),
            faq_url=data.get("faq_url"),
            source_url=data.get("source_url", "https://scholarships.gov.in/All-Scholarships"),
        )


@dataclass
class RawScholarshipData:
    """Raw scraped record preserving untouched text from NSP catalogue, specifications, and FAQs."""

    id: str
    name: str
    source_url: str
    specification_url: Optional[str] = None
    faq_url: Optional[str] = None
    academic_year: str = "2026-27"
    provider: Optional[str] = None
    raw: Dict[str, Any] = field(default_factory=dict)
    scraped_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "academic_year": self.academic_year,
            "provider": self.provider,
            "source_url": self.source_url,
            "specification_url": self.specification_url,
            "faq_url": self.faq_url,
            "raw": self.raw,
            "scraped_at": self.scraped_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RawScholarshipData":
        return cls(
            id=data["id"],
            name=data["name"],
            academic_year=data.get("academic_year", "2026-27"),
            provider=data.get("provider"),
            source_url=data.get("source_url", "https://scholarships.gov.in/All-Scholarships"),
            specification_url=data.get("specification_url"),
            faq_url=data.get("faq_url"),
            raw=data.get("raw", {}),
            scraped_at=data.get("scraped_at", datetime.now(timezone.utc).isoformat()),
        )


@dataclass
class EligibilityCriteria:
    """Structured eligibility constraints."""

    classes: List[int] = field(default_factory=lambda: [9, 10])
    states: List[str] = field(default_factory=lambda: ["ALL"])
    categories: List[str] = field(default_factory=list)
    income_max: Optional[int] = None
    gender: str = "ANY"
    disability: str = "ANY"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "classes": self.classes,
            "states": self.states,
            "categories": self.categories,
            "income_max": self.income_max,
            "gender": self.gender,
            "disability": self.disability,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EligibilityCriteria":
        return cls(
            classes=data.get("classes", [9, 10]),
            states=data.get("states", ["ALL"]),
            categories=data.get("categories", []),
            income_max=data.get("income_max"),
            gender=data.get("gender", "ANY"),
            disability=data.get("disability", "ANY"),
        )


@dataclass
class MeritRequirements:
    """Merit or examination prerequisites."""

    required: bool = False
    min_percentage: Optional[float] = None
    exam_required: bool = False
    details: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "required": self.required,
            "min_percentage": self.min_percentage,
            "exam_required": self.exam_required,
            "details": self.details,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MeritRequirements":
        return cls(
            required=data.get("required", False),
            min_percentage=data.get("min_percentage"),
            exam_required=data.get("exam_required", False),
            details=data.get("details"),
        )


@dataclass
class FinancialAssistance:
    """Structured financial benefit details."""

    amount_per_annum: Optional[int] = None
    disbursement_frequency: Optional[str] = None
    details: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "amount_per_annum": self.amount_per_annum,
            "disbursement_frequency": self.disbursement_frequency,
            "details": self.details,
        }

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> Optional["FinancialAssistance"]:
        if not data:
            return None
        return cls(
            amount_per_annum=data.get("amount_per_annum"),
            disbursement_frequency=data.get("disbursement_frequency"),
            details=data.get("details"),
        )


@dataclass
class OfficialLinks:
    """Official portals, specification, and FAQ links."""

    primary_url: Optional[str] = None
    source_url: str = "https://scholarships.gov.in/All-Scholarships"
    specification_url: Optional[str] = None
    faq_url: Optional[str] = None
    guidelines_url: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "primary_url": self.primary_url,
            "source_url": self.source_url,
            "specification_url": self.specification_url,
            "faq_url": self.faq_url,
            "guidelines_url": self.guidelines_url,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OfficialLinks":
        return cls(
            primary_url=data.get("primary_url"),
            source_url=data.get("source_url", "https://scholarships.gov.in/All-Scholarships"),
            specification_url=data.get("specification_url"),
            faq_url=data.get("faq_url"),
            guidelines_url=data.get("guidelines_url"),
        )


def get_scholarship_primary_url(item: Any) -> Optional[str]:
    """Phase 3 & 6: Resolve the exact canonical official URL for a scholarship or match result.

    Priority:
    1. Exact official scheme page / primary_url
    2. Official scheme specification URL (PDF / guidelines)
    3. Official FAQ URL
    4. General official portal source URL (as final fallback)
    """
    if item is None:
        return None

    raw_candidates = []

    # Case 1: StructuredScholarship or CatalogueItem object
    if hasattr(item, "official") and getattr(item, "official"):
        off = item.official
        if isinstance(off, dict):
            raw_candidates = [
                off.get("primary_url"),
                off.get("specification_url"),
                off.get("guidelines_url"),
                off.get("faq_url"),
                off.get("source_url"),
            ]
        else:
            raw_candidates = [
                getattr(off, "primary_url", None),
                getattr(off, "specification_url", None),
                getattr(off, "guidelines_url", None),
                getattr(off, "faq_url", None),
                getattr(off, "source_url", None),
            ]

    # Case 2: MatchResult object
    elif hasattr(item, "specification_url") or hasattr(item, "official_source_url"):
        raw_candidates = [
            getattr(item, "primary_url", None),
            getattr(item, "specification_url", None),
            getattr(item, "faq_url", None),
            getattr(item, "official_source_url", None),
        ]

    # Case 3: Dictionary
    elif isinstance(item, dict):
        official = item.get("official")
        if isinstance(official, dict):
            raw_candidates = [
                official.get("primary_url"),
                official.get("specification_url"),
                official.get("guidelines_url"),
                official.get("faq_url"),
                official.get("source_url"),
            ]
        else:
            raw_candidates = [
                item.get("primary_url"),
                item.get("specification_url"),
                item.get("guidelines_url"),
                item.get("faq_url"),
                item.get("official_source_url"),
                item.get("source_url"),
            ]

    for candidate in raw_candidates:
        if candidate and isinstance(candidate, str):
            clean = candidate.strip()
            # Phase 9: Validate URL format (avoid empty, hash, javascript, about:blank)
            if (
                clean
                and not clean.startswith("#")
                and not clean.startswith("javascript:")
                and not clean.startswith("about:")
            ):
                if clean.startswith("http://") or clean.startswith("https://"):
                    return clean

    return None


@dataclass
class ScholarshipMetadata:
    """Provenance and verification timestamps."""

    scraped_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    verified_at: Optional[str] = None
    source: str = "National Scholarship Portal"
    version: str = "1.0.0"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scraped_at": self.scraped_at,
            "verified_at": self.verified_at,
            "source": self.source,
            "version": self.version,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ScholarshipMetadata":
        return cls(
            scraped_at=data.get("scraped_at", datetime.now(timezone.utc).isoformat()),
            verified_at=data.get("verified_at"),
            source=data.get("source", "National Scholarship Portal"),
            version=data.get("version", "1.0.0"),
        )


@dataclass
class StructuredScholarship:
    """Complete structured scholarship record for local discovery and deterministic filtering."""

    id: str
    name: str
    academic_year: str = "2026-27"
    provider: str = "Government of India"
    scheme_type: str = "general"
    eligibility: EligibilityCriteria = field(default_factory=EligibilityCriteria)
    merit_requirements: MeritRequirements = field(default_factory=MeritRequirements)
    institution_requirements: List[str] = field(default_factory=list)
    financial_assistance: Optional[FinancialAssistance] = None
    official: OfficialLinks = field(default_factory=OfficialLinks)
    metadata: ScholarshipMetadata = field(default_factory=ScholarshipMetadata)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "academic_year": self.academic_year,
            "provider": self.provider,
            "scheme_type": self.scheme_type,
            "eligibility": self.eligibility.to_dict(),
            "merit_requirements": self.merit_requirements.to_dict(),
            "institution_requirements": self.institution_requirements,
            "financial_assistance": self.financial_assistance.to_dict()
            if self.financial_assistance
            else None,
            "official": self.official.to_dict(),
            "metadata": self.metadata.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StructuredScholarship":
        return cls(
            id=data["id"],
            name=data["name"],
            academic_year=data.get("academic_year", "2026-27"),
            provider=data.get("provider", "Government of India"),
            scheme_type=data.get("scheme_type", "general"),
            eligibility=EligibilityCriteria.from_dict(data.get("eligibility", {})),
            merit_requirements=MeritRequirements.from_dict(data.get("merit_requirements", {})),
            institution_requirements=data.get("institution_requirements", []),
            financial_assistance=FinancialAssistance.from_dict(data.get("financial_assistance")),
            official=OfficialLinks.from_dict(data.get("official", {})),
            metadata=ScholarshipMetadata.from_dict(data.get("metadata", {})),
        )


class EligibilityStatus:
    """Three discrete eligibility states."""

    LIKELY_MATCH = "likely_match"  # 🟢 All known required conditions match
    POSSIBLE_MATCH = (
        "possible_match"  # 🟡 Some conditions match, but some are unknown or need verification
    )
    DOES_NOT_MATCH = "does_not_match"  # 🔴 A known mandatory condition clearly fails


@dataclass
class StudentScholarshipProfile:
    """Safe, non-sensitive student profile for scholarship discovery.

    PRIVACY GUARANTEE:
    This profile strictly avoids collecting sensitive government identifiers
    (No Aadhaar, No OTR ID, No bank account details, No passwords/OTPs).
    """

    class_level: Optional[int] = None
    state: Optional[str] = "ALL"
    family_income: Optional[int] = None
    category: Optional[str] = None  # e.g., "General", "OBC", "SC", "ST", "EBC", "DNT", "Minorities"
    gender: Optional[str] = None  # e.g., "Male", "Female", "Other", "Any"
    disability_status: Optional[bool] = None
    school_type: Optional[str] = (
        None  # e.g., "Government", "Government-aided", "Local Body", "Top Class Schools", "Recognized Private"
    )
    academic_score: Optional[float] = None  # Previous class percentage
    occupational_background: Optional[str] = (
        None  # e.g., "Beedi Worker", "Cine Worker", "Mine Worker", "Sanitation / Waste Picker", "General"
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "class_level": self.class_level,
            "state": self.state,
            "family_income": self.family_income,
            "category": self.category,
            "gender": self.gender,
            "disability_status": self.disability_status,
            "school_type": self.school_type,
            "academic_score": self.academic_score,
            "occupational_background": self.occupational_background,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StudentScholarshipProfile":
        return cls(
            class_level=data.get("class_level"),
            state=data.get("state", "ALL"),
            family_income=data.get("family_income"),
            category=data.get("category"),
            gender=data.get("gender"),
            disability_status=data.get("disability_status"),
            school_type=data.get("school_type"),
            academic_score=data.get("academic_score"),
            occupational_background=data.get("occupational_background"),
        )


def normalize_student_profile(
    raw_data: Optional[Union[Dict[str, Any], "StudentScholarshipProfile"]] = None,
    default_class_level: Optional[int] = None,
) -> "StudentScholarshipProfile":
    """Phase 4 & Phase 2: Normalize and validate raw UI/API inputs into a canonical StudentScholarshipProfile.

    Conversions handled:
    - class_level: 'Class 10' -> 10, '9' -> 9, int -> int (strictly 9 or 10)
    - family_income: '₹1.5 Lakh' -> 150000, '250000' -> 250000, 250000.0 -> 250000, None -> None
    - category: 'Minorities (Muslim/Christian...)' -> 'Minorities', 'OBC' -> 'OBC', etc.
    - disability_status: 'Yes' -> True, 'No' -> False, True -> True, False -> False
    - academic_score: '75.5%' -> 75.5, 75 -> 75.0
    - school_type: string trimming
    - occupational_background: string trimming
    """
    import re

    if raw_data is None:
        return StudentScholarshipProfile(class_level=default_class_level or 10)

    if isinstance(raw_data, StudentScholarshipProfile):
        cls_lvl = raw_data.class_level or default_class_level or 10
        return StudentScholarshipProfile(
            class_level=cls_lvl,
            state=raw_data.state or "ALL",
            family_income=raw_data.family_income,
            category=raw_data.category,
            gender=raw_data.gender,
            disability_status=raw_data.disability_status,
            school_type=raw_data.school_type,
            academic_score=raw_data.academic_score,
            occupational_background=raw_data.occupational_background,
        )

    # Dictionary input normalization
    data = dict(raw_data)

    # 1. Class level
    raw_cls = (
        data.get("class_level")
        or data.get("selected_class")
        or data.get("class")
        or default_class_level
    )
    cls_int = 10
    if raw_cls is not None:
        if isinstance(raw_cls, int):
            cls_int = raw_cls
        elif isinstance(raw_cls, str):
            if "9" in raw_cls:
                cls_int = 9
            elif "10" in raw_cls:
                cls_int = 10

    # 2. Family income
    raw_inc = data.get("family_income") if "family_income" in data else data.get("income")
    inc_int: Optional[int] = None
    if raw_inc is not None and str(raw_inc).strip() != "":
        if isinstance(raw_inc, (int, float)):
            inc_int = int(raw_inc)
        elif isinstance(raw_inc, str):
            clean_str = raw_inc.replace("₹", "").replace(",", "").strip().lower()
            lakh_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:lakh|lac|lacs|lakhs)", clean_str)
            if lakh_match:
                inc_int = int(float(lakh_match.group(1)) * 100000)
            else:
                try:
                    inc_int = int(float(clean_str))
                except ValueError:
                    inc_int = None

    # 3. Category
    raw_cat = data.get("category")
    cat_str: Optional[str] = None
    if raw_cat is not None:
        raw_cat_str = str(raw_cat).strip()
        if "Minorities" in raw_cat_str or "Minority" in raw_cat_str:
            cat_str = "Minorities"
        elif "(" in raw_cat_str:
            cat_str = raw_cat_str.split("(")[0].strip()
        else:
            cat_str = raw_cat_str

    # 4. Disability status
    raw_dis = (
        data.get("disability_status") if "disability_status" in data else data.get("disability")
    )
    dis_bool: Optional[bool] = None
    if raw_dis is not None:
        if isinstance(raw_dis, bool):
            dis_bool = raw_dis
        elif isinstance(raw_dis, str):
            dis_bool = raw_dis.strip().lower() in ("yes", "true", "1", "required")

    # 5. Academic score
    raw_score = data.get("academic_score") if "academic_score" in data else data.get("score")
    score_float: Optional[float] = None
    if raw_score is not None and str(raw_score).strip() != "":
        if isinstance(raw_score, (int, float)):
            score_float = float(raw_score)
        elif isinstance(raw_score, str):
            try:
                score_float = float(raw_score.replace("%", "").strip())
            except ValueError:
                score_float = None

    # 6. School type
    raw_st = data.get("school_type")
    st_str = str(raw_st).strip() if raw_st else None

    # 7. Occupational background
    raw_occ = data.get("occupational_background") or data.get("occupation")
    occ_str = str(raw_occ).strip() if raw_occ else None

    return StudentScholarshipProfile(
        class_level=cls_int,
        state=str(data.get("state", "ALL")).strip(),
        family_income=inc_int,
        category=cat_str,
        gender=str(data.get("gender", "ANY")).strip() if data.get("gender") else None,
        disability_status=dis_bool,
        school_type=st_str,
        academic_score=score_float,
        occupational_background=occ_str,
    )


def compute_profile_signature(profile: StudentScholarshipProfile) -> str:
    """Phase 10: Compute a deterministic hash signature of a canonical student profile."""
    import hashlib
    import json

    data = {
        "class_level": profile.class_level,
        "state": profile.state or "ALL",
        "family_income": profile.family_income,
        "category": profile.category,
        "gender": profile.gender,
        "disability_status": profile.disability_status,
        "school_type": profile.school_type,
        "academic_score": profile.academic_score,
        "occupational_background": profile.occupational_background,
    }
    dumped = json.dumps(data, sort_keys=True)
    return hashlib.sha256(dumped.encode("utf-8")).hexdigest()


@dataclass
class EligibilityRule:
    """Generic eligibility rule representation."""

    field: str
    operator: str  # "in", "not_in", "<=", ">=", "==", "!=", "any_of", "boolean_eq"
    value: Any
    mandatory: bool = True
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "field": self.field,
            "operator": self.operator,
            "value": self.value,
            "mandatory": self.mandatory,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EligibilityRule":
        return cls(
            field=data["field"],
            operator=data["operator"],
            value=data["value"],
            mandatory=data.get("mandatory", True),
            description=data.get("description", ""),
        )


@dataclass
class MatchExplanation:
    """Deterministic, template-generated explanation of matching decisions."""

    summary: str
    reasons_matched: List[str] = field(default_factory=list)
    reasons_unmatched: List[str] = field(default_factory=list)
    verification_needed: List[str] = field(default_factory=list)
    action_guidance: str = (
        "Apply directly on the official portal (https://scholarships.gov.in) with valid OTR."
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "summary": self.summary,
            "reasons_matched": self.reasons_matched,
            "reasons_unmatched": self.reasons_unmatched,
            "verification_needed": self.verification_needed,
            "action_guidance": self.action_guidance,
        }


@dataclass
class MatchResult:
    """Result of evaluating a student profile against a single scholarship."""

    scholarship_id: str
    scholarship_name: str
    status: str  # "likely_match", "possible_match", "does_not_match"
    status_icon: str  # 🟢, 🟡, 🔴
    provider: str
    amount_per_annum: Optional[int]
    matched_rules: List[str]
    unmatched_rules: List[str]
    unknown_rules: List[str]
    score: float
    explanation: MatchExplanation
    official_source_url: str
    primary_url: Optional[str] = None
    specification_url: Optional[str] = None
    faq_url: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scholarship_id": self.scholarship_id,
            "scholarship_name": self.scholarship_name,
            "status": self.status,
            "status_icon": self.status_icon,
            "provider": self.provider,
            "amount_per_annum": self.amount_per_annum,
            "matched_rules": self.matched_rules,
            "unmatched_rules": self.unmatched_rules,
            "unknown_rules": self.unknown_rules,
            "score": self.score,
            "explanation": self.explanation.to_dict(),
            "official_source_url": self.official_source_url,
            "primary_url": self.primary_url,
            "specification_url": self.specification_url,
            "faq_url": self.faq_url,
        }


@dataclass
class QuestionDefinition:
    """Dynamic questionnaire item definition."""

    field_name: str
    label: str
    question_type: str  # "select", "number", "boolean", "text"
    options: List[str] = field(default_factory=list)
    help_text: str = ""
    priority: int = 1  # 1 = primary discovery, 2 = conditional refinement

    def to_dict(self) -> Dict[str, Any]:
        return {
            "field_name": self.field_name,
            "label": self.label,
            "question_type": self.question_type,
            "options": self.options,
            "help_text": self.help_text,
            "priority": self.priority,
        }
