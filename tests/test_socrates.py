"""Unit and integration tests for the Socrates Learning System in Quizzes."""

import asyncio
import unittest
from unittest.mock import MagicMock, patch

from backend.config import AppConfig
from backend.quiz.socrates import (
    _generate_fallback_hints,
    enrich_quiz_with_socrates,
    generate_socrates_dialogue_sync,
    generate_socrates_hints,
    generate_socrates_misconception,
    stream_socrates_dialogue,
)


class TestSocratesHints(unittest.TestCase):
    """Tests for 3-Tier Socratic Hint generation and fallback logic."""

    def test_fallback_hints_structure(self):
        """Verify fallback hints generate 3 distinct tiers."""
        question = "What is the unit of electric current?"
        options = ["A) Volt", "B) Ampere", "C) Ohm", "D) Joule"]
        explanation = "Electric current is measured in Ampere (A), named after André-Marie Ampère."
        chapter = "Electricity"
        class_level = 10

        hints = _generate_fallback_hints(question, options, explanation, chapter, class_level)
        self.assertIn("thought_starter", hints)
        self.assertIn("guiding_principle", hints)
        self.assertIn("socratic_deduction", hints)

        self.assertTrue(len(hints["thought_starter"]) > 10)
        self.assertTrue(len(hints["guiding_principle"]) > 10)
        self.assertTrue(len(hints["socratic_deduction"]) > 10)
        self.assertIn("Electricity", hints["thought_starter"])

    def test_fallback_hints_with_dict_options(self):
        """Verify fallback hints work when options are passed as a dictionary."""
        question = "Which law states F = ma?"
        options = {"A": "First Law", "B": "Second Law", "C": "Third Law", "D": "Law of Gravitation"}
        explanation = (
            "Newton's second law of motion gives the relation between force and acceleration."
        )

        hints = _generate_fallback_hints(
            question, options, explanation, "Force and Laws of Motion", 9
        )
        self.assertIn("thought_starter", hints)
        self.assertIn("guiding_principle", hints)
        self.assertIn("socratic_deduction", hints)

    @patch.object(AppConfig, "get_google_api_key", return_value=None)
    def test_generate_socrates_hints_without_api_key(self, mock_api_key):
        """Verify generate_socrates_hints falls back gracefully without API key."""
        hints = generate_socrates_hints(
            question="What is photosynthesis?",
            options=[
                "A) Respiration",
                "B) Food production in plants",
                "C) Transpiration",
                "D) Excretion",
            ],
            chapter="Life Processes",
            class_level=10,
            explanation="Plants prepare food through photosynthesis using sunlight and chlorophyll.",
        )
        self.assertEqual(len(hints), 3)
        self.assertIn("thought_starter", hints)
        self.assertIn("guiding_principle", hints)
        self.assertIn("socratic_deduction", hints)

    @patch.object(AppConfig, "get_google_api_key", return_value="dummy-key")
    @patch("backend.quiz.socrates.OpenAI")
    def test_generate_socrates_hints_with_llm(self, mock_openai_cls, mock_api_key):
        """Verify LLM-based hint generation parses valid JSON."""
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[
                MagicMock(
                    message=MagicMock(
                        content='{"thought_starter": "Consider energy changes.", "guiding_principle": "Law of Conservation of Energy.", "socratic_deduction": "Eliminate choices where energy is destroyed."}'
                    )
                )
            ]
        )

        hints = generate_socrates_hints(
            question="What happens in an exothermic reaction?",
            options=[
                "A) Heat absorbed",
                "B) Heat released",
                "C) No energy change",
                "D) Temperature decreases",
            ],
            chapter="Chemical Reactions and Equations",
            class_level=10,
            api_key="dummy-key",
        )
        self.assertEqual(hints["thought_starter"], "Consider energy changes.")
        self.assertEqual(hints["guiding_principle"], "Law of Conservation of Energy.")
        self.assertEqual(
            hints["socratic_deduction"], "Eliminate choices where energy is destroyed."
        )


class TestSocratesMisconception(unittest.TestCase):
    """Tests for Socratic reflection on incorrect options (elenchus)."""

    @patch.object(AppConfig, "get_google_api_key", return_value=None)
    def test_misconception_fallback(self, mock_api_key):
        """Verify misconception feedback without API key produces helpful inquiry."""
        reflection = generate_socrates_misconception(
            question_text="What is the resistance of an ideal ammeter?",
            options=["A) Zero", "B) Infinite", "C) 100 Ohms", "D) Variable"],
            chosen_option="B",
            correct_option="A",
            chapter="Electricity",
            class_level=10,
            explanation="An ideal ammeter has zero resistance so it does not alter the circuit current.",
            api_key=None,
        )
        self.assertIn("Socrates Reflection", reflection)
        self.assertIn("Option **B**", reflection)
        self.assertIn("Electricity", reflection)

    @patch.object(AppConfig, "get_google_api_key", return_value="dummy-key")
    @patch("backend.quiz.socrates.OpenAI")
    def test_misconception_llm(self, mock_openai_cls, mock_api_key):
        """Verify LLM-based misconception feedback."""
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[
                MagicMock(
                    message=MagicMock(
                        content="If an ammeter had infinite resistance, how could current flow through it? Think about what we measure in series."
                    )
                )
            ]
        )

        reflection = generate_socrates_misconception(
            question_text="What is the resistance of an ideal ammeter?",
            options=["A) Zero", "B) Infinite", "C) 100 Ohms", "D) Variable"],
            chosen_option="B",
            correct_option="A",
            chapter="Electricity",
            class_level=10,
            api_key="dummy-key",
        )
        self.assertIn("infinite resistance", reflection)


class TestSocratesDialogue(unittest.TestCase):
    """Tests for Socratic dialogue conversation."""

    @patch.object(AppConfig, "get_google_api_key", return_value=None)
    def test_dialogue_without_api_key(self, mock_api_key):
        """Verify dialogue prompt requires API key if missing."""

        async def run_test():
            chunks = []
            async for chunk in stream_socrates_dialogue(
                question_text="Why do stars twinkle?",
                options=[
                    "A) Atmospheric refraction",
                    "B) Reflection",
                    "C) Dispersion",
                    "D) Scattering",
                ],
                student_query="Can you explain this?",
                api_key=None,
            ):
                chunks.append(chunk)
            return "".join(chunks)

        result = asyncio.run(run_test())
        self.assertIn("Google Gemini API key", result)

    @patch.object(AppConfig, "get_google_api_key", return_value=None)
    def test_sync_dialogue_without_api_key(self, mock_api_key):
        """Verify sync dialogue without API key."""
        result = generate_socrates_dialogue_sync(
            question_text="Why do stars twinkle?",
            options=[
                "A) Atmospheric refraction",
                "B) Reflection",
                "C) Dispersion",
                "D) Scattering",
            ],
            student_query="Help me understand this.",
            api_key=None,
        )
        self.assertIn("Google Gemini API key", result)

    @patch(
        "backend.quiz.socrates.retrieve_ncert_context",
        return_value="[PAGE: 10] Refraction context.",
    )
    @patch.object(AppConfig, "get_google_api_key", return_value="dummy-key")
    @patch("backend.quiz.socrates.OpenAI")
    def test_sync_dialogue_with_llm(self, mock_openai_cls, mock_api_key, mock_retriever):
        """Verify sync dialogue calls LLM with Socratic prompt."""
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[
                MagicMock(
                    message=MagicMock(
                        content="Consider what happens to light as it travels through layers of varying density in the atmosphere."
                    )
                )
            ]
        )

        result = generate_socrates_dialogue_sync(
            question_text="Why do stars twinkle?",
            options=[
                "A) Atmospheric refraction",
                "B) Reflection",
                "C) Dispersion",
                "D) Scattering",
            ],
            student_query="Why not reflection?",
            chapter="Human Eye and Colourful World",
            class_level=10,
            api_key="dummy-key",
        )
        self.assertIn("varying density", result)


class TestQuizEnrichment(unittest.TestCase):
    """Tests for enriching quiz dictionaries with Socratic features."""

    def test_enrich_quiz_with_socrates(self):
        """Verify all questions receive socrates_hints."""
        quiz_data = {
            "chapter": "Light - Reflection and Refraction",
            "class_level": 10,
            "questions": [
                {
                    "question": "What is the focal length of a plane mirror?",
                    "options": ["A) Zero", "B) Infinity", "C) 25 cm", "D) -25 cm"],
                    "correct_answer": "B",
                    "explanation": "The focal length of a plane mirror is infinite because its radius of curvature is infinite.",
                },
                {
                    "question": "What is the unit of power of a lens?",
                    "options": ["A) Meter", "B) Dioptre", "C) Watt", "D) Candela"],
                    "correct_answer": "B",
                    "explanation": "Power of a lens is expressed in Dioptres (D), where 1 D = 1 m^-1.",
                },
            ],
        }

        enriched = enrich_quiz_with_socrates(quiz_data)
        self.assertTrue(enriched.get("socrates_enabled"))
        for q in enriched["questions"]:
            self.assertIn("socrates_hints", q)
            self.assertIn("thought_starter", q["socrates_hints"])
            self.assertIn("guiding_principle", q["socrates_hints"])
            self.assertIn("socratic_deduction", q["socrates_hints"])


if __name__ == "__main__":
    unittest.main()
