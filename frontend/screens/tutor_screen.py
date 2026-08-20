"""NCERT Q&A Tutor Screen component (No Emojis)."""

import asyncio
import logging
from typing import Optional
import streamlit as st

from src.academic_rag.rag.engine import stream_ncert_rag_response

logger = logging.getLogger(__name__)


async def render_tutor_screen(selected_model: str, user_api_key: str, selected_class: str) -> None:
    """Renders the conversational NCERT Science Q&A Tutor screen."""
    streaming_speed = 0.025

    # Suggested Prompts
    st.markdown("##### Suggested Questions")
    
    col1, col2, col3, col4 = st.columns(4)
    quick_prompts = [
        ("Ohm's Law and Resistance", "What is Ohm's law and how is resistance calculated in Class 10 Science?"),
        ("Cell Organelles", "What are the main cell organelles and function of the plasma membrane in Class 9 Science?"),
        ("Carbon Covalent Bonds", "Why does carbon form covalent bonds and what is catenation in Class 10 Science?"),
        ("Atmospheric Refraction", "Why does the sky appear blue and what causes atmospheric refraction in Class 10 Science?"),
    ]

    cols = [col1, col2, col3, col4]
    for idx, (label, prompt_text) in enumerate(quick_prompts):
        if cols[idx].button(label, key=f"qp_{idx}", use_container_width=True):
            st.session_state.active_prompt = prompt_text

    st.write("")

    # Chat History
    for message in st.session_state.get("messages", []):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Check API Key
    if not user_api_key:
        st.info("Please enter your Google Gemini API key in the sidebar to start asking questions.")
        return

    # Chat Input
    prompt_input = st.chat_input("Ask any question from NCERT Class 9 or 10 Science...")
    prompt = prompt_input or st.session_state.pop("active_prompt", None)

    if prompt:
        clean_prompt = prompt.strip()
        if len(clean_prompt) >= 2:
            logger.info(f"Tutor query: {clean_prompt}")
            st.session_state.messages.append({"role": "user", "content": clean_prompt})
            
            with st.chat_message("user"):
                st.markdown(clean_prompt)

            with st.chat_message("assistant"):
                with st.spinner("Searching NCERT Science textbooks..."):
                    message_placeholder = st.empty()
                    full_response = ""

                    cls_filter = 9 if selected_class == "Class 9" else (10 if selected_class == "Class 10" else None)

                    try:
                        async for delta in stream_ncert_rag_response(
                            query=clean_prompt,
                            class_filter=cls_filter,
                            api_key=user_api_key,
                            model_name=selected_model,
                            chat_history=st.session_state.messages[:-1],
                        ):
                            full_response += delta
                            message_placeholder.markdown(full_response + "▌")
                            await asyncio.sleep(streaming_speed)

                        if full_response and full_response.strip():
                            message_placeholder.markdown(full_response)
                        else:
                            error_msg = "I was unable to find a grounded answer in the NCERT textbooks. Please try rephrasing your question."
                            message_placeholder.error(error_msg)
                            full_response = error_msg

                    except Exception as e:
                        logger.error(f"Error in tutor response: {e}")
                        full_response = f"I encountered an error retrieving or generating the answer: {e}"
                        message_placeholder.error(full_response)

                st.session_state.messages.append({"role": "assistant", "content": full_response})
                st.rerun()
