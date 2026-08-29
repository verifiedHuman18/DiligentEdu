"""Unified Scholarship Screen (Phases 1 - 16).

Provides a single, cohesive scholarship experience on one page:
1. Student Profile Context (synced with master Class 9/10 selection)
2. Scholarships for You (Informational matching cards without per-card buttons)
3. Scholarship Questions (Interactive inline Q&A with dynamic suggestions)
4. Official Government Information (Single authoritative NSP destination)
"""

import textwrap
from typing import Any

import streamlit as st

from backend.scholarships.models import (
    EligibilityStatus,
    normalize_student_profile,
)
from backend.scholarships.service import (
    match_scholarships,
)
from frontend.components.navigation import render_back_to_home
from frontend.components.scholarship_official_info import render_official_scholarship_info
from frontend.state import get_student_class_level


def render_scholarships_screen() -> None:
    """Renders the single unified Scholarships Screen."""
    # Top Navigation Back to Home (Phases 1-19)
    render_back_to_home("scholarships")

    class_level = get_student_class_level()

    # Header section
    st.markdown(
        textwrap.dedent("""\
<div class="m3-hero-card" style="margin-bottom: 1.5rem; min-height: 130px;">
  <div class="m3-hero-content">
    <div class="m3-hero-title">
      <span style="color: var(--md-primary);">National Scholarships</span>
    </div>
    <div class="m3-chips-group" style="margin-bottom: 0.4rem;">
      <span class="m3-chip m3-chip-amber"><span class="material-symbols-outlined" style="font-size: 1.0rem;">verified</span> Live Matching</span>
      <span class="m3-chip m3-chip-secondary"><span class="material-symbols-outlined" style="font-size: 1.0rem;">speed</span> Fast Eligibility Matching</span>
    </div>
    <div style="font-size: 0.95rem; color: var(--text-secondary); line-height: 1.4;">
      Discover verified pre-matric scholarship opportunities, explore criteria matched to your profile, and ask questions backed by official government guidelines.
    </div>
  </div>
</div>
"""),
        unsafe_allow_html=True,
    )

    # ==========================================
    # SECTION 1: STUDENT PROFILE CONTEXT
    # ==========================================
    st.markdown(
        """
        <div class="section-header-bar">
            <div>
                <h4 class="section-title-text">Matching Profile Context</h4>
                <div class="section-subtitle-text">Adjust your family income, reservation category, and school type to update scheme recommendations.</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    _render_profile_section(class_level)

    st.write("")
    st.write("")

    # ==========================================
    # SECTION 2: SCHOLARSHIPS FOR YOU
    # ==========================================
    st.markdown(
        """
        <div class="section-header-bar">
            <div>
                <h4 class="section-title-text">Matched Scholarship Opportunities</h4>
                <div class="section-subtitle-text">Verified National Scholarship Portal (NSP) schemes evaluated against your current criteria.</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    _render_matches_section(class_level)

    st.write("")
    st.write("")

    # ==========================================
    # SECTION 4: GLOBAL GOVERNMENT INFORMATION SECTION
    # ==========================================
    st.markdown(
        """
        <div class="section-header-bar">
            <div>
                <h4 class="section-title-text">Official Government Portals</h4>
                <div class="section-subtitle-text">Authoritative links and guidelines from the National Scholarship Portal (NSP).</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    render_official_scholarship_info()


def _render_profile_section(class_level: int) -> None:
    """Renders the student profile context and customization bar."""
    # Stored preferences with sensible defaults
    saved_income = st.session_state.get("profile_income", "₹1.5–2.5 Lakh (₹1,50,000 – ₹2,50,000)")
    saved_cat = st.session_state.get("profile_category", "OBC")
    saved_school = st.session_state.get("profile_school_type", "Government School")
    saved_pwd = st.session_state.get("profile_pwd", "No")

    with st.expander(
        "Your Matching Profile (Click to adjust parameters)",
        icon=":material/person:",
        expanded=True,
    ):
        st.caption(
            "Matching is active based on your profile. *(To switch between Class 9 and 10, use the Class setting in the sidebar)*. "
            "No sensitive government identifiers (Aadhaar, OTR, bank details) are ever requested."
        )

        with st.form(key="scholarship_profile_form"):
            p_col1, p_col2 = st.columns(2)
            with p_col1:
                income_opts = [
                    "Below ₹1 Lakh (Below ₹1,00,000)",
                    "₹1–1.5 Lakh (₹1,00,000 – ₹1,50,000)",
                    "₹1.5–2.5 Lakh (₹1,50,000 – ₹2,50,000)",
                    "₹2.5–3.5 Lakh (₹2,50,000 – ₹3,50,000)",
                    "₹3.5–5 Lakh (₹3,50,000 – ₹5,00,000)",
                    "₹5–8 Lakh (₹5,00,000 – ₹8,00,000)",
                    "Above ₹8 Lakh",
                ]
                sel_income = st.selectbox(
                    "Annual Gross Family Income:",
                    options=income_opts,
                    index=income_opts.index(saved_income) if saved_income in income_opts else 2,
                    key="p_input_income",
                )

                cat_opts = [
                    "General / Unreserved",
                    "OBC (Other Backward Classes)",
                    "SC (Scheduled Castes)",
                    "ST (Scheduled Tribes)",
                    "Minorities (Muslim/Christian/Sikh/Jain/Buddhist/Parsi)",
                    "EBC / DNT (Economically Backward / De-Notified Tribes)",
                ]
                cat_idx = next(
                    (i for i, c in enumerate(cat_opts) if saved_cat.lower() in c.lower()), 1
                )
                sel_cat = st.selectbox(
                    "Social / Reservation Category:",
                    options=cat_opts,
                    index=cat_idx,
                    key="p_input_cat",
                )

            with p_col2:
                school_opts = [
                    "Government School",
                    "Government-aided School",
                    "Local Body / Municipal School",
                    "Recognized Private School",
                    "Top Class School (TCS)",
                ]
                school_idx = next(
                    (i for i, s in enumerate(school_opts) if saved_school.lower() in s.lower()), 0
                )
                sel_school = st.selectbox(
                    "School Management Type:",
                    options=school_opts,
                    index=school_idx,
                    key="p_input_school",
                )

                pwd_opts = [
                    "No (General Ability)",
                    "Yes (Certified ≥40% Disability with UDID)",
                ]
                pwd_idx = 1 if "yes" in str(saved_pwd).lower() else 0
                sel_pwd = st.selectbox(
                    "Person with Benchmark Disability (PwD):",
                    options=pwd_opts,
                    index=pwd_idx,
                    key="p_input_pwd",
                )

            submitted = st.form_submit_button(
                "Update & Apply Matching Criteria",
                type="primary",
                icon=":material/tune:",
                use_container_width=True,
            )
            if submitted:
                st.session_state["profile_income"] = sel_income
                st.session_state["profile_category"] = sel_cat
                st.session_state["profile_school_type"] = sel_school
                st.session_state["profile_pwd"] = "Yes" if "Yes" in sel_pwd else "No"
                st.rerun()


def _render_matches_section(class_level: int) -> None:
    """Renders the matching scholarships results based on the student profile."""
    # Stored preferences with sensible defaults
    saved_income = st.session_state.get("profile_income", "₹1.5–2.5 Lakh (₹1,50,000 – ₹2,50,000)")
    saved_cat = st.session_state.get("profile_category", "OBC")
    saved_school = st.session_state.get("profile_school_type", "Government School")
    saved_pwd = st.session_state.get("profile_pwd", "No")

    raw_profile = {
        "class_level": class_level,
        "income": saved_income,
        "category": saved_cat,
        "school_type": saved_school,
        "pwd": saved_pwd,
    }

    canonical_profile = normalize_student_profile(raw_profile)

    # Ensure class level is always synced with master state
    if canonical_profile.class_level != class_level:
        canonical_profile.class_level = class_level
        st.session_state["profile_canonical"] = canonical_profile

    matches = match_scholarships(canonical_profile, academic_year="2026-27")

    likely = [m for m in matches if m.status == EligibilityStatus.LIKELY_MATCH]
    possible = [m for m in matches if m.status == EligibilityStatus.POSSIBLE_MATCH]
    does_not = [m for m in matches if m.status == EligibilityStatus.DOES_NOT_MATCH]

    # Match summary chips
    st.markdown(
        f"""
        <div style="display: flex; gap: 10px; margin-bottom: 1.2rem; flex-wrap: wrap;">
            <span style="background: var(--md-tertiary-container); color: var(--md-on-tertiary-container); border: 1px solid var(--md-tertiary); padding: 4px 12px; border-radius: 16px; font-size: 0.85rem; font-weight: 700;">
                {len(likely)} Strong Matches
            </span>
            <span style="background: var(--md-amber-container); color: var(--md-on-amber-container); border: 1px solid var(--md-amber); padding: 4px 12px; border-radius: 16px; font-size: 0.85rem; font-weight: 700;">
                {len(possible)} Possible Matches
            </span>
            <span style="background: var(--md-error-container); color: var(--md-on-error-container); border: 1px solid var(--md-error); padding: 4px 12px; border-radius: 16px; font-size: 0.85rem; font-weight: 700;">
                {len(does_not)} Non-matching Schemes
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    primary_matches = likely + possible
    if primary_matches:
        for m in primary_matches:
            _render_scholarship_card(m)
    else:
        st.info(
            "No scholarships currently appear to match your profile based on the available criteria. "
            "You can still ask a question below or browse the official scholarship portal."
        )

    # Optional expandable section for non-matching schemes
    if does_not:
        with st.expander(
            f"Show {len(does_not)} Non-matching Schemes (Click to inspect criteria)",
            icon=":material/visibility:",
        ):
            for m in does_not:
                _render_scholarship_card(m)


def _render_scholarship_card(match: Any) -> None:
    """Render a focused, purely informational scholarship result card."""
    amt_str = (
        f"₹{match.amount_per_annum:,} / year"
        if match.amount_per_annum
        else "Tuition Waiver / Allowances"
    )
    status_label = match.status.replace("_", " ").title()

    badge_color = (
        "var(--md-tertiary)"
        if match.status == EligibilityStatus.LIKELY_MATCH
        else (
            "var(--md-amber)"
            if match.status == EligibilityStatus.POSSIBLE_MATCH
            else "var(--md-error)"
        )
    )
    badge_bg = (
        "var(--md-tertiary-container)"
        if match.status == EligibilityStatus.LIKELY_MATCH
        else (
            "var(--md-amber-container)"
            if match.status == EligibilityStatus.POSSIBLE_MATCH
            else "var(--md-error-container)"
        )
    )
    badge_text_color = (
        "var(--md-on-tertiary-container)"
        if match.status == EligibilityStatus.LIKELY_MATCH
        else (
            "var(--md-on-amber-container)"
            if match.status == EligibilityStatus.POSSIBLE_MATCH
            else "var(--md-on-error-container)"
        )
    )

    reasons_html_list = []
    if match.explanation.reasons_matched:
        items = "".join(
            f'<li style="margin-bottom: 2px;">{r.replace("✓", "").strip()}</li>'
            for r in match.explanation.reasons_matched
        )
        reasons_html_list.append(
            f'<div style="margin-top: 8px;"><strong style="font-size: 0.84rem; color: var(--on-surface);">Why this appears relevant:</strong><ul style="margin: 4px 0 0 0; padding-left: 18px; font-size: 0.84rem; color: var(--on-surface-variant);">{items}</ul></div>'
        )

    if match.explanation.verification_needed:
        items = "".join(
            f'<li style="margin-bottom: 2px;">{v.replace("", "").strip()}</li>'
            for v in match.explanation.verification_needed
        )
        reasons_html_list.append(
            f'<div style="margin-top: 8px;"><strong style="font-size: 0.84rem; color: var(--md-amber);">Requirements to verify:</strong><ul style="margin: 4px 0 0 0; padding-left: 18px; font-size: 0.84rem; color: var(--on-surface-variant);">{items}</ul></div>'
        )

    if match.explanation.reasons_unmatched:
        items = "".join(
            f'<li style="margin-bottom: 2px;">{u.replace("", "").replace("✗", "").strip()}</li>'
            for u in match.explanation.reasons_unmatched
        )
        reasons_html_list.append(
            f'<div style="margin-top: 8px;"><strong style="font-size: 0.84rem; color: var(--danger-text);">Why it does not match:</strong><ul style="margin: 4px 0 0 0; padding-left: 18px; font-size: 0.84rem; color: var(--on-surface-variant);">{items}</ul></div>'
        )

    explanation_block = (
        f'<div style="border-top: 1px dashed var(--outline-variant); margin-top: 10px; padding-top: 6px;">{"".join(reasons_html_list)}</div>'
        if reasons_html_list
        else ""
    )

    card_html = f"""
    <div style="background: var(--surface-container-high); border: 1px solid var(--outline-variant); border-radius: 12px; padding: 1.1rem 1.3rem; margin-bottom: 0.9rem;">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 10px;">
            <div>
                <span style="background: {badge_bg}; color: {badge_text_color}; border: 1px solid {badge_color}; padding: 2px 8px; border-radius: 12px; font-size: 0.74rem; font-weight: 700; text-transform: uppercase;">
                    {status_label}
                </span>
                <h4 style="margin: 0.4rem 0 0.2rem 0; color: var(--on-surface); font-size: 1.1rem; font-weight: 700;">{match.scholarship_name}</h4>
                <div style="font-size: 0.84rem; color: var(--text-secondary);">{match.provider}</div>
            </div>
            <div style="text-align: right;">
                <span style="font-size: 1.1rem; font-weight: 700; color: var(--md-primary);">{amt_str}</span>
                <div style="font-size: 0.74rem; color: var(--text-secondary);">Direct Benefit Transfer (DBT)</div>
            </div>
        </div>
        {explanation_block}
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)
