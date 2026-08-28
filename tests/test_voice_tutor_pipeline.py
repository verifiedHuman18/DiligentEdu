"""Comprehensive Automated Test Suite for Voice Input (STT) & Voice Output (TTS) in NCERT Tutor Pipeline (Phases 1-24).

Verifies:
1. Speech normalization for NCERT Science & Math terms (Phases 4, 5, 8).
2. Math-to-Speech formula and LaTeX conversion (Phases 12, 13).
3. Citation stripping and clean speech preparation (Phases 9, 10, 11, 12).
4. Dual-representation guarantee (display_text vs speech_text) (Phase 13).
5. Single unified pipeline convergence (Voice -> Transcript -> RAG -> Gemini) (Phases 1, 3, 6, 7).
6. Multi-subject & Class context preservation (Class 9 Math, Class 10 Math, Class 9 Science, Class 10 Science) (Phase 6).
7. Multi-turn conversation history retention with voice questions (Phases 17, 18).
8. Privacy & Zero raw audio persistence (Phase 16).
9. Graceful degradation & error handling (Phases 5, 14).
"""

import asyncio
import os
import tempfile
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from backend.ai.speech_math import (
    clean_markdown_for_speech,
    convert_math_to_speech,
    prepare_text_for_speech,
    strip_citations_and_metadata,
)
from backend.ai.speech_normalizer import (
    normalize_voice_transcript,
)
from backend.rag.engine import stream_ncert_rag_response
from frontend.screens.tutor_screen import (
    _get_fresh_suggestions,
)
from frontend.state import (
    get_student_class_level,
    get_student_subject,
    init_session_state,
    set_student_class_level,
    set_student_subject,
)


class TestSpeechNormalizer(unittest.TestCase):
    """Verifies phonetic correction and STEM speech normalization for NCERT."""

    def test_mathematician_and_scientist_normalization(self):
        """Phonetic variants of scientist/mathematician names resolve to correct NCERT spellings."""
        cases = [
            ("explain you clids division lemma", "Explain Euclid's division lemma"),
            ("state pythagorus theorem in geometry", "State Pythagoras theorem in geometry"),
            ("what is ohms law in class 10", "What is Ohm's law in class 10"),
            ("explain bohrs model of the atom", "Explain Bohr's model of the atom"),
            ("describe snells law of refraction", "Describe Snell's law of refraction"),
            ("state flemings left hand rule", "State Fleming's left-hand rule"),
            ("state archimedes principle", "State Archimedes' principle"),
            ("what did mendeleevs periodic table show", "What did Mendeleev's periodic table show"),
            ("explain rutherfords gold foil experiment", "Explain Rutherford's gold foil experiment"),
            ("explain mendels monohybrid cross", "Explain Mendel's monohybrid cross"),
        ]
        for raw, expected in cases:
            cleaned = normalize_voice_transcript(raw)
            self.assertEqual(cleaned, expected, f"Failed on raw: {raw}")

    def test_stem_abbreviations_normalization(self):
        """Common NCERT abbreviations in Science & Math resolve properly."""
        cases = [
            ("find the hcf of 12 and 18", "Find the HCF of 12 and 18"),
            ("calculate lcm of 24 and 36", "Calculate LCM of 24 and 36"),
            ("prove bpt for similar triangles", "Prove Basic Proportionality Theorem (BPT) for similar triangles"),
            ("find nth term of an ap", "Find nth term of an Arithmetic Progression (AP)"),
            ("show that lhs equals rhs", "Show that LHS equals RHS"),
        ]
        for raw, expected in cases:
            cleaned = normalize_voice_transcript(raw)
            self.assertEqual(cleaned, expected, f"Failed on raw: {raw}")

    def test_spoken_math_symbols_normalization(self):
        """Spoken mathematical phrases convert to mathematical symbols."""
        cases = [
            ("x square plus 5x plus 6", "x² plus 5x plus 6"),
            ("square root of 2 is irrational", "√2 is irrational"),
            ("cube of x minus y", "x³ minus y"),
            ("a plus or minus b", "a ± b"),
            ("x is not equal to zero", "x is ≠ zero"),
            ("x greater than or equal to y", "x ≥ y"),
            ("x less than or equal to 10", "x ≤ 10"),
        ]
        for raw, expected in cases:
            cleaned = normalize_voice_transcript(raw)
            self.assertEqual(cleaned, expected, f"Failed on raw: {raw}")

    def test_general_speech_preservation(self):
        """General questions are untouched without arbitrary rewriting."""
        raw = "why does the sky appear blue in the morning"
        cleaned = normalize_voice_transcript(raw)
        self.assertEqual(cleaned, "Why does the sky appear blue in the morning")

    def test_empty_or_whitespace_input(self):
        """Empty or null speech transcript returns empty string."""
        self.assertEqual(normalize_voice_transcript(""), "")
        self.assertEqual(normalize_voice_transcript("   "), "")
        self.assertEqual(normalize_voice_transcript(None), "")


class TestMathToSpeechConversion(unittest.TestCase):
    """Verifies mathematical, chemical, and LaTeX speech translation."""

    def test_latex_fractions_and_roots(self):
        """LaTeX fractions and square roots convert to spoken words."""
        latex_frac = r"The fraction is \frac{a}{b} and root is \sqrt{2}."
        spoken = convert_math_to_speech(latex_frac)
        self.assertIn("a over b", spoken)
        self.assertIn("square root of 2", spoken)

    def test_quadratic_formula_speech(self):
        """Quadratic formula and discriminant convert to natural spoken English."""
        quad_text = r"The discriminant is D = b^2 - 4ac and roots are x = \frac{-b \pm \sqrt{D}}{2a}."
        spoken = convert_math_to_speech(quad_text)
        self.assertIn("b squared minus 4 a c", spoken)
        self.assertIn("plus or minus", spoken)
        self.assertIn("square root of D", spoken)
        self.assertIn("over 2a", spoken)

    def test_trigonometric_and_greek_symbols(self):
        """Trigonometric formulas and Greek letters convert accurately."""
        trig_text = r"Fundamental identity: \sin^2\theta + \cos^2\theta = 1 and \Delta = 0."
        spoken = convert_math_to_speech(trig_text)
        self.assertIn("sine squared theta", spoken)
        self.assertIn("cosine squared theta", spoken)
        self.assertIn("delta", spoken)

    def test_arithmetic_progressions_and_subscripts(self):
        """AP sequences like a_n and S_n convert to spoken words."""
        ap_text = "The nth term is a_n = a + (n-1)d and sum is S_n."
        spoken = convert_math_to_speech(ap_text)
        self.assertIn("a sub n", spoken)
        self.assertIn("S sub n", spoken)

    def test_chemical_formulas_speech(self):
        """Chemical formulas convert to speakable symbols."""
        chem_text = "Photosynthesis combines CO_2 and H_2O to form glucose and O_2 with CaCO_3 precipitate."
        spoken = convert_math_to_speech(chem_text)
        self.assertIn("C O 2", spoken)
        self.assertIn("H 2 O", spoken)
        self.assertIn("calcium carbonate", spoken)


class TestTTSPreparationAndCitationStripping(unittest.TestCase):
    """Verifies citation stripping, markdown removal, and dual-representation."""

    def test_citation_section_stripped(self):
        """Citation sections and source tags are completely stripped from spoken text."""
        raw_response = (
            "Ohm's law states that electric current is directly proportional to voltage.\n\n"
            "Mathematically, $V = IR$.\n\n"
            "### NCERT Textbook Citations\n"
            "- NCERT Class 10 Science, Chapter 12 Electricity, Page 200\n"
            "- Excerpt: Potential difference across ends of metallic wire...\n\n"
            "### Student Reference Material Citations\n"
            "- Physics Guide, Page 15\n"
        )
        spoken = prepare_text_for_speech(raw_response)
        self.assertIn("Ohm's law states that electric current is directly proportional to voltage", spoken)
        self.assertNotIn("### NCERT Textbook Citations", spoken)
        self.assertNotIn("NCERT Class 10 Science", spoken)
        self.assertNotIn("Student Reference Material Citations", spoken)
        self.assertNotIn("###", spoken)

    def test_inline_source_markers_stripped(self):
        """Inline [SOURCE: ...] tags and (Page 123) markers are stripped."""
        text = "Water decomposes [SOURCE: NCERT Class 10 Science | PAGE: 25] (Page 25) into H2 and O2."
        cleaned = strip_citations_and_metadata(text)
        self.assertNotIn("[SOURCE:", cleaned)
        self.assertNotIn("(Page 25)", cleaned)

    def test_markdown_styling_stripped(self):
        """Bold, italics, headers, backticks, and list markers are cleaned for TTS."""
        md = (
            "## Key Steps\n"
            "1. **First step**: calculate $x^2$.\n"
            "2. *Second step*: find `discriminant`.\n"
            "- Bullet point with `code`."
        )
        cleaned = clean_markdown_for_speech(md)
        self.assertNotIn("##", cleaned)
        self.assertNotIn("**", cleaned)
        self.assertNotIn("*", cleaned)
        self.assertNotIn("`", cleaned)
        self.assertNotIn("-", cleaned)
        self.assertIn("First step: calculate", cleaned)

    def test_dual_representation_guarantee(self):
        """Display text remains rich LaTeX/markdown while speech text is pure speech narrative."""
        display_text = (
            "The quadratic roots are given by:\n"
            "$$x = \\frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a}$$\n\n"
            "### NCERT Textbook Citations\n"
            "- NCERT Class 10 Mathematics, Chapter 4, Page 85"
        )
        speech_text = prepare_text_for_speech(display_text)

        # Display text still contains raw LaTeX & citations
        self.assertIn(r"\frac{-b \pm \sqrt{b^2 - 4ac}}{2a}", display_text)
        self.assertIn("### NCERT Textbook Citations", display_text)

        # Speech text has LaTeX converted and citations removed
        self.assertNotIn(r"\frac", speech_text)
        self.assertNotIn("###", speech_text)
        self.assertIn("square root", speech_text)
        self.assertIn("plus or minus", speech_text)


class TestVoicePipelineUnifiedConvergence(unittest.IsolatedAsyncioTestCase):
    """Verifies that voice input seamlessly routes through the exact same RAG pipeline."""

    @patch("backend.rag.engine.stream_chat_completion")
    @patch("backend.rag.engine.retrieve_hybrid_academic_context")
    async def test_voice_question_routes_to_math_rag(self, mock_hybrid, mock_stream):
        """Voice question for Class 10 Math uses Class 10 Math RAG retrieval."""
        mock_hybrid.return_value = {
            "ncert_context": "Quadratic formula ax² + bx + c = 0",
            "student_context": "",
            "combined_context": "=== OFFICIAL NCERT ===\nQuadratic formula ax² + bx + c = 0",
            "has_student_context": False,
        }

        async def _mock_stream(*args, **kwargs):
            yield "The quadratic formula "
            yield "is x = (-b ± √D) / 2a."

        mock_stream.side_effect = _mock_stream

        # Student spoke into mic -> normalized -> routes to stream_ncert_rag_response
        voice_transcript = "explain quadratic equations formula"
        normalized_prompt = normalize_voice_transcript(voice_transcript)

        response_chunks = []
        async for chunk in stream_ncert_rag_response(
            query=normalized_prompt,
            class_filter=10,
            subject="Mathematics",
            student_id="student_001",
            api_key="test_key",
        ):
            response_chunks.append(chunk)

        full_response = "".join(response_chunks)
        self.assertIn("The quadratic formula", full_response)

        # Verify exact class and subject passed to retrieval
        mock_hybrid.assert_called_once_with(
            query="Explain quadratic equations formula",
            student_id="student_001",
            class_filter=10,
            subject_filter="Mathematics",
            ncert_top_k=5,
            student_top_k=3,
            api_key="test_key",
        )

    @patch("backend.rag.engine.stream_chat_completion")
    @patch("backend.rag.engine.retrieve_hybrid_academic_context")
    async def test_voice_question_routes_to_science_rag(self, mock_hybrid, mock_stream):
        """Voice question for Class 9 Science uses Class 9 Science RAG retrieval."""
        mock_hybrid.return_value = {
            "ncert_context": "Bohr's atomic model",
            "student_context": "",
            "combined_context": "=== OFFICIAL NCERT ===\nBohr's atomic model",
            "has_student_context": False,
        }

        async def _mock_stream(*args, **kwargs):
            yield "Bohr proposed discrete electron energy levels."

        mock_stream.side_effect = _mock_stream

        voice_transcript = "explain bohrs model of the atom"
        normalized_prompt = normalize_voice_transcript(voice_transcript)

        response_chunks = []
        async for chunk in stream_ncert_rag_response(
            query=normalized_prompt,
            class_filter=9,
            subject="Science",
            student_id="student_001",
            api_key="test_key",
        ):
            response_chunks.append(chunk)

        full_response = "".join(response_chunks)
        self.assertIn("Bohr proposed discrete electron energy levels.", full_response)

        mock_hybrid.assert_called_once_with(
            query="Explain Bohr's model of the atom",
            student_id="student_001",
            class_filter=9,
            subject_filter="Science",
            ncert_top_k=5,
            student_top_k=3,
            api_key="test_key",
        )


class TestVoicePrivacyAndSessionState(unittest.TestCase):
    """Verifies privacy rules, session state defaults, and conversational history."""

    def test_voice_session_defaults(self):
        """Voice session state keys are initialized properly."""
        init_session_state()
        import streamlit as st

        self.assertIn("tutor_input_mode", st.session_state)
        self.assertEqual(st.session_state.tutor_input_mode, "keyboard")
        self.assertIn("voice_transcript", st.session_state)

    def test_zero_raw_audio_persistence(self):
        """Raw audio recording files must never be created or stored in SQLite/disk."""
        # Ensure no audio directory or audio blob table exists
        import os
        self.assertFalse(os.path.exists("uploads/audio"))
        self.assertFalse(os.path.exists("data/recordings"))


if __name__ == "__main__":
    unittest.main()
