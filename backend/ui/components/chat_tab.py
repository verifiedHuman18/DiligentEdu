"""NCERT Q&A Tutor Chat Tab UI component."""

import asyncio
import logging

import streamlit as st

from backend.rag.engine import stream_ncert_rag_response

logger = logging.getLogger(__name__)


async def render_chat_tab(selected_model: str, user_api_key: str, selected_class: str):
    """Renders the conversational NCERT Q&A Tutor."""
    streaming_speed = 0.03

    # Grade banner
    if selected_class == "Class 9":
        st.info("**Active Mode:** Focused on **NCERT Class 9 Science** (Exploration)")
    elif selected_class == "Class 10":
        st.info("**Active Mode:** Focused on **NCERT Class 10 Science**")
    else:
        st.info("**Active Mode:** Comprehensive (Searching across Class 9 & Class 10)")

    # Quick Starter Prompts
    st.markdown("##### Suggested Questions to Explore:")
    prompt_cols = st.columns(4)
    quick_prompts = [
        (
            "What is Ohm's Law and resistance?",
            "What is Ohm's law and how is resistance calculated?",
        ),
        (
            "Cell Organelles & Plasma Membrane",
            "What are the main cell organelles and function of the plasma membrane in Class 9 Science?",
        ),
        (
            "Carbon Covalent Bonding",
            "Why does carbon form covalent bonds and what is catenation?",
        ),
        (
            "Why is the sky blue?",
            "Why does the sky appear blue and what causes atmospheric refraction?",
        ),
    ]

    for i, (label, p_text) in enumerate(quick_prompts):
        if prompt_cols[i].button(label, use_container_width=True, key=f"qp_{i}"):
            st.session_state.active_prompt = p_text

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # User input
    prompt_input = st.chat_input("Ask any question from NCERT Class 9 or 10 Science...")
    prompt = prompt_input or st.session_state.pop("active_prompt", None)

    if prompt:
        clean_prompt = prompt.strip()
        if len(clean_prompt) >= 2:
            logger.info(f"User query: {clean_prompt}")
            st.session_state.messages.append({"role": "user", "content": clean_prompt})
            with st.chat_message("user"):
                st.markdown(clean_prompt)

            with st.chat_message("assistant"):
                with st.spinner("Searching NCERT Science textbooks and synthesizing answer..."):
                    message_placeholder = st.empty()
                    full_response = ""

                    cls_filter = (
                        9
                        if selected_class == "Class 9"
                        else (10 if selected_class == "Class 10" else None)
                    )

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
                            error_msg = "I was unable to retrieve a complete answer. Please try rephrasing your question."
                            message_placeholder.error(error_msg)
                            full_response = error_msg

                    except Exception as e:
                        logger.error(f"Error processing response: {e}")
                        full_response = (
                            f"I encountered an error retrieving or generating the answer: {e}"
                        )
                        message_placeholder.error(full_response)

                st.session_state.messages.append({"role": "assistant", "content": full_response})
                st.rerun()
