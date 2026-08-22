"""NCERT Q&A Tutor Screen component with Material Icons (No Emojis)."""

import asyncio
import logging
from typing import Optional

import streamlit as st

from frontend.state import get_student_class_level, navigate_to
from src.academic_rag.rag.engine import stream_ncert_rag_response

logger = logging.getLogger(__name__)


async def render_tutor_screen(selected_model: str, user_api_key: str, selected_class: Optional[str] = None) -> None:
    """Renders the conversational NCERT Science Q&A Tutor screen bound to master profile class."""
    streaming_speed = 0.025

    if st.button(
        "Back to Home", icon=":material/arrow_back:", type="secondary", key="tutor_top_back_btn"
    ):
        navigate_to("home")
        st.rerun()

    class_level = get_student_class_level()

    st.write("")
    st.markdown(f"### Ask a Doubt — Class {class_level} · Science")
    st.caption(
        f"Ask conceptual science questions with verified textbook citations grounded strictly in **NCERT Class {class_level} Science**."
    )

    # Informational Standard Badge
    st.markdown(
        f"""
        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px;">
            <span style="background: var(--md-primary); color: var(--on-primary); font-weight: 700; font-size: 0.82rem; padding: 4px 10px; border-radius: 6px;">
                Your Class: Class {class_level} · Science
            </span>
            <span style="font-size: 0.8rem; color: var(--on-surface-variant);">
                (Grounded strictly in NCERT Class {class_level} textbooks)
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Suggested Prompts tailored to active standard
    st.markdown("##### Suggested Questions")

    if class_level == 9:
        quick_prompts = [
            (
                "Cell Organelles & Life",
                "What are the main cell organelles and function of the plasma membrane in Class 9 Science?",
            ),
            (
                "Motion & Acceleration",
                "Explain the difference between speed and velocity and how acceleration is defined in Class 9 Science.",
            ),
            (
                "Atomic Structure & Valency",
                "What is Bohr's model of the atom and how do you calculate valency in Class 9 Science?",
            ),
            (
                "Newton's Laws of Motion",
                "State Newton's three laws of motion with everyday real-world examples from Class 9 Science.",
            ),
        ]
    else:
        quick_prompts = [
            (
                "Ohm's Law & Resistance",
                "What is Ohm's law and how is electrical resistance calculated in Class 10 Science?",
            ),
            (
                "Chemical Reactions & Redox",
                "What are the different types of chemical reactions with balanced examples from Class 10 Science?",
            ),
            (
                "Carbon Covalent Bonds",
                "Why does carbon form covalent bonds and what is catenation in Class 10 Science?",
            ),
            (
                "Atmospheric Refraction",
                "Why does the sky appear blue and what causes atmospheric refraction in Class 10 Science?",
            ),
        ]

    col1, col2, col3, col4 = st.columns(4)
    cols = [col1, col2, col3, col4]
    for idx, (label, prompt_text) in enumerate(quick_prompts):
        if cols[idx].button(
            label, icon=":material/lightbulb:", key=f"qp_{class_level}_{idx}", use_container_width=True
        ):
            st.session_state.active_prompt = prompt_text

    st.write("")

    # Chat History
    for message in st.session_state.get("messages", []):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Check API Key
    if not user_api_key:
        st.info(
            "Please enter your Google Gemini API key in Settings (gear icon in the top right) to start asking questions."
        )
        return

    # Chat Input
    prompt_input = st.chat_input(f"Ask any question from NCERT Class {class_level} Science...")
    prompt = prompt_input or st.session_state.pop("active_prompt", None)

    if prompt:
        clean_prompt = prompt.strip()
        if len(clean_prompt) >= 2:
            if "messages" not in st.session_state:
                st.session_state.messages = []

            # Append user message
            st.session_state.messages.append({"role": "user", "content": clean_prompt})
            with st.chat_message("user"):
                st.markdown(clean_prompt)

            # Generate Assistant Response with strict class isolation
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                full_response = ""

                try:
                    async for chunk in stream_ncert_rag_response(
                        query=clean_prompt,
                        class_filter=class_level,
                        api_key=user_api_key,
                        model_name=selected_model,
                        chat_history=st.session_state.messages[:-1],
                    ):
                        full_response += chunk
                        message_placeholder.markdown(full_response + "▌")
                        await asyncio.sleep(streaming_speed)

                    message_placeholder.markdown(full_response)
                except Exception as e:
                    logger.error(f"Tutor response generation failed: {e}")
                    st.error(f"Error generating answer: {e}")
                    full_response = "Sorry, I encountered an issue generating the answer. Please check your API key."

            # Append assistant message
            st.session_state.messages.append({"role": "assistant", "content": full_response})
