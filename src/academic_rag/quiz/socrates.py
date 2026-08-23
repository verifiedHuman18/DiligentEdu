"""Socrates Learning System Engine for NCERT Science Quizzes.

Provides Socratic pedagogical features:
1. 3-Tier Progressive Socratic Hint Generation (Thought Starter -> Guiding Principle -> Socratic Deduction).
2. Live In-Quiz Socratic Dialogue Streaming (Elenchus & Guided Discovery without answer spoiling).
3. Socratic Misconception Reflection on Incorrect Attempts.
4. Quiz Enrichment for Socratic Mode.
"""

import json
import logging
from typing import Any, AsyncGenerator, Dict, List, Optional, Union

from openai import AsyncOpenAI, OpenAI

from src.academic_rag.config import config
from src.academic_rag.rag.prompts import (
    SOCRATES_HINT_GENERATOR_PROMPT_TEMPLATE,
    SOCRATES_MISCONCEPTION_PROMPT_TEMPLATE,
    SOCRATES_QUIZ_SYSTEM_PROMPT,
)
from src.academic_rag.rag.retriever import retrieve_ncert_context

logger = logging.getLogger(__name__)


def _generate_fallback_hints(
    question: str,
    options: Union[List[str], Dict[str, str]],
    explanation: str,
    chapter: str,
    class_level: int,
) -> Dict[str, str]:
    """Generates intelligent deterministic Socratic hints when LLM is offline or fast response is needed."""
    # Clean question text
    q_clean = question.strip().rstrip("?")

    # Extract key scientific keywords from explanation/question
    exp_first_sentence = explanation.split(".")[0].strip() if explanation else ""

    # Tier 1: Thought Starter
    thought_starter = (
        f"Consider what fundamental property or definition connects the conditions in '{q_clean}'. "
        f"What happens in the physical or chemical system as described in NCERT Class {class_level} '{chapter}'?"
    )

    # Tier 2: Guiding Principle
    if exp_first_sentence and len(exp_first_sentence) > 15:
        guiding_principle = (
            f"Recall the core NCERT scientific principle: {exp_first_sentence}. "
            f"How does this law or definition govern the relationship between the quantities or terms given?"
        )
    else:
        guiding_principle = (
            f"Refer to the core laws and definitions in NCERT Class {class_level} Science Chapter '{chapter}'. "
            f"Analyze how cause and effect are linked in this phenomenon."
        )

    # Tier 3: Socratic Deduction
    socratic_deduction = (
        f"Examine the 4 options carefully. Which choices contradict the foundational rule in '{chapter}'? "
        f"Eliminate extreme or reversed statements to isolate the scientifically accurate conclusion."
    )

    return {
        "thought_starter": thought_starter,
        "guiding_principle": guiding_principle,
        "socratic_deduction": socratic_deduction,
    }


def generate_socrates_hints(
    question: str,
    options: Union[List[str], Dict[str, str]],
    chapter: str,
    class_level: int = 10,
    explanation: str = "",
    api_key: Optional[str] = None,
    model: Optional[str] = None,
) -> Dict[str, str]:
    """
    Generates 3-tier progressive Socratic hints for a given question.
    Tier 1: Thought Starter (Intuitive inquiry)
    Tier 2: Guiding Principle (Core NCERT law / relationship)
    Tier 3: Socratic Deduction (Logical clue to eliminate distractors)
    """
    active_key = config.get_google_api_key(override=api_key)
    active_model = model or config.default_llm_model

    # If no API key or in fallback mode, use deterministic heuristic generator
    if not active_key:
        return _generate_fallback_hints(question, options, explanation, chapter, class_level)

    opts_str = ""
    if isinstance(options, dict):
        opts_str = "\n".join([f"{k}: {v}" for k, v in options.items()])
    elif isinstance(options, list):
        opts_str = "\n".join([str(o) for o in options])

    prompt = SOCRATES_HINT_GENERATOR_PROMPT_TEMPLATE.format(
        class_level=class_level,
        chapter=chapter,
        question=question,
        options=opts_str,
        explanation=explanation or f"NCERT Class {class_level} Science — {chapter}",
    )

    try:
        client = OpenAI(
            base_url=config.gemini_base_url,
            api_key=active_key,
        )
        response = client.chat.completions.create(
            model=active_model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a master Socratic teacher who generates progressive educational hints in valid JSON format.",
                },
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.3,
        )
        content = response.choices[0].message.content or "{}"
        hints = json.loads(content)

        # Validate required fields
        if (
            "thought_starter" in hints
            and "guiding_principle" in hints
            and "socratic_deduction" in hints
        ):
            return {
                "thought_starter": str(hints["thought_starter"]).strip(),
                "guiding_principle": str(hints["guiding_principle"]).strip(),
                "socratic_deduction": str(hints["socratic_deduction"]).strip(),
            }
    except Exception as e:
        logger.warning(f"Socratic hint generation via LLM failed: {e}. Using fallback hints.")

    return _generate_fallback_hints(question, options, explanation, chapter, class_level)


def generate_socrates_misconception(
    question_text: str,
    options: Union[List[str], Dict[str, str]],
    chosen_option: str,
    correct_option: str,
    chapter: str,
    class_level: int = 10,
    explanation: str = "",
    api_key: Optional[str] = None,
    model: Optional[str] = None,
) -> str:
    """
    Generates gentle Socratic reflection when a student chooses an incorrect option.
    Explains the common intuitive trap and asks a guiding counter-question without spoiling the real answer.
    """
    active_key = config.get_google_api_key(override=api_key)
    active_model = model or config.default_llm_model

    if not active_key:
        return (
            f"**Socrates Reflection:** You selected Option **{chosen_option}**. "
            f"Consider: why might this choice seem plausible at first, but break down under the core scientific laws of **{chapter}**? "
            f"Recall how NCERT defines this principle—what happens to the other variables involved? Re-read the options carefully and test another hypothesis."
        )

    opts_str = ""
    if isinstance(options, dict):
        opts_str = "\n".join([f"{k}: {v}" for k, v in options.items()])
    elif isinstance(options, list):
        opts_str = "\n".join([str(o) for o in options])

    prompt = SOCRATES_MISCONCEPTION_PROMPT_TEMPLATE.format(
        class_level=class_level,
        chapter=chapter,
        question=question_text,
        options=opts_str,
        chosen_option=chosen_option,
        explanation=explanation or f"NCERT Class {class_level} Science — {chapter}",
    )

    try:
        client = OpenAI(
            base_url=config.gemini_base_url,
            api_key=active_key,
        )
        response = client.chat.completions.create(
            model=active_model,
            messages=[
                {
                    "role": "system",
                    "content": "You are Socrates. Provide gentle Socratic misconception feedback without revealing the correct option.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.4,
        )
        ans = (response.choices[0].message.content or "").strip()
        if ans:
            return ans
    except Exception as e:
        logger.warning(f"Socratic misconception generation failed: {e}")

    return (
        f"**Socrates Reflection:** You selected Option **{chosen_option}**. "
        f"Take a moment to analyze: what underlying assumption in that choice conflicts with the scientific principles of **{chapter}**? "
        f"Examine what the textbook states about this concept and try again."
    )


async def stream_socrates_dialogue(
    question_text: str,
    options: Union[List[str], Dict[str, str]],
    student_query: str,
    chat_history: Optional[List[Dict[str, str]]] = None,
    chapter: str = "Science",
    class_level: int = 10,
    explanation: str = "",
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    top_k: int = 4,
) -> AsyncGenerator[str, None]:
    """
    Streams live Socratic dialogue for an individual quiz question.
    Grounded in NCERT context. Never gives away the answer directly.
    """
    active_key = config.get_google_api_key(override=api_key)
    if not active_key:
        yield "Please provide a valid Google Gemini API key in Settings (gear icon in the top right) to start your dialogue with Socrates."
        return

    active_model = model or config.default_llm_model

    # Retrieve NCERT Context with robust fallback
    retrieval_query = f"NCERT Class {class_level} Science {chapter} {question_text} {student_query}"
    ncert_context = ""
    try:
        ncert_context = retrieve_ncert_context(
            retrieval_query, class_filter=class_level, top_k=top_k
        )
    except Exception as ret_err:
        logger.warning(
            f"Pinecone context retrieval failed for Socrates dialogue ({ret_err}). Using question & chapter context."
        )
        ncert_context = f"[NCERT Class {class_level} Science — {chapter}]\nQuestion Context: {question_text}\nConcept: {explanation}"

    opts_str = ""
    if isinstance(options, dict):
        opts_str = "\n".join([f"- {k}: {v}" for k, v in options.items()])
    elif isinstance(options, list):
        opts_str = "\n".join([f"- {o}" for o in options])

    system_prompt = SOCRATES_QUIZ_SYSTEM_PROMPT.format(
        class_level=class_level,
        chapter=chapter,
    )

    messages = [{"role": "system", "content": system_prompt}]

    # Include recent conversation history for this question
    if chat_history:
        for msg in chat_history[-6:]:
            if msg.get("content"):
                messages.append({"role": msg["role"], "content": msg["content"]})

    user_content = f"""[NCERT TEXTBOOK EXCERPTS FOR CLASS {class_level} — {chapter}]:
{ncert_context}

[ACTIVE QUIZ QUESTION]:
Question: {question_text}
Options:
{opts_str}

[TEXTBOOK EXPLANATION BACKGROUND (INTERNAL TRUTH - DO NOT SPOIL)]:
{explanation}

[STUDENT SAYS / ASKS]:
{student_query}

Respond as Socrates: Guide the student's thought process with probing questions and conceptual insights grounded in NCERT science. Do NOT state which option letter is correct."""

    messages.append({"role": "user", "content": user_content})

    client = AsyncOpenAI(
        base_url=config.gemini_base_url,
        api_key=active_key,
    )

    try:
        stream = await client.chat.completions.create(
            model=active_model,
            messages=messages,
            stream=True,
            temperature=0.3,
        )

        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    except Exception as e:
        logger.error(f"Socratic streaming dialogue failed: {e}")
        yield f"An error occurred connecting to Socrates ({e}). What core scientific principle do you think connects the given terms in {chapter}?"


def generate_socrates_dialogue_sync(
    question_text: str,
    options: Union[List[str], Dict[str, str]],
    student_query: str,
    chat_history: Optional[List[Dict[str, str]]] = None,
    chapter: str = "Science",
    class_level: int = 10,
    explanation: str = "",
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    top_k: int = 4,
) -> str:
    """
    Synchronous Socratic dialogue generator for non-async UI callers or testing.
    """
    active_key = config.get_google_api_key(override=api_key)
    if not active_key:
        return "Please provide a valid Google Gemini API key in Settings (gear icon in the top right) to start your dialogue with Socrates."

    active_model = model or config.default_llm_model
    retrieval_query = f"NCERT Class {class_level} Science {chapter} {question_text} {student_query}"
    ncert_context = ""
    try:
        ncert_context = retrieve_ncert_context(
            retrieval_query, class_filter=class_level, top_k=top_k
        )
    except Exception as ret_err:
        logger.warning(f"Pinecone context retrieval failed ({ret_err}). Using fallback context.")
        ncert_context = f"[NCERT Class {class_level} Science — {chapter}]\nQuestion Context: {question_text}\nConcept: {explanation}"

    opts_str = ""
    if isinstance(options, dict):
        opts_str = "\n".join([f"- {k}: {v}" for k, v in options.items()])
    elif isinstance(options, list):
        opts_str = "\n".join([f"- {o}" for o in options])

    system_prompt = SOCRATES_QUIZ_SYSTEM_PROMPT.format(
        class_level=class_level,
        chapter=chapter,
    )

    messages = [{"role": "system", "content": system_prompt}]
    if chat_history:
        for msg in chat_history[-6:]:
            if msg.get("content"):
                messages.append({"role": msg["role"], "content": msg["content"]})

    user_content = f"""[NCERT TEXTBOOK EXCERPTS FOR CLASS {class_level} — {chapter}]:
{ncert_context}

[ACTIVE QUIZ QUESTION]:
Question: {question_text}
Options:
{opts_str}

[TEXTBOOK EXPLANATION BACKGROUND (INTERNAL TRUTH - DO NOT SPOIL)]:
{explanation}

[STUDENT SAYS / ASKS]:
{student_query}

Respond as Socrates: Guide the student's thought process with probing questions and conceptual insights grounded in NCERT science. Do NOT state which option letter is correct."""

    messages.append({"role": "user", "content": user_content})

    try:
        client = OpenAI(
            base_url=config.gemini_base_url,
            api_key=active_key,
        )
        response = client.chat.completions.create(
            model=active_model,
            messages=messages,
            temperature=0.3,
        )
        return (response.choices[0].message.content or "").strip()
    except Exception as e:
        logger.error(f"Socratic sync dialogue failed: {e}")
        return f"An error occurred during discourse ({e}). What core principle connects the terms in this question?"


def enrich_quiz_with_socrates(
    quiz_data: Dict[str, Any],
    api_key: Optional[str] = None,
    model: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Enriches each question in the quiz data with pre-calculated Socratic hints
    and Socratic scaffolding for instant zero-latency UI rendering.
    """
    if not quiz_data or "questions" not in quiz_data:
        return quiz_data

    chapter = quiz_data.get("chapter", "Science")
    class_level = int(quiz_data.get("class_level", 10))

    questions = quiz_data.get("questions", [])
    enriched_questions = []

    for q in questions:
        q_copy = dict(q)
        # If hints not already present, generate them
        if "socrates_hints" not in q_copy:
            q_text = q_copy.get("question", "")
            opts = q_copy.get("options", [])
            exp = q_copy.get("explanation", "")
            hints = generate_socrates_hints(
                question=q_text,
                options=opts,
                chapter=chapter,
                class_level=class_level,
                explanation=exp,
                api_key=api_key,
                model=model,
            )
            q_copy["socrates_hints"] = hints
        enriched_questions.append(q_copy)

    quiz_data["questions"] = enriched_questions
    quiz_data["socrates_enabled"] = True
    return quiz_data
