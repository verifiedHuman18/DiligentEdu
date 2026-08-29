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

# Ensure Prisma client is available (dynamic fallback for environments like Streamlit Cloud)
try:
    from prisma import Prisma  # noqa: F401
except ImportError:
    import subprocess
    import tempfile

    tmp_dir = tempfile.gettempdir()
    prisma_out_dir = os.path.join(tmp_dir, "prisma")
    custom_schema_path = os.path.join(tmp_dir, "schema.prisma")

    if not os.path.exists(os.path.join(prisma_out_dir, "client.py")):
        print(f"Prisma client not found in environment. Generating into {prisma_out_dir}...")

        schema_file = os.path.join(PROJECT_ROOT, "prisma", "schema.prisma")
        if os.path.exists(schema_file):
            with open(schema_file, "r", encoding="utf-8") as f:
                schema = f.read()

            out_dir_str = prisma_out_dir.replace("\\", "/")
            if "output" not in schema:
                schema = schema.replace(
                    'provider             = "prisma-client-py"',
                    f'provider             = "prisma-client-py"\n  output               = "{out_dir_str}"',
                )

            os.makedirs(os.path.dirname(custom_schema_path), exist_ok=True)
            with open(custom_schema_path, "w", encoding="utf-8") as f:
                f.write(schema)

            subprocess.check_call(
                [sys.executable, "-m", "prisma", "generate", "--schema", custom_schema_path]
            )

    if tmp_dir not in sys.path:
        sys.path.insert(0, tmp_dir)

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
    page_title="DiligentEdu - Equitable Learning for All",
    page_icon="frontend/assets/logo.png",
    layout="wide",
    initial_sidebar_state="collapsed",
)


async def render_screen_content(
    active_screen: str,
    user_role: str,
    selected_class: str,
    student_id: str,
    selected_model: str,
    user_api_key: str,
) -> None:
    """Centralized screen rendering boundary with robust error handling (Phases 3, 4, 18)."""
    from frontend.components.transition import finish_transition

    try:
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
    except Exception as screen_err:
        logger.exception(f"Screen render error on '{active_screen}': {screen_err}")
        from frontend.components.transition import render_error_boundary

        render_error_boundary(
            title="Unable to display this view",
            message=f"A problem occurred while loading {active_screen.replace('_', ' ').title()}. Please retry or navigate home.",
            retry_label="Reload Screen",
            key_suffix=f"{active_screen}_boundary",
        )
    finally:
        finish_transition()


async def main():
    """Main application orchestrator with atomic bootstrap, stable shell, global transition layer, and single screen boundary."""
    init_session_state()
    inject_custom_css()

    from frontend.components.transition import render_global_transition_layer

    render_global_transition_layer()

    # 3D Intro Splash Screen (Phases 1-23)
    if not st.session_state.get("intro_completed", False):
        from frontend.screens.intro_screen import render_intro_screen

        render_intro_screen()
        return

    user_role = get_user_role()

    # Restore session from URL query parameters if available
    if not user_role and "uid" in st.query_params:
        uid = st.query_params["uid"]
        from frontend.screens.login_screen import get_user_from_db

        user = get_user_from_db(uid)
        if user:
            from frontend.state import bootstrap_authenticated_session

            bootstrap_authenticated_session(
                user_id=user.id,
                role=user.role,
                name=user.name or uid,
                class_level=user.class_level,
                subject=user.subject,
                restore_screen=True,
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

    # Top Navbar (Persistent Application Shell Header)
    active_screen = render_navbar(selected_class=selected_class, student_id=student_id)

    # Render Screen Container Boundary
    with st.container():
        await render_screen_content(
            active_screen=active_screen,
            user_role=user_role,
            selected_class=selected_class,
            student_id=student_id,
            selected_model=selected_model,
            user_api_key=user_api_key,
        )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.exception(f"Application error: {e}")
