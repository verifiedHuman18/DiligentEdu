"""Home Screen with Class-Scoped Action Plan, SWAT-Annotated Curriculum Navigator, and Zero-LLM Fast Execution (Phases 9-17)."""

import textwrap
from typing import Optional

import streamlit as st

from backend.analytics.action_plan import generate_action_plan
from backend.analytics.swat import get_student_swat
from backend.curriculum.service import get_ncert_curriculum
from frontend.state import get_student_class_level, navigate_to


def render_home_screen(
    selected_class: Optional[str] = None, student_id: str = "student_001"
) -> None:
    """Renders the Home Screen with Action Plan, interactive curriculum navigator with SWAT indicators, and module action cards."""
    from frontend.state import get_student_subject

    # 1. Fetch active student data with master class & subject isolation (0 Gemini calls, Phase 14)
    class_level = get_student_class_level()
    subject = get_student_subject()

    col_hdr_1, col_hdr_2 = st.columns([0.7, 0.3])
    with col_hdr_2:
        from frontend.state import set_student_subject

        new_subj = st.selectbox(
            "Subject",
            ["Science", "Mathematics"],
            index=0 if subject == "Science" else 1,
            key="home_subj_switch",
            label_visibility="collapsed",
        )
        if new_subj != subject:
            set_student_subject(new_subj)
            st.rerun()

    swat = get_student_swat(student_id, class_level=class_level, subject=subject)
    has_data = swat.get("has_data", False)
    student_name = st.session_state.get("user_name", student_id)

    # Single-line clean SVG vector for hero header
    bg_vector_svg = '<svg class="m3-hero-bg-svg" viewBox="0 0 600 240" fill="none" xmlns="http://www.w3.org/2000/svg"><g transform="translate(110, 110)"><circle cx="0" cy="0" r="22" fill="var(--md-primary)" /><ellipse rx="90" ry="32" transform="rotate(0)" stroke="var(--md-primary)" stroke-width="3" /><circle cx="90" cy="0" r="8" fill="var(--md-amber)" /><ellipse rx="90" ry="32" transform="rotate(60)" stroke="var(--md-secondary)" stroke-width="3" /><circle cx="-45" cy="78" r="8" fill="var(--md-cyan)" /><ellipse rx="90" ry="32" transform="rotate(120)" stroke="var(--md-tertiary)" stroke-width="3" /><circle cx="-45" cy="-78" r="8" fill="var(--md-error)" /></g><g transform="translate(290, 80)"><circle cx="0" cy="0" r="42" fill="var(--md-amber)" /><ellipse rx="80" ry="20" transform="rotate(-18)" stroke="var(--md-amber-container)" stroke-width="10" /><ellipse rx="80" ry="20" transform="rotate(-18)" stroke="var(--md-amber)" stroke-width="4" /><circle cx="18" cy="-14" r="6" fill="var(--md-on-amber-container)" /></g><g transform="translate(450, 105)"><path d="M-18 -65 L18 -65 L18 -26 L56 50 C62 60 56 70 42 70 L-42 70 C-56 70 -62 60 -56 50 L-18 -26 Z" fill="var(--surface-container-low)" stroke="var(--md-cyan)" stroke-width="4" /><path d="M-36 30 L36 30 L42 62 C43 67 39 70 34 70 L-34 70 C-39 70 -43 67 -42 62 Z" fill="var(--md-cyan)" /><circle cx="-8" cy="-42" r="6" fill="var(--md-cyan)" /><circle cx="10" cy="-62" r="7" fill="var(--md-cyan)" /><circle cx="-4" cy="-85" r="9" fill="var(--md-cyan)" /></g><g transform="translate(565, 120)"><path d="M-18 -85 Q0 -42 -18 0 Q-36 42 -18 85" stroke="var(--md-secondary)" stroke-width="4.5" fill="none" /><path d="M18 -85 Q0 -42 18 0 Q36 42 18 85" stroke="var(--md-tertiary)" stroke-width="4.5" fill="none" /><line x1="-18" y1="-70" x2="18" y2="-70" stroke="var(--md-primary)" stroke-width="3" /><line x1="-8" y1="-35" x2="8" y2="-35" stroke="var(--md-amber)" stroke-width="3" /><line x1="-18" y1="0" x2="18" y2="0" stroke="var(--md-error)" stroke-width="3" /><line x1="-8" y1="35" x2="8" y2="35" stroke="var(--md-cyan)" stroke-width="3" /><line x1="-18" y1="70" x2="18" y2="70" stroke="var(--md-secondary)" stroke-width="3" /></g><g fill="var(--md-amber)"><polygon points="190,25 193,33 201,36 193,39 190,47 187,39 179,36 187,33" /><polygon points="380,165 382,171 388,173 382,175 380,181 378,175 372,173 378,171" /><polygon points="510,20 512,25 517,26 512,28 510,33 508,28 503,26 508,25" /><circle cx="40" cy="50" r="4" fill="var(--md-primary)" /><circle cx="360" cy="30" r="4.5" fill="var(--md-secondary)" /></g></svg>'

    uploaded_count = swat.get("uploaded_materials_count", 0)

    # Top Hero / Greeting Banner
    if has_data:
        avg_score = swat["overall"]["average"]
        total_q = swat["overall"]["total_questions"]
        total_corr = swat["overall"]["total_correct"]
        quizzes_count = swat["overall"]["quizzes_attempted"]

        hero_html = textwrap.dedent(f"""\
<div class="m3-hero-card">
{bg_vector_svg}
<div class="m3-hero-content">
<div class="m3-hero-title">
Welcome, <span style="color: var(--md-primary);">{student_name}</span>
</div>
<div class="m3-chips-group">
<span class="m3-chip m3-chip-cyan"><span class="material-symbols-outlined" style="font-size: 1.1rem;">description</span> Material: {uploaded_count} Active</span>
</div>
<div class="m3-stats-grid">
<div class="m3-stat-card" style="border-left: 4px solid var(--md-tertiary);">
<div class="m3-stat-label">Mastery Average</div>
<div class="m3-stat-val" style="color: var(--md-tertiary);">{avg_score}%</div>
</div>
<div class="m3-stat-card" style="border-left: 4px solid var(--md-secondary);">
<div class="m3-stat-label">Quizzes Completed</div>
<div class="m3-stat-val" style="color: var(--md-secondary);">{quizzes_count}</div>
</div>
<div class="m3-stat-card" style="border-left: 4px solid var(--md-primary);">
<div class="m3-stat-label">Questions Correct</div>
<div class="m3-stat-val" style="color: var(--md-primary);">{total_corr} / {total_q}</div>
</div>
</div>
</div>
</div>\
""")
        st.markdown(hero_html, unsafe_allow_html=True)
    else:
        hero_html = textwrap.dedent(f"""\
<div class="m3-hero-card" style="min-height: 180px;">
{bg_vector_svg}
<div class="m3-hero-content">
<div class="m3-hero-title">
Welcome, <span style="color: var(--md-primary);">{student_name}</span>
</div>
<div class="m3-chips-group" style="margin-bottom: 0.8rem;">
<span class="m3-chip m3-chip-cyan"><span class="material-symbols-outlined" style="font-size: 1.1rem;">description</span> Material: {uploaded_count} Active</span>
</div>
<div style="font-size: 1.0rem; color: var(--text-secondary); line-height: 1.5; max-width: 650px;">
Welcome! Explore your curriculum, upload personal reference books, take practice quizzes, or ask doubt questions below.
</div>
</div>
</div>\
""")
        st.markdown(hero_html, unsafe_allow_html=True)

    st.write("")

    # SECTION 1: YOUR ACTION PLAN
    st.markdown(
        """
        <div class="section-header-bar">
            <div>
                <h4 class="section-title-text">Your Action Plan</h4>
                <div class="section-subtitle-text">Priority study recommendations tailored to your recent mastery and teacher guidance.</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    plan = generate_action_plan(
        student_id, class_level=class_level, subject=subject, swat=swat
    )
    is_custom = plan.get("is_customized", False)

    if (has_data or is_custom) and plan.get("actions"):
        if is_custom:
            teacher_note_text = (
                plan.get("teacher_notes")
                or "Your teacher has assigned these specific priority topics for you."
            )
            st.markdown(
                f"""
                <div style="background: var(--surface-container); border-left: 4px solid var(--md-primary); border-radius: 8px; padding: 12px 16px; margin-bottom: 14px;">
                    <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px;">
                        <span style="background: var(--md-primary); color: var(--on-primary); font-weight: 700; font-size: 0.76rem; padding: 2px 8px; border-radius: 4px;">TEACHER ASSIGNED</span>
                        <span style="font-weight: 700; font-size: 0.9rem; color: var(--on-surface);">Customized Study Plan</span>
                    </div>
                    <div style="font-size: 0.86rem; color: var(--on-surface-variant);">{teacher_note_text}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        top_actions = plan["actions"][:3]
        act_cols = st.columns(len(top_actions))
        for idx, (col, act) in enumerate(zip(act_cols, top_actions)):
            with col:
                is_t_act = act.get("is_teacher_assigned", False)
                p_label = (
                    f"Priority {act['priority_rank']} · Teacher Assigned"
                    if (is_custom or is_t_act)
                    else f"Priority {act['priority_rank']} Target"
                )
                score_str = f"{act['score']}%" if act["score"] is not None else "Not attempted"
                ch_title = (
                    f"Ch {act['chapter_number']}: {act['chapter']}"
                    if act.get("chapter_number")
                    else act["chapter"]
                )
                diff_str = act.get("difficulty", "medium").capitalize()

                with st.container(border=True):
                    st.markdown(
                        f"""
                        <div style="min-height: 135px; display: flex; flex-direction: column; margin-bottom: 5px;">
                            <div style="font-size: 0.78rem; font-weight: 700; color: var(--md-primary); margin-bottom: 4px; text-transform: uppercase; letter-spacing: 0.5px; flex-shrink: 0;">{p_label}</div>
                            <div style="font-size: 0.98rem; font-weight: 700; color: var(--on-surface); margin-bottom: 2px; flex-shrink: 0;">{ch_title}</div>
                            <div style="font-size: 0.84rem; color: var(--md-secondary); font-weight: 600; margin-bottom: 6px; flex-shrink: 0;">
                                Score: {score_str} &nbsp;·&nbsp; Target: `{diff_str}`
                            </div>
                            <div style="font-size: 0.8rem; color: var(--on-surface-variant);">{act["reason"]}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    btn_key = f"home_action_btn_{class_level}_{idx}_{act['chapter']}"
                    btn_type = "primary" if act["priority_rank"] == 1 else "secondary"
                    if st.button(
                        "Start Practice",
                        icon=":material/play_arrow:",
                        key=btn_key,
                        type=btn_type,
                        use_container_width=True,
                        help=f"Practice {act['chapter']} now ({diff_str} difficulty)",
                    ):
                        st.session_state.quiz_difficulty = act["difficulty"]
                        navigate_to("quiz")
                        st.rerun()

    else:
        # Unattempted Student Onboarding State
        st.markdown(
            """
            <div style="background: var(--surface-container-low); border: 1px solid var(--outline-variant); border-radius: 10px; padding: 18px; text-align: center; margin-bottom: 12px;">
                <div style="font-size: 1.05rem; font-weight: 700; color: var(--on-surface); margin-bottom: 4px;">Start Exploring Your Curriculum</div>
                <div style="font-size: 0.86rem; color: var(--on-surface-variant); max-width: 540px; margin: 0 auto 12px auto;">
                    You haven't attempted any quizzes yet. Take an introductory diagnostic quiz to unlock your personal mastery roadmap.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        c_onb1, c_onb2, c_onb3 = st.columns([1, 1.6, 1])
        with c_onb2:
            if st.button(
                "Take Your First Quiz",
                type="primary",
                icon=":material/play_arrow:",
                key="home_onboarding_quiz_btn",
                use_container_width=True,
            ):
                navigate_to("quiz")
                st.rerun()

    st.write("")
    st.write("")

    # SECTION 2: Quick Action Modules
    st.markdown(
        """
        <div class="section-header-bar">
            <div>
                <h4 class="section-title-text">Core Learning Modules</h4>
                <div class="section-subtitle-text">Direct shortcuts to interactive tutoring, assessments, study twin, study material, analytics, and scholarships.</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button(
            "**NCERT Tutor**\n\nAsk doubts",
            key="btn_module_tutor",
            icon=":material/chat:",
            use_container_width=True,
        ):
            navigate_to("tutor")
            st.rerun()

    with col2:
        if st.button(
            "**Practice Quiz**\n\nQuizzes",
            key="btn_module_quiz",
            icon=":material/quiz:",
            use_container_width=True,
        ):
            navigate_to("quiz")
            st.rerun()

    with col3:
        if st.button(
            "**Study Twin**\n\nPeer match",
            key="btn_module_study_twin",
            icon=":material/group:",
            use_container_width=True,
        ):
            navigate_to("study_twin")
            st.rerun()

    with col4:
        if st.button(
            "**Knowledge Map**\n\nConcept web",
            key="btn_module_knowledge_graph",
            icon=":material/hub:",
            use_container_width=True,
        ):
            navigate_to("knowledge_graph")
            st.rerun()

    st.write("")
    _, col5, col6, col7, _ = st.columns([0.5, 1.0, 1.0, 1.0, 0.5])

    with col5:
        if st.button(
            "**My Material**\n\nUpload notes",
            key="btn_module_study_material",
            icon=":material/menu_book:",
            use_container_width=True,
        ):
            navigate_to("study_material")
            st.rerun()

    with col6:
        if st.button(
            "**Analytics**\n\nSWAT metrics",
            key="btn_module_analytics",
            icon=":material/insights:",
            use_container_width=True,
        ):
            navigate_to("swat")
            st.rerun()

    with col7:
        if st.button(
            "**Scholarships**\n\nDiscovery",
            key="btn_module_scholarships",
            icon=":material/verified:",
            use_container_width=True,
        ):
            navigate_to("scholarships")
            st.rerun()

    st.write("")
    st.write("")

    # SECTION 3: NCERT Curriculum Navigator
    st.markdown(
        """
        <div class="section-header-bar">
            <div>
                <h4 class="section-title-text">NCERT Curriculum</h4>
                <div class="section-subtitle-text">Click any chapter below to explore textbook PDF, practice quizzes, or ask questions.</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    curriculum_chapters = get_ncert_curriculum(class_level, subject=subject)
    breakdown = swat.get("chapter_breakdown", {})

    # 2-column interactive navigator with SWAT performance indicators
    ch_col1, ch_col2 = st.columns(2)
    for idx, ch in enumerate(curriculum_chapters):
        target_col = ch_col1 if idx % 2 == 0 else ch_col2
        with target_col:
            ch_num_str = f"{ch['chapter_number']:02d}"
            ch_name = ch["chapter"]
            ch_stats = breakdown.get(ch_name)

            if (
                ch_stats
                and ch_stats.get("status") != "unattempted"
                and ch_stats.get("score") is not None
            ):
                score = ch_stats["score"]
                status = ch_stats.get("status", "average")
                if status == "strong":
                    indicator = f"<span style='color: var(--md-primary); font-weight: 700;'>{score}% (Strong)</span>"
                elif status == "weak":
                    indicator = f"<span style='color: var(--md-error); font-weight: 700;'>{score}% (Weak)</span>"
                else:
                    indicator = f"<span style='color: var(--md-amber); font-weight: 700;'>{score}% (Average)</span>"
            else:
                indicator = "<span style='color: var(--on-surface-variant); font-weight: 600;'>Not Attempted</span>"

            with st.container(border=True):
                st.markdown(
                    f"""
                    <div style="height: 65px; display: flex; flex-direction: column; overflow: hidden; margin-bottom: 5px;">
                        <div style="font-size: 0.95rem; font-weight: 700; color: var(--on-surface); margin-bottom: 4px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;">
                            <span style="color: var(--md-primary); font-size: 0.8rem; text-transform: uppercase;">CH {ch_num_str}</span> &nbsp;{ch_name}
                        </div>
                        <div style="font-size: 0.82rem;">{indicator}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                if st.button(
                    "View Chapter",
                    key=f"home_ch_nav_btn_{class_level}_{ch['chapter_number']}",
                    icon=":material/arrow_forward:",
                    use_container_width=True,
                    help=f"View details and study options for {ch_name}",
                ):
                    st.session_state.active_chapter_detail = ch
                    navigate_to("chapter")
                    st.rerun()
