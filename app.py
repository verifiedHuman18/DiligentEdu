#!/usr/bin/env python3
"""
NCERT Academic Science Assistant — Streamlit Application Entry Point.
"""

import asyncio
import logging
import os
import sys
from datetime import datetime

import streamlit as st

# Ensure project root in sys.path
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Reconfigure stdout for UTF-8
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Streamlit Community Cloud: Generate Prisma client if not generated
# We generate to /tmp/prisma because site-packages is read-only on Streamlit Cloud
import os
import subprocess
import sys

if not os.path.exists("/tmp/prisma/client.py"):
    print("Prisma client not found in /tmp. Generating...")

    # Read the original schema
    with open("prisma/schema.prisma", "r") as f:
        schema = f.read()

    # Inject the local output directory into the generator block
    if "output" not in schema:
        schema = schema.replace(
            'provider             = "prisma-client-py"',
            'provider             = "prisma-client-py"\n  output               = "/tmp/prisma"',
        )

    # Write the modified schema to a temporary location
    with open("/tmp/schema.prisma", "w") as f:
        f.write(schema)

    # Generate the client using the modified schema
    subprocess.check_call(
        [sys.executable, "-m", "prisma", "generate", "--schema", "/tmp/schema.prisma"]
    )

# Prepend /tmp to sys.path so Python loads `prisma` from /tmp/prisma instead of site-packages
if "/tmp" not in sys.path:
    sys.path.insert(0, "/tmp")

from frontend import (
    get_user_role,
    init_session_state,
    inject_custom_css,
    render_chapter_screen,
    render_home_screen,
    render_knowledge_graph_screen,
    render_login_screen,
    render_navbar,
    render_quiz_screen,
    render_scholarships_screen,
    render_settings_screen,
    render_study_material_screen,
    render_study_twin_screen,
    render_swat_screen,
    render_teacher_screen,
    render_tutor_screen,
)
from frontend.screens.admin_screen import render_admin_screen


def setup_logging():
    """Configures application logging."""
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    os.makedirs("logs", exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.FileHandler(
                f"logs/app_{datetime.now().strftime('%Y%m%d')}.log", encoding="utf-8"
            ),
            logging.StreamHandler(sys.stdout),
        ],
    )
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("langchain").setLevel(logging.WARNING)
    logging.getLogger("pinecone").setLevel(logging.WARNING)
    return logging.getLogger(__name__)


logger = setup_logging()

# Handle async event loop
try:
    asyncio.get_running_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)


# Streamlit Page Configuration (Sidebar collapsed by default)
st.set_page_config(
    page_title="NCERT Science Academic Assistant",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def render_page_loader():
    """Renders a fullscreen loading animation that stays on screen until explicitly removed."""
    if st.session_state.get("is_navigating", False):
        st.markdown(
            """
        <style>
        @keyframes loader-appear {
            0% { opacity: 0; }
            99% { opacity: 0; }
            100% { opacity: 1; }
        }
        .page-loader-overlay {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            width: 100%;
            height: 100%;
            background-color: var(--bg-app);
            z-index: 9999999;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            pointer-events: none;
            opacity: 0;
            animation: loader-appear 0.2s forwards;
        }
        .page-loader-spinner {
            width: 48px;
            height: 48px;
            border: 4px solid var(--surface-container-highest);
            border-bottom-color: var(--md-primary);
            border-radius: 50%;
            display: inline-block;
            box-sizing: border-box;
            animation: rotation 1s linear infinite;
            margin-bottom: 20px;
        }
        @keyframes rotation {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .page-loader-text {
            color: var(--md-primary);
            font-family: 'Outfit', sans-serif;
            font-size: 1.2rem;
            font-weight: 600;
            letter-spacing: 1px;
        }
        </style>
        <div class="page-loader-overlay" id="page-loader">
            <div class="page-loader-spinner"></div>
            <div class="page-loader-text">Loading Workspace...</div>
        </div>
        """,
            unsafe_allow_html=True,
        )


def finalize_page_loader():
    """Fades out the loading animation after the page has fully finished rendering."""
    if st.session_state.get("is_navigating", False):
        st.markdown(
            """
            <style>
            @keyframes page-loader-fade {
                100% { opacity: 0; visibility: hidden; }
            }
            #page-loader {
                animation: page-loader-fade 0.5s cubic-bezier(0.4, 0, 0.2, 1) forwards;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )
        st.session_state.is_navigating = False


async def main():
    """Main application orchestrator with role selection portal and segregated routing."""
    init_session_state()
    inject_custom_css()
    render_page_loader()

    user_role = get_user_role()

    # Restore session from URL query parameters if available
    if not user_role and "uid" in st.query_params:
        uid = st.query_params["uid"]
        from frontend.screens.login_screen import get_user_from_db

        user = get_user_from_db(uid)
        if user:
            from frontend.state import set_student_class_level, set_user_role

            st.session_state.user_name = user.name or uid

            if user.role == "teacher":
                st.session_state.teacher_id = user.id
                st.session_state.teacher_subject = user.subject
                set_user_role("teacher", restore_screen=True)
            elif user.role == "admin":
                cls_int = user.class_level if user.class_level else 10
                set_student_class_level(cls_int)
                set_user_role("admin", restore_screen=True)
            else:
                st.session_state.student_id = user.id
                cls_int = user.class_level if user.class_level else 10
                set_student_class_level(cls_int)
                set_user_role("student", restore_screen=True)

            if "screen" in st.query_params:
                st.session_state.current_screen = st.query_params["screen"]
            else:
                st.session_state.current_screen = (
                    "admin_home"
                    if user.role == "admin"
                    else ("teacher" if user.role == "teacher" else "home")
                )

            user_role = get_user_role()

    # If no role is selected or current screen is login, render the Login / Role Selection Screen
    if not user_role or st.session_state.get("current_screen") == "login":
        render_login_screen()
        return

    from frontend.state import get_student_class_level

    cls_int = get_student_class_level()
    selected_class = f"Class {cls_int}"
    student_id = st.session_state.get("student_id", "student_001")
    selected_model = st.session_state.get("model", "gemini-3.5-flash-lite")
    user_api_key = st.session_state.get("user_gemini_api_key", "")

    # Top Navbar & Screen Selector
    active_screen = render_navbar(selected_class=selected_class, student_id=student_id)

    # Route based on User Role
    if user_role == "teacher":
        if active_screen == "settings":
            render_settings_screen()
        else:
            render_teacher_screen(student_id, selected_class=selected_class)
    elif user_role == "admin":
        if active_screen == "settings":
            render_settings_screen()
        else:
            render_admin_screen(selected_class=selected_class)
    else:
        # Student Persona Routing
        if active_screen == "home":
            render_home_screen(selected_class=selected_class, student_id=student_id)
        elif active_screen == "tutor":
            await render_tutor_screen(
                selected_model, user_api_key, selected_class, student_id=student_id
            )
        elif active_screen == "quiz":
            await render_quiz_screen(student_id, user_api_key, selected_model)
        elif active_screen == "knowledge_graph":
            render_knowledge_graph_screen(student_id=student_id, user_api_key=user_api_key)
        elif active_screen == "study_material":
            render_study_material_screen(student_id=student_id, user_api_key=user_api_key)
        elif active_screen == "study_twin":
            render_study_twin_screen(student_id=student_id)
        elif active_screen == "swat":
            render_swat_screen(student_id, selected_class=selected_class)
        elif active_screen == "scholarships":
            render_scholarships_screen()
        elif active_screen == "chapter":
            render_chapter_screen(student_id, user_api_key, selected_model)
        elif active_screen == "settings":
            render_settings_screen()
        else:
            render_home_screen(selected_class=selected_class, student_id=student_id)

    finalize_page_loader()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.exception(f"Application error: {e}")
