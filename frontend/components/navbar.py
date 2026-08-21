"""Minimalist Top Bar with Corner Brand and Clean Material Settings Icon Button."""

import textwrap

import streamlit as st

from frontend.state import navigate_to


def render_navbar(selected_class: str = "All Classes", student_id: str = "student_001") -> str:
    """
    Renders the ultra-minimal top bar with DiligentEdu brand in the corner and a sleek settings icon.

    Returns:
        The active screen identifier ('home', 'tutor', 'quiz', 'swat', 'teacher', 'settings').
    """
    current_screen = st.session_state.get("current_screen", "home")

    # Top Bar: Brand on Left, Sleek Settings Icon on Right
    left_col, right_col = st.columns([5, 1])

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
        is_settings = current_screen == "settings"
        if st.button(
            "", icon=":material/settings:", key="top_btn_settings", help="Settings & Configuration"
        ):
            navigate_to("settings" if not is_settings else "home")
            st.rerun()

    st.write("")

    return st.session_state.get("current_screen", "home")
