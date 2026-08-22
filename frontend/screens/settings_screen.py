"""Dedicated Configuration and Settings Screen with Compact Sidebar Navigation and Translucent Active Buttons."""

import os
from datetime import datetime

import streamlit as st

from frontend.state import navigate_to
from frontend.styles import inject_custom_css
from src.academic_rag.config import config
from src.academic_rag.curriculum.service import curriculum_service
from src.academic_rag.storage.repository import quiz_repository


def render_settings_screen() -> None:
    """Renders the dedicated application configuration screen with compact sidebar navigation buttons and icons."""
    # Top Navigation Back to Home
    if st.button(
        "Back to Home", icon=":material/arrow_back:", type="secondary", key="settings_top_back_btn"
    ):
        navigate_to("home")
        st.rerun()

    st.write("")
    st.markdown("### Settings")
    st.caption(
        "Manage API keys, student profile, AI model selection, theme, and local session data."
    )
    st.write("")

    if "settings_tab" not in st.session_state:
        st.session_state.settings_tab = "Authentication"

    active_tab = st.session_state.settings_tab

    # 2-Column Layout: Left Compact Sidebar Navigation, Right Dedicated Panel
    nav_col, content_col = st.columns([0.85, 3.15])

    with nav_col:
        tabs = [
            ("Authentication", "Authentication", ":material/key:"),
            ("Student Profile", "Student Profile", ":material/person:"),
            ("AI & Model", "AI & Model", ":material/smart_toy:"),
            ("Appearance", "Appearance", ":material/palette:"),
            ("Data & Storage", "Data & Storage", ":material/database:"),
        ]

        for label, tab_id, icon_name in tabs:
            is_active = active_tab == tab_id
            btn_type = "primary" if is_active else "secondary"
            if st.button(
                label,
                icon=icon_name,
                key=f"btn_tab_{tab_id}",
                type=btn_type,
                use_container_width=True,
            ):
                st.session_state.settings_tab = tab_id
                st.rerun()

    with content_col:
        # Tab 1: Authentication
        if active_tab == "Authentication":
            st.markdown("#### API Authentication")
            st.caption(
                "Configure your Google Gemini API key to power grounded Q&A and adaptive quizzes."
            )
            st.write("")

            api_key = st.text_input(
                "Google Gemini API Key",
                type="password",
                placeholder="AIzaSy...",
                value=st.session_state.get("api_key", config.get_google_api_key() or ""),
                help="Your API key is securely stored in active session memory.",
            )
            if api_key:
                st.session_state.api_key = api_key
                os.environ["GOOGLE_API_KEY"] = api_key
                st.success("API key configured and active for current session.")
            else:
                st.info("Please enter your Gemini API key to enable AI features.")

        # Tab 2: Student Profile (Phase 3 & Phase 4)
        elif active_tab == "Student Profile":
            from frontend.state import get_student_class_level, set_student_class_level

            st.markdown("#### Student Profile & Standard Settings")
            st.caption(
                "This is the master configuration for your student identity and NCERT textbook grade level."
            )
            st.write("")

            student_id = st.text_input(
                "Student Name / ID",
                value=st.session_state.get("student_id", "student_001"),
                help="Unique identifier for tracking your analytics and quiz attempts.",
                key="settings_student_id_input",
            )

            st.write("")
            curr_cls = get_student_class_level()
            selected_cls_label = st.radio(
                "Class / Standard",
                options=["Class 9", "Class 10"],
                index=0 if curr_cls == 9 else 1,
                help="Master standard setting (Class 9 or Class 10). Only one standard is active at a time.",
                key="settings_class_radio",
            )
            new_cls_int = 9 if selected_cls_label == "Class 9" else 10

            st.write("")
            chapter_options = ["All Chapters"]
            chs = curriculum_service.get_chapters_for_grade(new_cls_int)
            for ch in chs:
                chapter_options.append(f"Ch {ch.chapter_number}: {ch.chapter_title}")

            curr_chapter = st.session_state.get("selected_chapter", "All Chapters")
            curr_ch_idx = (
                chapter_options.index(curr_chapter) if curr_chapter in chapter_options else 0
            )
            selected_chapter = st.selectbox(
                "Default Focus Chapter (Optional)", chapter_options, index=curr_ch_idx
            )

            st.write("")
            if st.button(
                "Save Changes",
                type="primary",
                key="save_profile_settings_btn",
                icon=":material/save:",
            ):
                set_student_class_level(new_cls_int)
                st.session_state.student_id = student_id.strip() or "student_001"
                st.session_state.selected_chapter = selected_chapter
                st.success(
                    f"Profile saved successfully! Master Standard set to Class {new_cls_int}."
                )
                st.rerun()

        # Tab 3: AI & Model
        elif active_tab == "AI & Model":
            st.markdown("#### AI Model & Reasoning")
            st.caption("Select the Google Gemini model used for reasoning and quiz synthesis.")
            st.write("")

            model_options = [
                "gemini-3.5-flash-lite",
                "gemini-flash-lite-latest",
                "gemini-3-flash-preview",
                "gemini-3.6-flash",
                "gemini-3.7-flash",
                "gemini-2.5-pro",
            ]
            curr_model = st.session_state.get("model", "gemini-3.5-flash-lite")
            curr_model_idx = model_options.index(curr_model) if curr_model in model_options else 0
            selected_model = st.selectbox(
                "Gemini Model",
                model_options,
                index=curr_model_idx,
                help="Select model for reasoning and synthesis.",
            )
            st.session_state.model = selected_model

            st.write("")
            st.info(
                "Flash Lite models provide fastest streaming speed, while Pro models provide deeper conceptual synthesis."
            )

        # Tab 4: Appearance
        elif active_tab == "Appearance":
            st.markdown("#### Theme & Display")
            st.caption("Switch between Warm Cream (Light) and Warm Brown (Dark) palettes.")
            st.write("")

            theme_options = ["Light", "Dark"]
            curr_theme = st.session_state.get("theme", "Light")
            curr_theme_idx = theme_options.index(curr_theme) if curr_theme in theme_options else 0
            selected_theme = st.selectbox(
                "Theme Mode",
                theme_options,
                index=curr_theme_idx,
                help="Switch between Cream (Light) and Brown (Dark) mode",
            )
            if selected_theme != st.session_state.get("theme"):
                st.session_state.theme = selected_theme
                inject_custom_css(selected_theme)
                st.rerun()

        # Tab 5: Data & Storage
        elif active_tab == "Data & Storage":
            st.markdown("#### Session & Storage Management")
            st.caption("Export your conversation records or reset student quiz attempt data.")
            st.write("")

            d1, d2, d3 = st.columns(3)
            with d1:
                msg_count = len(st.session_state.get("messages", []))
                if msg_count > 0:
                    chat_text = ""
                    for msg in st.session_state.messages:
                        role = "Student" if msg["role"] == "user" else "NCERT Assistant"
                        chat_text += f"{role}:\n{msg['content']}\n\n"

                    st.download_button(
                        "Export Chat History",
                        chat_text,
                        f"ncert_chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                        "text/plain",
                        icon=":material/download:",
                        use_container_width=True,
                    )
                else:
                    st.button(
                        "Export Chat History",
                        icon=":material/download:",
                        disabled=True,
                        use_container_width=True,
                    )

            with d2:
                if st.button(
                    "Clear Chat History", icon=":material/delete_sweep:", use_container_width=True
                ):
                    st.session_state.messages = []
                    st.success("Chat history cleared.")
                    st.rerun()

            with d3:
                student_id = st.session_state.get("student_id", "student_001")
                if st.button(
                    "Clear Quiz History", icon=":material/restart_alt:", use_container_width=True
                ):
                    quiz_repository.clear_student_data(student_id)
                    st.success("Quiz history cleared.")
                    st.rerun()
