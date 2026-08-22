"""Minimalist Top Bar with Corner Brand and Clean Material Settings Icon Button."""

import textwrap

import streamlit as st

from frontend.state import get_student_class_level, navigate_to


def render_navbar(selected_class: str = "Class 10", student_id: str = "student_001") -> str:
    """
    Renders the ultra-minimal top bar with DiligentEdu brand on the left, and a non-editable student profile chip + settings icon on the right (Phase 16).

    Returns:
        The active screen identifier ('home', 'tutor', 'quiz', 'swat', 'teacher', 'settings').
    """
    current_screen = st.session_state.get("current_screen", "home")
    class_level = get_student_class_level()

    # Top Bar: Brand on Left, Student Chip + Sleek Settings Icon on Right
    left_col, right_col = st.columns([3.5, 2.5])

    with left_col:
        st.markdown(
            textwrap.dedent("""\
<div style="display: flex; align-items: baseline; gap: 0.5rem; padding: 0.1rem 0;">
<span class="brand-corner">Diligent<span class="brand-corner-accent">Edu</span></span>
<span class="brand-corner-sub">NCERT Science</span>
</div>\
"""),
            unsafe_allow_html=True,
        )

    with right_col:
        r_c1, r_c2 = st.columns([4, 1])
        with r_c1:
            st.markdown(
                f"""
                <div style="display: flex; justify-content: flex-end; align-items: center; height: 100%; gap: 6px; padding-top: 4px;">
                    <span style="background: var(--surface-container-high); color: var(--on-surface); font-size: 0.8rem; font-weight: 600; padding: 4px 10px; border-radius: 20px; border: 1px solid var(--outline-variant); display: inline-flex; align-items: center; gap: 4px;">
                        <span class="material-symbols-outlined" style="font-size: 0.95rem;">person</span>
                        {student_id} · Class {class_level}
                    </span>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with r_c2:
            is_settings = current_screen == "settings"
            if st.button(
                "",
                icon=":material/settings:",
                key="top_btn_settings",
                help="Settings & Profile Configuration",
            ):
                navigate_to("settings" if not is_settings else "home")
                st.rerun()

    st.write("")

    return st.session_state.get("current_screen", "home")
