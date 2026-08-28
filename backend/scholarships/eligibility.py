"""Generic Eligibility Evaluation Engine, Ranking, and Dynamic Questionnaire for Scholarships.

Features:
- Generic rule engine (Phase 7): decoupled from hardcoded scheme logic.
- Eligibility Engine (Phase 8): evaluates profiles against generic rules.
- Three Eligibility States (Phase 9): 🟢 Likely Match, 🟡 Possible Match, 🔴 Does Not Match.
- Student Profile Handler (Phase 10): non-sensitive, discovery-only profile.
- Dynamic Questionnaire (Phase 11): queries only missing/relevant fields.
- Multi-tier Ranking (Phase 12): sorts by eligibility state and financial benefit.
- Template-based Explanation Generator (Phase 13): deterministic, transparent rationale without LLM hallucinations.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple, Union

from backend.scholarships.models import (
    EligibilityRule,
    EligibilityStatus,
    MatchExplanation,
    MatchResult,
    QuestionDefinition,
    StructuredScholarship,
    StudentScholarshipProfile,
)
from backend.scholarships.storage import ScholarshipStorage

logger = logging.getLogger(__name__)


def build_rules_for_scholarship(scholarship: StructuredScholarship) -> List[EligibilityRule]:
    """Phase 7: Translate structured scholarship metadata into generic, decoupled rules."""
    rules: List[EligibilityRule] = []

    # 1. Class Level Rule
    if scholarship.eligibility.classes:
        rules.append(
            EligibilityRule(
                field="class_level",
                operator="in",
                value=scholarship.eligibility.classes,
                mandatory=True,
                description=f"Must be enrolled in {', '.join([f'Class {c}' for c in scholarship.eligibility.classes])}",
            )
        )

    # 2. Family Income Rule
    if scholarship.eligibility.income_max is not None:
        rules.append(
            EligibilityRule(
                field="family_income",
                operator="<=",
                value=scholarship.eligibility.income_max,
                mandatory=True,
                description=f"Annual family income must not exceed ₹{scholarship.eligibility.income_max:,}",
            )
        )

    # 3. Social / Reservation Category Rule
    if scholarship.eligibility.categories:
        rules.append(
            EligibilityRule(
                field="category",
                operator="any_of",
                value=scholarship.eligibility.categories,
                mandatory=True,
                description=f"Eligible categories: {', '.join(scholarship.eligibility.categories)}",
            )
        )

    # 4. Gender Rule
    if scholarship.eligibility.gender and scholarship.eligibility.gender != "ANY":
        rules.append(
            EligibilityRule(
                field="gender",
                operator="==",
                value=scholarship.eligibility.gender,
                mandatory=True,
                description=f"Applicable for {scholarship.eligibility.gender} students only",
            )
        )

    # 5. Disability Status Rule
    if scholarship.eligibility.disability in ("REQUIRED", "REQUIRED_MIN_40_PERCENT"):
        rules.append(
            EligibilityRule(
                field="disability_status",
                operator="boolean_eq",
                value=True,
                mandatory=True,
                description="Must possess a valid disability certificate with ≥40% disability (UDID)",
            )
        )

    # 6. Institution Type Rule
    if scholarship.institution_requirements:
        rules.append(
            EligibilityRule(
                field="school_type",
                operator="in",
                value=scholarship.institution_requirements,
                mandatory=False,  # Treated as a verification check unless confirmed invalid
                description=f"Must study in {', '.join(scholarship.institution_requirements)} school",
            )
        )

    # 7. Academic Score / Percentage Rule
    if scholarship.merit_requirements.min_percentage is not None:
        rules.append(
            EligibilityRule(
                field="academic_score",
                operator=">=",
                value=scholarship.merit_requirements.min_percentage,
                mandatory=True,
                description=f"Minimum {scholarship.merit_requirements.min_percentage}% marks in previous academic year",
            )
        )

    # 8. Occupational / Special Category Rule
    if "beedi" in scholarship.id or "mine" in scholarship.id:
        rules.append(
            EligibilityRule(
                field="occupational_background",
                operator="in",
                value=["Beedi Worker", "Cine Worker", "Mine Worker", "IOMC / LSDM"],
                mandatory=True,
                description="Ward of Beedi, Cine, or Mine worker",
            )
        )
    elif "hazardous" in scholarship.id or "unclean" in scholarship.id:
        rules.append(
            EligibilityRule(
                field="occupational_background",
                operator="in",
                value=[
                    "Sanitation Worker",
                    "Waste Picker",
                    "Tanner / Flayer",
                    "Hazardous Occupations",
                ],
                mandatory=True,
                description="Ward of parents engaged in sanitation, waste-picking, or hazardous occupations",
            )
        )

    return rules


def evaluate_rule(
    rule: EligibilityRule,
    profile: StudentScholarshipProfile,
) -> Tuple[str, str]:
    """Evaluate a single rule against student profile.

    Returns:
        (status, reason_message) where status is "matched", "unmatched", or "unknown".
    """
    student_val = getattr(profile, rule.field, None)

    # If student profile hasn't provided this field yet
    if student_val is None:
        return (
            "unknown",
            f"{rule.field.replace('_', ' ').title()} is not specified in profile ({rule.description})",
        )

    # Class level evaluation
    if rule.operator == "in":
        if isinstance(rule.value, list):
            # Normalization for string lists vs ints
            if isinstance(student_val, str) and all(isinstance(x, str) for x in rule.value):
                # Check case-insensitive match or substring
                matched = any(
                    student_val.strip().lower() in allowed.strip().lower()
                    or allowed.strip().lower() in student_val.strip().lower()
                    for allowed in rule.value
                )
                if matched:
                    return (
                        "matched",
                        f"Your {rule.field.replace('_', ' ')} ({student_val}) matches eligible types ({', '.join(rule.value)}).",
                    )
                return (
                    "unmatched",
                    f"Your {rule.field.replace('_', ' ')} ({student_val}) is not among eligible types ({', '.join(rule.value)}).",
                )

            if student_val in rule.value:
                return (
                    "matched",
                    f"Your {rule.field.replace('_', ' ')} ({student_val}) is eligible for this scheme.",
                )
            return (
                "unmatched",
                f"Your {rule.field.replace('_', ' ')} ({student_val}) does not meet the required classes ({', '.join(map(str, rule.value))}).",
            )
        return "unknown", "Invalid rule definition"

    # Numeric inequality (Income <= ceiling)
    elif rule.operator == "<=":
        try:
            val_num = float(student_val)
            limit_num = float(rule.value)
            if val_num <= limit_num:
                return (
                    "matched",
                    f"Your annual family income (₹{int(val_num):,}) is within the ceiling of ₹{int(limit_num):,}.",
                )
            return (
                "unmatched",
                f"Your annual family income (₹{int(val_num):,}) exceeds the maximum limit of ₹{int(limit_num):,}.",
            )
        except (ValueError, TypeError):
            return "unknown", "Could not parse income value"

    # Numeric inequality (Score >= threshold)
    elif rule.operator == ">=":
        try:
            val_num = float(student_val)
            limit_num = float(rule.value)
            if val_num >= limit_num:
                return (
                    "matched",
                    f"Your academic score ({val_num:.1f}%) meets the required threshold of {limit_num:.1f}%.",
                )
            return (
                "unmatched",
                f"Your academic score ({val_num:.1f}%) is below the required {limit_num:.1f}%.",
            )
        except (ValueError, TypeError):
            return "unknown", "Could not parse academic score"

    # Category matching (any_of)
    elif rule.operator == "any_of":
        if isinstance(rule.value, list):
            cand_cats = [c.strip().upper() for c in rule.value]
            student_cat = str(student_val).strip().upper()

            # If scheme allows ALL / General, or student matches category
            if "ALL" in cand_cats or student_cat in cand_cats:
                return "matched", f"Your category ({student_val}) is eligible for this scheme."

            # Check for Minorities sub-identities
            minority_groups = [
                "MUSLIM",
                "CHRISTIAN",
                "SIKH",
                "BUDDHIST",
                "JAIN",
                "PARSI",
                "MINORITY",
                "MINORITIES",
            ]
            if "MINORITY" in cand_cats or "MINORITIES" in cand_cats:
                if student_cat in minority_groups:
                    return (
                        "matched",
                        f"Your community ({student_val}) is eligible under the Minority scheme.",
                    )

            return (
                "unmatched",
                f"Your category ({student_val}) is not covered by this scheme (Requires: {', '.join(rule.value)}).",
            )
        return "unknown", "Invalid category rule"

    # Gender equality
    elif rule.operator == "==":
        if str(student_val).strip().lower() == str(rule.value).strip().lower():
            return "matched", f"Gender requirement ({rule.value}) matched."
        return "unmatched", f"Scheme is restricted to {rule.value} students."

    # Boolean equality (Disability status)
    elif rule.operator == "boolean_eq":
        if bool(student_val) == bool(rule.value):
            return "matched", "Disability eligibility requirement satisfied."
        return (
            "unmatched",
            "This scheme is exclusively for students with certified disabilities (≥40%).",
        )

    return "unknown", f"Unhandled operator {rule.operator}"


def generate_template_explanation(
    scholarship: StructuredScholarship,
    profile: StudentScholarshipProfile,
    matched: List[str],
    unmatched: List[str],
    unknown: List[str],
    status: str,
) -> MatchExplanation:
    """Phase 13: Deterministic, safe, template-generated explanation."""
    reasons_matched: List[str] = [f"✓ {m}" for m in matched]
    reasons_unmatched: List[str] = [f"✗ {u}" for u in unmatched]
    verification_needed: List[str] = []

    # Add unknown fields as verification items
    for unk in unknown:
        verification_needed.append(f"⚠ Verification Needed: {unk}")

    # Add special merit/exam warnings if applicable
    if scholarship.merit_requirements.exam_required:
        verification_needed.append(
            "⚠ Selection requires qualifying the State-level examination (e.g. MAT / SAT)."
        )

    if scholarship.institution_requirements:
        verification_needed.append(
            f"⚠ School Requirement: Must be a regular student in a recognized {', '.join(scholarship.institution_requirements)} school."
        )

    # Summary template
    if status == EligibilityStatus.LIKELY_MATCH:
        summary = f"Strong match! You satisfy all known mandatory criteria for {scholarship.name}."
    elif status == EligibilityStatus.POSSIBLE_MATCH:
        summary = f"Possible opportunity. You match core criteria, but {len(unknown)} requirement(s) require verification."
    else:
        summary = f"Does not appear to match. {len(unmatched)} mandatory condition(s) are currently not met."

    action_guidance = (
        "Check scheme timelines and apply directly on the National Scholarship Portal "
        "(https://scholarships.gov.in) using your 14-digit One Time Registration (OTR) ID."
    )

    return MatchExplanation(
        summary=summary,
        reasons_matched=reasons_matched,
        reasons_unmatched=reasons_unmatched,
        verification_needed=verification_needed,
        action_guidance=action_guidance,
    )


def evaluate_scholarship(
    scholarship: StructuredScholarship,
    profile: StudentScholarshipProfile,
) -> MatchResult:
    """Phase 8 & 9: Evaluate a single scholarship and determine its 3-tier eligibility state."""
    rules = build_rules_for_scholarship(scholarship)

    matched_reasons: List[str] = []
    unmatched_reasons: List[str] = []
    unknown_reasons: List[str] = []

    has_mandatory_fail = False
    has_mandatory_unknown = False

    for rule in rules:
        status, message = evaluate_rule(rule, profile)
        if status == "matched":
            matched_reasons.append(message)
        elif status == "unmatched":
            unmatched_reasons.append(message)
            if rule.mandatory:
                has_mandatory_fail = True
        elif status == "unknown":
            unknown_reasons.append(message)
            if rule.mandatory:
                has_mandatory_unknown = True

    # Phase 9: Three Eligibility States Determination
    if has_mandatory_fail:
        eligibility_state = EligibilityStatus.DOES_NOT_MATCH
        status_icon = "🔴"
        score = 0.0 + (len(matched_reasons) * 5.0)
    elif has_mandatory_unknown or len(matched_reasons) < 2:
        eligibility_state = EligibilityStatus.POSSIBLE_MATCH
        status_icon = "🟡"
        total_rules = max(len(rules), 1)
        score = 50.0 + (len(matched_reasons) / total_rules) * 40.0
    else:
        eligibility_state = EligibilityStatus.LIKELY_MATCH
        status_icon = "🟢"
        total_rules = max(len(rules), 1)
        score = 90.0 + (len(matched_reasons) / total_rules) * 10.0

    # Boost score slightly if financial assistance is high
    amount = (
        scholarship.financial_assistance.amount_per_annum if scholarship.financial_assistance else 0
    )
    if amount and eligibility_state != EligibilityStatus.DOES_NOT_MATCH:
        score += min(amount / 5000.0, 5.0)

    explanation = generate_template_explanation(
        scholarship=scholarship,
        profile=profile,
        matched=matched_reasons,
        unmatched=unmatched_reasons,
        unknown=unknown_reasons,
        status=eligibility_state,
    )

    return MatchResult(
        scholarship_id=scholarship.id,
        scholarship_name=scholarship.name,
        status=eligibility_state,
        status_icon=status_icon,
        provider=scholarship.provider,
        amount_per_annum=scholarship.financial_assistance.amount_per_annum
        if scholarship.financial_assistance
        else None,
        matched_rules=matched_reasons,
        unmatched_rules=unmatched_reasons,
        unknown_rules=unknown_reasons,
        score=round(score, 2),
        explanation=explanation,
        official_source_url=scholarship.official.source_url,
        primary_url=scholarship.official.primary_url
        or scholarship.official.specification_url
        or scholarship.official.source_url,
        specification_url=scholarship.official.specification_url,
        faq_url=scholarship.official.faq_url,
    )


def rank_matches(matches: List[MatchResult]) -> List[MatchResult]:
    """Phase 12: Multi-tier ranking of matched scholarships."""
    status_order = {
        EligibilityStatus.LIKELY_MATCH: 1,
        EligibilityStatus.POSSIBLE_MATCH: 2,
        EligibilityStatus.DOES_NOT_MATCH: 3,
    }

    def sort_key(m: MatchResult):
        tier = status_order.get(m.status, 99)
        amount = m.amount_per_annum or 0
        return (tier, -m.score, -amount, m.scholarship_name)

    return sorted(matches, key=sort_key)


def get_dynamic_questionnaire(
    profile: StudentScholarshipProfile,
    scholarships: Optional[List[StructuredScholarship]] = None,
) -> List[QuestionDefinition]:
    """Phase 11: Dynamic questionnaire generator.

    Inspects what profile fields are missing and returns only necessary questions.
    """
    questions: List[QuestionDefinition] = []

    # Primary discovery questions (Priority 1)
    if profile.class_level is None:
        questions.append(
            QuestionDefinition(
                field_name="class_level",
                label="What class/grade are you currently studying in?",
                question_type="select",
                options=["Class 9", "Class 10"],
                help_text="Current discovery catalogue focuses on secondary school students.",
                priority=1,
            )
        )

    if profile.family_income is None:
        questions.append(
            QuestionDefinition(
                field_name="family_income",
                label="What is your approximate annual family income (in INR)?",
                question_type="number",
                options=[],
                help_text="Most government school scholarships have income ceilings between ₹1.0 Lakh to ₹3.5 Lakh.",
                priority=1,
            )
        )

    if profile.category is None:
        questions.append(
            QuestionDefinition(
                field_name="category",
                label="What is your social / reservation category?",
                question_type="select",
                options=[
                    "General",
                    "OBC",
                    "SC",
                    "ST",
                    "EBC",
                    "DNT",
                    "Minority (Muslim/Sikh/Christian/Jain/Buddhist/Parsi)",
                ],
                help_text="Several NSP schemes are targeted to specific categories to promote equity.",
                priority=1,
            )
        )

    # Conditional refinement questions (Priority 2)
    # If any active scholarship checks disability and profile is not set:
    if profile.disability_status is None:
        questions.append(
            QuestionDefinition(
                field_name="disability_status",
                label="Do you have a certified benchmark disability (≥40% disability with UDID)?",
                question_type="boolean",
                options=["No", "Yes"],
                help_text="Enables qualification for the Pre-Matric Scholarship for Students with Disabilities.",
                priority=2,
            )
        )

    if profile.school_type is None:
        questions.append(
            QuestionDefinition(
                field_name="school_type",
                label="What type of school do you attend?",
                question_type="select",
                options=[
                    "Government School",
                    "Government-aided School",
                    "Local Body / Municipal School",
                    "Recognized Private School",
                    "Top Class School",
                ],
                help_text="Schemes like NMMSS and PM-YASASVI specify government or aided institutions.",
                priority=2,
            )
        )

    if profile.academic_score is None:
        questions.append(
            QuestionDefinition(
                field_name="academic_score",
                label="What was your aggregate percentage in your previous academic year?",
                question_type="number",
                options=[],
                help_text="Used to evaluate merit-based thresholds (e.g. 55% for NMMSS, 50% for Minorities).",
                priority=2,
            )
        )

    return sorted(questions, key=lambda q: q.priority)


def match_scholarships(
    student_profile: Union[StudentScholarshipProfile, Dict[str, Any]],
    scholarships: Optional[List[StructuredScholarship]] = None,
    academic_year: str = "2026-27",
    storage: Optional[ScholarshipStorage] = None,
) -> List[MatchResult]:
    """Phase 8 & 5: Pure matching function - evaluates canonical profile against scholarships."""
    from backend.scholarships.models import normalize_student_profile

    profile = normalize_student_profile(student_profile)

    if scholarships is not None:
        all_schemes = scholarships
    else:
        db_storage = storage or ScholarshipStorage()
        all_schemes = db_storage.load_structured_catalogue(academic_year=academic_year)

        if not all_schemes:
            logger.warning(
                f"No structured scholarships found for AY {academic_year}. Attempting to run scraper pipeline..."
            )
            from backend.scholarships.scraper import NSPCatalogueScraper

            scraper = NSPCatalogueScraper(storage=db_storage)
            scraper.run(academic_year=academic_year)
            all_schemes = db_storage.load_structured_catalogue(academic_year=academic_year)

    raw_matches = [evaluate_scholarship(scheme, profile) for scheme in all_schemes]
    ranked = rank_matches(raw_matches)

    return ranked
