import asyncio
from datetime import datetime
import os
import logging
import sys
import json
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
from openai import AsyncOpenAI
import streamlit as st
from pinecone import Pinecone
from quiz_generator import generate_quiz, get_available_chapters, create_student_quiz
from adaptive_engine import get_next_quiz_config
from quiz_storage import (
    record_quiz_attempt,
    get_student_history,
    get_student_chapter_summary,
    get_student_swat_metrics,
    clear_student_history,
    submit_and_grade_quiz,
)
from swat_analyzer import calculate_student_swat, format_swat_report
from teacher_engine import get_teacher_student_profile, get_student_status

# Configure logging
def setup_logging():
    """Setup logging configuration"""
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    if not os.path.exists("logs"):
        os.makedirs("logs")

    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.FileHandler(f'logs/app_{datetime.now().strftime("%Y%m%d")}.log', encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )

    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("langchain").setLevel(logging.WARNING)
    logging.getLogger("pinecone").setLevel(logging.WARNING)

    return logging.getLogger(__name__)


logger = setup_logging()

# User-friendly error messages
ERROR_MESSAGES = {
    "api_key_invalid": "❌ There seems to be an issue with your API key. Please check if it's correct and try again.",
    "connection_error": "🌐 Unable to connect to Pinecone vector store. Please check your internet connection and API keys.",
    "retrieval_error": "📚 I'm having trouble accessing the NCERT Science materials right now. Please try again in a moment.",
    "processing_error": "🤖 I encountered an issue while processing your request. Please try rephrasing your question.",
    "initialization_error": "⚙️ The assistant is having trouble starting up. Please refresh the page and try again.",
    "general_error": "😅 Something unexpected happened. Please try again, and if the problem persists, contact support.",
}

load_dotenv()

# Handle event loop for async operations
try:
    asyncio.get_running_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

# Environment variables
try:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
except (KeyError, FileNotFoundError, Exception):
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if GOOGLE_API_KEY:
    os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY

try:
    PINECONE_API_KEY = st.secrets["PINECONE_API_KEY"]
except (KeyError, FileNotFoundError, Exception):
    PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")

if PINECONE_API_KEY:
    os.environ["PINECONE_API_KEY"] = PINECONE_API_KEY

PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "ncert-science")
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# Disable OpenAI trace logging if key not present
try:
    OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
except (KeyError, FileNotFoundError, Exception):
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    os.environ["OPENAI_TRACING_ENABLED"] = "false"
    os.environ["OPENAI_API_KEY"] = "dummy-key"


def load_ncert_mapping() -> Dict[str, Any]:
    """Load NCERT chapter mapping file"""
    mapping_path = os.path.join("data", "metadata", "ncert_mapping.json")
    if os.path.exists(mapping_path):
        try:
            with open(mapping_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading ncert_mapping.json: {e}")
    return {}


NCERT_MAPPING = load_ncert_mapping()

# Streamlit Page Configuration
st.set_page_config(
    page_title="NCERT Science Academic Assistant",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling
st.markdown(
    """
<style>
.main-header {
    font-size: 2.4rem;
    color: #f6ad55;
    text-align: center;
    margin-bottom: 0.5rem;
    font-weight: 800;
    letter-spacing: -0.5px;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
}

.sub-header {
    font-size: 1.1rem;
    color: #cbd5e1;
    text-align: center;
    margin-bottom: 1.5rem;
}

.grade-badge {
    display: inline-block;
    padding: 0.25rem 0.75rem;
    border-radius: 9999px;
    font-weight: 600;
    font-size: 0.85rem;
    margin-right: 0.5rem;
}

.badge-class9 {
    background-color: #3b82f6;
    color: white;
}

.badge-class10 {
    background-color: #10b981;
    color: white;
}

.subject-badge {
    padding: 0.75rem;
    margin: 0.4rem 0;
    background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
    border-left: 4px solid #f6ad55;
    border-radius: 8px;
    border: 1px solid #334155;
    color: white;
    font-weight: 500;
    font-size: 0.9rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.15);
    transition: all 0.2s ease;
}

.subject-badge:hover {
    transform: translateX(3px);
    border-left: 4px solid #38bdf8;
}

.citation-card {
    background: rgba(30, 41, 59, 0.7);
    border: 1px solid #3b82f6;
    border-radius: 8px;
    padding: 0.75rem 1rem;
    margin-top: 0.75rem;
    color: #e2e8f0;
}

.prompt-chip {
    display: inline-block;
    background-color: #1e293b;
    border: 1px solid #475569;
    border-radius: 20px;
    padding: 6px 14px;
    margin: 4px;
    font-size: 0.85rem;
    color: #94a3b8;
    cursor: pointer;
    transition: all 0.2s;
}

.prompt-chip:hover {
    background-color: #334155;
    color: #f6ad55;
    border-color: #f6ad55;
}

.stTabs [data-baseweb="tab-list"] {
    gap: 0;
    justify-content: center !important;
    align-items: center !important;
    width: 100% !important;
    background-color: transparent !important;
}

.stTabs [data-baseweb="tab"] {
    flex: 1 !important;
    text-align: center !important;
    padding: 0.6rem 0.25rem !important;
    background-color: #1e293b !important;
    border: none !important;
    border-bottom: 3px solid #334155 !important;
    color: #94a3b8 !important;
    font-weight: 500 !important;
}

.stTabs [data-baseweb="tab"][aria-selected="true"] {
    background-color: #0f172a !important;
    border-bottom-color: #f6ad55 !important;
    color: #f6ad55 !important;
    font-weight: 600 !important;
}
</style>
""",
    unsafe_allow_html=True,
)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "selected_class" not in st.session_state:
    st.session_state.selected_class = "All Classes"
if "selected_chapter" not in st.session_state:
    st.session_state.selected_chapter = "All Chapters"


@st.cache_resource
def initialize_embeddings():
    """Initialize sentence-transformers embeddings (cached)"""
    try:
        logger.info(f"Initializing embeddings: {EMBEDDING_MODEL_NAME}")
        embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
        logger.info("Successfully initialized embeddings model")
        return embeddings
    except Exception as e:
        logger.error(f"Failed to initialize embeddings: {str(e)}")
        st.error(ERROR_MESSAGES["initialization_error"])
        return None


@st.cache_resource
def initialize_pinecone_index():
    """Initialize Pinecone index connection (cached)"""
    try:
        logger.info(f"Connecting to Pinecone index: {PINECONE_INDEX_NAME}")
        pc = Pinecone(api_key=PINECONE_API_KEY)
        index = pc.Index(PINECONE_INDEX_NAME)
        logger.info("Successfully connected to Pinecone index")
        return index
    except Exception as e:
        logger.error(f"Failed to connect to Pinecone: {str(e)}")
        st.error(ERROR_MESSAGES["connection_error"])
        return None


def retrieve_ncert_context(
    query: str,
    class_filter: Optional[int] = None,
    chapter_filter: Optional[int] = None,
    top_k: int = 4,
) -> str:
    """
    Retrieves relevant NCERT chunks from Pinecone with page & chapter metadata preserved.
    """
    try:
        embeddings = initialize_embeddings()
        index = initialize_pinecone_index()

        if not embeddings or not index:
            return "Unable to access NCERT vector store."

        # Build metadata filter
        filter_dict = {}
        if class_filter is not None:
            filter_dict["class"] = {"$eq": int(class_filter)}
        if chapter_filter is not None:
            filter_dict["chapter_number"] = {"$eq": int(chapter_filter)}

        query_vector = embeddings.embed_query(query)

        query_kwargs = {
            "vector": query_vector,
            "top_k": top_k,
            "include_metadata": True,
        }
        if filter_dict:
            query_kwargs["filter"] = filter_dict

        results = index.query(**query_kwargs)
        matches = results.get("matches", [])

        if not matches:
            return "No matching NCERT textbook content found for this query."

        formatted_chunks = []
        for match in matches:
            meta = match.get("metadata", {})
            cls_num = int(meta.get("class", 0))
            ch_num = int(meta.get("chapter_number", 0))
            ch_name = meta.get("chapter", "Science")
            page_num = int(meta.get("page", 0))
            text = meta.get("text", "").strip()

            chunk_header = f"[SOURCE: NCERT Class {cls_num} Science | CHAPTER {ch_num}: {ch_name} | PAGE: {page_num}]"
            formatted_chunks.append(f"{chunk_header}\n{text}")

        return "\n\n---\n\n".join(formatted_chunks)

    except Exception as e:
        logger.error(f"Error during context retrieval: {str(e)}")
        return f"Error retrieving NCERT context: {str(e)}"


async def stream_ncert_rag_response(
    query: str,
    class_filter: Optional[int],
    api_key: str,
    model_name: str = "gemini-3.5-flash-lite",
    chat_history: Optional[List[Dict[str, str]]] = None,
):
    """
    Direct NCERT RAG streaming engine (Zero tool-calling / function-calling overhead).
    1. Retrieves top NCERT chunks from Pinecone filtered by Class level.
    2. Directly invokes Gemini 3.5 Flash-Lite in a single streaming request.
    3. Streams response token-by-token with grounded textbook explanations & exact page citations.
    """
    # 1. Retrieve NCERT Context
    context = retrieve_ncert_context(query, class_filter=class_filter, top_k=5)

    # 2. Build System Prompt & Grounding Instructions
    system_prompt = """You are an Expert NCERT Academic Science Tutor for Class 9 and Class 10 secondary school students.
Your mission is to explain scientific concepts clearly, accurately, and patiently using ONLY the provided official NCERT Science textbook excerpts.

INSTRUCTIONS:
1. Explain the scientific concept step-by-step with clear reasoning, definitions, and helpful examples.
2. If mathematical formulas or chemical equations are involved, write them clearly using Markdown/LaTeX (e.g., $V = IR$, $F = ma$, or $2H_2 + O_2 \\rightarrow 2H_2O$).
3. Ground your explanations directly in the provided NCERT textbook context.
4. OUT-OF-SYLLABUS HANDLING: If the provided NCERT context does not contain relevant information to answer the question (or the topic is outside the Class 9 & Class 10 NCERT Science curriculum), politely state that this topic is not covered in the NCERT Class 9/10 Science syllabus, and do NOT hallucinate facts or false citations.
5. ALWAYS conclude your answer with an explicit, polished citation block in the following exact format:

### 📚 NCERT Textbook Citations
- **Source:** NCERT Class [9 or 10] Science
- **Chapter:** Chapter [Number] — [Chapter Title]
- **Page(s):** Page [Page Number(s)]
- **Key Reference:** "[Key quote or definition from the textbook]"
"""

    messages = [{"role": "system", "content": system_prompt}]

    if chat_history:
        for msg in chat_history[-4:]:
            if msg.get("content"):
                messages.append({"role": msg["role"], "content": msg["content"]})

    user_content = f"""NCERT TEXTBOOK EXCERPTS:
{context}

STUDENT QUESTION:
{query}

Please provide a thorough, pedagogically structured explanation with step-by-step reasoning followed by the exact NCERT citation:"""

    messages.append({"role": "user", "content": user_content})

    client = AsyncOpenAI(
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        api_key=api_key,
    )

    response_stream = await client.chat.completions.create(
        model=model_name,
        messages=messages,
        stream=True,
        temperature=0.2,
    )

    async for chunk in response_stream:
        if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content


def handle_sidebar():
    """Handle sidebar configuration, syllabus view, and grade selection"""
    with st.sidebar:
        st.markdown("### 🔬 NCERT Science Tutor")
        tab1, tab2, tab3 = st.tabs(["⚙️ Settings", "📚 Syllabus", "📊 Info"])

        # Configuration Tab
        with tab1:
            st.markdown("#### 🔑 Authentication")
            api_key = st.text_input(
                "Google Gemini API Key",
                type="password",
                placeholder="AIzaSy...",
                value=st.session_state.get("api_key", GOOGLE_API_KEY or ""),
                help="Your key is kept securely in your current browser session.",
            )
            if api_key:
                st.session_state.api_key = api_key
                os.environ["GOOGLE_API_KEY"] = api_key
            else:
                st.info("💡 Enter your Google Gemini API key to begin.")

            st.markdown("#### 👤 Student Profile")
            student_id = st.text_input(
                "Student ID",
                value=st.session_state.get("student_id", "student_001"),
                help="Unique ID used to track your quiz performance and SWAT analytics.",
            )
            st.session_state.student_id = student_id

            st.markdown("#### 🎓 Student Grade & Focus")
            grade_options = ["All Classes", "Class 9", "Class 10"]
            current_grade_idx = grade_options.index(st.session_state.selected_class) if st.session_state.selected_class in grade_options else 0
            selected_class = st.selectbox(
                "Select Grade / Class",
                grade_options,
                index=current_grade_idx,
                help="Filters retrieval to Class 9 or Class 10 NCERT Science",
            )
            if selected_class != st.session_state.selected_class:
                st.session_state.selected_class = selected_class
                st.session_state.agent_initialized = False

            # Chapter selection filter (optional)
            chapter_options = ["All Chapters"]
            if selected_class == "Class 9" and "class9" in NCERT_MAPPING:
                for fname, info in sorted(NCERT_MAPPING["class9"].items(), key=lambda x: x[1].get("chapter_number", 0)):
                    chapter_options.append(f"Ch {info['chapter_number']}: {info['chapter']}")
            elif selected_class == "Class 10" and "class10" in NCERT_MAPPING:
                for fname, info in sorted(NCERT_MAPPING["class10"].items(), key=lambda x: x[1].get("chapter_number", 0)):
                    chapter_options.append(f"Ch {info['chapter_number']}: {info['chapter']}")

            selected_chapter = st.selectbox("Focus Chapter (Optional)", chapter_options)
            st.session_state.selected_chapter = selected_chapter

            st.divider()

            st.markdown("#### 🤖 LLM Model")
            model_options = [
                "gemini-3.5-flash-lite",
                "gemini-flash-lite-latest",
                "gemini-3-flash-preview",
                "gemini-3.6-flash",
                "gemini-3.7-flash",
                "gemini-2.5-pro",
            ]
            selected_model = st.selectbox(
                "Gemini Model",
                model_options,
                index=0,
                help="Choose Google Gemini model for answering and reasoning (gemini-3.5-flash-lite recommended for high quota)",
            )
            st.session_state.model = selected_model

            if "previous_model" not in st.session_state:
                st.session_state.previous_model = selected_model
            elif st.session_state.previous_model != selected_model:
                st.session_state.agent_initialized = False
                st.session_state.previous_model = selected_model

        # Syllabus Tab
        with tab2:
            st.markdown("#### 📖 NCERT Science Curriculum")
            
            with st.expander("📘 Class 9 Science (13 Chapters)", expanded=(selected_class == "Class 9")):
                if "class9" in NCERT_MAPPING:
                    for fname, info in sorted(NCERT_MAPPING["class9"].items(), key=lambda x: x[1].get("chapter_number", 0)):
                        st.markdown(f"**Ch {info['chapter_number']}:** {info['chapter']}")
                else:
                    st.info("Class 9 mapping loaded.")

            with st.expander("📗 Class 10 Science (13 Chapters)", expanded=(selected_class == "Class 10")):
                if "class10" in NCERT_MAPPING:
                    for fname, info in sorted(NCERT_MAPPING["class10"].items(), key=lambda x: x[1].get("chapter_number", 0)):
                        st.markdown(f"**Ch {info['chapter_number']}:** {info['chapter']}")
                else:
                    st.info("Class 10 mapping loaded.")

        # Info Tab
        with tab3:
            msg_count = len(st.session_state.messages)
            st.metric("Questions Asked", msg_count // 2 if msg_count > 0 else 0)
            st.info(f"**Active Model:**\n{selected_model}")
            st.info(f"**Vector Store:**\nPinecone (`{PINECONE_INDEX_NAME}`)\n`sentence-transformers` 384-dim")

            if msg_count > 0:
                st.divider()
                chat_text = ""
                for msg in st.session_state.messages:
                    role = "Student" if msg["role"] == "user" else "NCERT Assistant"
                    chat_text += f"{role}:\n{msg['content']}\n\n"

                st.download_button(
                    "📥 Export Conversation",
                    chat_text,
                    f"ncert_chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    "text/plain",
                    use_container_width=True,
                )

            if st.button("🗑️ Clear Chat", use_container_width=True):
                st.session_state.messages = []
                st.rerun()

    return selected_model, st.session_state.get("api_key"), selected_class, st.session_state.get("student_id", "student_001")


async def main():
    """Main application loop"""
    streaming_speed = 0.03
    try:
        # App Title & Header
        st.markdown('<h1 class="main-header">🔬 NCERT Academic Science Assistant</h1>', unsafe_allow_html=True)
        st.markdown(
            '<p class="sub-header">Interactive Agentic RAG Tutor for <b>Class 9</b> & <b>Class 10</b> NCERT Science with Exact Page Citations</p>',
            unsafe_allow_html=True,
        )

        selected_model, user_api_key, selected_class, student_id = handle_sidebar()

        # Main App Navigation Tabs
        tab_chat, tab_quiz, tab_history, tab_teacher = st.tabs(["💬 NCERT Q&A Tutor", "📝 Practice Quiz", "📊 Student SWAT", "👨‍🏫 Teacher Dashboard"])

        with tab_chat:
            # Grade banner
            if selected_class == "Class 9":
                st.info("🎯 **Active Mode:** Focused on **NCERT Class 9 Science** (Exploration)")
            elif selected_class == "Class 10":
                st.info("🎯 **Active Mode:** Focused on **NCERT Class 10 Science**")
            else:
                st.info("🌐 **Active Mode:** Comprehensive (Searching across Class 9 & Class 10)")

            # Quick Starter Prompts
            st.markdown("##### 💡 Suggested Questions to Explore:")
            prompt_cols = st.columns(4)
            quick_prompts = [
                ("⚡ What is Ohm's Law and resistance?", "What is Ohm's law and how is resistance calculated?"),
                ("🧬 Cell Organelles & Plasma Membrane", "What are the main cell organelles and function of the plasma membrane in Class 9 Science?"),
                ("🧪 Carbon Covalent Bonding", "Why does carbon form covalent bonds and what is catenation?"),
                ("🌈 Why is the sky blue?", "Why does the sky appear blue and what causes atmospheric refraction?"),
            ]
            
            for i, (label, p_text) in enumerate(quick_prompts):
                if prompt_cols[i].button(label, use_container_width=True, key=f"qp_{i}"):
                    st.session_state.active_prompt = p_text

            # Display chat history
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

            if not user_api_key:
                st.warning("👈 Please enter your Google Gemini API key in the sidebar to start asking questions.")
                return

            # Handle user prompt from input or quick prompt button
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
                        with st.spinner("🔍 Searching NCERT Science textbooks and synthesizing answer..."):
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
                                    error_msg = "I was unable to retrieve a complete answer. Please try rephrasing your question."
                                    message_placeholder.error(error_msg)
                                    full_response = error_msg

                            except Exception as e:
                                logger.error(f"Error processing response: {str(e)}")
                                full_response = f"I encountered an error retrieving or generating the answer: {str(e)}"
                                message_placeholder.error(full_response)

                        st.session_state.messages.append({"role": "assistant", "content": full_response})
                        st.rerun()

        with tab_quiz:
            st.markdown("### 📝 NCERT Science Practice Quiz")
            st.caption("Generate grounded, multiple-choice quizzes with instant grading, textbook explanations, and exact page citations in **1 single Gemini request**.")

            q_col1, q_col2, q_col3, q_col4 = st.columns([1.2, 2.4, 1.1, 1.1])

            with q_col1:
                quiz_grade = st.selectbox("Grade", ["Class 10", "Class 9"], key="quiz_grade_sel")
                quiz_cls_int = 10 if quiz_grade == "Class 10" else 9

            with q_col2:
                # Fetch available chapters with SWAT annotations
                available_chs = get_available_chapters(quiz_cls_int, student_id=student_id)
                ch_display_map = {}
                ch_labels = []
                for ch in available_chs:
                    icon = "🟢" if ch["status"] == "strong" else ("🟡" if ch["status"] == "average" else ("🔴" if ch["status"] == "weak" else "⚪"))
                    badge = f" ({ch['score']}%)" if ch["score"] is not None else " (New)"
                    label = f"{icon} Ch {ch['chapter_number']}: {ch['chapter']}{badge}"
                    ch_display_map[label] = ch["chapter"]
                    ch_labels.append(label)

                selected_ch_label = st.selectbox("Chapter (Freely Choose Any)", ch_labels, key="quiz_ch_sel")
                selected_ch_title = ch_display_map.get(selected_ch_label, available_chs[0]["chapter"] if available_chs else "Electricity")

            with q_col3:
                quiz_diff = st.selectbox("Difficulty", ["medium", "easy", "hard"], key="quiz_diff_sel")

            with q_col4:
                quiz_count = st.selectbox("Questions", [5, 3, 7, 10], index=0, key="quiz_count_sel")

            if st.button("⚡ Generate NCERT Quiz", type="primary", use_container_width=True):
                if not user_api_key:
                    st.warning("👈 Please enter your Google Gemini API key in the sidebar.")
                else:
                    with st.spinner(f"Generating {quiz_count}-question {quiz_diff} quiz for {selected_ch_title} from NCERT in 1 request..."):
                        try:
                            generated = create_student_quiz(
                                student_id=student_id,
                                class_level=quiz_cls_int,
                                chapter=selected_ch_title,
                                difficulty=quiz_diff,
                                num_questions=quiz_count,
                                api_key=user_api_key,
                                model=selected_model,
                            )
                            st.session_state.current_quiz = generated
                            st.session_state.quiz_submitted = False
                            st.session_state.quiz_user_answers = {}
                            st.rerun()
                        except Exception as e:
                            st.error(f"Quiz generation error: {e}")

            # Render active quiz if available
            curr_quiz = st.session_state.get("current_quiz")
            if curr_quiz and "questions" in curr_quiz:
                st.divider()
                st.markdown(f"#### 📖 Quiz: Class {curr_quiz.get('class_level')} Science — {curr_quiz.get('chapter')}")
                st.caption(f"Difficulty: **{curr_quiz.get('difficulty', '').upper()}** | Total Questions: **{curr_quiz.get('total_questions', len(curr_quiz['questions']))}** | Student: `{student_id}`")

                user_answers = st.session_state.get("quiz_user_answers", {})
                is_submitted = st.session_state.get("quiz_submitted", False)

                for idx, q_data in enumerate(curr_quiz["questions"], 1):
                    st.markdown(f"**Q{idx}. {q_data['question']}**")
                    options = q_data.get("options", [])

                    choice_key = f"q_choice_{idx}"
                    current_val = user_answers.get(choice_key, None)

                    if not is_submitted:
                        selected_opt = st.radio(
                            f"Options for Q{idx}:",
                            options,
                            key=choice_key,
                            index=options.index(current_val) if current_val in options else None,
                            label_visibility="collapsed",
                        )
                        user_answers[choice_key] = selected_opt
                    else:
                        user_ans_text = user_answers.get(choice_key)
                        correct_key = q_data.get("correct_answer", "A").upper()

                        correct_opt_text = next((o for o in options if o.startswith(f"{correct_key})") or o.startswith(f"{correct_key}.")), options[0] if options else "")

                        is_correct = user_ans_text and user_ans_text.startswith(f"{correct_key}")
                        if is_correct:
                            st.success(f"✅ **Your Answer:** {user_ans_text}")
                        else:
                            st.error(f"❌ **Your Answer:** {user_ans_text or 'No answer selected'}  \n**Correct Answer:** {correct_opt_text}")

                        with st.expander(f"💡 Explanation & NCERT Citations (Q{idx})", expanded=True):
                            st.markdown(f"**Explanation:** {q_data.get('explanation', 'Refer to NCERT textbook.')}")
                            sp = q_data.get("source_pages", [])
                            sp_str = ", ".join(str(p) for p in sp) if sp else "Referenced in Chapter"
                            st.markdown(f"📚 **NCERT Citation:** Class {curr_quiz.get('class_level')} Science | *{curr_quiz.get('chapter')}* | **Page(s): {sp_str}**")

                    st.write("")

                st.session_state.quiz_user_answers = user_answers

                if not is_submitted:
                    if st.button("📊 Submit Quiz", type="primary", use_container_width=True):
                        try:
                            sub_result = submit_and_grade_quiz(
                                student_id=student_id,
                                quiz_data=curr_quiz,
                                user_answers=user_answers,
                            )
                            st.session_state.last_submission_result = sub_result
                        except Exception as e:
                            logger.error(f"Failed to submit and grade quiz: {e}")
                            st.error(f"Submission error: {e}")

                        st.session_state.quiz_submitted = True
                        st.rerun()
                else:
                    sub_res = st.session_state.get("last_submission_result", {})
                    correct_count = sub_res.get("score", 0)
                    total_q = sub_res.get("total", len(curr_quiz["questions"]))
                    pct = sub_res.get("percentage", 0)

                    st.divider()

                    score_col1, score_col2 = st.columns([2.5, 1])
                    with score_col1:
                        if pct >= 70:
                            st.success(f"🎉 **Outstanding Job!** Score: **{correct_count}/{total_q}** ({pct}%)")
                        elif pct >= 50:
                            st.info(f"👍 **Good Effort!** Score: **{correct_count}/{total_q}** ({pct}%)")
                        else:
                            st.warning(f"📖 **Needs Review:** Score: **{correct_count}/{total_q}** ({pct}%) — Review the cited pages above!")

                        # Render Automatic SWAT Update Banner
                        if sub_res:
                            stat_icon = "🟢" if sub_res.get("new_status") == "strong" else ("🟡" if sub_res.get("new_status") == "average" else "🔴")
                            if sub_res.get("status_changed"):
                                st.success(f"🔄 **SWAT Updated!** {sub_res.get('status_change_summary')} {stat_icon}")
                            else:
                                st.info(f"📊 **SWAT Chapter Score:** {sub_res.get('chapter')} average is **{sub_res.get('new_chapter_score')}%** ({sub_res.get('new_status', '').upper()} {stat_icon})")

                    with score_col2:
                        if st.button("🔄 Take Another Quiz", type="primary", use_container_width=True):
                            st.session_state.current_quiz = None
                            st.session_state.quiz_submitted = False
                            st.session_state.quiz_user_answers = {}
                            st.session_state.last_submission_result = None
                            st.rerun()

        with tab_history:
            st.markdown(f"### 📊 Student SWAT Analysis (`{student_id}`)")
            st.caption("Descriptive chapter-wise performance analysis. Identifies your strengths, average areas, and weaknesses so you can decide your own study focus.")

            swat = calculate_student_swat(student_id)
            history = get_student_history(student_id, include_questions=True)

            if not swat.get("has_data"):
                st.info("ℹ️ No quiz attempts recorded yet for this student ID. Complete a quiz in the **📝 Practice Quiz** tab to view your performance data.")
            else:
                # Top metrics
                m_col1, m_col2, m_col3, m_col4 = st.columns(4)
                m_col1.metric("Overall Average", f"{swat['overall_average']:.1f}%")
                m_col2.metric("Questions Attempted", swat["questions_attempted"])
                m_col3.metric("Questions Correct", swat["questions_correct"])
                m_col4.metric("Quizzes Completed", swat["total_quizzes"])

                st.divider()

                # Key Highlights: Highest, Lowest, Trend
                h_col1, h_col2, h_col3 = st.columns(3)
                with h_col1:
                    high = swat.get("highest_performing_chapter")
                    if high:
                        st.success(f"🏆 **Top Chapter:** {high['chapter']} (**{high['accuracy']:.0f}%**)")
                with h_col2:
                    low = swat.get("lowest_performing_chapter")
                    if low:
                        st.warning(f"🔍 **Needs Focus:** {low['chapter']} (**{low['accuracy']:.0f}%**)")
                with h_col3:
                    trend = swat.get("recent_trend", {})
                    st.info(f"📈 **Recent Trend ({trend.get('direction', '—')}):** {trend.get('summary', 'Steady')}")

                st.divider()

                # SWAT Categorization
                st.markdown("#### 🎯 Chapter-Wise SWAT Breakdown")
                st.caption("🟢 **STRONG** (≥ 70%) | 🟡 **AVERAGE** (50%–69%) | 🔴 **WEAK** (< 50%)")

                c_col1, c_col2, c_col3 = st.columns(3)

                with c_col1:
                    st.markdown("##### 🟢 STRONG")
                    strong_items = swat["categories"]["strong"]
                    if strong_items:
                        for item in strong_items:
                            st.success(f"**{item['chapter']}**  \nAccuracy: **{item['accuracy']:.0f}%** ({item['questions_correct']}/{item['questions_attempted']} Qs in {item['quizzes_taken']} quiz{'zes' if item['quizzes_taken'] > 1 else ''})")
                    else:
                        st.caption("No chapters currently in Strong.")

                with c_col2:
                    st.markdown("##### 🟡 AVERAGE")
                    avg_items = swat["categories"]["average"]
                    if avg_items:
                        for item in avg_items:
                            st.info(f"**{item['chapter']}**  \nAccuracy: **{item['accuracy']:.0f}%** ({item['questions_correct']}/{item['questions_attempted']} Qs in {item['quizzes_taken']} quiz{'zes' if item['quizzes_taken'] > 1 else ''})")
                    else:
                        st.caption("No chapters currently in Average.")

                with c_col3:
                    st.markdown("##### 🔴 WEAK")
                    weak_items = swat["categories"]["weak"]
                    if weak_items:
                        for item in weak_items:
                            st.warning(f"**{item['chapter']}**  \nAccuracy: **{item['accuracy']:.0f}%** ({item['questions_correct']}/{item['questions_attempted']} Qs in {item['quizzes_taken']} quiz{'zes' if item['quizzes_taken'] > 1 else ''})")
                    else:
                        st.caption("No weak chapters identified!")

                st.divider()

                # Chapter Progression Summary
                st.markdown("#### 📈 Chapter Progression Summary")
                ch_summary = get_student_chapter_summary(student_id)
                for ch_name, attempts in ch_summary.items():
                    with st.expander(f"📚 {ch_name} ({len(attempts)} attempt{'s' if len(attempts) > 1 else ''})", expanded=False):
                        for a in attempts:
                            pct_color = "🟢" if a["percentage"] >= 70 else ("🟡" if a["percentage"] >= 50 else "🔴")
                            st.markdown(
                                f"{pct_color} **Quiz {a['quiz_num']}** ({a['difficulty'].capitalize()}) — "
                                f"**{a['percentage']:.0f}%** ({a['score']}/{a['total_questions']})  \n"
                                f"🕒 *{a['timestamp'][:19].replace('T', ' ')} UTC*"
                            )

                st.divider()

                # Full Detailed Timeline
                st.markdown("#### 🕒 Detailed Quiz History Timeline")
                for att in reversed(history):
                    with st.expander(f"🗓️ {att['timestamp'][:19].replace('T', ' ')} | Class {att['class_level']} — {att['chapter']} | {att['percentage']:.0f}% ({att['score']}/{att['total_questions']})", expanded=False):
                        st.markdown(f"**Quiz ID:** `{att['quiz_id']}` | **Difficulty:** `{att['difficulty'].upper()}`")
                        if "questions" in att and att["questions"]:
                            for q_idx, q_rec in enumerate(att["questions"], 1):
                                q_icon = "✅" if q_rec["is_correct"] else "❌"
                                st.markdown(f"{q_icon} **Q{q_idx}:** {q_rec['question_text']}")
                                st.caption(f"Your answer: `{q_rec['user_answer']}` | Correct: `{q_rec['correct_answer']}`")

                if st.button("🗑️ Clear My Quiz History", type="secondary"):
                    clear_student_history(student_id)
                    st.rerun()

        with tab_teacher:
            st.markdown(f"### 👨‍🏫 Teacher Analytics & Early-Warning Dashboard")
            st.caption(f"Detailed pedagogical analysis and transparent early-warning diagnostic indicators for **`{student_id}`**.")

            prof = get_teacher_student_profile(student_id)

            if not prof.get("has_data"):
                st.info(f"ℹ️ No quiz data found for student `{student_id}`. Quizzes taken by the student will populate this dashboard.")
            else:
                st_overview = prof["overview"]
                st_status = prof["status"]
                st_chapters = prof["chapter_statistics"]
                st_history = prof["quiz_history"]
                st_swat = prof["swat_summary"]

                # 1. Early-Warning Status Alert Banner (Phase 14)
                status_icon = st_status["status_icon"]
                status_title = st_status["overall_status"]
                status_code = st_status["status_code"]

                if status_code == "performing_well":
                    st.success(f"### {status_icon} Overall Standing: **{status_title}** (Overall Average: {st_overview['overall_average']}%)")
                elif status_code in ["improving", "improving_low_base"]:
                    st.info(f"### {status_icon} Overall Standing: **{status_title}** (Upward Trajectory: {st_status['trend']['earlier_average']}% ➔ {st_status['trend']['recent_average']}%)")
                elif status_code == "monitor":
                    st.warning(f"### {status_icon} Overall Standing: **{status_title}** (Overall Average: {st_overview['overall_average']}%)")
                else:
                    st.error(f"### {status_icon} Overall Standing: **{status_title}** (Overall Average: {st_overview['overall_average']}%)")

                # Display Active Alerts / Positive Notes
                if st_status.get("alerts"):
                    for alert in st_status["alerts"]:
                        st.warning(alert["message"])

                if st_status.get("positive_notes"):
                    for note in st_status["positive_notes"]:
                        st.success(note)

                st.divider()

                # 2. Key Student Overview Metrics (Phase 13.1)
                st.markdown("#### 📈 Student Lifetime Metrics")
                t_m1, t_m2, t_m3, t_m4, t_m5 = st.columns(5)
                t_m1.metric("Class Level", f"Class {st_overview['class']}")
                t_m2.metric("Overall Average", f"{st_overview['overall_average']}%")
                t_m3.metric("Quizzes Completed", st_overview["total_quizzes"])
                t_m4.metric("Questions Attempted", f"{st_overview['questions_attempted']} (✓ {st_overview['questions_correct']})")
                t_m5.metric("Accuracy", f"{st_overview['accuracy']}%")

                st.divider()

                # 3. Chapter Performance Breakdown (Phase 13.2)
                st.markdown("#### 📚 Chapter-Wise Performance Statistics")
                if st_chapters:
                    ch_table_rows = []
                    for c in st_chapters:
                        icon = "🟢" if c["status"] == "strong" else ("🟡" if c["status"] == "average" else "🔴")
                        ch_table_rows.append({
                            "Chapter": f"{icon} {c['chapter']}",
                            "Average Score": f"{c['average']}%",
                            "Accuracy": f"{c['accuracy']}%",
                            "Attempts": c["attempts"],
                            "Questions (Corr/Att)": f"{c['questions_correct']}/{c['questions_attempted']}",
                            "SWAT Category": c["status"].upper(),
                        })
                    st.table(ch_table_rows)

                st.divider()

                # 4. Strength / Weakness Summary (Phase 13.4)
                st.markdown("#### 🎯 Teacher SWAT Diagnostic")
                ts_col1, ts_col2, ts_col3 = st.columns(3)
                with ts_col1:
                    st.markdown("##### 🟢 Strengths (≥ 70%)")
                    if st_swat.get("strengths"):
                        for s in st_swat["strengths"]:
                            st.success(f"**{s['chapter']}** ({s['score']}%)")
                    else:
                        st.caption("None yet.")

                with ts_col2:
                    st.markdown("##### 🟡 Average Topics (50%–69%)")
                    if st_swat.get("average_topics"):
                        for a in st_swat["average_topics"]:
                            st.info(f"**{a['chapter']}** ({a['score']}%)")
                    else:
                        st.caption("None.")

                with ts_col3:
                    st.markdown("##### 🔴 Weak Topics (< 50%)")
                    if st_swat.get("weak_topics"):
                        for w in st_swat["weak_topics"]:
                            st.error(f"**{w['chapter']}** ({w['score']}%)")
                    else:
                        st.caption("None.")

                st.divider()

                # 5. Chronological Quiz Log (Phase 13.3)
                st.markdown("#### 🕒 Chronological Quiz History Log")
                if st_history:
                    hist_display = []
                    for row in reversed(st_history):
                        hist_display.append({
                            "Date": row["date"],
                            "Chapter": row["chapter"],
                            "Difficulty": row["difficulty"],
                            "Score": row["score_display"],
                            "Questions": f"{row['score']}/{row['total_questions']}",
                            "Timestamp (UTC)": row["timestamp"][:19].replace("T", " "),
                        })
                    st.dataframe(hist_display, use_container_width=True)

    except Exception as e:
        logger.error(f"Critical error in main: {str(e)}")
        st.error(ERROR_MESSAGES["general_error"])


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Application error: {str(e)}")
