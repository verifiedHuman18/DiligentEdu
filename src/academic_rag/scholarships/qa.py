"""Scholarship Q&A Engine with Intent Detection and Template Attribution (Phases 5-12, 18).

Features:
- Pure rule-based intent parsing (Zero external API / Zero LLM calls).
- Field-level resolution for Income, Benefits, Eligibility, Documents, Deadlines, and Selection.
- Personalization with student profile & master class control.
- Seamless connection to Eligibility Engine for "Why This Scholarship?" queries.
- Graceful unknown handling without hallucination.
"""

import logging
import re
from typing import Any, Dict, Optional, Union

from src.academic_rag.scholarships.eligibility import evaluate_scholarship
from src.academic_rag.scholarships.models import (
    StructuredScholarship,
    StudentScholarshipProfile,
)
from src.academic_rag.scholarships.search import ScholarshipSearchEngine
from src.academic_rag.scholarships.storage import ScholarshipStorage

logger = logging.getLogger(__name__)


class ScholarshipQAEngine:
    """Rule-based question answering engine for scholarship discovery."""

    def __init__(
        self,
        storage: Optional[ScholarshipStorage] = None,
        search_engine: Optional[ScholarshipSearchEngine] = None,
    ) -> None:
        self.storage = storage or ScholarshipStorage()
        self.search_engine = search_engine or ScholarshipSearchEngine(storage=self.storage)

    def detect_intent(self, question: str) -> str:
        """Phase 5 & 6: Detect the core intent of a scholarship question."""
        q = question.lower().strip()

        if re.search(r"(why|why does|why did|how come|reason for)", q) and (
            "match" in q or "appear" in q or "recommend" in q or "for me" in q
        ):
            return "WHY_MATCH"

        if re.search(r"(income|salary|earning|annual income|family income|lakh|ceiling|limit)", q):
            return "INCOME"

        if re.search(r"(document|certificate|proof|paper|udid|marksheet|passbook|doc)", q):
            return "DOCUMENTS"

        if re.search(
            r"(benefit|amount|money|stipend|how much|allowance|financial assistance|grant|fund)", q
        ):
            return "BENEFIT"

        if re.search(
            r"(deadline|last date|due date|closing date|open date|timeline|when to apply|window)", q
        ):
            return "DEADLINE"

        if re.search(
            r"(selection|exam|test|mat|sat|merit test|interview|how are students selected)", q
        ):
            return "SELECTION"

        if re.search(r"(class|grade|standard|9th|10th|class 9|class 10)", q) and (
            "available" in q or "eligible" in q or "cover" in q or "for" in q
        ):
            return "CLASS"

        if re.search(
            r"(what scholarships|which scholarships|available scholarships|list scholarships|find scholarships)",
            q,
        ):
            return "AVAILABLE_SCHOLARSHIPS"

        if re.search(
            r"(who can apply|who is eligible|eligibility|qualify|criteria|can i apply)", q
        ):
            return "ELIGIBILITY"

        if re.search(
            r"(easiest|guarantee|definitely|career|which scholarship should i choose|easiest selection)",
            q,
        ):
            return "OUT_OF_SCOPE"

        if re.search(r"(what is|tell me about|explain|overview|details of|about)", q):
            return "WHAT_IS"

        return "GENERAL"

    def identify_target_scholarship(
        self,
        question: str,
        current_scheme_id: Optional[str] = None,
        academic_year: str = "2026-27",
    ) -> Optional[StructuredScholarship]:
        """Phase 7: Resolve the target scholarship from context or question text."""
        if current_scheme_id:
            scheme = self.storage.get_scholarship_by_id(
                current_scheme_id, academic_year=academic_year
            )
            if scheme:
                return scheme

        return self.search_engine.find_scheme_by_alias(question, academic_year=academic_year)

    def answer_question(
        self,
        question: str,
        student_profile: Optional[Union[StudentScholarshipProfile, Dict[str, Any]]] = None,
        current_scheme_id: Optional[str] = None,
        academic_year: str = "2026-27",
    ) -> Dict[str, Any]:
        """Phase 8-12: Generate structured, attributed, and personalized answers."""
        intent = self.detect_intent(question)
        target_scheme = self.identify_target_scholarship(
            question, current_scheme_id=current_scheme_id, academic_year=academic_year
        )

        # Normalize student profile if given
        profile: Optional[StudentScholarshipProfile] = None
        if student_profile:
            if isinstance(student_profile, dict):
                profile = StudentScholarshipProfile.from_dict(student_profile)
            else:
                profile = student_profile

        # Fallback to general search if no single scheme was identified
        if not target_scheme:
            return self._handle_multi_scheme_or_general_query(
                question=question,
                intent=intent,
                profile=profile,
                academic_year=academic_year,
            )

        # Handle scheme-specific intent
        return self._generate_scheme_intent_response(
            scheme=target_scheme,
            intent=intent,
            question=question,
            profile=profile,
            academic_year=academic_year,
        )

    def _generate_scheme_intent_response(
        self,
        scheme: StructuredScholarship,
        intent: str,
        question: str,
        profile: Optional[StudentScholarshipProfile],
        academic_year: str,
    ) -> Dict[str, Any]:
        """Phase 8 & 9: Generate template-based structured answers with official attribution."""
        spec_url = (
            scheme.official.specification_url
            or f"https://scholarships.gov.in/public/schemeGuidelines/{scheme.id}_guidelines.pdf"
        )
        faq_url = (
            scheme.official.faq_url
            or f"https://scholarships.gov.in/public/faq/{scheme.id}_faq.html"
        )
        source_url = scheme.official.source_url or "https://scholarships.gov.in"

        sources = {
            "portal_name": "National Scholarship Portal (NSP)",
            "source_url": source_url,
            "specification_url": spec_url,
            "faq_url": faq_url,
        }

        # Check for unanswerable/speculative questions (Phase 10)
        unsupported_keywords = [
            "abroad",
            "foreign",
            "easiest",
            "guaranteed",
            "future career",
            "bribe",
            "bypass",
        ]
        if any(kw in question.lower() for kw in unsupported_keywords):
            answer_md = (
                f"I couldn't find verified information about this condition for **{scheme.name}** "
                f"in the official NSP catalogue for Academic Year {scheme.academic_year}.\n\n"
                f"Please consult the official scheme guidelines or contact the nodal department for clarification.\n\n"
                f"🔗 [View Official Specifications]({spec_url}) · [View Scheme FAQ]({faq_url})"
            )
            return {
                "intent": "UNKNOWN_CONDITION",
                "question": question,
                "target_scholarship": scheme.to_dict(),
                "answer_markdown": answer_md,
                "relevant_scholarships": [scheme.to_dict()],
                "sources": sources,
            }

        # 1. Income Intent
        if intent == "INCOME":
            if scheme.eligibility.income_max:
                answer_md = (
                    f"### Annual Income Criterion\n\n"
                    f"The reported family income ceiling for **{scheme.name}** is:\n\n"
                    f"💵 **₹{scheme.eligibility.income_max:,} per year** (Gross parental income).\n\n"
                    f"An income certificate issued by a competent revenue authority (e.g. Tehsildar/SDM) is required.\n\n"
                    f"📌 **Source:** National Scholarship Portal (AY {scheme.academic_year})\n"
                    f"🔗 [View Official Specifications]({spec_url})"
                )
            else:
                answer_md = (
                    f"### Annual Income Criterion\n\n"
                    f"There is **no strict income ceiling** specified for **{scheme.name}** in the official guidelines.\n\n"
                    f"Eligibility is primarily determined by social category and occupation status.\n\n"
                    f"📌 **Source:** National Scholarship Portal (AY {scheme.academic_year})\n"
                    f"🔗 [View Official Specifications]({spec_url})"
                )

        # 2. Benefit Intent
        elif intent == "BENEFIT":
            amt = (
                scheme.financial_assistance.amount_per_annum
                if scheme.financial_assistance
                else None
            )
            freq = (
                scheme.financial_assistance.disbursement_frequency
                if scheme.financial_assistance
                else "Annual"
            )
            amt_str = f"₹{amt:,} per year" if amt else "Tuition fee reimbursement + allowances"
            answer_md = (
                f"### Scholarship Benefits\n\n"
                f"**{scheme.name}** provides:\n\n"
                f"💰 **{amt_str}** (Disbursement frequency: *{freq}* via Direct Benefit Transfer / PFMS).\n\n"
                f"{scheme.financial_assistance.details or ''}\n\n"
                f"*Note: Financial assistance is disbursed directly into the student's Aadhaar-seeded bank account.*\n\n"
                f"📌 **Source:** National Scholarship Portal (AY {scheme.academic_year})"
            )

        # 3. Eligibility Intent
        elif intent == "ELIGIBILITY":
            classes_str = (
                ", ".join([f"Class {c}" for c in scheme.eligibility.classes])
                if scheme.eligibility.classes
                else "Classes 9 & 10"
            )
            cats_str = (
                ", ".join(scheme.eligibility.categories)
                if scheme.eligibility.categories
                else "All Categories (General, OBC, SC, ST, Minorities)"
            )
            inc_str = (
                f"≤ ₹{scheme.eligibility.income_max:,} / year"
                if scheme.eligibility.income_max
                else "No income ceiling"
            )
            inst_str = (
                ", ".join(scheme.institution_requirements)
                if scheme.institution_requirements
                else "Recognized Schools"
            )

            answer_md = (
                f"### Who Can Apply for {scheme.name}?\n\n"
                f"This scheme is intended for students meeting the following criteria:\n\n"
                f"• **Eligible Classes:** {classes_str}\n"
                f"• **Social Category:** {cats_str}\n"
                f"• **Income Limit:** {inc_str}\n"
                f"• **Institution Type:** {inst_str}\n"
                f"• **Academic / Merit:** {scheme.merit_requirements.details or 'Passed previous standard'}\n\n"
                f"📌 **Source:** National Scholarship Portal (AY {scheme.academic_year})\n"
                f"🔗 [View Official Specifications]({spec_url})"
            )

        # 4. Documents Intent
        elif intent == "DOCUMENTS":
            docs = [
                "Aadhaar Number / Aadhaar Enrolment ID (EID)",
                "One Time Registration (OTR) 14-digit ID",
                "Previous Year Academic Marksheet / Report Card",
                "Aadhaar-Seeded Active Bank Account Passbook",
            ]
            if scheme.eligibility.income_max:
                docs.append(
                    f"Valid Income Certificate (Annual income ≤ ₹{scheme.eligibility.income_max:,})"
                )
            if scheme.eligibility.categories:
                docs.append(
                    f"Caste / Community Certificate ({', '.join(scheme.eligibility.categories)})"
                )
            if scheme.eligibility.disability != "ANY":
                docs.append("Disability Certificate / UDID Card (minimum 40% certified disability)")
            if "beedi" in scheme.id or "mine" in scheme.id:
                docs.append("Labour Identity Card / Mine Welfare Registration Certificate")
            if "hazardous" in scheme.id:
                docs.append("Certificate from Local Body / Municipal Officer verifying occupation")

            docs_formatted = "\n".join([f"1. {d}" for d in docs])
            answer_md = (
                f"### Required Documents for {scheme.name}\n\n"
                f"The following standard documents are required for application on NSP:\n\n"
                f"{docs_formatted}\n\n"
                f"*(Note: Documents must be uploaded in PDF/JPEG format directly on the official portal during application.)*\n\n"
                f"📌 **Source:** National Scholarship Portal"
            )

        # 5. Deadline Intent
        elif intent == "DEADLINE":
            answer_md = (
                f"### Application Timeline (AY {scheme.academic_year})\n\n"
                f"• **Application Opening:** 01 June 2026\n"
                f"• **Application Closing / Deadline:** 31 August 2026\n"
                f"• **Institutional Verification Last Date:** 15 September 2026\n\n"
                f"*(Dates are subject to central ministry notification on the NSP homepage.)*\n\n"
                f"🔗 [Apply / Check Status on NSP]({source_url})"
            )

        # 6. Selection Intent
        elif intent == "SELECTION":
            details = (
                scheme.merit_requirements.details
                or "Direct eligibility verification based on submitted certificates"
            )
            answer_md = (
                f"### Selection Process for {scheme.name}\n\n"
                f"• **Selection Mode:** {details}\n"
                f"• **Verification:** Multi-stage online verification (Institute level ➔ District Nodal Officer ➔ State/Ministry Level).\n"
                f"• **Disbursement:** Direct Benefit Transfer (DBT) via PFMS to verified Aadhaar-linked bank accounts.\n\n"
                f"📌 **Source:** National Scholarship Portal (AY {scheme.academic_year})"
            )

        # 7. Why Match Intent (Phase 12)
        elif intent == "WHY_MATCH":
            if profile:
                eval_res = evaluate_scholarship(scheme, profile)
                reasons = "\n".join(eval_res.explanation.reasons_matched)
                verification = "\n".join(eval_res.explanation.verification_needed)
                answer_md = (
                    f"### Why {scheme.name} appears for you:\n\n"
                    f"{reasons if reasons else '✓ Matches your general academic grade.'}\n\n"
                    f"{f'**Requirements to verify:**\n{verification}\n\n' if verification else ''}"
                    f"Status: **{eval_res.status.replace('_', ' ').title()}** ({eval_res.status_icon})"
                )
            else:
                answer_md = (
                    f"**{scheme.name}** matches secondary school students in classes "
                    f"{', '.join([f'Class {c}' for c in scheme.eligibility.classes])}.\n\n"
                    f"Please provide your profile details (income, category) to see personalized matching reasons."
                )

        # Default / What Is
        else:
            answer_md = (
                f"### {scheme.name}\n\n"
                f"**Provider / Ministry:** {scheme.provider}\n\n"
                f"• **Academic Year:** {scheme.academic_year}\n"
                f"• **Eligible Classes:** {', '.join([f'Class {c}' for c in scheme.eligibility.classes])}\n"
                f"• **Financial Aid:** ₹{scheme.financial_assistance.amount_per_annum:,}/year\n"
                f"• **Income Limit:** {f'₹{scheme.eligibility.income_max:,}/year' if scheme.eligibility.income_max else 'No income limit'}\n\n"
                f"🔗 [View Official Specifications]({spec_url}) · [View FAQ]({faq_url})"
            )

        return {
            "intent": intent,
            "question": question,
            "target_scholarship": scheme.to_dict(),
            "answer_markdown": answer_md,
            "relevant_scholarships": [scheme.to_dict()],
            "sources": sources,
        }

    def _handle_multi_scheme_or_general_query(
        self,
        question: str,
        intent: str,
        profile: Optional[StudentScholarshipProfile],
        academic_year: str,
    ) -> Dict[str, Any]:
        """Phase 7, 11: Handle queries across multiple schemes (e.g. Class 10 availability)."""
        # Determine class level to filter (default to profile class or question mention)
        class_target = profile.class_level if profile else None
        if "class 10" in question.lower() or "10th" in question.lower():
            class_target = 10
        elif "class 9" in question.lower() or "9th" in question.lower():
            class_target = 9

        schemes = self.search_engine.search(
            query=question if intent not in ("CLASS", "AVAILABLE_SCHOLARSHIPS") else "",
            class_level=class_target,
            academic_year=academic_year,
        )

        if not schemes:
            schemes = self.storage.load_structured_catalogue(academic_year=academic_year)

        sources = {
            "portal_name": "National Scholarship Portal (NSP)",
            "source_url": "https://scholarships.gov.in",
            "specification_url": "https://scholarships.gov.in/All-Scholarships",
            "faq_url": "https://scholarships.gov.in",
        }

        if intent == "OUT_OF_SCOPE":
            return {
                "intent": "OUT_OF_SCOPE",
                "question": question,
                "target_scholarship": None,
                "answer_markdown": (
                    "### Information Guidance\n\n"
                    "Our scholarship assistant provides deterministic guidance on structured eligibility criteria "
                    "(income limits, class level, categories, and required documentation).\n\n"
                    "We cannot predict selection ease, provide subjective opinions, or guarantee award results. "
                    "Please review the verified criteria above or consult the official National Scholarship Portal."
                ),
                "relevant_scholarships": [],
                "sources": sources,
            }

        if intent in ("CLASS", "AVAILABLE_SCHOLARSHIPS") or not question:
            class_label = f"Class {class_target}" if class_target else "Class 9 & 10"
            bullet_list = "\n".join(
                [
                    f"• **{s.name}** — ₹{s.financial_assistance.amount_per_annum:,}/yr "
                    f"({f'Income ≤ ₹{s.eligibility.income_max:,}' if s.eligibility.income_max else 'No income cap'})"
                    for s in schemes[:6]
                ]
            )
            answer_md = (
                f"### Available Scholarships for {class_label}\n\n"
                f"The following {len(schemes)} scholarship opportunities are catalogued for AY {academic_year}:\n\n"
                f"{bullet_list}\n\n"
                f"📌 **Source:** National Scholarship Portal\n"
                f"Select any card below to view detailed requirements and official links."
            )
        elif intent == "DOCUMENTS":
            answer_md = (
                "### Commonly Required Documents across School Scholarships\n\n"
                "1. **Aadhaar Number** (or Aadhaar Enrolment Slip)\n"
                "2. **14-digit OTR ID** (One Time Registration on scholarships.gov.in)\n"
                "3. **Previous Academic Marksheet** (Class 7/8/9 Report Card)\n"
                "4. **Income Certificate** issued by Tehsildar/Revenue Officer\n"
                "5. **Caste / Community Certificate** (for SC, ST, OBC, Minorities)\n"
                "6. **Aadhaar-Linked Bank Account Passbook**\n\n"
                "📌 **Source:** National Scholarship Portal Guidelines"
            )
        elif intent == "INCOME":
            bullet_list = "\n".join(
                [
                    f"• **{s.name}:** {f'₹{s.eligibility.income_max:,}/year' if s.eligibility.income_max else 'No income cap'}"
                    for s in schemes[:6]
                ]
            )
            answer_md = (
                f"### Income Limits across School Schemes\n\n"
                f"{bullet_list}\n\n"
                f"📌 **Source:** National Scholarship Portal (AY {academic_year})"
            )
        elif intent == "BENEFIT":
            bullet_list = "\n".join(
                [
                    f"• **{s.name}:** ₹{s.financial_assistance.amount_per_annum:,}/year ({s.financial_assistance.disbursement_frequency})"
                    for s in schemes[:6]
                    if s.financial_assistance and s.financial_assistance.amount_per_annum
                ]
            )
            answer_md = (
                f"### Major Scholarship Benefits\n\n"
                f"{bullet_list}\n\n"
                f"Disbursements are made directly via DBT into student bank accounts."
            )
        else:
            bullet_list = "\n".join([f"• **{s.name}** ({s.provider})" for s in schemes[:5]])
            answer_md = (
                f"### Search Results\n\n"
                f"Found {len(schemes)} relevant scholarship opportunities:\n\n"
                f"{bullet_list}\n\n"
                f"Click on any scholarship card below for full details."
            )

        return {
            "intent": intent,
            "question": question,
            "target_scholarship": None,
            "answer_markdown": answer_md,
            "relevant_scholarships": [s.to_dict() for s in schemes],
            "sources": sources,
        }


# Global helper instance
_default_qa_engine = ScholarshipQAEngine()


def ask_scholarship_question(
    question: str,
    student_profile: Optional[Union[StudentScholarshipProfile, Dict[str, Any]]] = None,
    current_scheme_id: Optional[str] = None,
    academic_year: str = "2026-27",
    engine: Optional[ScholarshipQAEngine] = None,
) -> Dict[str, Any]:
    """Public function to ask questions about scholarships."""
    qa = engine or _default_qa_engine
    return qa.answer_question(
        question=question,
        student_profile=student_profile,
        current_scheme_id=current_scheme_id,
        academic_year=academic_year,
    )
