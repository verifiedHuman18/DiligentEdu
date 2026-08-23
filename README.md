# DiligentEdu

> **Intelligent NCERT Academic Science RAG Assistant, Socratic AI Tutor, Adaptive Diagnostic System & National Scholarship Discovery Platform**

![Python](https://img.shields.io/badge/python-v3.12+-blue.svg)
![Streamlit](https://img.shields.io/badge/streamlit-v1.49+-red.svg)
![LangChain](https://img.shields.io/badge/langchain-v0.3+-green.svg)
![Google Gemini](https://img.shields.io/badge/google%20gemini-2.5%20%2F%202.0%20%2F%201.5-orange.svg)
![Pinecone](https://img.shields.io/badge/vector%20store-pinecone-blueviolet.svg)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)
[![Ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

---

## Overview

**DiligentEdu** is an enterprise-grade, multi-role academic learning platform and intelligent tutoring system designed for Indian secondary education. Built specifically around the authoritative **NCERT Class 9 and Class 10 Science curriculum**, DiligentEdu combines advanced Retrieval-Augmented Generation (RAG), Socratic pedagogical guidance, continuous diagnostic assessment, early-warning analytics for educators, and a centralized government scholarship discovery engine.

Whether a student needs step-by-step conceptual guidance on *Chemical Reactions and Equations*, an educator needs real-time mastery analytics to identify at-risk learners, or a family is searching for eligible National Scholarship schemes, DiligentEdu provides an integrated, curriculum-grounded solution.

---

## Key Features

### 🎓 1. NCERT Science RAG Assistant & Textbook Integration
- **Curriculum-Grounded Retrieval**: Powered by Pinecone vector storage with strict class-level isolation (`class9`, `class10`) across all 25 NCERT Science chapters.
- **Page-Level Verifiable Citations**: Every explanation includes direct chapter and page citations from the official NCERT textbooks.
- **Built-in Textbook PDF Viewer**: Seamlessly view authoritative textbook PDFs directly within the application via static streaming.
- **Real-Time Streaming**: Low-latency token streaming with dynamic visual indicators and responsive formatting.

### 🧠 2. Intelligent Socratic & Exploratory Tutor
- **Dual Tutoring Modes**: Choose between *Exploratory Mode* (broad conceptual explanations) and *Socrates Mode* (guided inquiry prompting the student to deduce answers).
- **Dynamic Suggested Questions**: Context-aware suggested prompts tailored specifically to the selected class and chapter.
- **Mathematical & Chemical Precision**: Full LaTeX formula rendering and structured tables for reactions, equations, and physics laws.

### 📝 3. Adaptive Quiz & Diagnostic Engine
- **Bloom's Taxonomy Progression**: Dynamic quiz generation scaling from foundational recall to conceptual understanding and analytical application.
- **Interactive Socrates Quiz Mode**: Step-by-step question breakdown offering progressive hints without prematurely revealing solutions.
- **Instant Automated Grading**: Real-time evaluation, point breakdown, and detailed explanations for every option.

### 📊 4. Student SWAT Performance Analysis
- **SWAT Diagnostics**: Automated assessment of **S**trengths (≥75%), **W**eaknesses (<50%), **A**ptitude (50–74%), and **T**argets (unattempted chapters).
- **Mastery Heatmaps & Radar Charts**: Visual score distributions tracking curriculum mastery over time.
- **Prescriptive Action Plans**: Tailored recommendations and targeted revision pathways generated from individual quiz performance.

### 👩‍🏫 5. Educator / Teacher Early-Warning Dashboard
- **Cohort-Wide Monitoring**: Class-level performance metrics, completion rates, and average score distributions.
- **Early-Warning Alerts**: Immediate flagging of students requiring academic intervention or falling behind in core chapters.
- **Customizable Action Plans**: Review, modify, or override AI-generated student action plans with custom educator remarks.

### 🏛️ 6. National Scholarship Portal (NSP) Discovery Hub
- **Curated Scholarship Catalog**: Comprehensive database of central and state schemes (Pre-Matric, PM-YASASVI, NMMS, Disabilities, Minorities).
- **Multi-Factor Eligibility Matchmaker**: Instant scheme matching based on class, gender, social category, annual family income, and disability status.
- **AI Scholarship Assistant**: Interactive Q&A engine answering questions about application timelines, document checklists, and eligibility criteria with official portal links.

### 🔐 7. Dual-Key Resilient AI Architecture
- **Primary + Fallback Resolution**: Seamless fallback from primary environment/secrets keys to user-provided session keys.
- **Zero Disk Leakage**: Session API keys are retained exclusively in volatile memory and never persisted to disk or logs.
- **Intelligent Error Categorization**: Automated recovery and clear guidance for authentication errors (HTTP 401/403), quota limits (HTTP 429), and service disruptions (HTTP 500/503).

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                             STREAMLIT UI LAYER                              │
│   ┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐   │
│   │ Student Space │ │ Socratic Quiz │ │ SWAT Analysis │ │ Teacher Radar │   │
│   └───────┬───────┘ └───────┬───────┘ └───────┬───────┘ └───────┬───────┘   │
│           │                 │                 │                 │           │
│   ┌───────┴───────┐ ┌───────┴───────┐ ┌───────┴───────┐ ┌───────┴───────┐   │
│   │ Chapter Hub   │ │ PDF Reader    │ │ Scholarships  │ │ Settings/Keys │   │
│   └───────┬───────┘ └───────┬───────┘ └───────┬───────┘ └───────┬───────┘   │
└───────────┼─────────────────┼─────────────────┼─────────────────┼───────────┘
            ▼                 ▼                 ▼                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                   UNIFIED BACKEND FACADE (backend.py)                       │
│  Central single-source-of-truth API orchestrating all subsystem operations   │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
            ┌──────────────────────────┼──────────────────────────┐
            ▼                          ▼                          ▼
┌───────────────────────┐  ┌───────────────────────┐  ┌───────────────────────┐
│     RAG / TUTOR       │  │    DIAGNOSTICS &      │  │     SCHOLARSHIPS      │
│      SUBSYSTEM        │  │       ANALYTICS       │  │       SUBSYSTEM       │
│                       │  │                       │  │                       │
│ • NCERT RAG Engine    │  │ • Adaptive Generator  │  │ • Eligibility Engine  │
│ • Prompt Orchestrator │  │ • Socrates Evaluator  │  │ • Scheme Searcher     │
│ • Suggested Prompts   │  │ • SWAT Diagnostic     │  │ • Scholarship QA Bot  │
│ • PDF Page Resolver   │  │ • Teacher Action Plan │  │ • NSP Scraper/Parser  │
└───────────┬───────────┘  └───────────┬───────────┘  └───────────┬───────────┘
            │                          │                          │
            ▼                          ▼                          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            AI & DATA LAYER                                  │
│  ┌──────────────────────┐ ┌──────────────────────┐ ┌─────────────────────┐  │
│  │ Google Gemini Models │ │ HuggingFace MiniLM   │ │ Pinecone Vector DB  │  │
│  │ (2.5 Pro/Flash/Lite) │ │ Embeddings (384-dim) │ │ (class9 / class10)  │  │
│  └──────────────────────┘ └──────────────────────┘ └─────────────────────┘  │
│  ┌──────────────────────┐ ┌──────────────────────┐ ┌─────────────────────┐  │
│  │ SQLite Database      │ │ Static NCERT PDFs    │ │ Scholarship Catalog │  │
│  │ (quiz_history.db)    │ │ (/static/class{9,10})│ │ (sources.json)      │  │
│  └──────────────────────┘ └──────────────────────┘ └─────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Supported NCERT Curriculum

<details>
<summary><strong>Class 9 Science (12 Chapters)</strong></summary>

1. **Chapter 1**: Matter in Our Surroundings
2. **Chapter 2**: Is Matter Around Us Pure
3. **Chapter 3**: Atoms and Molecules
4. **Chapter 4**: Structure of the Atom
5. **Chapter 5**: The Fundamental Unit of Life
6. **Chapter 6**: Tissues
7. **Chapter 7**: Motion
8. **Chapter 8**: Force and Laws of Motion
9. **Chapter 9**: Gravitation
10. **Chapter 10**: Work and Energy
11. **Chapter 11**: Sound
12. **Chapter 12**: Improvement in Food Resources
</details>

<details>
<summary><strong>Class 10 Science (13 Chapters)</strong></summary>

1. **Chapter 1**: Chemical Reactions and Equations
2. **Chapter 2**: Acids, Bases and Salts
3. **Chapter 3**: Metals and Non-metals
4. **Chapter 4**: Carbon and its Compounds
5. **Chapter 5**: Life Processes
6. **Chapter 6**: Control and Coordination
7. **Chapter 7**: How do Organisms Reproduce?
8. **Chapter 8**: Heredity
9. **Chapter 9**: Light – Reflection and Refraction
10. **Chapter 10**: The Human Eye and the Colourful World
11. **Chapter 11**: Electricity
12. **Chapter 12**: Magnetic Effects of Electric Current
13. **Chapter 13**: Our Environment
</details>

---

## Tech Stack

| Component | Technology / Library | Description |
| :--- | :--- | :--- |
| **Frontend UI** | Streamlit, Custom Dark CSS | Responsive multi-role user interface |
| **Backend Facade** | Python 3.12+ | Unified synchronous/asynchronous data layer |
| **AI / LLM Integration** | Google Gemini (via OpenAI Agents SDK) | High-speed reasoning, tutoring, and quiz generation |
| **Embeddings** | HuggingFace `sentence-transformers/all-MiniLM-L6-v2` | Dense 384-dimensional vector embeddings |
| **Vector Database** | Pinecone | Managed vector store partitioned by grade namespaces |
| **Relational Storage** | SQLite (`quiz_history.db`) | Student profiles, attempt histories, and action plans |
| **Package Manager** | `uv` / `pip` | Fast dependency resolution and environment management |
| **Code Quality** | Ruff, Pre-Commit | Strict linting, formatting, and type adherence |

---

## Quick Start

### 1. Prerequisites
- **Python 3.12** or higher
- **Google Gemini API Key** ([Google AI Studio](https://aistudio.google.com/app/apikey))
- **Pinecone API Key** ([Pinecone Console](https://app.pinecone.io/)) with an index named `ncert-science`

### 2. Clone the Repository
```bash
git clone https://github.com/verifiedHuman18/DiligentEdu.git
cd DiligentEdu
```

### 3. Install Dependencies

Using **`uv`** (recommended):
```bash
uv sync --group dev
```

Or using standard **`pip`**:
```bash
pip install -r requirements.txt
```

### 4. Set Up Pre-Commit Git Hooks
To enable automated linting and formatting on every commit:
```bash
# 1-step automated setup
bash scripts/setup_hooks.sh

# Or via uv pre-commit
uv run pre-commit install
```

### 5. Configure Environment Variables
Create a `.env` file in the root directory (or `.streamlit/secrets.toml`):

```bash
cp .env.example .env
```

Edit `.env` with your API credentials:
```env
GOOGLE_API_KEY=your_google_gemini_api_key_here
PINECONE_API_KEY=your_pinecone_api_key_here
```

### 6. Run the Application
```bash
streamlit run app.py
```

Open your browser and navigate to: **`http://localhost:8501`**

---

## Configuration Reference

### Environment Variables

| Variable | Required | Default | Description |
| :--- | :---: | :--- | :--- |
| `GOOGLE_API_KEY` | Optional* | None | Primary Google Gemini API key (*can also be entered in UI) |
| `PINECONE_API_KEY` | Yes | None | Pinecone vector database API key |
| `PINECONE_INDEX_NAME`| No | `ncert-science` | Target Pinecone vector index name |

### Supported Gemini Models

| Model Identifier | Capabilities & Use Case |
| :--- | :--- |
| `gemini-2.5-flash` | **Default / Recommended**: Ultra-fast responses and high accuracy |
| `gemini-2.5-pro` | Advanced reasoning for complex multi-step physics and chemistry proofs |
| `gemini-2.5-flash-lite` | Lightweight and cost-efficient for rapid query resolution |
| `gemini-2.0-flash` | High throughput baseline model |
| `gemini-1.5-pro` | High context window model for large document analysis |
| `gemini-1.5-flash` | Fast baseline model |

---

## Docker Deployment

Build and run DiligentEdu inside an isolated Docker container:

```bash
# 1. Build the Docker image
docker build -t diligentedu .

# 2. Run container with environment configuration
docker run -p 8501:8501 --env-file .env diligentedu
```

Access the containerized instance at `http://localhost:8501`.

---

## Project Structure

```
DiligentEdu/
├── app.py                              # Main Streamlit application entry point
├── backend.py                          # Unified backend facade (single source of truth)
├── adaptive_engine.py                  # Adaptive quiz backward-compatibility module
├── quiz_generator.py                   # Quiz generation backward-compatibility module
├── quiz_storage.py                     # Quiz storage backward-compatibility module
├── swat_analyzer.py                    # SWAT analytics backward-compatibility module
├── teacher_engine.py                   # Teacher analytics backward-compatibility module
│
├── frontend/                           # Streamlit UI & Presentation Layer
│   ├── assets/                         # UI illustrations and hero images
│   ├── components/                     # Reusable UI widgets (navbar, sidebar, cards, etc.)
│   ├── screens/                        # Role-specific screens (home, tutor, quiz, teacher, etc.)
│   ├── state.py                        # Unified session state management
│   └── styles.py                       # Custom themes and CSS styling system
│
├── src/academic_rag/                   # Core Business Logic & Algorithms
│   ├── ai/                             # Centralized Gemini client factory & dual-key management
│   ├── analytics/                      # SWAT diagnostic engine & teacher action plans
│   ├── curriculum/                     # NCERT Class 9 & 10 curriculum service & PDF resolvers
│   ├── models/                         # Domain data dataclasses (quiz, curriculum, analytics)
│   ├── quiz/                           # Socrates tutor, quiz generator, and evaluators
│   ├── rag/                            # Pinecone retriever, prompts, and streaming engine
│   ├── scholarships/                   # NSP scraper, eligibility matchmaker, and QA engine
│   ├── storage/                        # SQLite connection manager and repositories
│   ├── config.py                       # Centralized application path and settings config
│   └── exceptions.py                   # Domain-specific exception hierarchy
│
├── scholarships/                       # Scholarship dataset and sources metadata
│   └── sources.json                    # Canonical government scholarship guidelines and portals
│
├── data/                               # Local storage and mapping metadata
│   ├── metadata/                       # NCERT curriculum chapter JSON mappings
│   └── storage/                        # SQLite databases (quiz_history.db)
│
├── static/                             # Authoritative NCERT textbook PDFs
│   ├── class9/                         # Class 9 science textbook PDFs
│   └── class10/                        # Class 10 science textbook PDFs
│
├── scripts/                            # Maintenance, benchmark, and ingestion scripts
│   ├── ingest_corpus.py                # NCERT PDF chunking and vector index ingestion
│   ├── retrieval_benchmark.py          # Vector search accuracy and latency benchmark
│   └── setup_hooks.sh                  # One-step pre-commit hook setup
│
├── tests/                              # Comprehensive Unit & Integration Test Suite (203+ tests)
├── .githooks/                          # Version-controlled Git pre-commit hooks
├── .github/workflows/                  # GitHub Actions CI/CD workflows (lint & quality)
├── requirements.txt                    # Python runtime dependencies
├── pyproject.toml                      # Project metadata, Ruff & Pyright configurations
├── DockerFile                          # Containerization build specification
└── LICENSE                             # GNU General Public License v3.0
```

---

## Testing & Quality Assurance

DiligentEdu maintains an automated test suite comprising **203+ unit and integration tests** covering class isolation, RAG retriever integrity, Socrates evaluation, SWAT analytics, teacher customization, and scholarship match accuracy.

### Running the Test Suite
```bash
# Run all tests using unittest
uv run python -m unittest discover -s tests

# Or with verbose output
uv run python -m unittest discover -s tests -v
```

### Running Code Quality Checks
```bash
# Run Ruff lint checks
uv run ruff check .

# Run Ruff formatting checks
uv run ruff format --check .

# Auto-format all code
uv run ruff format .
```

---

## Contributing

Contributions are welcome! To contribute:

1. **Fork the repository** on GitHub.
2. **Create a descriptive feature branch**:
   ```bash
   git checkout -b feature/interactive-concept-map
   ```
3. **Set up local development hooks**:
   ```bash
   bash scripts/setup_hooks.sh
   ```
4. **Make your changes** with thorough docstrings and unit tests.
5. **Ensure all linters and tests pass**:
   ```bash
   uv run ruff check . && uv run python -m unittest discover -s tests
   ```
6. **Commit your changes**:
   ```bash
   git commit -m "Add interactive concept map feature"
   ```
7. **Push to your branch and open a Pull Request**.

---

## License

DiligentEdu is open-source software licensed under the **GNU General Public License v3.0 (GPLv3)**. See the [LICENSE](LICENSE) file for complete details.

---

## Acknowledgments

- **National Council of Educational Research and Training (NCERT)** for standardizing and publishing open curriculum textbooks.
- **National Scholarship Portal (NSP)** for central and state scholarship scheme guidelines.
- **Streamlit**, **LangChain**, **Pinecone**, and **Google AI Studio** for the foundational technologies empowering this platform.
