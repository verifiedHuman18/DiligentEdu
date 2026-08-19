import asyncio
from datetime import datetime
import os
import logging
import sys
import json
from typing import Optional, Dict, Any, List
from agents import (
    Agent,
    OpenAIChatCompletionsModel,
    RunResultStreaming,
    Runner,
    SQLiteSession,
    function_tool,
)
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_google_genai.llms import GoogleGenerativeAI
from langchain_core.output_parsers import StrOutputParser
from openai import AsyncOpenAI
from openai.types.responses import ResponseTextDeltaEvent
import streamlit as st
from pinecone import Pinecone

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
if "agent_initialized" not in st.session_state:
    st.session_state.agent_initialized = False
if "session_name" not in st.session_state:
    st.session_state.session_name = SQLiteSession("ncert_academic_memory")
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


def create_function_tools(model_name: str):
    """Create RAG function tools for the agent"""
    logger.info(f"Creating NCERT Science function tools for model: {model_name}")
    llm = GoogleGenerativeAI(model=model_name)

    prompt_template = PromptTemplate.from_template(
        """
You are an expert NCERT Academic Science Tutor helping a secondary school student (Grade 9-10).
You have access to verified excerpts from the official NCERT Science textbooks.

NCERT Textbook Context:
{context}

Student Question: {question}

Instructions:
1. Explain the scientific concept step-by-step with clear reasoning, definitions, and helpful examples.
2. If mathematical formulas or chemical equations are involved, write them clearly using Markdown/LaTeX (e.g., $V = IR$, $F = ma$, or $2H_2 + O_2 \\rightarrow 2H_2O$).
3. Ground your explanations directly in the provided NCERT textbook context.
4. OUT-OF-SYLLABUS HANDLING: If the provided NCERT context does not contain relevant information to answer the question (or the topic is outside the Class 9 & Class 10 NCERT Science curriculum, such as advanced college physics, corporate finance, or non-school topics), politely state that this topic is not covered in the NCERT Class 9/10 Science syllabus, and do NOT hallucinate facts or false citations.
5. If the context contains specific textbook activities, examples, or solved problems, reference them appropriately.
6. When NCERT textbook content is used, ALWAYS conclude your answer with an explicit, polished citation block in the following exact format:

### 📚 NCERT Textbook Citations
- **Source:** NCERT Class [9 or 10] Science
- **Chapter:** Chapter [Number] — [Chapter Title]
- **Page(s):** Page [Page Number(s)]
- **Key Reference:** "[Key quote or definition from the textbook]"

Provide a thorough, pedagogically supportive response:
"""
    )

    parser = StrOutputParser()

    @function_tool
    def answer_from_class9_science(query: str) -> str:
        """
        Retrieval tool for NCERT Class 9 Science textbook.
        Use for Class 9 topics: Cells, Tissues, Motion, Forces, Work/Energy, Atoms, Sound, Diversity, Earth as a system.
        """
        try:
            logger.info(f"Class 9 query received: {query[:80]}...")
            context = retrieve_ncert_context(query, class_filter=9, top_k=4)

            chain = prompt_template | llm | parser
            result = chain.invoke({
                "context": context,
                "question": query,
            })
            return result
        except Exception as e:
            logger.error(f"Error in Class 9 tool: {str(e)}")
            return f"I encountered an error retrieving Class 9 Science materials: {str(e)}"

    @function_tool
    def answer_from_class10_science(query: str) -> str:
        """
        Retrieval tool for NCERT Class 10 Science textbook.
        Use for Class 10 topics: Chemical Reactions, Acids/Bases, Metals, Carbon, Life Processes, Control/Coordination, Reproduction, Heredity, Light, Eye, Electricity, Magnetic Effects, Environment.
        """
        try:
            logger.info(f"Class 10 query received: {query[:80]}...")
            context = retrieve_ncert_context(query, class_filter=10, top_k=4)

            chain = prompt_template | llm | parser
            result = chain.invoke({
                "context": context,
                "question": query,
            })
            return result
        except Exception as e:
            logger.error(f"Error in Class 10 tool: {str(e)}")
            return f"I encountered an error retrieving Class 10 Science materials: {str(e)}"

    @function_tool
    def search_all_ncert_science(query: str) -> str:
        """
        Search across both Class 9 and Class 10 NCERT Science textbooks when comparing concepts across grades or grade is unspecified.
        """
        try:
            logger.info(f"Cross-grade query received: {query[:80]}...")
            context = retrieve_ncert_context(query, class_filter=None, top_k=5)

            chain = prompt_template | llm | parser
            result = chain.invoke({
                "context": context,
                "question": query,
            })
            return result
        except Exception as e:
            logger.error(f"Error in cross-grade search: {str(e)}")
            return f"I encountered an error retrieving NCERT Science materials: {str(e)}"

    return [
        answer_from_class9_science,
        answer_from_class10_science,
        search_all_ncert_science,
    ]


def agent_initialization(model_name: str, _api_key: str, selected_class_pref: str = "All Classes") -> Optional[Agent]:
    """Initialize Agent with Gemini model and NCERT Science tools"""
    try:
        logger.info(f"Initializing NCERT Science Agent with model: {model_name}")

        if not _api_key or len(_api_key) < 20:
            st.error(ERROR_MESSAGES["api_key_invalid"])
            return None

        external_client = AsyncOpenAI(
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            api_key=_api_key,
        )

        model = OpenAIChatCompletionsModel(
            model=model_name,
            openai_client=external_client,
        )

        tools = create_function_tools(model_name)

        instructions = f"""
You are an Expert NCERT Academic Science Tutor for Class 9 and Class 10 students.
Your role is to guide students through concepts, definitions, formulas, numericals, and experiments
using the official NCERT Science textbook content provided by the retrieval tools.

STUDENT PROFILE & CONTEXT:
- Active Grade Filter: {selected_class_pref}

TOOLS AVAILABLE:
1. `answer_from_class9_science(query)`:
   - For Class 9 topics: Cells, Tissues, Motion, Forces, Work/Energy, Atoms, Sound, Diversity, Biogeochemical cycles.
2. `answer_from_class10_science(query)`:
   - For Class 10 topics: Chemical Reactions, Acids/Bases/Salts, Metals/Non-metals, Carbon Compounds, Life Processes,
     Nervous system/Hormones, Reproduction, Heredity, Light/Optics, Human Eye, Electricity, Electromagnetism, Environment.
3. `search_all_ncert_science(query)`:
   - For general science queries or when comparing concepts across both grades.

WORKFLOW RULES:
1. Formulate an enriched, academically precise query based on the student's question.
2. If the student has selected Class 9 or Class 10 specifically, prioritize calling the corresponding tool!
3. If no specific class is chosen, inspect the topic and call the most relevant grade tool.
4. OUT-OF-SYLLABUS HANDLING: If a query is unrelated to school science or outside the Class 9 and 10 NCERT syllabus, politely explain that the topic is not covered in NCERT Class 9/10 Science, and do not make up fake citations.
5. Provide clear, supportive, and structured explanations with examples.
6. Preserve and highlight textbook page citations in every final answer.
"""

        agent = Agent(
            name="NCERT Academic Science Assistant",
            instructions=instructions,
            tools=tools,
            model=model,
        )

        logger.info("Successfully initialized NCERT Science Agent")
        return agent
    except Exception as e:
        logger.error(f"Failed to initialize agent: {str(e)}")
        st.error(ERROR_MESSAGES["initialization_error"])
        return None


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

            st.divider()

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

    return selected_model, st.session_state.get("api_key"), selected_class


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

        selected_model, user_api_key, selected_class = handle_sidebar()

        # Grade banner
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
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
            if prompt_cols[i].button(label, use_container_width=True):
                st.session_state.active_prompt = p_text

        # Display chat history
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        if not user_api_key:
            st.warning("👈 Please enter your Google Gemini API key in the sidebar to start asking questions.")
            return

        # Initialize Agent
        if not st.session_state.agent_initialized:
            with st.spinner("Initializing NCERT Science Tutor & Vector Store..."):
                agent = agent_initialization(selected_model, user_api_key, selected_class)
                if agent:
                    st.session_state.agent = agent
                    st.session_state.agent_initialized = True
                else:
                    st.error("Failed to initialize the assistant. Please check your API key.")
                    return

        # Handle user prompt from input or quick prompt button
        prompt_input = st.chat_input("Ask any question from NCERT Class 9 or 10 Science...")
        prompt = prompt_input or st.session_state.pop("active_prompt", None)

        if prompt:
            clean_prompt = prompt.strip()
            if len(clean_prompt) < 2:
                return

            logger.info(f"User query: {clean_prompt}")

            # Append user message
            st.session_state.messages.append({"role": "user", "content": clean_prompt})
            with st.chat_message("user"):
                st.markdown(clean_prompt)

            # Assistant response container
            with st.chat_message("assistant"):
                with st.spinner("🔍 Searching NCERT Science textbooks and synthesizing answer..."):
                    message_placeholder = st.empty()
                    full_response = ""

                    try:
                        agent = st.session_state.agent
                        result: RunResultStreaming = Runner.run_streamed(
                            agent, clean_prompt, session=st.session_state.session_name
                        )

                        async for event in result.stream_events():
                            if event.type == "raw_response_event" and isinstance(
                                event.data, ResponseTextDeltaEvent
                            ):
                                if hasattr(event.data, "delta") and event.data.delta:
                                    full_response += event.data.delta
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
                        full_response = ERROR_MESSAGES["processing_error"]
                        message_placeholder.error(full_response)

                st.session_state.messages.append({"role": "assistant", "content": full_response})
                st.rerun()

    except Exception as e:
        logger.error(f"Critical error in main: {str(e)}")
        st.error(ERROR_MESSAGES["general_error"])


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Application error: {str(e)}")
