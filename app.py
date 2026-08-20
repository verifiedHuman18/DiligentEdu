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
    render_header,
    render_sidebar,
    render_tutor_screen,
    render_quiz_screen,
    render_swat_screen,
    render_teacher_screen,
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


# Streamlit Page Configuration
st.set_page_config(
    page_title="NCERT Science Academic Assistant",
    layout="wide",
    initial_sidebar_state="expanded",
)


async def main():
    """Main application orchestrator."""
    init_session_state()
    inject_custom_css()

    selected_model, user_api_key, selected_class, student_id = render_sidebar()

    # Top Header with Status Badges
    render_header(selected_class=selected_class, student_id=student_id)

    # Navigation Tabs
    tab_chat, tab_quiz, tab_swat, tab_teacher = st.tabs([
        "NCERT Q&A Tutor",
        "Practice Quiz",
        "Student SWAT",
        "Teacher Dashboard",
    ])

    with tab_chat:
        await render_tutor_screen(selected_model, user_api_key, selected_class)

    with tab_quiz:
        render_quiz_screen(student_id, user_api_key, selected_model)

    with tab_swat:
        render_swat_screen(student_id)

    with tab_teacher:
        render_teacher_screen(student_id)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Application error: {e}")
