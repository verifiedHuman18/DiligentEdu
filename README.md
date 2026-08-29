# DiligentEdu

> **Intelligent NCERT Academic Science RAG Assistant, Socratic AI Tutor, Adaptive Diagnostic System, Study Twin Matchmaker and National Scholarship Discovery Platform**

![Python](https://img.shields.io/badge/python-v3.12+-blue.svg)
![Streamlit](https://img.shields.io/badge/streamlit-v1.49+-red.svg)
![Prisma](https://img.shields.io/badge/orm-prisma-2D3748.svg)
![Google Gemini](https://img.shields.io/badge/google%20gemini-2.5%20%2F%202.0%20%2F%201.5-orange.svg)
![Pinecone](https://img.shields.io/badge/vector%20store-pinecone-blueviolet.svg)
![Firebase](https://img.shields.io/badge/auth-firebase-FFA611.svg)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)
[![Ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

---

## Overview

**DiligentEdu** is an enterprise-grade, multi-role academic learning platform and intelligent tutoring system designed for Indian secondary education. Built around the authoritative **NCERT Class 9 and Class 10 Science curriculum**, DiligentEdu integrates Retrieval-Augmented Generation (RAG), Socratic pedagogical guidance, continuous diagnostic assessment, collaborative peer matching, early-warning analytics for educators, administrative governance, and a centralized government scholarship matching engine.

Whether a student needs step-by-step conceptual guidance on *Chemical Reactions and Equations*, an educator needs cohort mastery analytics to identify at-risk learners, an administrator needs curriculum scope management, or a family is searching for eligible National Scholarship schemes, DiligentEdu provides a unified, curriculum-grounded solution.

---

## Key Features

### 1. Interactive 3D Knowledge Universe Intro
* **Three.js WebGL Landing Scene**: High-performance 3D scene featuring a pulsing Knowledge Core, counter-rotating wireframe cage, 3 angled orbital tracks, and 3 academic concept satellites.
* **Cinematic Phased Assembly**: Dynamic particle convergence timeline (~3s) transitioning into branding without blocking AI or database initialization.
* **Accessibility and Resilience**: Native prefers-reduced-motion support, WebGL fallback to static branding, and zero browser-level URL manipulation.
* **Seamless State Handoff**: Single centered button triggering pure Python session transition directly into the authentication portal.

### 2. Multi-Role Authentication and Profile Isolation
* **Firebase Authentication**: Secure email and password authentication integrated with institutional rosters.
* **Role-Based Workspaces**: Dedicated interfaces and access controls for Students, Teachers, and Administrators.
* **Session Persistence**: URL parameter session restoration (`?uid=...`) with persistent Prisma database state.

### 3. NCERT Science RAG Assistant and Textbook Viewer
* **Curriculum-Grounded Retrieval**: Powered by Pinecone vector storage with strict class-level isolation (`class9`, `class10`) across all 25 NCERT Science chapters.
* **Page-Level Verifiable Citations**: Explanations include direct chapter and page citations matching the official NCERT textbooks.
* **Integrated Textbook PDF Viewer**: Built-in static PDF streaming allows students to review source textbooks alongside AI responses.
* **Real-Time Token Streaming**: Low-latency token generation with full LaTeX formula rendering and structured tables for physics laws, chemical reactions, and mathematical proofs.

### 4. Intelligent Socratic and Exploratory Tutor
* **Dual Pedagogical Modes**: Choose between *Exploratory Mode* (direct conceptual explanations) and *Socrates Mode* (guided inquiry prompting the student to deduce answers).
* **Contextual Suggested Prompts**: Context-aware questions tailored specifically to the selected class level and chapter.
* **Mathematical and Scientific Formatting**: Full support for chemical equations, reaction conditions, and physics derivations.

### 5. Adaptive Quiz and Diagnostic Engine
* **Bloom's Taxonomy Progression**: Dynamic question generation scaling from foundational recall to conceptual understanding and analytical application.
* **Socrates Quiz Mode**: Interactive step-by-step breakdown offering progressive hints without prematurely revealing answers.
* **Automated Evaluation and Explanations**: Instant scoring, point breakdown, and detailed rationales for correct and incorrect choices.

### 6. Student SWAT Performance Analytics
* **Automated SWAT Diagnostics**: Classifies chapter performance into **S**trengths (>=75%), **W**eaknesses (<50%), **A**ptitudes (50-74%), and **T**argets (unattempted chapters).
* **Mastery Radar and Trend Analysis**: Visual score distributions tracking curriculum mastery over time.
* **Prescriptive Action Plans**: Personalized revision pathways generated from individual quiz performance.

### 7. Interactive Knowledge Graph
* **Visual Concept Maps**: Interactive graphical networks displaying relationships between core NCERT science topics, definitions, and formulas.
* **Cross-Chapter Linkages**: Helps students discover prerequisites and conceptual connections across biology, chemistry, and physics.

### 8. Study Twin and Collaborative Peer Matching
* **Complementary Profile Matching**: Algorithmic matchmaker pairing learners based on mastery levels, active focus topics, and SWAT priorities.
* **Peer Learning Facilitation**: Connects students who excel in specific chapters with peers targeting improvement in those areas.
* **Persistent Matching Records**: Tracks similarity scores and historical study partnerships in the Prisma database.

### 9. Educator and Teacher Early-Warning Dashboard
* **Cohort-Wide Monitoring**: Class-level performance metrics, quiz completion rates, and average score distributions.
* **Early-Warning Alerts**: Immediate flagging of students requiring academic intervention or falling behind in foundational chapters.
* **Customizable Action Plans**: Review, modify, and augment AI-generated student action plans with educator remarks.

### 10. Administrator Portal and Governance
* **Class Scope Management**: Institutional toggles for curriculum visibility, active class levels, and academic years.
* **User and Roster Management**: Overview of registered students, teachers, and system access logs.

### 11. National Scholarship Portal (NSP) Matching Hub
* **Curated Central and State Catalog**: Database of verified government schemes (Pre-Matric, PM-YASASVI, NMMS, Top Class Schools, PwD allowances).
* **Multi-Factor Eligibility Matchmaker**: Instant evaluation based on class level, annual family income brackets, reservation category, school management type, and disability status.
* **Direct Official Links**: Authoritative links to the National Scholarship Portal and Direct Benefit Transfer (DBT) guidelines.

### 12. Dual-Key Resilient AI Architecture
* **Primary and Fallback Resolution**: Automatic fallback from primary environment/secrets keys to user-provided session keys.
* **Zero Disk Leakage**: Session API keys are retained exclusively in volatile memory and never written to disk or logs.
* **Intelligent Error Categorization**: Automated handling for authentication errors (HTTP 401/403), quota limits (HTTP 429), and service disruptions (HTTP 500/503).

---

## Tech Stack

| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| **Frontend Framework** | Streamlit (Python) | Interactive web application and multi-screen state orchestration |
| **3D Graphics** | Three.js (r128 WebGL) | Fullscreen procedural 3D Knowledge Universe splash screen |
| **Styling & Design System** | Material Design 3 / Custom CSS | Curated dark theme, glassmorphism, responsive cards, and tokens |
| **Relational Database & ORM** | Prisma ORM, SQLite (`prisma/dev.db`) | User profiles, quiz attempts, question logs, action plans, study twins |
| **Authentication** | Firebase Authentication REST API | Identity verification and token-based session management |
| **AI / LLM Integration** | Google Gemini (via OpenAI Agents SDK) | Socratic tutoring, query answers, and adaptive quiz generation |
| **Vector Database** | Pinecone | Cloud vector database partitioned by class namespaces (`class9`, `class10`) |
| **Embeddings Model** | HuggingFace `all-MiniLM-L6-v2` | Dense 384-dimensional vector embeddings for textbook retrieval |
| **Package Management** | `uv` / `pip` | High-speed dependency resolution and virtual environments |
| **Code Quality & CI/CD** | Ruff, GitHub Actions | Strict linting, automated formatting, and unit testing |

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
9. **Chapter 9**: Light: Reflection and Refraction
10. **Chapter 10**: The Human Eye and the Colourful World
11. **Chapter 11**: Electricity
12. **Chapter 12**: Magnetic Effects of Electric Current
13. **Chapter 13**: Our Environment
</details>

---

## Project Structure

```
academic-rag-assistant/
├── app.py                              # Streamlit application entry point and screen routing
├── backend/                            # Core business logic and database interfaces
│   ├── auth/                           # Firebase authentication client
│   ├── curriculum/                     # NCERT Class 9 and 10 metadata and PDF resolvers
│   ├── rag/                            # Pinecone retriever, prompts, and streaming engine
│   ├── quiz/                           # Socrates quiz generator, evaluators, and models
│   ├── analytics/                      # SWAT diagnostic engine and teacher action plans
│   ├── scholarships/                   # NSP guidelines, models, and eligibility matchmaker
│   ├── storage/                        # Prisma client singleton and database repositories
│   └── exceptions.py                   # Domain-specific exception hierarchy
│
├── frontend/                           # Streamlit UI presentation layer
│   ├── assets/                         # Application logos and static illustrations
│   ├── components/                     # Reusable widgets (navbar, transitions, cards, PDF viewer)
│   ├── screens/                        # Screen views (intro, login, home, tutor, quiz, SWAT, etc.)
│   ├── state.py                        # Unified session state management
│   └── styles.py                       # Material Design 3 tokens and dark CSS stylesheets
│
├── prisma/                             # Database schema and migrations
│   ├── schema.prisma                   # Prisma schema (User, QuizAttempt, QuestionResponse, etc.)
│   └── dev.db                          # Local SQLite database instance
│
├── static/                             # Authoritative NCERT textbook PDFs
│   ├── class9/                         # Class 9 science textbook PDFs
│   └── class10/                        # Class 10 science textbook PDFs
│
├── scholarships/                       # Scholarship dataset and sources metadata
│   └── sources.json                    # Canonical government scholarship guidelines
│
├── scripts/                            # Maintenance, benchmarking, and database seed scripts
│   ├── provision_users.py              # User provisioning in Firebase and Prisma
│   ├── seed_mock_data.py               # Generates sample student quiz attempts and SWAT history
│   ├── ingest_corpus.py                # NCERT PDF chunking and vector index ingestion
│   └── retrieval_benchmark.py          # Vector search accuracy and latency benchmarks
│
├── tests/                              # Automated test suite (unit, integration, regression)
├── requirements.txt                    # Python runtime dependencies
├── pyproject.toml                      # Project metadata, Ruff and Pyright configuration
├── DockerFile                          # Docker container build specification
└── LICENSE                             # GNU General Public License v3.0
```

---

## Getting Started

### 1. Prerequisites
* **Python 3.12** or higher
* **Google Gemini API Key** from [Google AI Studio](https://aistudio.google.com/app/apikey)
* **Pinecone API Key** from [Pinecone Console](https://app.pinecone.io/) with an index named `ncert-science`
* **Firebase Project** (optional for cloud auth, fallback mode available)

### 2. Clone the Repository
```bash
git clone https://github.com/verifiedHuman18/DiligentEdu.git
cd DiligentEdu
```

### 3. Set Up Virtual Environment and Dependencies

Using **`uv`** (recommended):
```bash
uv sync --group dev
```

Or using standard **`pip`**:
```bash
python -m venv .venv
# On Windows:
.\.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
```

### 4. Initialize the Prisma Database
Generate the Prisma client and apply the database schema:
```bash
python -m prisma generate
python -m prisma db push
```

### 5. Seed Initial User and Academic Data
```bash
python scripts/provision_users.py
python scripts/seed_mock_data.py
```

### 6. Configure Environment Variables
Create a `.env` file in the root directory (or `.streamlit/secrets.toml`):

```env
GOOGLE_API_KEY=your_google_gemini_api_key_here
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_INDEX_NAME=ncert-science
FIREBASE_API_KEY=your_firebase_api_key_here
```

### 7. Run the Application
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
| `PINECONE_INDEX_NAME` | No | `ncert-science` | Target Pinecone vector index name |
| `FIREBASE_API_KEY` | No | None | Firebase Authentication Web API key |

### Supported Gemini Models

| Model Identifier | Description and Recommended Use Case |
| :--- | :--- |
| `gemini-2.5-flash` | **Default / Recommended**: Ultra-fast responses and high conceptual precision |
| `gemini-2.5-pro` | Advanced multi-step reasoning for complex physics derivations and chemical mechanisms |
| `gemini-2.5-flash-lite` | Lightweight and cost-effective model for rapid query resolution |
| `gemini-2.0-flash` | High-throughput baseline model |
| `gemini-1.5-pro` | High context window model for large text analysis |
| `gemini-1.5-flash` | Rapid general-purpose model |

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

## Testing and Quality Assurance

DiligentEdu maintains an automated test suite covering class isolation, RAG retriever accuracy, Socratic dialogs, SWAT analytics, teacher customization, 3D intro performance, and scholarship matching.

### Running Tests
```bash
# Run all unit tests
python -m unittest discover -s tests

# Run with verbose output
python -m unittest discover -s tests -v
```

### Running Code Quality and Lint Checks
```bash
# Run Ruff lint checks
ruff check .

# Run Ruff formatting checks
ruff format --check .

# Auto-format all code
ruff format .
```

---

## Contributing

Contributions are welcome. To contribute:

1. **Fork the repository** on GitHub.
2. **Create a descriptive feature branch**:
   ```bash
   git checkout -b feature/interactive-study-guide
   ```
3. **Make your changes** with thorough docstrings, type hints, and unit tests.
4. **Ensure all linters and tests pass**:
   ```bash
   ruff check . && python -m unittest discover -s tests
   ```
5. **Commit your changes**:
   ```bash
   git commit -m "Add interactive study guide feature"
   ```
6. **Push to your branch and open a Pull Request**.

---

## License

DiligentEdu is open-source software licensed under the **GNU General Public License v3.0 (GPLv3)**. See the [LICENSE](LICENSE) file for complete details.

---

## Acknowledgments

* **National Council of Educational Research and Training (NCERT)** for publishing open curriculum textbooks and syllabi.
* **National Scholarship Portal (NSP)** for central and state scholarship scheme guidelines.
* **Streamlit**, **Three.js**, **Prisma**, **Pinecone**, and **Google AI Studio** for the technologies powering this platform.
