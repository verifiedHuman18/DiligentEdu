"""NCERT Q&A Tutor Screen component with Material Icons (No Emojis)."""

import asyncio
import logging
from typing import Optional
import streamlit as st

from src.academic_rag.rag.engine import stream_ncert_rag_response
from frontend.state import navigate_to

logger = logging.getLogger(__name__)


async def render_tutor_screen(selected_model: str, user_api_key: str, selected_class: str) -> None:
    """Renders the conversational NCERT Science Q&A Tutor screen."""
    streaming_speed = 0.025

    if st.button("Back to Home", icon=":material/arrow_back:", type="secondary", key="tutor_top_back_btn"):
        navigate_to("home")
        st.rerun()

    st.write("")
    st.markdown("### NCERT Q&A Tutor")
    st.caption("Ask conceptual science questions with verified textbook citations.")

    # Suggested Prompts
    st.markdown("##### Suggested Questions")
    
    col1, col2, col3, col4 = st.columns(4)
    quick_prompts = [
        ("Ohm's Law & Resistance", "What is Ohm's law and how is resistance calculated in Class 10 Science?"),
        ("Cell Organelles & Life", "What are the main cell organelles and function of the plasma membrane in Class 9 Science?"),
        ("Carbon Covalent Bonds", "Why does carbon form covalent bonds and what is catenation in Class 10 Science?"),
        ("Atmospheric Refraction", "Why does the sky appear blue and what causes atmospheric refraction in Class 10 Science?"),
    ]

    cols = [col1, col2, col3, col4]
    for idx, (label, prompt_text) in enumerate(quick_prompts):
        if cols[idx].button(label, icon=":material/lightbulb:", key=f"qp_{idx}", use_container_width=True):
            st.session_state.active_prompt = prompt_text

    st.write("")

    # Chat History
    for message in st.session_state.get("messages", []):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Check API Key
    if not user_api_key:
        st.info("Please enter your Google Gemini API key in Settings (gear icon in the top right) to start asking questions.")
        return

    # Chat Input
    prompt_input = st.chat_input("Ask any question from NCERT Class 9 or 10 Science...")
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

            # Generate Assistant Response
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                full_response = ""

                try:
                    target_grade = None
                    if selected_class == "Class 9":
                        target_grade = 9
                    elif selected_class == "Class 10":
                        target_grade = 10

                    async for chunk in stream_ncert_rag_response(
                        query=clean_prompt,
                        class_filter=target_grade,
                        api_key=user_api_key,
                        model_name=selected_model,
                        chat_history=st.session_state.messages[:-1],
                    ):
                        full_response += chunk
                        message_placeholder.markdown(full_response + "▌")
                        await asyncio.sleep(streaming_speed)

                    message_placeholder.markdown(full_response)
                    st.session_state.messages.append({"role": "assistant", "content": full_response})

                except Exception as e:
                    err_msg = f"Unable to process question: {str(e)}"
                    message_placeholder.error(err_msg)
                    st.session_state.messages.append({"role": "assistant", "content": err_msg})
