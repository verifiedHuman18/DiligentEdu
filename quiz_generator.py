#!/usr/bin/env python3
"""
NCERT Science Quiz Generation Engine (Phase 7)
Generates high-quality, grounded multiple-choice quizzes from NCERT textbooks in a single Gemini request.
"""

import os
import sys
import json
import logging
from typing import Dict, Any, List, Optional, Union, Tuple
from dotenv import load_dotenv
from openai import OpenAI
from pinecone import Pinecone
from langchain_huggingface import HuggingFaceEmbeddings

# Reconfigure stdout for UTF-8
sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()
logger = logging.getLogger(__name__)

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
MAPPING_FILE = os.path.join(PROJECT_ROOT, "data", "metadata", "ncert_mapping.json")
INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "ncert-science")
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
DEFAULT_MODEL = "gemini-3.5-flash-lite"

_cached_embeddings = None
_cached_pinecone_index = None
_cached_mapping = None


def load_ncert_mapping() -> Dict[str, Any]:
    """Load NCERT chapter mapping file with caching."""
    global _cached_mapping
    if _cached_mapping is not None:
        return _cached_mapping

    if os.path.exists(MAPPING_FILE):
        try:
            with open(MAPPING_FILE, "r", encoding="utf-8") as f:
                _cached_mapping = json.load(f)
                return _cached_mapping
        except Exception as e:
            logger.error(f"Error loading ncert_mapping.json: {e}")
    return {}


def get_embeddings():
    """Get or initialize cached HuggingFace embeddings."""
    global _cached_embeddings
    if _cached_embeddings is None:
        _cached_embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
    return _cached_embeddings


def get_pinecone_index():
    """Get or initialize cached Pinecone index."""
    global _cached_pinecone_index
    if _cached_pinecone_index is None:
        api_key = os.getenv("PINECONE_API_KEY")
        if not api_key:
            raise ValueError("PINECONE_API_KEY is not set.")
        pc = Pinecone(api_key=api_key)
        _cached_pinecone_index = pc.Index(INDEX_NAME)
    return _cached_pinecone_index


def resolve_chapter(class_level: int, chapter_identifier: Union[str, int]) -> Tuple[int, str]:
    """
    Resolves chapter name or number into (chapter_number, canonical_chapter_title).
    Handles integers, exact names, and fuzzy/partial string matches.
    """
    mapping = load_ncert_mapping()
    class_key = f"class{class_level}"
    class_map = mapping.get(class_key, {})

    if not class_map:
        raise ValueError(f"No mapping data found for Class {class_level}")

    # Case 1: Integer chapter number
    if isinstance(chapter_identifier, int) or (isinstance(chapter_identifier, str) and chapter_identifier.strip().isdigit()):
        target_num = int(chapter_identifier)
        for fname, info in class_map.items():
            if info.get("chapter_number") == target_num:
                return target_num, info.get("chapter")
        raise ValueError(f"Chapter number {target_num} not found in Class {class_level} NCERT Science.")

    # Case 2: String matching (clean prefix/title)
    clean_query = str(chapter_identifier).strip().lower()
    # Strip optional "Ch 11: " or "Chapter 11 - "
    if ":" in clean_query:
        clean_query = clean_query.split(":", 1)[1].strip()
    elif "-" in clean_query:
        clean_query = clean_query.split("-", 1)[1].strip()

    best_match = None
    for fname, info in class_map.items():
        ch_title = info.get("chapter", "")
        ch_title_lower = ch_title.lower()

        # Exact or substring match
        if clean_query == ch_title_lower or clean_query in ch_title_lower or ch_title_lower in clean_query:
            return info.get("chapter_number"), ch_title

    # Fallback to closest match if available
    for fname, info in class_map.items():
        ch_title = info.get("chapter", "")
        words = [w for w in clean_query.split() if len(w) > 3]
        if any(w in ch_title.lower() for w in words):
            return info.get("chapter_number"), ch_title

    raise ValueError(f"Could not resolve chapter '{chapter_identifier}' for Class {class_level}.")


def retrieve_chapter_context_for_quiz(
    class_level: int,
    chapter_number: int,
    chapter_title: str,
    top_k: int = 8,
) -> str:
    """
    Retrieves representative, rich NCERT textbook chunks across the chapter for quiz generation.
    """
    embeddings = get_embeddings()
    index = get_pinecone_index()

    # Query with chapter title and diverse core concepts
    query_text = f"NCERT Class {class_level} Science Chapter {chapter_number} {chapter_title} concepts, definitions, formulas, laws, experiments, and activities"
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
        # Fallback query without text vector if needed
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
    model: str = DEFAULT_MODEL,
) -> Dict[str, Any]:
    """
    Generates a complete, structured NCERT multiple-choice quiz in ONE Gemini API request.

    Args:
        class_level: Grade level (9 or 10)
        chapter: Chapter title string or chapter integer
        difficulty: 'easy', 'medium', or 'hard'
        num_questions: Number of MCQs to generate (default: 5)
        api_key: Optional Google Gemini API key (defaults to GOOGLE_API_KEY env var)
        model: Gemini model identifier (default: 'gemini-3.5-flash-lite')

    Returns:
        Structured dictionary containing quiz metadata and list of questions with options,
        correct answers, explanations, and exact source pages.
    """
    active_api_key = api_key or os.getenv("GOOGLE_API_KEY")
    if not active_api_key:
        raise ValueError("Google Gemini API key not provided and GOOGLE_API_KEY environment variable is not set.")

    # 1. Resolve chapter to canonical number and name
    ch_number, ch_title = resolve_chapter(class_level, chapter)
    logger.info(f"Generating Quiz: Class {class_level} | Ch {ch_number}: {ch_title} | Difficulty: {difficulty} | Qs: {num_questions}")

    # 2. Retrieve chapter context from Pinecone
    context = retrieve_chapter_context_for_quiz(
        class_level=class_level,
        chapter_number=ch_number,
        chapter_title=ch_title,
        top_k=8,
    )

    if not context or "No matching" in context:
        raise RuntimeError(f"Could not retrieve textbook context for Class {class_level} Chapter {ch_number}.")

    # 3. Create single OpenAI-compatible Gemini client
    client = OpenAI(
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        api_key=active_api_key,
    )

    system_prompt = f"""
You are an expert NCERT Science Exam Creator and Teacher.
Your task is to create a high-quality, concept-testing Multiple Choice Quiz (MCQ) for students based STRICTLY on the provided NCERT textbook excerpts.

GUIDELINES:
1. Generate EXACTLY {num_questions} questions covering key concepts, formulas, definitions, and experimental principles from the chapter.
2. Difficulty Level: '{difficulty.upper()}'.
   - Easy: Direct definitions, basic formulas, fundamental identification questions.
   - Medium: Conceptual understanding, formula applications, distinguishing features, multi-step reasoning.
   - Hard: Deep conceptual analysis, tricky numericals, experimental interpretation, assertion-reasoning style.
3. Grounding: All questions, correct answers, and distractors MUST be directly supported by the provided NCERT excerpts.
4. Each question MUST have exactly 4 options prefixed as 'A) ...', 'B) ...', 'C) ...', 'D) ...'.
5. 'correct_answer' MUST be a single letter string: 'A', 'B', 'C', or 'D'.
6. 'source_pages' MUST be a list of integer page numbers corresponding to the [PAGE: X] tags in the excerpts where the concept is taught.
7. 'explanation' MUST be a detailed, pedagogical explanation justifying why the correct answer is right and why other options are incorrect.

OUTPUT FORMAT (JSON OBJECT):
You MUST respond with a valid JSON object matching this exact JSON schema:
{{
  "class_level": {class_level},
  "chapter": "{ch_title}",
  "chapter_number": {ch_number},
  "difficulty": "{difficulty}",
  "total_questions": {num_questions},
  "questions": [
    {{
      "question": "Clear question text here?",
      "options": [
        "A) Option A text",
        "B) Option B text",
        "C) Option C text",
        "D) Option D text"
      ],
      "correct_answer": "B",
      "explanation": "Step-by-step reasoning explaining the correct answer referencing NCERT textbook concepts.",
      "difficulty": "{difficulty}",
      "chapter": "{ch_title}",
      "source_pages": [6]
    }}
  ]
}}
"""

    user_prompt = f"""
NCERT Textbook Excerpts (Class {class_level} Science — Chapter {ch_number}: {ch_title}):
{context}

Generate the complete {num_questions}-question '{difficulty}' quiz now as a valid JSON object.
"""

    # 4. ONE single Gemini API request
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.3,
        )
    except Exception as e:
        # Fallback to flash-lite-latest or 3-flash-preview if specific model string has temporary issue
        logger.warning(f"Primary model '{model}' failed ({e}). Retrying with fallback 'gemini-flash-lite-latest'...")
        response = client.chat.completions.create(
            model="gemini-flash-lite-latest",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.3,
        )

    raw_json_str = response.choices[0].message.content or "{}"

    # 5. Parse and Validate JSON
    try:
        quiz_data = json.loads(raw_json_str)
    except json.JSONDecodeError as err:
        logger.error(f"Failed to parse model response as JSON: {err}. Raw output:\n{raw_json_str}")
        raise ValueError(f"Model did not return valid JSON: {err}")

    # Ensure top-level fields
    quiz_data["class_level"] = int(class_level)
    quiz_data["chapter"] = ch_title
    quiz_data["chapter_number"] = ch_number
    quiz_data["difficulty"] = difficulty

    questions = quiz_data.get("questions", [])
    if not isinstance(questions, list) or len(questions) == 0:
        raise ValueError("Generated quiz has no valid questions list.")

    # Validate each question
    for idx, q in enumerate(questions, 1):
        if "question" not in q or not q["question"]:
            q["question"] = f"Question {idx}"

        options = q.get("options", [])
        if not isinstance(options, list) or len(options) != 4:
            raise ValueError(f"Question {idx} does not have exactly 4 options.")

        # Ensure correct answer is normalized to 'A', 'B', 'C', or 'D'
        ans = str(q.get("correct_answer", "A")).strip().upper()
        if len(ans) > 1 and ans.startswith(("A", "B", "C", "D")):
            ans = ans[0]
        if ans not in ["A", "B", "C", "D"]:
            ans = "A"
        q["correct_answer"] = ans

        if "explanation" not in q or not q["explanation"]:
            q["explanation"] = f"Refer to NCERT Class {class_level} Science Chapter '{ch_title}'."

        q["difficulty"] = difficulty
        q["chapter"] = ch_title

        # Validate source_pages
        sp = q.get("source_pages", [])
        if isinstance(sp, int):
            sp = [sp]
        elif not isinstance(sp, list):
            sp = []
        q["source_pages"] = [int(p) for p in sp if str(p).isdigit()]

    quiz_data["total_questions"] = len(questions)
    return quiz_data


def get_available_chapters(
    class_level: int,
    student_id: Optional[str] = None,
    db_path: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Returns available NCERT chapters for a grade level annotated with student's SWAT status.

    Args:
        class_level: Grade level (9 or 10)
        student_id: Optional student ID to look up previous performance
        db_path: Optional path to SQLite database

    Returns:
        List of chapter objects:
        [
            {
                "chapter_number": 1,
                "chapter": "Chemical Reactions and Equations",
                "status": "strong",
                "score": 84,
                "attempts": 2
            },
            ...
        ]
    """
    try:
        class_level_int = int(class_level)
    except (ValueError, TypeError):
        raise ValueError(f"Invalid class level: {class_level}. Must be 9 or 10.")

    if class_level_int not in [9, 10]:
        raise ValueError(f"Invalid class level: {class_level_int}. Supported class levels are 9 and 10.")

    mapping = load_ncert_mapping()
    class_key = f"class{class_level_int}"
    class_map = mapping.get(class_key, {})

    if not class_map:
        raise ValueError(f"No mapping data found for Class {class_level_int}")

    # Fetch student SWAT profile if student_id is provided
    swat_profile = {}
    if student_id:
        try:
            from swat_analyzer import get_student_swat
            swat_profile = get_student_swat(student_id, db_path=db_path)
        except Exception as e:
            logger.warning(f"Could not load SWAT profile for {student_id}: {e}")

    ch_breakdown = swat_profile.get("chapter_breakdown", {})

    available_chapters = []
    for fname, info in class_map.items():
        ch_num = int(info.get("chapter_number", 0))
        ch_title = info.get("chapter", "")

        # Check if student has attempted this chapter
        ch_data = ch_breakdown.get(ch_title)
        if ch_data:
            status = ch_data.get("category", "average")
            score = ch_data.get("score")
            attempts = ch_data.get("attempts", 0)
        else:
            status = "not_attempted"
            score = None
            attempts = 0

        available_chapters.append({
            "chapter_number": ch_num,
            "chapter": ch_title,
            "status": status,
            "score": score,
            "attempts": attempts,
            "filename": fname,
        })

    available_chapters.sort(key=lambda x: x["chapter_number"])
    return available_chapters


def create_student_quiz(
    student_id: str,
    class_level: int,
    chapter: Union[str, int],
    difficulty: str = "medium",
    num_questions: int = 5,
    api_key: Optional[str] = None,
    model: str = DEFAULT_MODEL,
) -> Dict[str, Any]:
    """
    Main entry point for Phase 11 Student-Directed Quiz Generation.
    Validates student inputs, allows completely free chapter and difficulty selection,
    and generates the full quiz in ONE single Gemini API request.

    Args:
        student_id: Unique student ID (e.g. "student_001")
        class_level: 9 or 10
        chapter: Chapter title string or chapter number int
        difficulty: 'easy', 'medium', or 'hard'
        num_questions: Number of questions (default: 5, valid: 1-20)
        api_key: Optional Gemini API key
        model: Model identifier (default: 'gemini-3.5-flash-lite')

    Returns:
        Structured Quiz dictionary matching the Phase 7/11 specification.
    """
    # 1. Validate student_id
    if not student_id or not str(student_id).strip():
        raise ValueError("student_id cannot be empty.")
    clean_student_id = str(student_id).strip()

    # 2. Validate class_level
    try:
        class_level_int = int(class_level)
    except (ValueError, TypeError):
        raise ValueError(f"Invalid class level: {class_level}. Must be 9 or 10.")
    if class_level_int not in [9, 10]:
        raise ValueError(f"Invalid class level: {class_level_int}. Supported class levels are 9 and 10.")

    # 3. Validate difficulty
    clean_diff = str(difficulty).strip().lower()
    if clean_diff not in ["easy", "medium", "hard"]:
        raise ValueError(f"Invalid difficulty: '{difficulty}'. Supported difficulties are 'easy', 'medium', or 'hard'.")

    # 4. Validate num_questions
    try:
        num_q_int = int(num_questions)
    except (ValueError, TypeError):
        raise ValueError(f"Invalid num_questions: {num_questions}. Must be an integer.")
    if not (1 <= num_q_int <= 20):
        raise ValueError(f"Invalid num_questions: {num_q_int}. Must be between 1 and 20.")

    # 5. Validate chapter existence in NCERT curriculum
    try:
        ch_num, ch_title = resolve_chapter(class_level_int, chapter)
    except Exception as e:
        raise ValueError(f"Invalid chapter '{chapter}' for Class {class_level_int}: {e}")

    logger.info(
        f"create_student_quiz: Student={clean_student_id} | Class={class_level_int} | "
        f"Ch={ch_num} ({ch_title}) | Diff={clean_diff} | Qs={num_q_int}"
    )

    # 6. Generate quiz in 1 single Gemini request
    quiz_data = generate_quiz(
        class_level=class_level_int,
        chapter=ch_title,
        difficulty=clean_diff,
        num_questions=num_q_int,
        api_key=api_key,
        model=model,
    )

    # Attach student metadata
    quiz_data["student_id"] = clean_student_id
    return quiz_data


if __name__ == "__main__":
    print("Testing Phase 11 Student Chapter Selection & Quiz Configuration...")
    try:
        chapters = get_available_chapters(class_level=10, student_id="student_001")
        print(f"Available Class 10 chapters ({len(chapters)}):")
        for ch in chapters[:4]:
            print(f"  Ch {ch['chapter_number']}: {ch['chapter']} -> Status: {ch['status']} (Score: {ch['score']})")

        print("\nTesting input validation...")
        try:
            create_student_quiz("student_001", 10, "InvalidChapterXYZ", "medium")
        except ValueError as ve:
            print(f"✓ Rejection test passed: {ve}")

        print("\n✅ Phase 11 components verified!")
    except Exception as e:
        print(f"❌ Error: {e}")
