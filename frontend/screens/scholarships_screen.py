"""Unified Scholarship Screen (Phases 1 - 16).

Provides a single, cohesive scholarship experience on one page:
1. 👤 Student Profile Context (synced with master Class 9/10 selection)
2. 🔎 Scholarships for You (Informational matching cards without per-card buttons)
3. 💬 Scholarship Questions (Interactive inline Q&A with dynamic suggestions)
4. 🏛️ Official Government Information (Single authoritative NSP destination)
"""

import textwrap
from typing import Any, Dict, List, Optional

import streamlit as st

from frontend.components.navigation import render_back_to_home
from frontend.components.scholarship_official_info import render_official_scholarship_info
from frontend.state import get_student_class_level
from src.academic_rag.scholarships.models import (
    EligibilityStatus,
    StudentScholarshipProfile,
    compute_profile_signature,
    normalize_student_profile,
)
from src.academic_rag.scholarships.service import (
    ask_question,
    get_available_scholarships,
    match_scholarships,
)


def render_scholarships_screen() -> None:
    """Renders the single unified 🎓 Scholarships Screen."""
    # Top Navigation Back to Home (Phases 1-19)
    render_back_to_home("scholarships")

    class_level = get_student_class_level()
    student_id = st.session_state.get("student_id", "student_001")

    # Header section
    st.markdown(
        textwrap.dedent(f"""\
<div class="m3-hero-card" style="margin-bottom: 1.5rem; min-height: 130px;">
  <div class="m3-hero-content">
    <div class="m3-hero-title">
      🎓 <span style="color: var(--md-primary);">Scholarships</span>
    </div>
    <div class="m3-chips-group" style="margin-bottom: 0.4rem;">
      <span class="m3-chip m3-chip-primary"><span class="material-symbols-outlined" style="font-size: 1.0rem;">school</span> Class {class_level}</span>
      <span class="m3-chip m3-chip-purple"><span class="material-symbols-outlined" style="font-size: 1.0rem;">verified</span> National Scholarship Portal</span>
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
    # 1. TOP SECTION: STUDENT PROFILE CONTEXT (Phase 5)
    # ==========================================
    _render_profile_section(class_level)

    st.write("")
    st.divider()

    # ==========================================
    # 2. MAIN SECTION: SCHOLARSHIPS FOR YOU (Phases 6 & 7)
    # ==========================================
    _render_matches_section(class_level)

    st.write("")
    st.divider()

    # ==========================================
    # 3. CONVERSATIONAL Q&A SECTION (Phases 8 - 11)
    # ==========================================
    _render_qa_section(class_level)

    st.write("")
    st.divider()

    # ==========================================
    # 4. GLOBAL GOVERNMENT INFORMATION SECTION (Phases 4, 12, 13)
    # ==========================================
    render_official_scholarship_info()


def _render_profile_section(class_level: int) -> None:
    """Renders the student profile context and customization bar (Phase 5)."""
    # Stored preferences with sensible defaults
    saved_income = st.session_state.get("profile_income", "₹1.5–2.5 Lakh (₹1,50,000 – ₹2,50,000)")
    saved_cat = st.session_state.get("profile_category", "OBC")
    saved_school = st.session_state.get("profile_school_type", "Government School")
    saved_pwd = st.session_state.get("profile_pwd", "No")

    with st.expander("👤 Your Matching Profile (Click to adjust parameters)", expanded=True):
        st.caption(
            f"Matching is active for **Class {class_level}**. *(To switch between Class 9 and 10, use the Class setting in the sidebar)*. "
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
                sel_cat = st.selectbox(
                    "Social / Reservation Category:",
                    options=cat_opts,
                    index=1,
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
                sel_school = st.selectbox(
                    "School Management Type:",
                    options=school_opts,
                    index=0,
                    key="p_input_school",
                )

                pwd_opts = [
                    "No (General Ability)",
                    "Yes (Certified ≥40% Disability with UDID)",
                ]
                sel_pwd = st.selectbox(
                    "Person with Benchmark Disability (PwD):",
                    options=pwd_opts,
                    index=0,
                    key="p_input_pwd",
                )

            submitted = st.form_submit_button(
                "Update Matches",
                type="primary",
                icon=":material/refresh:",
                use_container_width=False,
            )

        if submitted or "profile_canonical" not in st.session_state:
            # Map into canonical profile (Phase 4 & 5)
            st.session_state["profile_income"] = sel_income
            st.session_state["profile_category"] = sel_cat
            st.session_state["profile_school_type"] = sel_school
            st.session_state["profile_pwd"] = sel_pwd

            raw_dict = {
                "class_level": class_level,
                "family_income": sel_income,
                "category": sel_cat,
                "school_type": sel_school,
                "disability_status": "Yes" if "Yes" in sel_pwd else "No",
                "academic_score": 75.0,
            }
            canonical = normalize_student_profile(raw_dict, default_class_level=class_level)
            st.session_state["profile_canonical"] = canonical


def _render_matches_section(class_level: int) -> None:
    """Renders the main scholarship matching cards without per-card buttons (Phases 6 & 7)."""
    canonical_profile = st.session_state.get(
        "profile_canonical",
        normalize_student_profile({"class_level": class_level}, default_class_level=class_level),
    )

    # Ensure class level is always synced with master state (Phase 13)
    if canonical_profile.class_level != class_level:
        canonical_profile.class_level = class_level
        st.session_state["profile_canonical"] = canonical_profile

    # Pure evaluation without stale cache (Phase 13)
    matches = match_scholarships(canonical_profile, academic_year="2026-27")

    likely = [m for m in matches if m.status == EligibilityStatus.LIKELY_MATCH]
    possible = [m for m in matches if m.status == EligibilityStatus.POSSIBLE_MATCH]
    does_not = [m for m in matches if m.status == EligibilityStatus.DOES_NOT_MATCH]

    st.markdown("### 🔎 Scholarships You May Qualify For")

    # Match summary chips
    st.markdown(
        f"""
        <div style="display: flex; gap: 10px; margin-bottom: 1.2rem; flex-wrap: wrap;">
            <span style="background: rgba(46, 125, 50, 0.15); color: #81c784; border: 1px solid #2e7d32; padding: 4px 12px; border-radius: 16px; font-size: 0.85rem; font-weight: 600;">
                🟢 {len(likely)} Strong Matches
            </span>
            <span style="background: rgba(245, 124, 0, 0.15); color: #ffb74d; border: 1px solid #f57c00; padding: 4px 12px; border-radius: 16px; font-size: 0.85rem; font-weight: 600;">
                🟡 {len(possible)} Possible Matches
            </span>
            <span style="background: rgba(211, 47, 47, 0.15); color: #e57373; border: 1px solid #d32f2f; padding: 4px 12px; border-radius: 16px; font-size: 0.85rem; font-weight: 600;">
                🔴 {len(does_not)} Non-matching Schemes
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
        # Phase 7: Clean handling when no schemes match
        st.info(
            "No scholarships currently appear to match your profile based on the available criteria. "
            "You can still ask a question below or browse the official scholarship portal."
        )

    # Optional expandable section for non-matching schemes
    if does_not:
        with st.expander(f"🔴 Show {len(does_not)} Non-matching Schemes (Click to inspect criteria)"):
            for m in does_not:
                _render_scholarship_card(m)


def _render_scholarship_card(match: Any) -> None:
    """Phases 1, 3, 6: Render a focused, purely informational scholarship result card without per-card buttons."""
    amt_str = f"₹{match.amount_per_annum:,} / year" if match.amount_per_annum else "Tuition Waiver / Allowances"
    status_label = match.status.replace("_", " ").title()

    badge_color = "#2e7d32" if match.status == EligibilityStatus.LIKELY_MATCH else ("#f57c00" if match.status == EligibilityStatus.POSSIBLE_MATCH else "#d32f2f")
    badge_bg = "rgba(46, 125, 50, 0.15)" if match.status == EligibilityStatus.LIKELY_MATCH else ("rgba(245, 124, 0, 0.15)" if match.status == EligibilityStatus.POSSIBLE_MATCH else "rgba(211, 47, 47, 0.15)")

    with st.container():
        st.markdown(
            f"""
            <div style="background: var(--surface-container-high); border: 1px solid var(--outline-variant); border-radius: 12px; padding: 1.2rem; margin-bottom: 0.8rem;">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.5rem; flex-wrap: wrap; gap: 10px;">
                    <div>
                        <span style="background: {badge_bg}; color: {badge_color}; border: 1px solid {badge_color}; padding: 2px 8px; border-radius: 12px; font-size: 0.75rem; font-weight: 700; text-transform: uppercase;">
                            {match.status_icon} {status_label}
                        </span>
                        <h4 style="margin: 0.4rem 0 0.2rem 0; color: var(--on-surface); font-size: 1.15rem; font-weight: 700;">🎓 {match.scholarship_name}</h4>
                        <div style="font-size: 0.85rem; color: var(--text-secondary);">{match.provider}</div>
                    </div>
                    <div style="text-align: right;">
                        <span style="font-size: 1.15rem; font-weight: 700; color: var(--md-primary);">{amt_str}</span>
                        <div style="font-size: 0.75rem; color: var(--text-secondary);">Direct Benefit Transfer (DBT)</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if match.explanation.reasons_matched:
            st.markdown("**Why this appears relevant:**")
            for r in match.explanation.reasons_matched:
                st.markdown(f"✓ {r}")

        if match.explanation.verification_needed:
            st.markdown("**Requirements to verify:**")
            for v in match.explanation.verification_needed:
                st.markdown(f"⚠ {v}")

        if match.explanation.reasons_unmatched:
            st.markdown("**Why it does not match:**")
            for u in match.explanation.reasons_unmatched:
                st.markdown(f"🔴 {u}")

        st.divider()


def _render_qa_section(class_level: int) -> None:
    """Phases 8, 9, 10, 11: Renders the inline rule-based Q&A section on the same page."""
    st.markdown("### 💬 Scholarship Questions")
    st.caption("Have a question about scholarships? Ask below for instant, verified answers.")

    # Contextual suggested questions respecting class_level (Phase 9)
    st.markdown("**Try asking:**")
    sugg_cols = st.columns(4)
    suggested = [
        f"What scholarships are available for Class {class_level}?",
        "What is the income limit for NMMSS?",
        "Who can apply for PM-YASASVI?",
        "What documents are commonly required?",
    ]

    selected_suggestion = None
    for idx, (col, pr) in enumerate(zip(sugg_cols, suggested)):
        with col:
            if st.button(pr, key=f"unified_sugg_{idx}", use_container_width=True):
                selected_suggestion = pr

    # Search / Query Input (Phase 8)
    query_text = st.text_input(
        "Ask about scholarships:",
        value=selected_suggestion if selected_suggestion else "",
        placeholder="e.g. What is the income limit for NMMSS? or Who can apply for PM-YASASVI?",
        key="unified_qa_query_input",
    )

    col_btn, _ = st.columns([1, 4])
    with col_btn:
        ask_clicked = st.button("Ask", type="primary", icon=":material/search:", key="btn_unified_ask")

    # Inline response rendering (Phases 10 & 11)
    if (ask_clicked or selected_suggestion) and query_text.strip():
        canonical_profile = st.session_state.get("profile_canonical")
        res = ask_question(
            question=query_text.strip(),
            student_profile=canonical_profile,
            academic_year="2026-27",
        )

        st.write("")
        st.markdown(
            f"""
            <div style="background: var(--surface-container-high); border: 1px solid var(--outline-variant); border-left: 4px solid var(--md-primary); border-radius: 12px; padding: 1.4rem; margin-top: 1rem;">
                <div style="font-size: 0.82rem; font-weight: 700; color: var(--md-primary); text-transform: uppercase; margin-bottom: 4px;">
                    Question
                </div>
                <div style="font-size: 1.05rem; font-weight: 600; color: var(--on-surface); margin-bottom: 12px;">
                    "{query_text.strip()}"
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            f"""
            <div style="background: var(--surface-container-low); border: 1px solid var(--outline-variant); border-radius: 12px; padding: 1.4rem; margin-top: 0.5rem; line-height: 1.6;">
            """,
            unsafe_allow_html=True,
        )
        st.markdown(res["answer_markdown"])
        st.markdown(
            """
                <div style="font-size: 0.75rem; color: var(--text-secondary); margin-top: 12px; border-top: 1px dashed var(--outline-variant); padding-top: 8px;">
                    <b>Source:</b> National Scholarship Portal (AY 2026-27 Guidelines)
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
