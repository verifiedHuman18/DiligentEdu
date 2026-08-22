"""Minimalist Top Bar with Corner Brand, Role Badge, Settings, and Switch Role Buttons."""

import textwrap

import streamlit as st

from frontend.state import get_student_class_level, get_user_role, logout, navigate_to


def render_navbar(selected_class: str = "Class 10", student_id: str = "student_001") -> str:
    """Renders the role-aware ultra-minimal top bar with DiligentEdu brand, role identity badge, settings, and switch role buttons."""
    current_screen = st.session_state.get("current_screen", "home")
    role = get_user_role() or "student"
    class_level = get_student_class_level()

    # Brand Title Subtext based on Role
    brand_sub = "Teacher Portal" if role == "teacher" else "NCERT Science"

    # Profile Badge based on Role
    if role == "teacher":
        teacher_id = st.session_state.get("teacher_id", "teacher_001")
        badge_html = (
            f'<span style="background: var(--surface-container-high); color: var(--on-surface); font-size: 0.8rem; font-weight: 600; padding: 4px 10px; border-radius: 20px; border: 1px solid var(--outline-variant); display: inline-flex; align-items: center; gap: 4px;">'
            f'<span class="material-symbols-outlined" style="font-size: 0.95rem; color: var(--md-tertiary);">supervisor_account</span>'
            f"{teacher_id} · Educator"
            f"</span>"
        )
    else:
        badge_html = (
            f'<span style="background: var(--surface-container-high); color: var(--on-surface); font-size: 0.8rem; font-weight: 600; padding: 4px 10px; border-radius: 20px; border: 1px solid var(--outline-variant); display: inline-flex; align-items: center; gap: 4px;">'
            f'<span class="material-symbols-outlined" style="font-size: 0.95rem; color: var(--md-primary);">person</span>'
            f"{student_id} · Class {class_level}"
            f"</span>"
        )

    # Top Bar: Brand on Left, Role Chip + Settings + Switch Role on Right
    left_col, right_col = st.columns([3.2, 2.8])

    with left_col:
        st.markdown(
            textwrap.dedent(f"""\
<div style="display: flex; align-items: baseline; gap: 0.5rem; padding: 0.1rem 0;">
<span class="brand-corner">Diligent<span class="brand-corner-accent">Edu</span></span>
<span class="brand-corner-sub">{brand_sub}</span>
</div>\
"""),
            unsafe_allow_html=True,
        )

    with right_col:
        r_c1, r_c2, r_c3 = st.columns([3.5, 0.75, 0.75])
        with r_c1:
            profile_bar_html = textwrap.dedent(f"""\
<div style="display: flex; justify-content: flex-end; align-items: center; height: 100%; gap: 6px; padding-top: 4px;">
{badge_html}
</div>\
""")
            st.markdown(profile_bar_html, unsafe_allow_html=True)
        with r_c2:
            is_settings = current_screen == "settings"
            default_home = "teacher" if role == "teacher" else "home"
            if st.button(
                "",
                icon=":material/settings:",
                key="top_btn_settings",
                help="Settings & Configuration",
            ):
                navigate_to("settings" if not is_settings else default_home)
                st.rerun()
        with r_c3:
            if st.button(
                "",
                icon=":material/logout:",
                key="top_btn_switch_role",
                help="Switch Role / Sign Out",
            ):
                logout()
                st.rerun()

    st.write("")

    return st.session_state.get("current_screen", "home")
