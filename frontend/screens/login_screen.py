"""Role Selection & Step-Based Authentication Screens for DiligentEdu (Flat, Minimalist Layout)."""

import textwrap

import streamlit as st

from frontend.state import get_student_class_level, set_student_class_level, set_user_role


def render_login_screen() -> None:
    """Renders the step-based login flow: Step 1 (Role Selection) -> Step 2 (Dedicated Role Login)."""
    login_step = st.session_state.get("login_step", "select_role")

    if login_step == "student_login":
        _render_student_login_step()
    elif login_step == "teacher_login":
        _render_teacher_login_step()
    else:
        _render_role_selection_step()


def _render_role_selection_step() -> None:
    """Step 1: Flat Role Selection Portal (Choose Student or Teacher without card boxes)."""
    hero_html = textwrap.dedent("""\
<div class="login-hero">
<div class="login-brand">Diligent<span class="login-brand-accent">Edu</span></div>
<div class="login-tagline">NCERT Science Assistant & Diagnostic Portal</div>
<div class="login-subtagline">Select your role to access your personalized learning or pedagogical workspace</div>
</div>\
""")
    st.markdown(hero_html, unsafe_allow_html=True)
    st.write("")

    col_pad_left, col_student, col_div, col_teacher, col_pad_right = st.columns(
        [0.1, 1.2, 0.1, 1.2, 0.1]
    )

    # 1. Student Role Option (Flat)
    with col_student:
        student_header_html = textwrap.dedent("""\
<div style="margin-bottom: 0.8rem;">
<div style="display: flex; align-items: center; gap: 10px; margin-bottom: 0.4rem;">
<span class="material-symbols-outlined" style="font-size: 1.8rem; color: var(--md-primary);">school</span>
<div style="font-size: 1.35rem; font-weight: 700; color: var(--text-primary);">Student Portal</div>
</div>
<div style="font-size: 0.78rem; color: var(--md-primary); font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.5rem;">Learner Workspace</div>
<div style="font-size: 0.9rem; color: var(--text-secondary); line-height: 1.5; min-height: 54px;">
Interactive textbook AI tutor, chapter practice quizzes, personalized SWAT mastery analytics, and national scholarship discovery.
</div>
</div>\
""")
        st.markdown(student_header_html, unsafe_allow_html=True)
        st.write("")
        if st.button(
            "Continue as Student",
            key="btn_goto_student_login",
            type="primary",
            icon=":material/arrow_forward:",
            use_container_width=True,
        ):
            st.session_state.login_step = "student_login"
            st.rerun()

    # 2. Teacher Role Option (Flat)
    with col_teacher:
        teacher_header_html = textwrap.dedent("""\
<div style="margin-bottom: 0.8rem;">
<div style="display: flex; align-items: center; gap: 10px; margin-bottom: 0.4rem;">
<span class="material-symbols-outlined" style="font-size: 1.8rem; color: var(--md-tertiary);">monitoring</span>
<div style="font-size: 1.35rem; font-weight: 700; color: var(--text-primary);">Teacher Portal</div>
</div>
<div style="font-size: 0.78rem; color: var(--md-tertiary); font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.5rem;">Educator Workspace</div>
<div style="font-size: 0.9rem; color: var(--text-secondary); line-height: 1.5; min-height: 54px;">
Pedagogical diagnostics, student intervention alerts, 4-category cohort SWAT breakdown, and chronological quiz histories.
</div>
</div>\
""")
        st.markdown(teacher_header_html, unsafe_allow_html=True)
        st.write("")
        if st.button(
            "Continue as Teacher",
            key="btn_goto_teacher_login",
            type="primary",
            icon=":material/arrow_forward:",
            use_container_width=True,
        ):
            st.session_state.login_step = "teacher_login"
            st.rerun()


def _render_student_login_step() -> None:
    """Step 2A: Dedicated Student Sign In Screen (Flat, no card box)."""
    if st.button(
        "Back to Role Selection",
        icon=":material/arrow_back:",
        type="secondary",
        key="btn_back_to_roles_from_student",
    ):
        st.session_state.login_step = "select_role"
        st.rerun()

    c_left, c_center, c_right = st.columns([0.3, 1.4, 0.3])
    with c_center:
        student_form_header = textwrap.dedent("""\
<div style="margin: 1rem 0 1.5rem 0;">
<div style="display: flex; align-items: center; gap: 10px; margin-bottom: 0.3rem;">
<span class="material-symbols-outlined" style="font-size: 1.8rem; color: var(--md-primary);">school</span>
<div style="font-size: 1.45rem; font-weight: 700; color: var(--text-primary);">Student Sign In</div>
</div>
<div style="font-size: 0.9rem; color: var(--text-secondary);">Enter your student details to access your learning portal</div>
</div>\
""")
        st.markdown(student_form_header, unsafe_allow_html=True)

        student_id = st.text_input(
            "Student ID / Name",
            value=st.session_state.get("student_id", "student_001"),
            key="login_student_id_input",
            help="Unique identifier for tracking your progress and quiz attempts.",
        )

        curr_cls = get_student_class_level()
        student_class = st.radio(
            "Class / Standard",
            options=["Class 10", "Class 9"],
            index=0 if curr_cls == 10 else 1,
            horizontal=True,
            key="login_student_class_radio",
        )
        cls_int = 10 if student_class == "Class 10" else 9

        st.write("")
        if st.button(
            "Sign In to Student Portal",
            key="btn_submit_student_login",
            type="primary",
            icon=":material/login:",
            use_container_width=True,
        ):
            set_student_class_level(cls_int)
            st.session_state.student_id = student_id.strip() or "student_001"
            st.session_state.login_step = "select_role"
            set_user_role("student")
            st.rerun()


def _render_teacher_login_step() -> None:
    """Step 2B: Dedicated Teacher Sign In Screen (Flat, no inspection class needed)."""
    if st.button(
        "Back to Role Selection",
        icon=":material/arrow_back:",
        type="secondary",
        key="btn_back_to_roles_from_teacher",
    ):
        st.session_state.login_step = "select_role"
        st.rerun()

    c_left, c_center, c_right = st.columns([0.3, 1.4, 0.3])
    with c_center:
        teacher_form_header = textwrap.dedent("""\
<div style="margin: 1rem 0 1.5rem 0;">
<div style="display: flex; align-items: center; gap: 10px; margin-bottom: 0.3rem;">
<span class="material-symbols-outlined" style="font-size: 1.8rem; color: var(--md-tertiary);">monitoring</span>
<div style="font-size: 1.45rem; font-weight: 700; color: var(--text-primary);">Teacher Sign In</div>
</div>
<div style="font-size: 0.9rem; color: var(--text-secondary);">Enter your educator credentials to access student diagnostic insights</div>
</div>\
""")
        st.markdown(teacher_form_header, unsafe_allow_html=True)

        teacher_id = st.text_input(
            "Teacher Name / ID",
            value=st.session_state.get("teacher_id", "teacher_001"),
            key="login_teacher_id_input",
            help="Educator identifier for diagnostics dashboard.",
        )

        st.write("")
        if st.button(
            "Sign In to Teacher Portal",
            key="btn_submit_teacher_login",
            type="primary",
            icon=":material/supervisor_account:",
            use_container_width=True,
        ):
            st.session_state.teacher_id = teacher_id.strip() or "teacher_001"
            st.session_state.login_step = "select_role"
            set_user_role("teacher")
            st.rerun()
