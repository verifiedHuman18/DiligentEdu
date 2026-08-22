"""Sidebar component handling settings, authentication, curriculum, and theme controls (No Emojis)."""

import os
from datetime import datetime
from typing import Tuple

import streamlit as st

from frontend.components.theme_switcher import render_theme_switcher
from src.academic_rag.config import config
from src.academic_rag.curriculum.service import curriculum_service


def render_sidebar() -> Tuple[str, str, str, str]:
    """
    Renders the minimalist application sidebar.

    Returns:
        Tuple of (selected_model, api_key, selected_class, student_id)
    """
    with st.sidebar:
        st.markdown("### DiligentEdu Tutor")
        st.caption("NCERT Science AI Assistant")

        # Tabs
        tab_config, tab_syllabus, tab_session = st.tabs(["Settings", "Syllabus", "Session"])

        # Tab 1: Configuration
        with tab_config:
            # 1. Authentication
            st.markdown("#### Authentication")
            api_key = st.text_input(
                "Google Gemini API Key",
                type="password",
                placeholder="AIzaSy...",
                value=st.session_state.get("api_key", config.get_google_api_key() or ""),
                help="Your API key remains securely in your current browser session.",
            )
            if api_key:
                st.session_state.api_key = api_key
                os.environ["GOOGLE_API_KEY"] = api_key
            else:
                st.info("Enter your Gemini API key to enable AI features.")

            # 2. Student Profile
            st.markdown("#### Student Profile")
            student_id = st.text_input(
                "Student ID",
                value=st.session_state.get("student_id", "student_001"),
                help="Tracks your personal SWAT analysis and quiz metrics.",
                key="sidebar_student_id_input",
            )
            st.session_state.student_id = student_id.strip() or "student_001"

            # 3. Class & Focus Chapter
            st.markdown("#### Class & Focus")
            from frontend.state import get_student_class_level, set_student_class_level

            curr_cls = get_student_class_level()
            class_options = ["Class 10", "Class 9"]
            curr_cls_idx = 0 if curr_cls == 10 else 1
            selected_class_label = st.radio(
                "Class",
                class_options,
                index=curr_cls_idx,
                key="sidebar_class_radio",
                help="Filters NCERT textbook retrieval to Class 10 or Class 9.",
            )
            selected_class = selected_class_label
            target_cls_int = 10 if selected_class_label == "Class 10" else 9
            if target_cls_int != curr_cls:
                set_student_class_level(target_cls_int)
                st.rerun()

            # Focus Chapter
            chapter_options = ["All Chapters"]
            chs = curriculum_service.get_chapters_for_grade(target_cls_int)
            for ch in chs:
                chapter_options.append(f"Ch {ch.chapter_number}: {ch.chapter_title}")

            selected_chapter = st.selectbox(
                "Focus Chapter (Optional)", chapter_options, key="sidebar_ch_select"
            )
            st.session_state.selected_chapter = selected_chapter

            st.divider()

            # 4. LLM Model Selection
            st.markdown("#### Model")
            model_options = [
                "gemini-3.5-flash-lite",
                "gemini-flash-lite-latest",
                "gemini-3-flash-preview",
                "gemini-3.6-flash",
                "gemini-3.7-flash",
                "gemini-2.5-pro",
            ]
            selected_model = st.selectbox(
                "Gemini Model",
                model_options,
                index=0,
                help="Model used for reasoning, synthesis, and quiz generation",
            )
            st.session_state.model = selected_model

            st.divider()

            # 5. Theme Switcher
            render_theme_switcher(location="sidebar")

        # Tab 2: Syllabus Explorer
        with tab_syllabus:
            st.markdown("#### NCERT Science Chapters")

            with st.expander(
                "Class 9 Science (13 Chapters)", expanded=(selected_class == "Class 9")
            ):
                cls9_chs = curriculum_service.get_chapters_for_grade(9)
                for ch in cls9_chs:
                    st.markdown(f"**Ch {ch.chapter_number}:** {ch.chapter_title}")

            with st.expander(
                "Class 10 Science (13 Chapters)", expanded=(selected_class == "Class 10")
            ):
                cls10_chs = curriculum_service.get_chapters_for_grade(10)
                for ch in cls10_chs:
                    st.markdown(f"**Ch {ch.chapter_number}:** {ch.chapter_title}")

        # Tab 3: Session & Export
        with tab_session:
            st.markdown("#### Session Overview")
            msg_count = len(st.session_state.get("messages", []))
            questions_asked = msg_count // 2 if msg_count > 0 else 0

            st.metric("Questions Asked", questions_asked)
            st.info(
                f"**Active Model:** {selected_model}\n\n**Vector Index:** Pinecone ({config.pinecone_index_name})"
            )

            if msg_count > 0:
                st.divider()
                chat_text = ""
                for msg in st.session_state.messages:
                    role = "Student" if msg["role"] == "user" else "NCERT Assistant"
                    chat_text += f"{role}:\n{msg['content']}\n\n"

                st.download_button(
                    "Export Chat History",
                    chat_text,
                    f"ncert_chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    "text/plain",
                    use_container_width=True,
                )

            if st.button("Clear Chat History", use_container_width=True):
                st.session_state.messages = []
                st.rerun()

    return (
        selected_model,
        st.session_state.get("api_key", ""),
        selected_class,
        st.session_state.get("student_id", "student_001"),
    )
