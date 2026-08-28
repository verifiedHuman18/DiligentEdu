"""Dedicated Configuration and Settings Screen with Compact Sidebar Navigation and Translucent Active Buttons."""

import streamlit as st

from frontend.components.navigation import render_back_to_home
from frontend.state import navigate_to
from frontend.styles import inject_custom_css
from src.academic_rag.curriculum.service import curriculum_service


def render_settings_screen() -> None:
    """Renders the dedicated application configuration screen with compact sidebar navigation buttons and icons."""
    from frontend.state import get_user_role, logout

    role = get_user_role() or "student"

    # Top Navigation Back button based on role
    if role == "teacher":
        if st.button(
            "Back to Teacher Dashboard",
            icon=":material/arrow_back:",
            type="secondary",
            key="btn_back_to_teacher_dashboard",
            help="Return to Teacher Portal",
        ):
            navigate_to("teacher")
            st.rerun()
        st.write("")
    else:
        render_back_to_home("settings")

    st.markdown("### Settings")
    st.caption("Manage API keys, profile identity, AI model selection, and theme.")
    st.write("")

    if "settings_tab" not in st.session_state or st.session_state.settings_tab in (
        "Data & Storage",
        "Authentication",
        "AI & Model",
    ):
        st.session_state.settings_tab = "AI Configuration"

    active_tab = st.session_state.settings_tab

    profile_tab_label = "Teacher Profile" if role == "teacher" else "Student Profile"

    # 2-Column Layout: Left Compact Sidebar Navigation, Right Dedicated Panel
    nav_col, content_col = st.columns([0.95, 3.05])

    with nav_col:
        tabs = [
            ("AI Configuration", "AI Configuration", ":material/smart_toy:"),
            (profile_tab_label, "Profile", ":material/person:"),
            ("Appearance", "Appearance", ":material/palette:"),
        ]

        for label, tab_id, icon_name in tabs:
            is_active = (active_tab == tab_id) or (
                tab_id == "Profile"
                and active_tab in ("Student Profile", "Teacher Profile", "Profile")
            )
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

        st.write("")
        st.divider()
        if st.button(
            "Switch Role",
            icon=":material/logout:",
            key="btn_settings_logout",
            type="secondary",
            use_container_width=True,
            help="Sign out and return to the Role Selection portal.",
        ):
            logout()
            st.rerun()

    with content_col:
        # Tab 1: AI Configuration (Phases 7, 8, 9, 14, 18, 19, 24, 25)
        if active_tab in ("AI Configuration", "Authentication", "AI & Model"):
            from src.academic_rag.ai import (
                get_api_status,
                has_user_fallback_api_key,
                remove_user_fallback_api_key,
                set_user_fallback_api_key,
                test_gemini_api_key,
            )

            api_status = get_api_status()

            st.markdown("#### AI Configuration")
            st.caption("Manage AI model reasoning and active API connectivity.")
            st.write("")

            # 1. Primary AI Service Status (Phase 7 & 19)
            st.markdown("##### AI Service Status")
            if api_status["primary_configured"]:
                st.success(
                    "● **Application AI Service:** Connected and ready for NCERT Tutor & Quiz generation."
                )
            elif api_status["fallback_configured"]:
                st.info("● **Using Your Fallback API:** Active for this session.")
            else:
                st.warning(
                    "**No AI Service Configured:** Please provide an optional session fallback API key below."
                )

            st.divider()

            # 2. AI Model Selection
            st.markdown("##### AI Model & Reasoning")
            st.caption(
                "Select the Google Gemini model used for conceptual explanations and quiz synthesis."
            )
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
                help="Flash Lite provides fast streaming speed; Pro provides deep reasoning.",
            )
            st.session_state.model = selected_model

            st.divider()

            # 3. Optional Fallback API (Phases 8, 9, 14, 18, 24, 25)
            st.markdown("##### Optional Fallback API")
            st.caption(
                "DiligentEdu normally uses the application's configured AI service. "
                "If the service reaches its usage limit or becomes temporarily unavailable, "
                "you can provide your own Gemini API key for this session."
            )

            fallback_active = has_user_fallback_api_key()

            if fallback_active:
                st.write("")
                st.success("● **Session Fallback API Configured**")
                st.caption(
                    "Your key is active in session memory and will be used if the primary service reaches quota limit."
                )
                if st.button(
                    "Remove API Key",
                    type="secondary",
                    icon=":material/delete:",
                    key="btn_remove_fallback_key",
                ):
                    remove_user_fallback_api_key()
                    st.success("Fallback API key removed.")
                    st.rerun()
            else:
                fallback_input = st.text_input(
                    "Gemini API Key",
                    type="password",
                    placeholder="Enter your Gemini API key (AIzaSy...)",
                    key="settings_fallback_key_input",
                    help="Your API key is used strictly for this session and is never stored in the database.",
                )
                st.caption(
                    "Your API key is used only for this session and is not stored as part of your student profile."
                )

                if st.button(
                    "Save & Test",
                    type="primary",
                    icon=":material/verified:",
                    key="btn_save_test_fallback_key",
                ):
                    if not fallback_input or not fallback_input.strip():
                        st.warning("Please enter a valid Gemini API key before testing.")
                    else:
                        with st.spinner("Testing API key with 1 lightweight request..."):
                            is_valid, msg = test_gemini_api_key(
                                fallback_input, model_name=selected_model
                            )
                            if is_valid:
                                set_user_fallback_api_key(fallback_input)
                                st.success("API key verified and activated for this session!")
                                st.rerun()
                            else:
                                st.error(f"Unable to use the provided Gemini API key: {msg}")

        # Tab 2: Profile (Student or Teacher)
        elif active_tab in ("Profile", "Student Profile", "Teacher Profile"):
            from frontend.state import (
                get_student_class_level,
                get_student_subject,
                set_student_class_level,
                set_student_subject,
            )

            if role == "teacher":
                st.markdown("#### Teacher Profile & Diagnostic Settings")
                st.caption(
                    "Manage your educator identity and default class level/subject for telemetry inspection."
                )
                st.write("")

                teacher_id = st.text_input(
                    "Teacher Name / ID",
                    value=st.session_state.get("teacher_id", "teacher_001"),
                    help="Unique identifier for educator diagnostic session.",
                    key="settings_teacher_id_input",
                )

                st.write("")
                col_cls, col_subj = st.columns(2)
                with col_cls:
                    curr_cls = get_student_class_level()
                    selected_cls_label = st.radio(
                        "Default Inspection Class",
                        options=["Class 10", "Class 9"],
                        index=0 if curr_cls == 10 else 1,
                        key="settings_teacher_class_radio",
                    )
                    new_cls_int = 10 if selected_cls_label == "Class 10" else 9

                with col_subj:
                    curr_subj = get_student_subject()
                    selected_subj = st.radio(
                        "Default Inspection Subject",
                        options=["Science", "Mathematics"],
                        index=0 if curr_subj == "Science" else 1,
                        key="settings_teacher_subject_radio",
                    )

                st.write("")
                if st.button(
                    "Save Changes",
                    type="primary",
                    key="save_teacher_profile_btn",
                    icon=":material/save:",
                ):
                    set_student_class_level(new_cls_int)
                    set_student_subject(selected_subj)
                    st.session_state.teacher_id = teacher_id.strip() or "teacher_001"
                    st.success("Teacher profile saved successfully!")
                    st.rerun()
            else:
                st.markdown("#### Student Profile & Standard Settings")
                st.caption(
                    "This is the master configuration for your student identity, NCERT textbook grade level, and active subject."
                )
                st.write("")

                student_id = st.text_input(
                    "Student Name / ID",
                    value=st.session_state.get("student_id", "student_001"),
                    help="Unique identifier for tracking your analytics and quiz attempts.",
                    key="settings_student_id_input",
                )

                st.write("")
                col_cls, col_subj = st.columns(2)
                with col_cls:
                    curr_cls = get_student_class_level()
                    selected_cls_label = st.radio(
                        "Class / Standard",
                        options=["Class 10", "Class 9"],
                        index=0 if curr_cls == 10 else 1,
                        help="Master standard setting (Class 10 or Class 9). Only one standard is active at a time.",
                        key="settings_class_radio",
                    )
                    new_cls_int = 10 if selected_cls_label == "Class 10" else 9

                with col_subj:
                    curr_subj = get_student_subject()
                    selected_subj = st.radio(
                        "Subject",
                        options=["Science", "Mathematics"],
                        index=0 if curr_subj == "Science" else 1,
                        help="Active subject for NCERT chapters, quizzes, SWAT analytics, and AI Tutor.",
                        key="settings_subject_radio",
                    )

                st.write("")
                chapter_options = ["All Chapters"]
                chs = curriculum_service.get_chapters_for_grade(new_cls_int, subject=selected_subj)
                for ch in chs:
                    chapter_options.append(f"Ch {ch.chapter_number}: {ch.chapter_title}")

                curr_chapter = st.session_state.get("selected_chapter", "All Chapters")
                curr_ch_idx = (
                    chapter_options.index(curr_chapter) if curr_chapter in chapter_options else 0
                )
                selected_chapter = st.selectbox(
                    f"Default Focus Chapter ({selected_subj})", chapter_options, index=curr_ch_idx
                )

                st.write("")
                if st.button(
                    "Save Changes",
                    type="primary",
                    key="save_profile_settings_btn",
                    icon=":material/save:",
                ):
                    set_student_class_level(new_cls_int)
                    set_student_subject(selected_subj)
                    st.session_state.student_id = student_id.strip() or "student_001"
                    st.session_state.selected_chapter = selected_chapter
                    st.success(
                        f"Profile saved successfully! Master Standard set to Class {new_cls_int} ({selected_subj})."
                    )
                    st.rerun()

        # Tab 3: Appearance
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
