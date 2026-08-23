"""Sidebar UI component handling authentication, syllabus view, and grade focus."""

import os

import streamlit as st

from src.academic_rag.config import config
from src.academic_rag.curriculum.service import curriculum_service


def render_sidebar():
    """Renders the application sidebar tabs: Settings, Syllabus."""
    with st.sidebar:
        st.markdown("### 🔬 NCERT Science Tutor")
        tab1, tab2 = st.tabs(["⚙️ Settings", "📚 Syllabus"])

        # Tab 1: Configuration & Settings
        with tab1:
            st.markdown("#### 🔑 Authentication")
            api_key = st.text_input(
                "Google Gemini API Key",
                type="password",
                placeholder="AIzaSy...",
                value=st.session_state.get("api_key", config.get_google_api_key() or ""),
                help="Your key is kept securely in your current browser session.",
            )
            if api_key:
                st.session_state.api_key = api_key
                os.environ["GOOGLE_API_KEY"] = api_key
            else:
                st.info("💡 Enter your Google Gemini API key to begin.")

            st.markdown("#### 👤 Student Profile")
            student_id = st.text_input(
                "Student ID",
                value=st.session_state.get("student_id", "student_001"),
                help="Unique ID used to track your quiz performance and SWAT analytics.",
            )
            st.session_state.student_id = student_id

            st.markdown("#### 🎓 Student Grade & Focus")
            grade_options = ["All Classes", "Class 9", "Class 10"]
            current_grade_idx = (
                grade_options.index(st.session_state.selected_class)
                if st.session_state.selected_class in grade_options
                else 0
            )
            selected_class = st.selectbox(
                "Select Grade / Class",
                grade_options,
                index=current_grade_idx,
                help="Filters retrieval to Class 9 or Class 10 NCERT Science",
            )
            if selected_class != st.session_state.selected_class:
                st.session_state.selected_class = selected_class

            # Focus Chapter
            chapter_options = ["All Chapters"]
            if selected_class in ("Class 9", "Class 10"):
                cls_int = 9 if selected_class == "Class 9" else 10
                chs = curriculum_service.get_chapters_for_grade(cls_int)
                for ch in chs:
                    chapter_options.append(f"Ch {ch.chapter_number}: {ch.chapter_title}")

            selected_chapter = st.selectbox("Focus Chapter (Optional)", chapter_options)
            st.session_state.selected_chapter = selected_chapter

            st.divider()

            st.markdown("#### 🤖 LLM Model")
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
                help="Choose Google Gemini model for answering and reasoning",
            )
            st.session_state.model = selected_model

        # Tab 2: Syllabus
        with tab2:
            st.markdown("#### 📖 NCERT Science Curriculum")

            with st.expander(
                "📘 Class 9 Science (13 Chapters)", expanded=(selected_class == "Class 9")
            ):
                cls9_chs = curriculum_service.get_chapters_for_grade(9)
                for ch in cls9_chs:
                    st.markdown(f"**Ch {ch.chapter_number}:** {ch.chapter_title}")

            with st.expander(
                "📗 Class 10 Science (13 Chapters)", expanded=(selected_class == "Class 10")
            ):
                cls10_chs = curriculum_service.get_chapters_for_grade(10)
                for ch in cls10_chs:
                    st.markdown(f"**Ch {ch.chapter_number}:** {ch.chapter_title}")

    return (
        selected_model,
        st.session_state.get("api_key"),
        selected_class,
        st.session_state.get("student_id", "student_001"),
    )
