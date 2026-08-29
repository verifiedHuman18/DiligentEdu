"""Study Twin Screen for DiligentEdu (Academic Peer Compatibility Hub)."""

import streamlit as st

from backend.analytics.study_twin import find_study_twin
from frontend.components.navigation import render_back_to_home
from frontend.state import (
    get_student_class_level,
    get_student_subject,
    navigate_to,
    set_student_subject,
)


def render_study_twin_screen(student_id: str = "student_001") -> None:
    """Renders the comprehensive Study Twin compatibility screen."""
    render_back_to_home("study_twin")

    class_level = get_student_class_level()
    subject = get_student_subject()

    # Header and Subject Toggle
    col_hdr_1, col_hdr_2 = st.columns([0.7, 0.3])
    with col_hdr_1:
        st.markdown("###  Study Twin")
        st.caption(
            "Find a peer whose learning priorities, syllabus pace, and concept weaknesses align with yours."
        )
    with col_hdr_2:
        new_subj = st.selectbox(
            "Subject",
            ["Science", "Mathematics"],
            index=0 if subject == "Science" else 1,
            key="twin_subj_switch",
            label_visibility="collapsed",
        )
        if new_subj != subject:
            set_student_subject(new_subj)
            st.rerun()

    st.write("")

    # Run matching service (Deterministic, 0 LLM calls)
    force_refresh = st.session_state.pop("twin_force_refresh", False)
    with st.spinner("Analyzing multidimensional academic similarity across Class syllabus..."):
        match = find_study_twin(
            student_id=student_id,
            class_level=class_level,
            subject=subject,
            force_refresh=force_refresh,
        )

    # 1. State: Insufficient Data (Phase 13)
    if match.status == "insufficient_data":
        insuf_html = (
            '<div style="background: var(--surface-container-low); border: 1px dashed var(--outline-variant); border-radius: 16px; padding: 32px 24px; text-align: center; margin: 12px 0;">'
            '<div style="font-size: 2.0rem; margin-bottom: 8px;"><span class="material-symbols-outlined" style="font-size: 2.5rem; color: var(--md-primary);">assignment_ind</span></div>'
            '<div style="font-size: 1.2rem; font-weight: 700; color: var(--on-surface); margin-bottom: 8px;">Build Your Study Profile</div>'
            '<div style="font-size: 0.92rem; color: var(--on-surface-variant); max-width: 540px; margin: 0 auto 20px auto; line-height: 1.6;">'
            "To pair you with an academically compatible Study Twin, the system needs a diagnostic baseline of your concept mastery and action priorities."
            "</div>"
            "</div>"
        )
        st.markdown(insuf_html, unsafe_allow_html=True)
        st.write("")
        c_btn1, c_btn2, c_btn3 = st.columns([1, 1.4, 1])
        with c_btn2:
            if st.button(
                "Take a Practice Quiz to Find Twin",
                type="primary",
                icon=":material/quiz:",
                use_container_width=True,
                key="btn_twin_start_quiz",
            ):
                navigate_to("quiz")
                st.rerun()
        return

    # 2. State: No Candidates or Low Similarity
    if match.status in ("no_candidates", "no_strong_match"):
        score_display = (
            f" (Closest match: {match.similarity_score}%)" if match.similarity_score > 0 else ""
        )
        no_cand_html = (
            '<div style="background: var(--surface-container); border: 1px solid var(--outline-variant); border-radius: 16px; padding: 32px 24px; text-align: center; margin: 12px 0;">'
            '<div style="font-size: 2.0rem; margin-bottom: 8px;"><span class="material-symbols-outlined" style="font-size: 2.5rem; color: var(--md-secondary);">search_off</span></div>'
            f'<div style="font-size: 1.15rem; font-weight: 700; color: var(--on-surface); margin-bottom: 6px;">No Active Study Twin Found Yet{score_display}</div>'
            f'<div style="font-size: 0.90rem; color: var(--on-surface-variant); max-width: 520px; margin: 0 auto 18px auto; line-height: 1.5;">{match.explanation}</div>'
            "</div>"
        )
        st.markdown(no_cand_html, unsafe_allow_html=True)
        st.write("")
        c_r1, c_r2, c_r3 = st.columns([1, 1.2, 1])
        with c_r2:
            if st.button(
                "Re-Check Candidates",
                icon=":material/refresh:",
                use_container_width=True,
                key="btn_twin_recheck",
            ):
                st.session_state.twin_force_refresh = True
                st.rerun()
        return

    # 3. State: Active Study Twin Match Found (Phases 17-18)
    sim_score = match.similarity_score
    score_color = (
        "var(--md-primary)"
        if sim_score >= 70
        else ("var(--md-amber)" if sim_score >= 50 else "var(--md-cyan)")
    )
    # Fetch Twin's real name from DB
    from backend.storage.repository import get_prisma_client

    db = get_prisma_client()
    if not db.is_connected():
        db.connect()
    twin_user = db.user.find_unique(where={"id": match.twin_student_id})
    twin_name = (
        twin_user.name
        if twin_user and twin_user.name
        else twin_user.email.split("@")[0]
        if twin_user and twin_user.email
        else "Peer Student"
    )

    hero_card_html = (
        f'<div style="background: var(--surface-container); border: 1px solid var(--outline-variant); border-radius: 18px; padding: 24px; margin-bottom: 20px; box-shadow: 0 4px 20px rgba(0,0,0,0.18);">'
        f'<div style="display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 16px; margin-bottom: 14px;">'
        f'<div style="display: flex; align-items: center; gap: 12px;">'
        f'<div style="width: 52px; height: 52px; border-radius: 50%; background: var(--surface-container-high); border: 2px solid {score_color}; display: flex; align-items: center; justify-content: center; font-size: 1.6rem; font-weight: 700; color: {score_color};">{twin_name[0].upper() if twin_name else "P"}</div>'
        f"<div>"
        f'<div style="font-size: 1.25rem; font-weight: 700; color: var(--on-surface); display: flex; align-items: center; gap: 8px;">{twin_name} <span style="background: var(--surface-container-high); color: var(--on-surface-variant); font-size: 0.75rem; font-weight: 600; padding: 2px 8px; border-radius: 12px; border: 1px solid var(--outline-variant);">Match Active</span></div>'
        f'<div style="font-size: 0.86rem; color: var(--on-surface-variant); margin-top: 2px;">Matched via multidimensional topic mastery, active focus, and SWAT priorities</div>'
        f"</div>"
        f"</div>"
        f'<div style="background: var(--surface-container-high); border: 1px solid var(--outline-variant); border-radius: 14px; padding: 10px 18px; text-align: center;">'
        f'<div style="font-size: 1.65rem; font-weight: 800; color: {score_color}; line-height: 1;">{sim_score}%</div>'
        f'<div style="font-size: 0.74rem; font-weight: 600; color: var(--on-surface-variant); text-transform: uppercase; letter-spacing: 0.5px; margin-top: 4px;">Study Similarity</div>'
        f"</div>"
        f"</div>"
        f'<div style="background: var(--surface-container-low); border-left: 4px solid {score_color}; border-radius: 8px; padding: 12px 16px; font-size: 0.90rem; color: var(--on-surface); line-height: 1.5;">{match.explanation}</div>'
        f"</div>"
    )
    st.markdown(hero_card_html, unsafe_allow_html=True)

    # 3-Pillar Breakdown
    col_p1, col_p2, col_p3 = st.columns(3)

    with col_p1:
        st.markdown("##### :material/track_changes: Current Focus")
        if match.shared_current_chapters:
            html = '<div style="max-height: 220px; overflow-y: auto; padding-right: 4px;">'
            for ch in match.shared_current_chapters:
                html += f'<div style="background: var(--surface-container-low); padding: 8px 12px; border-radius: 8px; border-left: 3px solid var(--md-cyan); margin-bottom: 6px; font-size: 0.85rem; font-weight: 600;"> {ch}</div>'
            html += "</div>"
            st.markdown(html, unsafe_allow_html=True)
        else:
            st.caption("No concurrent chapter overlap at this moment.")

    with col_p2:
        st.markdown("##### :material/warning: Shared Weaknesses")
        if match.shared_weak_topics:
            html = '<div style="max-height: 220px; overflow-y: auto; padding-right: 4px;">'
            for ch in match.shared_weak_topics:
                html += f'<div style="background: var(--surface-container-low); padding: 8px 12px; border-radius: 8px; border-left: 3px solid var(--md-amber); margin-bottom: 6px; font-size: 0.85rem; font-weight: 600;"> {ch}</div>'
            html += "</div>"
            st.markdown(html, unsafe_allow_html=True)
        else:
            st.caption("No common weak topics identified.")

    with col_p3:
        st.markdown("##### :material/flag: Shared Action Goals")
        if match.shared_action_goals:
            html = '<div style="max-height: 220px; overflow-y: auto; padding-right: 4px;">'
            for ch in match.shared_action_goals:
                html += f'<div style="background: var(--surface-container-low); padding: 8px 12px; border-radius: 8px; border-left: 3px solid var(--md-primary); margin-bottom: 6px; font-size: 0.85rem; font-weight: 600;"> Practice {ch}</div>'
            html += "</div>"
            st.markdown(html, unsafe_allow_html=True)
        else:
            st.caption("Action priorities are independent.")

    st.write("")
    st.divider()

    # Detailed Similarity Breakdown Meters
    st.markdown("##### :material/bar_chart: Academic Alignment Breakdown")
    comps = match.component_scores or {}

    col_m1, col_m2 = st.columns(2)
    with col_m1:
        st.write(f"**Action Plan Priority Overlap:** {comps.get('action_plan_similarity', 0)}%")
        st.progress(comps.get("action_plan_similarity", 0) / 100.0)

        st.write(f"**Weak Topics Alignment:** {comps.get('weak_topics_similarity', 0)}%")
        st.progress(comps.get("weak_topics_similarity", 0) / 100.0)

    with col_m2:
        st.write(
            f"**Current Syllabus Focus Overlap:** {comps.get('current_topics_similarity', 0)}%"
        )
        st.progress(comps.get("current_topics_similarity", 0) / 100.0)

        st.write(f"**Mastery Vector Closeness:** {comps.get('mastery_profile_similarity', 0)}%")
        st.progress(comps.get("mastery_profile_similarity", 0) / 100.0)

    st.write("")
    st.write("")

    # Interactive Action Buttons
    c_act1, c_act2 = st.columns(2)
    with c_act1:
        target_ch = (
            match.shared_weak_topics[0]
            if match.shared_weak_topics
            else (
                match.shared_action_goals[0]
                if match.shared_action_goals
                else (match.shared_current_chapters[0] if match.shared_current_chapters else None)
            )
        )
        btn_txt = f"Practice {target_ch}" if target_ch else "Take Practice Quiz"
        if st.button(
            btn_txt,
            type="primary",
            icon=":material/quiz:",
            use_container_width=True,
            key="btn_twin_practice_shared",
        ):
            if target_ch:
                st.session_state.selected_chapter = target_ch
            navigate_to("quiz")
            st.rerun()

    with c_act2:
        if st.button(
            "Re-Evaluate Study Twin",
            type="secondary",
            icon=":material/refresh:",
            use_container_width=True,
            key="btn_twin_force_recalc",
            help="Recalculate your study twin match against the latest platform activity.",
        ):
            st.session_state.twin_force_refresh = True
            st.rerun()
