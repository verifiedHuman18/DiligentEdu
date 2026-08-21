"""Home Screen with Large Translucent Background Vector Art, M3 Hero Container, and Aligned Action Buttons with Hover Arrows."""

import textwrap

import streamlit as st

from frontend.state import navigate_to
from src.academic_rag.analytics.swat import get_student_swat
from src.academic_rag.curriculum.service import curriculum_service


def render_home_screen(selected_class: str, student_id: str) -> None:
    """Renders the Home Screen with large translucent background vector illustrations and aligned module buttons."""

    # Fetch active student data
    swat = get_student_swat(student_id)
    has_data = swat.get("has_data", False)
    selected_chapter = st.session_state.get("selected_chapter", "All Chapters")
    class_display = selected_class if selected_class != "All Classes" else "Class 9 & 10"

    # Single-line clean SVG vector to prevent Markdown from interpreting spaces as code blocks
    bg_vector_svg = '<svg class="m3-hero-bg-svg" viewBox="0 0 600 240" fill="none" xmlns="http://www.w3.org/2000/svg"><g transform="translate(110, 110)"><circle cx="0" cy="0" r="22" fill="var(--md-primary)" /><ellipse rx="90" ry="32" transform="rotate(0)" stroke="var(--md-primary)" stroke-width="3" /><circle cx="90" cy="0" r="8" fill="var(--md-amber)" /><ellipse rx="90" ry="32" transform="rotate(60)" stroke="var(--md-secondary)" stroke-width="3" /><circle cx="-45" cy="78" r="8" fill="var(--md-cyan)" /><ellipse rx="90" ry="32" transform="rotate(120)" stroke="var(--md-tertiary)" stroke-width="3" /><circle cx="-45" cy="-78" r="8" fill="var(--md-error)" /></g><g transform="translate(290, 80)"><circle cx="0" cy="0" r="42" fill="var(--md-amber)" /><ellipse rx="80" ry="20" transform="rotate(-18)" stroke="var(--md-amber-container)" stroke-width="10" /><ellipse rx="80" ry="20" transform="rotate(-18)" stroke="var(--md-amber)" stroke-width="4" /><circle cx="18" cy="-14" r="6" fill="var(--md-on-amber-container)" /></g><g transform="translate(450, 105)"><path d="M-18 -65 L18 -65 L18 -26 L56 50 C62 60 56 70 42 70 L-42 70 C-56 70 -62 60 -56 50 L-18 -26 Z" fill="var(--surface-container-low)" stroke="var(--md-cyan)" stroke-width="4" /><path d="M-36 30 L36 30 L42 62 C43 67 39 70 34 70 L-34 70 C-39 70 -43 67 -42 62 Z" fill="var(--md-cyan)" /><circle cx="-8" cy="-42" r="6" fill="var(--md-cyan)" /><circle cx="10" cy="-62" r="7" fill="var(--md-cyan)" /><circle cx="-4" cy="-85" r="9" fill="var(--md-cyan)" /></g><g transform="translate(565, 120)"><path d="M-18 -85 Q0 -42 -18 0 Q-36 42 -18 85" stroke="var(--md-secondary)" stroke-width="4.5" fill="none" /><path d="M18 -85 Q0 -42 18 0 Q36 42 18 85" stroke="var(--md-tertiary)" stroke-width="4.5" fill="none" /><line x1="-18" y1="-70" x2="18" y2="-70" stroke="var(--md-primary)" stroke-width="3" /><line x1="-8" y1="-35" x2="8" y2="-35" stroke="var(--md-amber)" stroke-width="3" /><line x1="-18" y1="0" x2="18" y2="0" stroke="var(--md-error)" stroke-width="3" /><line x1="-8" y1="35" x2="8" y2="35" stroke="var(--md-cyan)" stroke-width="3" /><line x1="-18" y1="70" x2="18" y2="70" stroke="var(--md-secondary)" stroke-width="3" /></g><g fill="var(--md-amber)"><polygon points="190,25 193,33 201,36 193,39 190,47 187,39 179,36 187,33" /><polygon points="380,165 382,171 388,173 382,175 380,181 378,175 372,173 378,171" /><polygon points="510,20 512,25 517,26 512,28 510,33 508,28 503,26 508,25" /><circle cx="40" cy="50" r="4" fill="var(--md-primary)" /><circle cx="360" cy="30" r="4.5" fill="var(--md-secondary)" /></g></svg>'

    # 1. Hero Card with Translucent Background Vectors & Student Details on top
    if has_data:
        avg_score = swat["overall"]["average"]
        total_q = swat["overall"]["total_questions"]
        total_corr = swat["overall"]["total_correct"]
        quizzes_count = swat["overall"]["quizzes_attempted"]

        top_strength = swat["strengths"][0]["chapter"] if swat.get("strengths") else "In Progress"
        focus_area = (
            swat["weak_topics"][0]["chapter"]
            if swat.get("weak_topics")
            else (
                swat["average_topics"][0]["chapter"]
                if swat.get("average_topics")
                else "None identified"
            )
        )

        hero_html = textwrap.dedent(f"""\
<div class="m3-hero-card">
{bg_vector_svg}
<div class="m3-hero-content">
<div class="m3-hero-title">
Student Profile: <span style="color: var(--md-primary);">{student_id}</span>
</div>
<div class="m3-chips-group">
<span class="m3-chip m3-chip-primary"><span class="material-symbols-outlined" style="font-size: 1.1rem;">school</span> Grade: {class_display}</span>
<span class="m3-chip m3-chip-purple"><span class="material-symbols-outlined" style="font-size: 1.1rem;">auto_stories</span> Focus: {selected_chapter}</span>
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
<div class="m3-stat-card" style="border-left: 4px solid var(--md-tertiary);">
<div class="m3-stat-label">Top Strength</div>
<div class="m3-stat-val" style="font-size: 1.1rem; color: var(--md-tertiary);">{top_strength}</div>
</div>
<div class="m3-stat-card" style="border-left: 4px solid var(--md-amber);">
<div class="m3-stat-label">Needs Focus</div>
<div class="m3-stat-val" style="font-size: 1.1rem; color: var(--md-amber);">{focus_area}</div>
</div>
</div>
</div>
</div>\
""")
        st.markdown(hero_html, unsafe_allow_html=True)

    else:
        hero_html = textwrap.dedent(f"""\
<div class="m3-hero-card" style="min-height: 220px;">
{bg_vector_svg}
<div class="m3-hero-content">
<div class="m3-hero-title">
Student Profile: <span style="color: var(--md-primary);">{student_id}</span>
</div>
<div class="m3-chips-group" style="margin-bottom: 1.25rem;">
<span class="m3-chip m3-chip-primary"><span class="material-symbols-outlined" style="font-size: 1.1rem;">school</span> Grade: {class_display}</span>
<span class="m3-chip m3-chip-purple"><span class="material-symbols-outlined" style="font-size: 1.1rem;">auto_stories</span> Focus: {selected_chapter}</span>
</div>
<div style="font-size: 1.08rem; color: var(--text-secondary); line-height: 1.6; max-width: 650px;">
Welcome to NCERT Science! Choose a module below to ask questions, take practice quizzes, or track your mastery.
</div>
</div>
</div>\
""")
        st.markdown(hero_html, unsafe_allow_html=True)

    # 2. Material 3 Interactive Module Action Buttons with Animated Hover Arrows
    st.markdown("### Modules")
    st.write("")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button(
            "**NCERT Tutor**\n\nAsk questions & get citations",
            key="btn_module_tutor",
            icon=":material/chat:",
            use_container_width=True,
        ):
            navigate_to("tutor")
            st.rerun()

    with col2:
        if st.button(
            "**Practice Quiz**\n\nChapter quizzes & instant scoring",
            key="btn_module_quiz",
            icon=":material/quiz:",
            use_container_width=True,
        ):
            navigate_to("quiz")
            st.rerun()

    with col3:
        if st.button(
            "**Student Analytics**\n\nMastery breakdown & quiz history",
            key="btn_module_analytics",
            icon=":material/insights:",
            use_container_width=True,
        ):
            navigate_to("swat")
            st.rerun()

    with col4:
        if st.button(
            "**Teacher View**\n\nDiagnostic alerts & class metrics",
            key="btn_module_teacher",
            icon=":material/school:",
            use_container_width=True,
        ):
            navigate_to("teacher")
            st.rerun()

    st.write("")
    st.write("")

    # 3. NCERT Curriculum Overview
    st.markdown("### NCERT Science Curriculum")
    st.caption("Expand below to view all chapters covered in Class 9 and Class 10.")

    curr1, curr2 = st.columns(2)
    with curr1:
        with st.expander("Class 9 Science (13 Chapters)", expanded=False):
            cls9_chs = curriculum_service.get_chapters_for_grade(9)
            for ch in cls9_chs:
                st.markdown(f"**Ch {ch.chapter_number}:** {ch.chapter_title}")

    with curr2:
        with st.expander("Class 10 Science (13 Chapters)", expanded=False):
            cls10_chs = curriculum_service.get_chapters_for_grade(10)
            for ch in cls10_chs:
                st.markdown(f"**Ch {ch.chapter_number}:** {ch.chapter_title}")
