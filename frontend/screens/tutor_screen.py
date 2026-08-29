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

# Curated pools of conceptual NCERT Science & Math questions strictly grounded in uploaded curriculum
CLASS_9_SUGGESTIONS: List[Tuple[str, str]] = [
    (
        "Scientific Inquiry & Methods",
        "How do hypothesis formulation, controlled variables, and scientific observation work in Class 9 Science?",
    ),
    (
        "Cell Organelles & Life",
        "What are the main cell organelles and function of the plasma membrane in Class 9 Science?",
    ),
    (
        "Osmosis & Cell Pressure",
        "What happens to a plant cell in hypotonic, isotonic, and hypertonic solutions during osmosis?",
    ),
    (
        "Plant & Animal Tissues",
        "What is the difference between xylem and phloem complex permanent tissues in Class 9 Science?",
    ),
    (
        "Epithelial & Muscular Tissues",
        "Describe the structure and functions of epithelial, connective, muscular, and nervous tissues.",
    ),
    (
        "Motion & Acceleration",
        "Explain the difference between speed and velocity and how acceleration is defined in Class 9 Science.",
    ),
    (
        "Motion Graphs & Velocity",
        "How do distance-time and velocity-time graphs represent uniform and accelerated motion?",
    ),
    (
        "Mixtures & Separation",
        "How do solutions, suspensions, and colloids differ, and what methods are used to separate mixtures?",
    ),
    (
        "Tyndall Effect & Colloids",
        "What causes the Tyndall effect in colloidal solutions and how is concentration calculated?",
    ),
    (
        "Newton's Laws of Motion",
        "State Newton's three laws of motion with everyday real-world examples from Class 9 Science.",
    ),
    (
        "Inertia & Momentum",
        "Explain inertia and the relationship between applied force, mass, and acceleration (F = ma).",
    ),
    (
        "Work & Kinetic Energy",
        "How is work done calculated, and what is the relationship between work and kinetic energy?",
    ),
    (
        "Energy Conservation & Power",
        "Explain the principle of conservation of energy and how mechanical power is calculated in Watts.",
    ),
    (
        "Rutherford & Thomson Models",
        "Describe Rutherford's alpha-particle scattering experiment and the resulting nuclear model of the atom.",
    ),
    (
        "Bohr Model & Shells",
        "Explain Bohr's model of the atom and the maximum electron capacity of K, L, M, and N shells.",
    ),
    (
        "Atomic Number & Valency",
        "What is atomic number, mass number, and how do you calculate valency in Class 9 Science?",
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
        "Echo & Sonar Applications",
        "What is the minimum distance required to hear an echo, and how do sonar and ultrasound work?",
    ),
    (
        "Modes of Reproduction",
        "What are the differences between asexual and sexual reproduction, including binary fission and budding?",
    ),
    (
        "Diversity & Classification",
        "Why is biological classification essential, and what are the main criteria for classifying living organisms?",
    ),
    (
        "Earth Systems & Cycles",
        "Explain how the atmosphere, hydrosphere, lithosphere, and biosphere interact in Earth's system.",
    ),
    (
        "Biogeochemical Cycles",
        "How do carbon and nitrogen cycles transfer matter and energy through Earth's ecosystem?",
    ),
]

CLASS_10_SUGGESTIONS: List[Tuple[str, str]] = [
    (
        "Chemical Reactions & Redox",
        "What are the different types of chemical reactions with balanced examples from Class 10 Science?",
    ),
    (
        "Acids, Bases & pH Scale",
        "How is the pH scale defined and what is the importance of pH in everyday life and digestion?",
    ),
    (
        "Salts & Chlor-Alkali",
        "Explain the chlor-alkali process and the preparation and uses of Bleaching Powder and Baking Soda.",
    ),
    (
        "Corrosion & Rusting",
        "What is corrosion and rancidity in Class 10 Science, and how does galvanization prevent rusting?",
    ),
    (
        "Metals & Reactivity Series",
        "Explain the reactivity series of metals and how ionic compounds are formed with properties.",
    ),
    (
        "Carbon Covalent Bonds",
        "Why does carbon form covalent bonds and what is catenation and tetravalency in Class 10 Science?",
    ),
    (
        "Homologous Series",
        "What is a homologous series of carbon compounds and how do you identify structural isomers?",
    ),
    (
        "Photosynthesis & Nutrition",
        "Explain the chemical equation for photosynthesis and the major events occurring during the process.",
    ),
    (
        "Nephron & Excretion",
        "Explain the structure and filtration mechanism of a nephron in human kidneys during urine formation.",
    ),
    (
        "Human Heart & Circulation",
        "Describe the double circulation system in the human heart and why separation of oxygenated blood is necessary.",
    ),
    (
        "Reflex Arc & Neurons",
        "Describe the pathway of a reflex arc and how electrical impulses travel across a synapse.",
    ),
    (
        "Plant Hormones & Tropisms",
        "How do auxins, gibberellins, and abscisic acid control plant growth and phototropism?",
    ),
    (
        "Flower Reproduction",
        "Explain the process of pollination and fertilization in flowering plants leading to seed formation.",
    ),
    (
        "Mendel's Monohybrid Cross",
        "Explain Mendel's law of segregation and the 3:1 phenotypic ratio in a monohybrid cross.",
    ),
    (
        "Sex Determination",
        "How is sex genetically determined in human offspring by X and Y chromosomes?",
    ),
    (
        "Refraction & Snell's Law",
        "State the laws of refraction of light and calculate refractive index using Snell's Law in Class 10 Science.",
    ),
    (
        "Mirror & Lens Formula",
        "Explain the sign convention, mirror formula 1/f = 1/v + 1/u, and lens formula with magnification.",
    ),
    (
        "Atmospheric Refraction",
        "Why does the sky appear blue and what causes atmospheric refraction and twinkling of stars?",
    ),
    (
        "Human Eye & Defects",
        "What are the causes of myopia (near-sightedness) and hypermetropia, and how are they corrected?",
    ),
    (
        "Ohm's Law & Resistance",
        "What is Ohm's law and how is electrical resistance calculated in series and parallel circuits?",
    ),
    (
        "Joule's Law of Heating",
        "Explain Joule's heating effect H = I²Rt and how electric fuses protect electrical circuits.",
    ),
    (
        "Electric Motor Principle",
        "Explain the working principle of an electric motor and the application of Fleming's Left-Hand Rule.",
    ),
    (
        "Magnetic Field of Solenoid",
        "Describe the magnetic field lines inside and around a current-carrying solenoid in Class 10 Science.",
    ),
    (
        "Food Chains & 10% Law",
        "Explain trophic levels in an ecosystem and why energy flow is unidirectional under Lindeman's 10% law.",
    ),
    (
        "Ozone Layer Depletion",
        "How does ozone layer depletion occur due to CFCs and why is the ozone shield vital for life on Earth?",
    ),
]


CLASS_9_MATH_SUGGESTIONS: List[Tuple[str, str]] = [
    (
        "Coordinate Geometry & Plane",
        "How do Cartesian coordinates work and how do you plot points on the coordinate plane in Class 9 Mathematics?",
    ),
    (
        "Quadrants & Axes",
        "How do you identify the signs of coordinates in the four quadrants and on the coordinate axes?",
    ),
    (
        "Linear Polynomials & Zeroes",
        "What is a linear polynomial and how do you find its zeroes and graph in Class 9 Mathematics?",
    ),
    (
        "Polynomial Degree & Roots",
        "How is the degree of a polynomial defined and how do you evaluate polynomials at given points?",
    ),
    (
        "Rational & Real Numbers",
        "Explain rational vs irrational numbers, decimal expansions, and real numbers in Class 9 Mathematics.",
    ),
    (
        "Irrational Numbers on Line",
        "How do you represent irrational numbers like √2 and √3 geometrically on the number line?",
    ),
    (
        "Algebraic Identities",
        "Explain key algebraic identities like (a+b)², (a-b)², (a+b)³, and (x+y+z)² with examples.",
    ),
    (
        "Factorization with Identities",
        "How do you factorize algebraic expressions using standard algebraic identities in Class 9?",
    ),
    (
        "Circular Motion & Angles",
        "How are angles, rotation, and circular geometric patterns analyzed in Chapter 5 I'm Up and Down, and Round and Round?",
    ),
    (
        "Angles in Circles & Symmetry",
        "Explain the properties of angles subtended by arcs and chords in circular geometry.",
    ),
    (
        "Perimeter & Area Formulas",
        "How do you calculate the perimeter and area of triangles, quadrilaterals, and circles in Class 9 Mathematics?",
    ),
    (
        "Heron's Area Formula",
        "How do you use Heron's formula to find the area of a triangle when all three side lengths are given?",
    ),
    (
        "Introduction to Probability",
        "How is experimental probability defined and calculated using the formula P(E) = m/n?",
    ),
    (
        "Sample Spaces & Outcomes",
        "How do you determine the sample space and favorable outcomes for coin tosses and dice rolls?",
    ),
    (
        "Sequences & Progressions",
        "What is a mathematical sequence and how do you predict patterns and subsequent terms in progressions?",
    ),
    (
        "Pattern Rules & Terms",
        "How do you formulate algebraic rules to determine any term in an arithmetic or geometric sequence?",
    ),
]

CLASS_10_MATH_SUGGESTIONS: List[Tuple[str, str]] = [
    (
        "Real Numbers & HCF",
        "Explain the Fundamental Theorem of Arithmetic and how to find HCF and LCM by prime factorization.",
    ),
    (
        "Polynomials & Zeroes",
        "What is the relationship between the zeroes and coefficients of quadratic polynomials α+β = -b/a and αβ = c/a?",
    ),
    (
        "Pair of Linear Equations",
        "How do you solve a pair of linear equations in two variables using substitution and elimination methods?",
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
        "Similar Triangles & BPT",
        "State the Basic Proportionality Theorem (Thales Theorem) and criteria for similarity of triangles (AAA, SSS, SAS).",
    ),
    (
        "Distance & Section Formula",
        "How do you apply the distance formula and section formula in Class 10 coordinate geometry?",
    ),
    (
        "Trigonometric Identities",
        "State and prove fundamental trigonometric identities like sin²θ + cos²θ = 1 and 1 + tan²θ = sec²θ.",
    ),
    (
        "Heights & Distances",
        "How do angles of elevation and depression solve real-world heights and distances problems?",
    ),
    (
        "Tangent to a Circle",
        "Prove that lengths of tangents drawn from an external point to a circle are equal.",
    ),
    (
        "Sector & Segment Areas",
        "How do you calculate the area of a sector and segment of a circle with central angle θ?",
    ),
    (
        "Surface Areas & Volumes",
        "How do you find the volume and surface area of combination of solids (cylinder, cone, hemisphere)?",
    ),
    (
        "Statistics & Mean/Median",
        "How is the mean, median, and mode calculated for grouped frequency distribution data in Class 10?",
    ),
    (
        "Theoretical Probability",
        "How do you calculate the theoretical probability of simple and complementary events P(E) + P(not E) = 1?",
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

    ref_suggestions = []
    if student_id:
        try:
            from backend.storage.repository import study_material_repository

            docs = study_material_repository.get_student_documents(
                student_id=student_id, class_level=class_level, subject=subject
            )
            for doc in docs:
                m_name = doc.get("material_name") or doc.get("filename") or "Ref Material"
                chap = doc.get("chapter") or "Reference"
                ref_suggestions.append(
                    (f"Ref: {m_name[:18]}", f"Explain key concepts from {m_name} regarding {chap}.")
                )
        except Exception:
            pass

    if ref_suggestions:
        ref_pick = random.sample(ref_suggestions, min(2, len(ref_suggestions)))
        ncert_pick = random.sample(ncert_pool, min(4 - len(ref_pick), len(ncert_pool)))
        return ref_pick + ncert_pick

    return random.sample(ncert_pool, min(4, len(ncert_pool)))


async def render_tutor_screen(
    selected_model: str,
    user_api_key: str,
    selected_class: Optional[str] = None,
    student_id: Optional[str] = None,
) -> None:
    """Renders the conversational NCERT Q&A Tutor screen bound to master profile class and subject with Voice STT/TTS support."""
    # Top Navigation Back to Home (Phases 1-19)
    render_back_to_home("tutor")

    from backend.ai.speech_normalizer import normalize_voice_transcript
    from frontend.components.voice_assistant import (
        render_tts_player_component,
        render_voice_recorder_component,
    )
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
    st.markdown("### Ask a Doubt")
    st.caption(
        "Ask conceptual questions via voice or text with verified citations grounded in the **NCERT Curriculum** and your uploaded study materials."
    )

    # Active Sources Bar (M3 Chip Group)
    sources_chips = [
        '<div class="m3-chips-group" style="margin-bottom: 12px;">',
        '<span class="m3-chip m3-chip-primary"><span class="material-symbols-outlined" style="font-size: 1.05rem;">menu_book</span> NCERT Curriculum (Authoritative)</span>',
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

    # 1. Suggested Questions Region (Phases 3 & 9: Content-driven height only)
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
            st.rerun()

    st.write("")

    # 2. Conversation Area (Phases 3, 4, 7, 8: Transparent when empty, clean message bubbles when populated)
    conversation_container = st.container()

    # 3. Chat Composer Region (Phases 5, 11, 14: Anchored at bottom)
    prompt_input = st.chat_input(
        placeholder="Ask any question from the NCERT curriculum or your notes...",
    )
    prompt = prompt_input or st.session_state.pop("active_prompt", None)
    input_method = st.session_state.pop("last_input_method", "text")

    # In-Textbar Microphone Injector (100% invisible script injector)
    render_voice_recorder_component(
        component_key=f"voice_rec_{class_level}_{subject}",
        class_level=class_level,
        subject=subject,
    )

    with conversation_container:
        # Render historical chat messages
        for msg_idx, message in enumerate(st.session_state.get("messages", [])):
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                # Add Speech Audio Player for Assistant Answers
                if message["role"] == "assistant" and len(message.get("content", "").strip()) > 10:
                    render_tts_player_component(
                        display_text=message["content"],
                        message_idx=msg_idx,
                        button_label="Listen to Answer",
                        auto_play=False,
                    )

        # Handle active new prompt submission inside conversation area
        if prompt:
            is_voice = False
            raw_prompt = prompt.strip()
            if "\u200b[voice]" in raw_prompt:
                is_voice = True
                raw_prompt = raw_prompt.replace("\u200b[voice]", "").strip()
                clean_prompt = normalize_voice_transcript(raw_prompt)
                input_method = "voice"
            elif input_method == "voice":
                is_voice = True
                clean_prompt = normalize_voice_transcript(raw_prompt)
            else:
                clean_prompt = raw_prompt
                input_method = "text"

            if len(clean_prompt) >= 2:
                if "messages" not in st.session_state:
                    st.session_state.messages = []

                # Append user message (preserves input_method for multi-turn conversational history)
                st.session_state.messages.append(
                    {
                        "role": "user",
                        "content": clean_prompt,
                        "input_method": input_method,
                    }
                )
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

                        chunk_counter = 0
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
                            chunk_counter += 1
                            if chunk_counter % 2 == 0 or "\n" in chunk:
                                message_placeholder.markdown(full_response + "▌")
                                await asyncio.sleep(0)

                        message_placeholder.markdown(full_response)

                        # Render TTS Audio Player with auto-play ONLY if question was asked by voice
                        render_tts_player_component(
                            display_text=full_response,
                            message_idx=len(st.session_state.messages),
                            button_label="Listen to Answer",
                            auto_play=is_voice,
                        )

                    except GeminiQuotaExhaustedError:
                        message_placeholder.empty()
                        st.warning(
                            "**AI service temporarily unavailable**\n\n"
                            "The configured AI service has reached its current usage limit. "
                            "You can add your own Gemini API key in Settings to continue."
                        )
                        from frontend.state import navigate_to

                        if st.button(
                            "Open Settings",
                            icon=":material/settings:",
                            key="tutor_open_settings_btn",
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
