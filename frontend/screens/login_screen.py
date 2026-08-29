"""Role Selection & Authentication Screens for DiligentEdu (Firebase Integrated)."""

import textwrap

import streamlit as st

from backend.auth.firebase_auth import sign_in_with_email_and_password
from frontend.state import set_student_class_level, set_user_role
from prisma import Prisma


def get_user_from_db(uid: str):
    db = Prisma()
    db.connect()
    user = db.user.find_unique(where={"id": uid})
    db.disconnect()
    return user


def render_login_screen() -> None:
    """Renders the single Firebase authentication portal."""
    hero_html = textwrap.dedent("""\
<div class="login-hero">
<div class="login-brand">Diligent<span class="login-brand-accent">Edu</span></div>
<div class="login-tagline">Equitable Learning For All</div>
<div class="login-subtagline">Sign in with your school-provided credentials</div>
</div>\
""")
    st.markdown(hero_html, unsafe_allow_html=True)
    st.write("")

    c_left, c_center, c_right = st.columns([0.3, 1.4, 0.3])
    with c_center:
        st.markdown("### Secure Login Portal")

        with st.form("login_form", border=False):
            email = st.text_input(
                "School Email", key="login_email_input", placeholder="name@school.edu"
            )
            password = st.text_input("Password", type="password", key="login_password_input")

            st.write("")
            submitted = st.form_submit_button("Sign In", type="primary", use_container_width=True)

        if submitted:
            if not email or not password:
                st.error("Please provide both email and password.")
                return

            with st.spinner("Authenticating and securely loading workspace..."):
                try:
                    # 1. Firebase Auth
                    auth_data = sign_in_with_email_and_password(email, password)
                    uid = auth_data["localId"]

                    # 2. Check Database for Role
                    # Since the school provides credentials, they should exist in our Prisma DB.
                    # If this is a mock test and they don't exist, we will fallback to email inspection.
                    user = get_user_from_db(uid)

                    if user:
                        role = user.role
                        subject = user.subject
                        student_id = user.id
                    else:
                        # Fallback for testing: deduce role from email
                        role = "teacher" if "teacher" in email.lower() else "student"
                        subject = "science"
                        student_id = uid

                    # 3. Set Session State
                    st.session_state.firebase_token = auth_data["idToken"]
                    db_name = user.name if user and user.name else None
                    st.session_state.user_name = (
                        db_name or auth_data.get("displayName") or email.split("@")[0]
                    )

                    if role == "teacher":
                        st.session_state.teacher_id = student_id
                        st.session_state.teacher_subject = subject
                        set_user_role("teacher")
                    elif role == "admin":
                        cls_int = user.class_level if user and user.class_level else 10
                        set_student_class_level(cls_int)
                        set_user_role("admin")
                    else:
                        st.session_state.student_id = student_id
                        cls_int = user.class_level if user and user.class_level else 10
                        set_student_class_level(cls_int)
                        set_user_role("student")

                    st.query_params["uid"] = uid
                    st.rerun()

                except Exception as e:
                    st.error(f"Authentication failed: {str(e)}")
