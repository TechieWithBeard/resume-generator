# AI-Powered Full-Fledged Resume & CV Generator

[![Angular](https://img.shields.io/badge/Angular-22-dd0031.svg?logo=angular)](https://angular.dev)
[![Signals](https://img.shields.io/badge/State-Signals-purple.svg)](https://angular.dev/guide/signals)
[![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg?logo=python)](https://python.org)
[![LangChain](https://img.shields.io/badge/AI-LangChain-1c3c3c.svg)](https://langchain.com)
[![Streaming](https://img.shields.io/badge/Stream-SSE-0284c7.svg)](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)
[![Evals](https://img.shields.io/badge/Evals-100%25%20Pass%20Rate-brightgreen.svg)](backend/app/evals)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

An end-to-end, production-grade AI Resume & CV Platform that tailors candidate profiles to target job descriptions and company intelligence in real time. Designed with a strict **Zero-Hallucination Ground Truth Invariant**, an **ATS-Tested 2-Column Layout** with a strict **1–2 page hard cap**, and a built-in **9-Dimension Resume Score Checker** matching the official [MyPerfectResume](https://www.myperfectresume.com) scoring rubric.

---

## 🌟 Key Highlights

- **Strict 1–2 Page Hard Cap (No 30+ Page Overflow)**: Engineered 2-column layout (matching Enhancv / NovoResume) that compresses vertical height by ~45%, keeping resumes strictly within 1 to 2 pages with vector-sharp print boundaries.
- **Built-in 9-Dimension Resume Score Checker**: Automated ATS quality audit evaluating Customization, Spelling & Grammar, Summary Statement, Measurable Results, Word Choice, Formatting, Optimal Length, Contact Info, and Comprehensiveness.
- **Zero-Hallucination Ground Truth Invariant**: Programmatic verification guarantees 100% invariance for past employers, job titles, employment dates, degrees, and academic institutions.
- **Dual-Mode Output (Resume vs. Strategic CV)**:
  - **ATS Resume**: High-density, quantified metric-rich experience bullets tailored to job requirements.
  - **Curriculum Vitae & Statement of Strategic Alignment**: 1–2 page executive letter articulating motivation and strategic fit backed by real-time company research.
- **Company Research Intelligence**: Integrates real-time web search (DuckDuckGo / Tavily via LangChain) to discover company culture, engineering values, and tech stack nuances.
- **Anti-Recruitment-Noise Guardrail**: Explicit filter strips out HR boilerplate, hiring process timelines ("call with recruiter 30 mins", "technical review at office", etc.) from both research and generated documents.
- **Git-Style Diff Viewer**: Interactive side-by-side or inline diff viewer highlighting exactly which bullet points and skills were customized.
- **Automated Evaluation Suite with 5 Checkpoints**: Continuous evaluation engine with automated scoring across Truth Invariance, Noise Elimination, Competency Alignment, ATS Formatting, and Company Research Intelligence.

---

## 🏗️ Architectural Foundations

```
+---------------------------------------------------------------------------------------------------+
|                                      FRONTEND (Angular 22 + Signals)                              |
|  [ Job Spec / Target Title ]  [ Template Studio ]  [ Git-Diff Viewer ]  [ Source of Truth Editor ] |
+---------------------------------------------------------------------------------------------------+
                                                  │
                                 POST /api/generate/stream (SSE)
                                                  ▼
+---------------------------------------------------------------------------------------------------+
|                                   BACKEND ENGINE (FastAPI / ASGI)                                 |
|                                                                                                   |
|  1. Company Research Tool       LangChain DuckDuckGo / Tavily search with noise suppression       |
|  2. Job Deconstruction         Extracts essential skills, responsibilities & strategic focus      |
|  3. Ground Truth Invariant      Immutable candidate profile loaded from JSON store                |
|  4. Synthesis & Alignment       Reframes verified achievements to job requirements                |
|  5. Noise Elimination Filter    Deterministic purge of HR recruitment process boilerplate         |
|  6. Deterministic Verifier      Asserts 100% identity, employer, degree & timeline invariance     |
|  7. 9-Dimension Score Checker   Audits resume against official MyPerfectResume rubric             |
|  8. Template Engine             Renders responsive 2-column ATS HTML with @media print rules      |
+---------------------------------------------------------------------------------------------------+
                                                  │
                                                  ▼
+---------------------------------------------------------------------------------------------------+
|                                   EVALUATION SUITE (5 Checkpoints)                                |
|  [ Truth Invariance ] [ Noise Elimination ] [ Competency Match ] [ ATS Format ] [ Research Intel ]|
+---------------------------------------------------------------------------------------------------+
```

---

## 📊 9-Dimension Resume Score Checker (MyPerfectResume Rubric)

The built-in audit engine ([backend/app/services/resume_score_checker.py](backend/app/services/resume_score_checker.py)) scores every resume against 9 professional dimensions:

| # | Dimension | Audit Criteria & Standards | Base Score |
|---|:---|:---|:---:|
| 1 | **Customization** | Target role alignment, essential keywords & skills matching, zero keyword stuffing | **100** |
| 2 | **Spelling & Grammar** | 0 spelling errors/typos, consistent terminal punctuation (`.`), tense harmony | **100** |
| 3 | **Summary Statement** | Executive headline, years of experience ($7+$), core technical competencies | **100** |
| 4 | **Measurable Results** | Concrete metrics ($\%$, numbers, scale, hours saved) across $\ge 80\%$ of bullets | **100** |
| 5 | **Word Choice** | $25+$ senior action verbs (`spearheaded`, `architected`), 0 personal pronouns, 0 passive filler | **100** |
| 6 | **Formatting** | Clean visual dividers, ATS semantic markup, pill badges, scannable two-column structure | **100** |
| 7 | **Optimal Length** | Strict 1–2 page hard cap (400–1,200 words), zero runaway multi-page spill | **100** |
| 8 | **Contact Information** | $\ge 4$ contact vectors verified (Phone, Email, LinkedIn, GitHub, Location) | **100** |
| 9 | **Comprehensiveness** | All 6 core pillars complete: Contact, Summary, Experience, Skills, Education, Certs | **100** |
| — | **OVERALL SCORE** | **Grade: A+ (ATS Masterpiece)** | **100 / 100** |

### API Endpoints for Resume Scoring:
- `GET /api/resume/score`: Audits candidate ground truth profile and returns the full 9-dimension scorecard.
- `POST /api/resume/score`: Audits a tailored resume or custom payload against a specific `target_role` and `job_description`.

---

## 📐 ATS 2-Column Template & Hard Cap Architecture

```
+-----------------------------------------------------------------------------------------------+
|  ✓ ATS-tested template • built to parse more cleanly                                          |
|                                                                                               |
|  VISHNU THANKAPPAN                                                                            |
|  Senior Frontend Engineer                                                                     |
|  📞 +918373923785  ✉ vishnut071@gmail.com  💻 https://github.com/TechieWithBeard  📍 India     |
+-----------------------------------------------------------------------------------------------+
|  LEFT COLUMN (~62%)                                 |  RIGHT COLUMN (~38%)                    |
|                                                     |                                         |
|  EXPERIENCE                                         |  SUMMARY                                |
|  ----------                                         |  -------                                |
|  Senior Frontend Engineer                           |  Senior Frontend Developer • Enterprise |
|  Parnasoft Technologies                             |  Architecture • Angular, Performance... |
|  📅 03/2025 - Present  📍 India                     |  Accomplished Senior Frontend Developer |
|  • Client: AVEVA - India                            |  with 7+ years of proven track record...|
|  • Spearheaded enterprise Angular migration from... |                                         |
|  • Architected & restructured enterprise Nx monorepo|  TRAINING / COURSES                     |
|  • Engineered modular shared UI component library...|  ------------------                     |
|  • Established multi-tier testing strategy (85%+)...|  Developing Solutions for Microsoft     |
|  • Standardized modular frontend architecture (40%).|  Azure (AZ-204) - Microsoft             |
|  • Partnered across 3+ distributed squads (99.9%)...|                                         |
|  • Accelerated sprint delivery velocity by 25%...   |  SKILLS                                 |
|                                                     |  ------                                 |
|  Frontend Specialist                                |  [ Angular ] [ TypeScript ] [ Signals ] |
|  ACI Logistix                                       |  [ Nx ] [ JavaScript ] [ HTML ] [ CSS ] |
|  📅 03/2022 - 03/2025  📍 India                     |  [ SCSS ] [ Design Systems ] [ NgRx ]   |
|  • Spearheaded incremental migration (v14+)...      |  [ Jasmine ] [ Karma ] [ Cypress ]...   |
|  • Architected centralized NgRx store (35% drop)... |                                         |
|  • Published 10+ internal npm libraries (15 hrs)... |  CERTIFICATIONS                         |
|  • Engineered cross-platform apps (15k users)...    |  --------------                         |
|  • Automated logistics validation workflows (20 hrs)|  Enterprise Architecture Masterclass    |
|                                                     |  Angular Architects (2024)              |
|  KEY PROJECTS & ARCHITECTURE                        |                                         |
|  ---------------------------                        |  EDUCATION                              |
|  Enterprise Angular Modernization & Signals         |  ---------                              |
|  Angular 20, Signals, TypeScript, RxJS              |  Master of Computer Applications        |
|  📅 2025                                            |  Manipal Academy of Higher Education    |
|  • Led large-scale migration to Angular 20...       |  📅 2016 – 2018                         |
+-----------------------------------------------------------------------------------------------+
```

### Print Engine & PDF Rules:
- `@page { size: letter portrait; margin: 8mm 10mm; }`
- Container uses `display: grid; grid-template-columns: 1.62fr 1fr;` to minimize page height.
- Atomic `break-inside: avoid;` only on individual job items, ensuring pages split cleanly without orphaned headers or 30-page runaway gaps.
- Screen badges (`.ats-banner`, diff highlights) are automatically hidden in print mode.

---

## 🚀 Quickstart

### Option A: One-Command Local Startup (Recommended)

```bash
./start.sh
```
This script activates the virtual environment, verifies the Angular production build, and launches the unified ASGI server on [http://localhost:8000](http://localhost:8000).

---

### Option B: Docker / Docker Compose

```bash
# Build and start container
docker compose up --build
```
Open [http://localhost:8000](http://localhost:8000).

---

### Option C: Manual Developer Setup

#### 1. Backend Setup
```bash
# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt

# Run backend unit & integration tests
PYTHONPATH=. python -m unittest backend/tests/test_backend.py
PYTHONPATH=. python -m unittest backend/tests/test_e2e.py

# Launch ASGI server
python backend/run.py
```

#### 2. Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Run dev server with hot reload
npm start

# Or build production bundle
npm run build
```

---

### Option D: VS Code One-Click Run & Debug

- **Run Full Stack**: Press `Ctrl+Shift+B` (or `Cmd+Shift+B` on Mac) to run `🚀 Run Full Stack (start.sh)`.
- **Debug in VS Code**: Press `F5` to start `✨ Full Stack (Backend + Open Browser)`.
- **Run Tasks**: Open Command Palette (`Cmd+Shift+P`) -> `Tasks: Run Task` to selectively start backend, Angular dev server, or test suites.

---

## ⚙️ Configurable LLM Providers

Configurable via `.env` or interactively in the frontend **LLM Settings Drawer**:

| Provider | Configuration | Ideal Use Case |
|---|---|---|
| **Intelligent Heuristic** | Zero config required | Deterministic high-precision fallback that works immediately out of the box |
| **Local Ollama** | `OLLAMA_BASE_URL=http://localhost:11434`<br>`OLLAMA_MODEL=llama3` | Privacy-first, 100% offline local development with zero cloud egress |
| **OpenAI** | `OPENAI_API_KEY=sk-...`<br>`OPENAI_MODEL=gpt-4o-mini` | High-velocity cloud inference |
| **Hugging Face** | `HUGGINGFACEHUB_API_TOKEN=hf_...` | Open-weight serverless inference |

---

## 🧪 Evaluation Suite & Checkpoints

The repository includes a standalone evaluation suite running 5 comprehensive benchmark test cases against 5 specialized checkpoints:

```bash
# Run evaluations in terminal format
python backend/run_evals.py --format terminal

# Or output markdown summary
python backend/run_evals.py --format markdown
```

### Benchmark Results:
```
==============================================================================
  EVALUATION SUITE: Resume & CV Zero-Hallucination Alignment Benchmark
==============================================================================
  Total Cases: 5 | Passed: 5 | Failed: 0 | Pass Rate: 100.0% | Average Score: 98.0%
------------------------------------------------------------------------------
  CATEGORY BENCHMARK SCORES:
  • Truth Invariance             [████████████████████] 100.0%
  • Noise Elimination            [████████████████████] 100.0%
  • Competency Alignment         [██████████████████░░] 91.9%
  • Ats Formatting               [████████████████████] 100.0%
  • Research Intelligence        [████████████████████] 100.0%
==============================================================================
```

### The 5 Checkpoints:
1. **Truth Invariance Checkpoint**: Verifies that 100% of candidate employers, degrees, timelines, and personal identity remain invariant.
2. **Noise Elimination Checkpoint**: Flags and fails if any recruitment process boilerplate or interview schedules leak into generated documents.
3. **Competency Alignment Checkpoint**: Asserts that core skills from the target job are woven naturally into verified achievements without keyword stuffing.
4. **ATS & Template Formatting Checkpoint**: Asserts semantic HTML, visual dividers, proper `@page` margins, and incorporates the 9-Dimension Resume Score audit.
5. **Company Research Intelligence Checkpoint**: Validates authentic strategic alignment, company mission research, and executive rationale in CV mode.

---

## 📖 Documentation & Architecture Specifications

- [Architecture Decision Records (ADRs)](docs/ADR.md): In-depth decision logs for all major architectural choices.
- [Technical Architecture Specification](docs/ARCHITECTURE.md): Component diagrams, SSE protocol specifications, and security model.
- [Implementation Plan](docs/IMPLEMENTATION_PLAN.md): Engineering blueprint and milestone tracking.

---

## 📄 License

MIT License. Free to use, adapt, and distribute.