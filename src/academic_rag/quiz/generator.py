"""Quiz Generation Engine. Generates grounded MCQ practice quizzes in 1 single Gemini request."""

import json
import logging
from typing import Any, Dict, List, Optional, Union

from src.academic_rag.ai.client_factory import execute_chat_completion
from src.academic_rag.config import config
from src.academic_rag.curriculum.service import curriculum_service
from src.academic_rag.exceptions import (
    QuizGenerationError,
)
from src.academic_rag.rag.prompts import QUIZ_GENERATOR_SYSTEM_PROMPT_TEMPLATE
from src.academic_rag.rag.retriever import get_embeddings, get_pinecone_index

logger = logging.getLogger(__name__)


def retrieve_chapter_context_for_quiz(
    class_level: int,
    chapter_number: int,
    chapter_title: str,
    top_k: int = 8,
    pinecone_api_key: Optional[str] = None,
    api_key: Optional[str] = None,
) -> str:
    """Retrieves representative NCERT textbook chunks across the chapter."""
    embeddings = get_embeddings()
    effective_pinecone_key = pinecone_api_key or (
        api_key if api_key and not api_key.startswith("AIza") else None
    )
    index = get_pinecone_index(api_key=effective_pinecone_key)

    query_text = (
        f"NCERT Class {class_level} Science Chapter {chapter_number} {chapter_title} "
        f"concepts, definitions, formulas, laws, experiments, and activities"
    )
    query_vector = embeddings.embed_query(query_text)

    filter_dict = {
        "class": {"$eq": int(class_level)},
        "chapter_number": {"$eq": int(chapter_number)},
    }

    results = index.query(
        vector=query_vector,
        top_k=top_k,
        include_metadata=True,
        filter=filter_dict,
    )

    matches = results.get("matches", [])
    if not matches:
        results = index.query(
            vector=[0.0] * 384,
            top_k=top_k,
            include_metadata=True,
            filter=filter_dict,
        )
        matches = results.get("matches", [])

    formatted_chunks = []
    for match in matches:
        meta = match.get("metadata", {})
        cls_num = int(meta.get("class", class_level))
        ch_num = int(meta.get("chapter_number", chapter_number))
        ch_name = meta.get("chapter", chapter_title)
        page_num = int(meta.get("page", 0))
        text = meta.get("text", "").strip()

        chunk_header = f"[SOURCE: NCERT Class {cls_num} Science | CHAPTER {ch_num}: {ch_name} | PAGE: {page_num}]"
        formatted_chunks.append(f"{chunk_header}\n{text}")

    return "\n\n---\n\n".join(formatted_chunks)


def generate_quiz(
    class_level: int = 10,
    chapter: Union[str, int] = "Electricity",
    difficulty: str = "medium",
    num_questions: int = 5,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    model_name: Optional[str] = None,
    pinecone_api_key: Optional[str] = None,
    **kwargs: Any,
) -> Dict[str, Any]:
    """Generates structured MCQ practice quiz in 1 single Gemini API request."""
    active_model = model or model_name or config.default_llm_model

    # 1. Resolve chapter
    ch_number, ch_title = curriculum_service.resolve_chapter(class_level, chapter)
    logger.info(
        f"Generating Quiz: Class {class_level} | Ch {ch_number}: {ch_title} | "
        f"Difficulty: {difficulty} | Qs: {num_questions}"
    )

    # 2. Retrieve chapter context from Pinecone
    context = retrieve_chapter_context_for_quiz(
        class_level=class_level,
        chapter_number=ch_number,
        chapter_title=ch_title,
        top_k=8,
        pinecone_api_key=pinecone_api_key,
    )

    if not context or "No matching" in context:
        raise QuizGenerationError(
            f"Could not retrieve textbook context for Class {class_level} Chapter {ch_number} ({ch_title})."
        )

    system_prompt = QUIZ_GENERATOR_SYSTEM_PROMPT_TEMPLATE.format(
        num_questions=num_questions,
        difficulty_upper=difficulty.upper(),
        class_level=class_level,
        ch_title=ch_title,
        ch_number=ch_number,
        difficulty=difficulty,
    )

    user_prompt = f"""
NCERT Textbook Excerpts (Class {class_level} Science — Chapter {ch_number}: {ch_title}):
{context}

Generate the complete {num_questions}-question '{difficulty}' quiz now as a valid JSON object.
"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    try:
        response = execute_chat_completion(
            messages=messages,
            model=active_model,
            response_format={"type": "json_object"},
            temperature=0.3,
            override_api_key=api_key,
        )
    except Exception as e:
        logger.warning(
            f"Primary model '{active_model}' failed ({e}). Retrying with fallback model '{config.fallback_llm_model}'..."
        )
        try:
            response = execute_chat_completion(
                messages=messages,
                model=config.fallback_llm_model,
                response_format={"type": "json_object"},
                temperature=0.3,
                override_api_key=api_key,
            )
        except Exception as retry_err:
            raise QuizGenerationError(f"Gemini quiz generation failed: {retry_err}") from retry_err

    raw_json_str = response.choices[0].message.content or "{}"

    try:
        quiz_dict = json.loads(raw_json_str)
    except json.JSONDecodeError as err:
        logger.error(f"Failed to parse quiz response as JSON: {err}. Raw output:\n{raw_json_str}")
        raise QuizGenerationError(f"Model did not return valid JSON: {err}")

    quiz_dict["class_level"] = int(class_level)
    quiz_dict["chapter"] = ch_title
    quiz_dict["chapter_number"] = ch_number
    quiz_dict["difficulty"] = difficulty

    raw_questions = quiz_dict.get("questions", [])
    if not isinstance(raw_questions, list) or len(raw_questions) == 0:
        raise QuizGenerationError("Generated quiz has no valid questions list.")

    # Extract any available page numbers from retrieved chapter context as fallback
    import re

    context_pages = [int(n) for n in re.findall(r"PAGE:\s*(\d+)", context)]
    default_pages = sorted(list(set(context_pages))) if context_pages else []

    validated_questions: List[Dict[str, Any]] = []
    for idx, q in enumerate(raw_questions, 1):
        q_text = str(q.get("question") or f"Question {idx}").strip()
        options = q.get("options", [])
        if not isinstance(options, list) or len(options) != 4:
            raise QuizGenerationError(f"Question {idx} does not have exactly 4 options.")

        ans = str(q.get("correct_answer", "A")).strip().upper()
        if len(ans) > 1 and ans.startswith(("A", "B", "C", "D")):
            ans = ans[0]
        if ans not in ["A", "B", "C", "D"]:
            ans = "A"

        explanation = str(
            q.get("explanation")
            or f"Refer to NCERT Class {class_level} Science Chapter '{ch_title}'."
        ).strip()

        # Robust source page parsing across int, list, string, and explanation mentions
        raw_sp = None
        for k in ["source_pages", "source_page", "pages", "page", "citation_pages", "page_numbers"]:
            if k in q and q[k] is not None and q[k] != "":
                raw_sp = q[k]
                break

        found_pages: List[int] = []
        if isinstance(raw_sp, (int, float)):
            found_pages.append(int(raw_sp))
        elif isinstance(raw_sp, str):
            nums = [int(n) for n in re.findall(r"\b\d+\b", raw_sp)]
            found_pages.extend(nums)
        elif isinstance(raw_sp, list):
            for item in raw_sp:
                if isinstance(item, (int, float)):
                    found_pages.append(int(item))
                elif isinstance(item, str):
                    nums = [int(n) for n in re.findall(r"\b\d+\b", item)]
                    found_pages.extend(nums)
                elif isinstance(item, dict):
                    p_val = item.get("page") or item.get("number")
                    if p_val and str(p_val).isdigit():
                        found_pages.append(int(p_val))

        if not found_pages:
            exp_nums = [
                int(n)
                for n in re.findall(
                    r"(?:\[PAGE:\s*|page\s+|pages\s+|p\.\s*)(\d+)", explanation, re.IGNORECASE
                )
            ]
            if exp_nums:
                found_pages.extend(exp_nums)

        valid_pages = [p for p in found_pages if 1 <= p <= 600]
        if valid_pages:
            seen_p = set()
            source_pages = [p for p in valid_pages if not (p in seen_p or seen_p.add(p))]
        else:
            source_pages = default_pages[:2] if default_pages else []

        validated_questions.append(
            {
                "question": q_text,
                "options": options,
                "correct_answer": ans,
                "explanation": explanation,
                "difficulty": difficulty,
                "chapter": ch_title,
                "source_pages": source_pages,
            }
        )

    quiz_dict["questions"] = validated_questions
    quiz_dict["total_questions"] = len(validated_questions)
    return quiz_dict


def create_student_quiz(
    student_id: str,
    class_level: int,
    chapter: Union[str, int],
    difficulty: str = "medium",
    num_questions: int = 5,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    model_name: Optional[str] = None,
    pinecone_api_key: Optional[str] = None,
    **kwargs: Any,
) -> Dict[str, Any]:
    """Validates student inputs, allows free choice, and generates quiz."""
    if not student_id or not str(student_id).strip():
        raise ValueError("student_id cannot be empty.")
    clean_student_id = str(student_id).strip()

    try:
        class_level_int = int(class_level)
    except (ValueError, TypeError):
        raise ValueError(f"Invalid class level: {class_level}. Must be 9 or 10.")
    if class_level_int not in [9, 10]:
        raise ValueError(
            f"Invalid class level: {class_level_int}. Supported class levels are 9 and 10."
        )

    clean_diff = str(difficulty).strip().lower()
    if clean_diff not in ["easy", "medium", "hard"]:
        raise ValueError(
            f"Invalid difficulty: '{difficulty}'. Supported difficulties are 'easy', 'medium', or 'hard'."
        )

    try:
        num_q_int = int(num_questions)
    except (ValueError, TypeError):
        raise ValueError(f"Invalid num_questions: {num_questions}. Must be an integer.")
    if not (1 <= num_q_int <= 20):
        raise ValueError(f"Invalid num_questions: {num_q_int}. Must be between 1 and 20.")

    ch_num, ch_title = curriculum_service.resolve_chapter(class_level_int, chapter)

    chosen_model = model or model_name
    quiz_data = generate_quiz(
        class_level=class_level_int,
        chapter=ch_title,
        difficulty=clean_diff,
        num_questions=num_q_int,
        api_key=api_key,
        model=chosen_model,
        pinecone_api_key=pinecone_api_key,
        **kwargs,
    )
    quiz_data["student_id"] = clean_student_id
    return quiz_data
