#!/usr/bin/env python3
"""
NCERT Academic Science Assistant — Streamlit Application Entry Point.
"""

import asyncio
import os
import sys
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
import streamlit as st

# Ensure project root in sys.path
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Reconfigure stdout for UTF-8
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from src.academic_rag.config import config
from src.academic_rag.rag.engine import stream_ncert_rag_response
from src.academic_rag.rag.retriever import retrieve_ncert_context
from src.academic_rag.ui import (
    inject_custom_css,
    init_session_state,
    render_sidebar,
    render_chat_tab,
    render_quiz_tab,
    render_swat_tab,
    render_teacher_tab,
)

# Configure logging
def setup_logging():
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
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)


async def main():
    """Main application orchestrator."""
    inject_custom_css()
    init_session_state()

    # Title & Header
    st.markdown('<h1 class="main-header">🔬 NCERT Academic Science Assistant</h1>', unsafe_allow_html=True)
    st.markdown(
        '<p class="sub-header">Interactive Agentic RAG Tutor for <b>Class 9</b> & <b>Class 10</b> NCERT Science with Exact Page Citations</p>',
        unsafe_allow_html=True,
    )

    selected_model, user_api_key, selected_class, student_id = render_sidebar()

    # Navigation Tabs
    tab_chat, tab_quiz, tab_history, tab_teacher = st.tabs([
        "💬 NCERT Q&A Tutor",
        "📝 Practice Quiz",
        "📊 Student SWAT",
        "👨‍🏫 Teacher Dashboard",
    ])

    with tab_chat:
        await render_chat_tab(selected_model, user_api_key, selected_class)

    with tab_quiz:
        render_quiz_tab(student_id, user_api_key, selected_model)

    with tab_history:
        render_swat_tab(student_id)

    with tab_teacher:
        render_teacher_tab(student_id)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Application error: {e}")
