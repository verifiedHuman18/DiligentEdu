"""NCERT Q&A Tutor Screen component with Material Icons (No Emojis)."""

import asyncio
import logging
import random
from typing import List, Optional, Tuple

import streamlit as st

from backend.rag.engine import stream_ncert_rag_response
from frontend.components.navigation import render_back_to_home
from frontend.state import get_student_class_level

logger = logging.getLogger(__name__)

# Curated pools of conceptual NCERT Science questions for dynamic suggestion rotation
CLASS_9_SUGGESTIONS: List[Tuple[str, str]] = [
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
    (
        "Plant & Animal Tissues",
        "What is the difference between xylem and phloem complex permanent tissues in Class 9 Science?",
    ),
    (
        "Mixtures & Tyndall Effect",
        "How do solutions, suspensions, and colloids differ, and what causes the Tyndall effect?",
    ),
    (
        "Work & Kinetic Energy",
        "How is work done calculated, and what is the relationship between work and kinetic energy?",
    ),
    (
        "Gravitation & Free Fall",
        "State Newton's Universal Law of Gravitation and explain why acceleration due to gravity (g) varies.",
    ),
    (
        "Conservation of Mass",
        "Explain the Law of Conservation of Mass and the Law of Constant Proportions with examples.",
    ),
    (
        "Sound Waves & Frequency",
        "How does sound propagate as a longitudinal wave, and what is the relationship between wavelength and speed?",
    ),
    (
        "Archimedes' Principle",
        "State Archimedes' Principle and explain how buoyant force determines whether an object floats or sinks.",
    ),
    (
        "States of Matter & Heat",
        "What is latent heat of fusion and vaporization, and how does evaporation cause cooling?",
    ),
    (
        "Rutherford's Gold Foil",
        "Describe Rutherford's alpha-particle scattering experiment and the resulting nuclear model of the atom.",
    ),
    (
        "Osmosis & Cell Pressure",
        "What happens to a plant cell in hypotonic, isotonic, and hypertonic solutions during osmosis?",
    ),
    (
        "Echo & Reverberation",
        "What is the minimum distance required to hear an echo, and how is reverberation reduced in halls?",
    ),
    (
        "Energy Conservation",
        "Explain the principle of conservation of energy using the example of a freely falling body.",
    ),
]

CLASS_10_SUGGESTIONS: List[Tuple[str, str]] = [
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
        "Why does carbon form covalent bonds and what is catenation and tetravalency in Class 10 Science?",
    ),
    (
        "Atmospheric Refraction",
        "Why does the sky appear blue and what causes atmospheric refraction and twinkling of stars?",
    ),
    (
        "Photosynthesis & Nutrition",
        "Explain the chemical equation for photosynthesis and the major events occurring during the process.",
    ),
    (
        "Acids, Bases & pH Scale",
        "How is the pH scale defined and what is the importance of pH in everyday life and digestion?",
    ),
    (
        "Refraction & Snell's Law",
        "State the laws of refraction of light and calculate refractive index using Snell's Law in Class 10 Science.",
    ),
    (
        "Electric Motor Principle",
        "Explain the working principle of an electric motor and the application of Fleming's Left-Hand Rule.",
    ),
    (
        "Mendel's Monohybrid Cross",
        "Explain Mendel's law of segregation and the 3:1 phenotypic ratio in a monohybrid cross.",
    ),
    (
        "Reflex Arc & Neurons",
        "Describe the pathway of a reflex arc and how electrical impulses travel across a synapse.",
    ),
    (
        "Corrosion & Rusting",
        "What is corrosion and rancidity in Class 10 Science, and how does galvanization prevent rusting?",
    ),
    (
        "Human Eye & Myopia",
        "What are the causes of myopia (near-sightedness) and hypermetropia, and how are they corrected?",
    ),
    (
        "Food Chains & 10% Law",
        "Explain trophic levels in an ecosystem and why energy flow is unidirectional under Lindeman's 10% law.",
    ),
    (
        "Homologous Series",
        "What is a homologous series of carbon compounds and how do you identify structural isomers?",
    ),
    (
        "Magnetic Field of Solenoid",
        "Describe the magnetic field lines inside and around a current-carrying solenoid in Class 10 Science.",
    ),
    (
        "Nephron & Excretion",
        "Explain the structure and filtration mechanism of a nephron in human kidneys during urine formation.",
    ),
]


CLASS_9_MATH_SUGGESTIONS: List[Tuple[str, str]] = [
    (
        "Coordinate Geometry",
        "How do Cartesian coordinates work and how do you plot points on the coordinate plane in Class 9 Mathematics?",
    ),
    (
        "Linear Polynomials",
        "What is a linear polynomial and how do you find its zeroes and graph in Class 9 Mathematics?",
    ),
    (
        "World of Numbers",
        "Explain rational vs irrational numbers, decimal expansions, and real numbers in Class 9 Mathematics.",
    ),
    (
        "Algebraic Identities",
        "Explain key algebraic identities like (a+b)², (a-b)², (a+b)³, and (x+y+z)² with examples.",
    ),
    (
        "Perimeter & Area",
        "How do you calculate the perimeter and area of triangles, quadrilaterals, and circles in Class 9 Mathematics?",
    ),
    (
        "Introduction to Probability",
        "How is experimental probability defined and calculated using the formula P(E) = m/n?",
    ),
    (
        "Sequences & Progressions",
        "What is a mathematical sequence and how do you predict patterns and subsequent terms?",
    ),
    (
        "Shapes, Lines & Angles",
        "What are complementary, supplementary, and vertically opposite angles in geometry?",
    ),
]

CLASS_10_MATH_SUGGESTIONS: List[Tuple[str, str]] = [
    (
        "Real Numbers & HCF",
        "Explain the Fundamental Theorem of Arithmetic and how to find HCF and LCM by prime factorization.",
    ),
    (
        "Quadratic Equations",
        "Explain the quadratic formula, the discriminant D = b² - 4ac, and nature of roots in Class 10 Mathematics.",
    ),
    (
        "Arithmetic Progressions",
        "How do you derive the nth term a_n = a + (n-1)d and sum of n terms S_n in an Arithmetic Progression?",
    ),
    (
        "Trigonometric Identities",
        "State and prove fundamental trigonometric identities like sin²θ + cos²θ = 1 and 1 + tan²θ = sec²θ.",
    ),
    (
        "Similar Triangles & BPT",
        "State the Basic Proportionality Theorem (Thales Theorem) and criteria for similarity of triangles.",
    ),
    (
        "Pair of Linear Equations",
        "How do you solve a pair of linear equations in two variables using substitution and elimination methods?",
    ),
    (
        "Surface Areas & Volumes",
        "How do you find the volume and surface area of combination of solids (cylinder, cone, hemisphere)?",
    ),
    (
        "Statistics & Mean/Median",
        "How is the mean, median, and mode calculated for grouped frequency distribution data in Class 10?",
    ),
]


def _get_fresh_suggestions(
    class_level: int, subject: str = "Science", student_id: Optional[str] = None
) -> List[Tuple[str, str]]:
    """Samples 4 diverse suggested questions from active class/subject pool and uploaded reference books."""
    is_math = "math" in subject.lower()
    if is_math:
        ncert_pool = list(
            CLASS_9_MATH_SUGGESTIONS if class_level == 9 else CLASS_10_MATH_SUGGESTIONS
        )
    else:
        ncert_pool = list(CLASS_9_SUGGESTIONS if class_level == 9 else CLASS_10_SUGGESTIONS)

    return random.sample(ncert_pool, min(4, len(ncert_pool)))


async def render_tutor_screen(
    selected_model: str,
    user_api_key: str,
    selected_class: Optional[str] = None,
    student_id: Optional[str] = None,
) -> None:
    """Renders the conversational NCERT Q&A Tutor screen bound to master profile class and subject."""
    streaming_speed = 0.025

    # Top Navigation Back to Home (Phases 1-19)
    render_back_to_home("tutor")

    from frontend.state import get_student_subject

    class_level = get_student_class_level()
    subject = get_student_subject()
    active_student_id = student_id or st.session_state.get("student_id", "student_001")

    # Fetch student uploaded reference materials for current class and subject
    mat_count = 0
    try:
        from backend.storage.repository import study_material_repository

        mat_count = study_material_repository.count_student_documents(
            student_id=active_student_id, class_level=class_level, subject=subject
        )
    except Exception:
        pass

    st.write("")
    st.markdown(f"### Ask a Doubt — Class {class_level} · {subject}")
    st.caption(
        f"Ask conceptual {subject.lower()} questions with verified citations grounded in **NCERT Class {class_level} {subject}** and your uploaded study materials."
    )

    # Active Sources Bar (M3 Chip Group)
    sources_chips = [
        '<div class="m3-chips-group" style="margin-bottom: 12px;">',
        f'<span class="m3-chip m3-chip-primary"><span class="material-symbols-outlined" style="font-size: 1.05rem;">menu_book</span> NCERT Class {class_level} {subject} (Authoritative)</span>',
    ]
    if mat_count > 0:
        sources_chips.append(
            f'<span class="m3-chip m3-chip-cyan"><span class="material-symbols-outlined" style="font-size: 1.05rem;">auto_stories</span> {mat_count} Uploaded Reference Book(s) (Supplementary)</span>'
        )
    sources_chips.append("</div>")
    st.markdown("".join(sources_chips), unsafe_allow_html=True)
    st.write("")

    # Auto-update suggested questions on page navigation or class/subject switch
    needs_refresh = st.session_state.get("tutor_needs_refresh", True)
    stored_suggestions = st.session_state.get("tutor_suggested_questions")
    stored_class = st.session_state.get("tutor_suggested_class")
    stored_subject = st.session_state.get("tutor_suggested_subject")

    if (
        needs_refresh
        or stored_suggestions is None
        or stored_class != class_level
        or stored_subject != subject
    ):
        stored_suggestions = _get_fresh_suggestions(
            class_level, subject=subject, student_id=active_student_id
        )
        st.session_state.tutor_suggested_questions = stored_suggestions
        st.session_state.tutor_suggested_class = class_level
        st.session_state.tutor_suggested_subject = subject
        st.session_state.tutor_needs_refresh = False

    # Suggested Prompts tailored to active standard
    st.markdown("##### Suggested Questions")

    col1, col2, col3, col4 = st.columns(4)
    cols = [col1, col2, col3, col4]
    for idx, (label, prompt_text) in enumerate(stored_suggestions):
        if cols[idx].button(
            label,
            icon=":material/lightbulb:",
            key=f"qp_{class_level}_{subject}_{idx}_{label[:12]}",
            use_container_width=True,
        ):
            st.session_state.active_prompt = prompt_text

    st.write("")

    # Chat History
    for message in st.session_state.get("messages", []):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat Input
    prompt_input = st.chat_input(
        f"Ask any question from NCERT Class {class_level} {subject} or your notes..."
    )
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

            # Generate Assistant Response with strict class and student isolation
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                full_response = ""

                try:
                    from backend.exceptions import (
                        GeminiAuthError,
                        GeminiConfigurationError,
                        GeminiQuotaExhaustedError,
                    )

                    async for chunk in stream_ncert_rag_response(
                        query=clean_prompt,
                        class_filter=class_level,
                        subject=subject,
                        student_id=active_student_id,
                        api_key=user_api_key,
                        model_name=selected_model,
                        chat_history=st.session_state.messages[:-1],
                    ):
                        full_response += chunk
                        message_placeholder.markdown(full_response + "▌")
                        await asyncio.sleep(streaming_speed)

                    message_placeholder.markdown(full_response)
                except GeminiQuotaExhaustedError:
                    message_placeholder.empty()
                    st.warning(
                        "**AI service temporarily unavailable**\n\n"
                        "The configured AI service has reached its current usage limit. "
                        "You can add your own Gemini API key in Settings to continue."
                    )
                    from frontend.state import navigate_to

                    if st.button(
                        "Open Settings", icon=":material/settings:", key="tutor_open_settings_btn"
                    ):
                        navigate_to("settings")
                        st.rerun()
                    full_response = "*(AI service reached usage limit. Add your fallback API key in Settings to continue.)*"
                except (GeminiAuthError, GeminiConfigurationError) as auth_err:
                    message_placeholder.empty()
                    st.error(f"**Authentication Error:** {auth_err}")
                    from frontend.state import navigate_to

                    if st.button(
                        "Configure API Key in Settings",
                        icon=":material/key:",
                        key="tutor_open_settings_auth_btn",
                    ):
                        navigate_to("settings")
                        st.rerun()
                    full_response = "*(API key configuration error. Please check Settings.)*"
                except Exception as e:
                    logger.error(f"Tutor response generation failed: {e}")
                    st.error(f"Error generating answer: {e}")
                    full_response = (
                        "Sorry, I encountered an issue generating the answer. Please try again."
                    )

            # Append assistant message
            st.session_state.messages.append({"role": "assistant", "content": full_response})
