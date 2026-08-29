"""Role Selection & Authentication Screens for DiligentEdu (Firebase Integrated)."""

import textwrap

import streamlit as st

from backend.auth.firebase_auth import sign_in_with_email_and_password
from frontend.state import set_student_class_level, set_user_role
from prisma import Prisma


def get_user_from_db(uid: str):
    try:
        from backend.storage.repository import get_prisma_client

        db = get_prisma_client()
        if not db.is_connected():
            db.connect()
        return db.user.find_unique(where={"id": uid})
    except Exception as e:
        import logging

        logging.getLogger(__name__).warning(f"Failed to query user {uid} from DB: {e}")
        return None


def render_login_screen() -> None:
    """Renders the single Firebase authentication portal."""
    st.markdown(
        """
        <style>
            /* Reset any intro screen overrides so login screen is fully visible */
            header[data-testid="stHeader"] {
                display: block !important;
                visibility: visible !important;
                height: auto !important;
            }
            html, body, .stApp {
                overflow: auto !important;
                height: auto !important;
                min-height: 100vh !important;
            }
            .main, [data-testid="stAppViewContainer"], [data-testid="stMainBlockContainer"], [data-testid="stVerticalBlock"], [data-testid="stVerticalBlockBorderWrapper"] {
                height: auto !important;
                overflow: visible !important;
                max-width: 1200px !important;
                margin: 0 auto !important;
                padding: 1.5rem 1rem !important;
            }
            div[data-testid="stCustomComponentV1"] {
                position: static !important;
                width: auto !important;
                height: auto !important;
                z-index: auto !important;
                background: transparent !important;
            }
            div[data-testid="stCustomComponentV1"] > iframe {
                position: static !important;
                width: 100% !important;
                height: auto !important;
                background: transparent !important;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

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

                    # 3. Atomically bootstrap session state
                    st.session_state.firebase_token = auth_data["idToken"]
                    display_name = (
                        (user.name if user and user.name else None)
                        or auth_data.get("displayName")
                        or email.split("@")[0]
                    )
                    class_lvl = user.class_level if user and user.class_level else 10

                    from frontend.state import bootstrap_authenticated_session

                    bootstrap_authenticated_session(
                        user_id=student_id,
                        role=role,
                        name=display_name,
                        class_level=class_lvl,
                        subject=subject,
                        restore_screen=False,
                    )

                    st.rerun()

                except Exception as e:
                    st.error(f"Authentication failed: {str(e)}")
