"""Parsing utilities for NSP Scholarship catalogue, specifications, and FAQs."""

import re
from html.parser import HTMLParser
from typing import List, Optional

from src.academic_rag.scholarships.models import (
    EligibilityCriteria,
    FinancialAssistance,
    MeritRequirements,
    OfficialLinks,
    RawScholarshipData,
    ScholarshipMetadata,
    StructuredScholarship,
)


class HTMLTextExtractor(HTMLParser):
    """Clean HTML text extractor that removes scripts, styles, and tags."""

    def __init__(self) -> None:
        super().__init__()
        self._pieces: List[str] = []
        self._ignore: bool = False

    def handle_starttag(self, tag: str, attrs: List[tuple]) -> None:
        if tag.lower() in ("script", "style", "noscript"):
            self._ignore = True

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in ("script", "style", "noscript"):
            self._ignore = False
        elif tag.lower() in ("p", "div", "br", "li", "tr", "h1", "h2", "h3", "h4", "h5", "h6"):
            self._pieces.append("\n")

    def handle_data(self, data: str) -> None:
        if not self._ignore:
            text = data.strip()
            if text:
                self._pieces.append(text + " ")

    def get_text(self) -> str:
        raw = "".join(self._pieces)
        lines = [re.sub(r"\s+", " ", line).strip() for line in raw.splitlines()]
        return "\n".join([line for line in lines if line])


def extract_clean_text(html_or_text: str) -> str:
    """Extract clean readable text from HTML string."""
    if not html_or_text:
        return ""
    if "<" in html_or_text and ">" in html_or_text:
        try:
            parser = HTMLTextExtractor()
            parser.feed(html_or_text)
            return parser.get_text()
        except Exception:
            return re.sub(r"<[^>]+>", " ", html_or_text).strip()
    return html_or_text.strip()


def parse_classes(text: str) -> List[int]:
    """Identify eligible school classes (specifically 9, 10, etc.) from raw text."""
    classes = set()
    normalized = text.lower()

    # Check for range: Class 9 to 12 / Class 9-12 / Class 1 to 10
    range_match = re.search(r"\bclass\s*(\d{1,2})\s*(?:to|-)\s*(\d{1,2})\b", normalized)
    if range_match:
        start_c = int(range_match.group(1))
        end_c = int(range_match.group(2))
        if start_c <= end_c and end_c <= 12:
            for c in range(start_c, end_c + 1):
                classes.add(c)

    if re.search(r"\b(class\s*9|class\s*ix|9th\s*class|9th\s*standard|grade\s*9)\b", normalized):
        classes.add(9)
    if re.search(
        r"\b(class\s*10|class\s*x|10th\s*class|10th\s*standard|grade\s*10|secondary)\b", normalized
    ):
        classes.add(10)
    if re.search(r"\bpre[\s-]*matric\b", normalized):
        classes.add(9)
        classes.add(10)
    if re.search(r"\b(class\s*11|class\s*xi|11th)\b", normalized):
        classes.add(11)
    if re.search(r"\b(class\s*12|class\s*xii|12th)\b", normalized):
        classes.add(12)

    # Default to [9, 10] if pre-matric / school is detected but specific number isn't parsed
    if not classes and (
        "school" in normalized or "pre-matric" in normalized or "secondary" in normalized
    ):
        return [9, 10]

    return sorted(list(classes)) if classes else [9, 10]


def parse_income_ceiling(text: str) -> Optional[int]:
    """Extract annual income ceiling in INR from raw text. Returns None if no limit or undetermined."""
    normalized = text.replace(",", "").lower()

    # Generic lakh pattern: ₹ 3.5 Lakh / 2.50 lakh / 1 lakh / 8.0 lakh
    lakh_match = re.search(
        r"(?:rs\.?|inr|₹)?\s*(\d+(?:\.\d+)?)\s*(?:lakh|lac|lacs|lakhs)", normalized
    )
    if lakh_match:
        try:
            return int(float(lakh_match.group(1)) * 100000)
        except ValueError:
            pass

    if (
        re.search(r"(?:rs\.?|inr|₹)?\s*10000\s*(?:per month|\/month|p\.m\.)", normalized)
        or "120000" in normalized
    ):
        return 120000

    # Explicit direct numbers with optional colon/text: "income ceiling: Rs. 350000"
    match = re.search(
        r"(?:income|ceiling|limit)\s*[:=]?\s*(?:of|not exceeding|less than|up to|is|below)?\s*[:=]?\s*(?:rs\.?|inr|₹)?\s*(\d{5,7})",
        normalized,
    )
    if match:
        try:
            return int(match.group(1))
        except ValueError:
            pass

    # Direct 5-7 digit currency capture: Rs. 350000 / Rs 250000
    direct_curr = re.search(r"(?:rs\.?|inr|₹)\s*(\d{5,7})\b", normalized)
    if direct_curr:
        try:
            return int(direct_curr.group(1))
        except ValueError:
            pass

    # Specific common ceilings in school schemes
    if "350000" in normalized or "3.5 lakh" in normalized:
        return 350000
    if "250000" in normalized or "2.5 lakh" in normalized:
        return 250000
    if "150000" in normalized or "1.5 lakh" in normalized:
        return 150000
    if "100000" in normalized or "1 lakh" in normalized:
        return 100000
    if "800000" in normalized or "8 lakh" in normalized:
        return 800000

    return None


def parse_categories(text: str, scheme_id: str = "") -> List[str]:
    """Identify eligible reservation or social categories from raw text and scheme ID."""
    sid = scheme_id.lower()
    if "nmmss" in sid or "disabilit" in sid or "beedi" in sid or "hazardous" in sid:
        # Open to all social categories
        return []

    cats = []
    normalized = text.lower()

    # Look for explicit scheme targets with exclusion handling
    if (
        re.search(r"(scheduled caste|\bsc\b|sc/st|for sc\b|component.*sc)", normalized)
        and "not covered under sc" not in normalized
        and "not covered under sc/st" not in normalized
        and "except sc" not in normalized
    ):
        cats.append("SC")
    if (
        re.search(r"(scheduled tribe|\bst\b|sc/st|for st\b|component.*st)", normalized)
        and "not covered under st" not in normalized
        and "not covered under sc/st" not in normalized
        and "except st" not in normalized
    ):
        cats.append("ST")
    if re.search(r"(other backward class|\bobc\b|pm-yasasvi)", normalized):
        cats.append("OBC")
    if re.search(r"(economically backward class|\bebc\b)", normalized):
        cats.append("EBC")
    if re.search(r"(de-notified|denotified|\bdnt\b|\bsnt\b)", normalized):
        cats.append("DNT")
    if re.search(r"(minority|minorities|muslim|christian|sikh|buddhist|jain|parsi)", normalized):
        cats.append("Minorities")
    if re.search(r"(beedi|cine|iomc|lsdm|mine worker)", normalized):
        cats.append("Labour Wards")
    if re.search(
        r"(manual scavenger|sanitation worker|tanner|flayer|hazardous occupation)", normalized
    ):
        cats.append("Vulnerable Occupations")

    return sorted(list(set(cats)))


def parse_disability_requirement(text: str, scheme_id: str = "", scheme_name: str = "") -> str:
    """Check if disability certification is required or optional for the scheme."""
    normalized_name = scheme_name.lower()
    normalized_id = scheme_id.lower()
    normalized_text = text.lower()

    # If scheme_id is provided and belongs to other specific affirmative schemes (e.g. SC / ST / Minorities / Beedi)
    if scheme_id and not any(
        k in normalized_id or k in normalized_name for k in ("disabilit", "pwd", "divyang")
    ):
        return "ANY"

    if "40%" in normalized_text or "minimum 40" in normalized_text:
        return "REQUIRED_MIN_40_PERCENT"
    if "disabilit" in normalized_text or "pwd" in normalized_text or "divyang" in normalized_text:
        return "REQUIRED"

    return "ANY"


def parse_gender(text: str) -> str:
    """Determine gender exclusivity."""
    normalized = text.lower()
    if re.search(r"\b(girls only|only for girls|female only|girl student)\b", normalized):
        return "FEMALE"
    if re.search(r"\b(boys only|only for boys|male only)\b", normalized):
        return "MALE"
    return "ANY"


def parse_institution_types(text: str) -> List[str]:
    """Extract required school / institution types."""
    institutions = []
    normalized = text.lower()

    if (
        "government," in normalized
        or "government school" in normalized
        or "govt school" in normalized
        or "government " in normalized
    ):
        institutions.append("Government")
    if (
        "government-aided" in normalized
        or "aided school" in normalized
        or "govt aided" in normalized
    ):
        institutions.append("Government-aided")
    if "local body" in normalized or "panchayat" in normalized or "municipal" in normalized:
        institutions.append("Local Body")
    if "recognized private" in normalized or "private school" in normalized:
        institutions.append("Recognized Private")
    if "top class" in normalized or "identified school" in normalized:
        institutions.append("Top Class Schools")

    return sorted(list(set(institutions))) if institutions else ["Government", "Recognized Schools"]


def parse_scholarship_amount(text: str) -> Optional[int]:
    """Extract financial assistance amount per annum in INR."""
    normalized = text.replace(",", "").lower()

    # Specific common amounts
    if "12000" in normalized or "1000 per month" in normalized:
        return 12000
    if "75000" in normalized or "75 thousand" in normalized:
        return 75000
    if "4000" in normalized or "4 thousand" in normalized:
        return 4000
    if "10000" in normalized or "10 thousand" in normalized:
        return 10000
    if "3000" in normalized or "3 thousand" in normalized:
        return 3000

    match = re.search(
        r"(?:rs\.?|inr|₹)?\s*(\d{4,6})\s*(?:per annum|per year|\/year|\/annum|p\.a\.)", normalized
    )
    if match:
        try:
            return int(match.group(1))
        except ValueError:
            pass

    return None


def raw_to_structured(
    raw_data: RawScholarshipData, verified_at: Optional[str] = None
) -> StructuredScholarship:
    """Convert RawScholarshipData into strict StructuredScholarship without hallucination."""
    all_text = " ".join(
        [
            raw_data.name,
            str(raw_data.raw.get("catalogue_text", "")),
            str(raw_data.raw.get("specification_text", "")),
            str(raw_data.raw.get("faq_text", "")),
            str(raw_data.raw.get("eligibility_summary", "")),
            str(raw_data.raw.get("benefits_summary", "")),
        ]
    )

    classes = parse_classes(all_text)
    income_max = parse_income_ceiling(all_text)
    categories = parse_categories(all_text, scheme_id=raw_data.id)
    gender = parse_gender(all_text)
    disability = parse_disability_requirement(
        all_text, scheme_id=raw_data.id, scheme_name=raw_data.name
    )
    institutions = parse_institution_types(all_text)

    # Merit & Exam requirements
    is_merit = (
        "merit" in raw_data.name.lower()
        or "mat/sat" in all_text.lower()
        or "examination" in all_text.lower()
    )
    min_perc = None
    if "55%" in all_text or "55 percent" in all_text:
        min_perc = 55.0
    elif "50%" in all_text or "50 percent" in all_text:
        min_perc = 50.0

    exam_req = bool(
        re.search(r"(selection test|entrance exam|competitive test|mat/sat)", all_text.lower())
    )

    # Financial Assistance
    amount = parse_scholarship_amount(all_text)
    disbursement = (
        "Monthly"
        if ("1000 per month" in all_text.lower() or "monthly" in all_text.lower())
        else "Annual"
    )

    # Scheme type classification
    scheme_type = (
        "merit_cum_means"
        if (is_merit and income_max)
        else ("merit" if is_merit else "pre_matric_welfare")
    )

    return StructuredScholarship(
        id=raw_data.id,
        name=raw_data.name,
        academic_year=raw_data.academic_year,
        provider=raw_data.provider or "Government of India",
        scheme_type=scheme_type,
        eligibility=EligibilityCriteria(
            classes=classes,
            states=["ALL"],
            categories=categories,
            income_max=income_max,
            gender=gender,
            disability=disability,
        ),
        merit_requirements=MeritRequirements(
            required=is_merit,
            min_percentage=min_perc,
            exam_required=exam_req,
            details="Selection via merit/prescribed examination"
            if (is_merit or exam_req)
            else None,
        ),
        institution_requirements=institutions,
        financial_assistance=FinancialAssistance(
            amount_per_annum=amount,
            disbursement_frequency=disbursement if amount else None,
            details=f"Financial assistance up to ₹{amount:,} per annum" if amount else None,
        ),
        official=OfficialLinks(
            primary_url=raw_data.raw.get("primary_url")
            or raw_data.specification_url
            or raw_data.source_url,
            source_url=raw_data.source_url,
            specification_url=raw_data.specification_url,
            faq_url=raw_data.faq_url,
        ),
        metadata=ScholarshipMetadata(
            scraped_at=raw_data.scraped_at,
            verified_at=verified_at,
            source="National Scholarship Portal",
            version="1.0.0",
        ),
    )
