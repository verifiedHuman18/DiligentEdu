#!/usr/bin/env python3
"""
NCERT Academic Science Assistant — Streamlit Application Entry Point.
"""

import asyncio
import os
import sys
import logging
from datetime import datetime
import streamlit as st

# Ensure project root in sys.path
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Reconfigure stdout for UTF-8
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from frontend import (
    inject_custom_css,
    init_session_state,
    render_navbar,
    render_home_screen,
    render_tutor_screen,
    render_quiz_screen,
    render_swat_screen,
    render_teacher_screen,
    render_settings_screen,
)


def setup_logging():
    """Configures application logging."""
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    os.makedirs("logs", exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.FileHandler(f'logs/app_{datetime.now().strftime("%Y%m%d")}.log', encoding="utf-8"),
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


async def main():
    """Main application orchestrator with screen-based routing and no sidebar."""
    init_session_state()
    inject_custom_css()

    selected_class = st.session_state.get("selected_class", "All Classes")
    student_id = st.session_state.get("student_id", "student_001")
    selected_model = st.session_state.get("model", "gemini-3.5-flash-lite")
    user_api_key = st.session_state.get("api_key", "")

    # Top Navbar & Screen Selector
    active_screen = render_navbar(selected_class=selected_class, student_id=student_id)

    # Route to dedicated screen
    if active_screen == "home":
        render_home_screen(selected_class=selected_class, student_id=student_id)
    elif active_screen == "tutor":
        await render_tutor_screen(selected_model, user_api_key, selected_class)
    elif active_screen == "quiz":
        render_quiz_screen(student_id, user_api_key, selected_model)
    elif active_screen == "swat":
        render_swat_screen(student_id)
    elif active_screen == "teacher":
        render_teacher_screen(student_id)
    elif active_screen == "settings":
        render_settings_screen()
    else:
        render_home_screen(selected_class=selected_class, student_id=student_id)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Application error: {e}")
