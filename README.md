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

- **Human-in-the-Loop (HITL) Mismatch Workflow**: Fast preflight evaluation (`POST /api/generate/preflight`) detects severe competency mismatches ($<40\%$ match or extensive unverified requirements) without artificial score inflation. Prompts candidates with an interactive modal to choose an alignment strategy (`Transferable Skills` vs. `Strict Factual`) or update their Source of Truth before synthesis begins.
- **Check 7: Strict Skills Non-Fabrication Gate**: Deterministic anti-hallucination verification scans every skill in `generated.skills` against candidate ground truth (`skills`, `experience`, `projects`, `certifications`, `raw_text`, `summary`) and automatically purges any ungrounded technical competencies (e.g. FreeRTOS, Swift, Go, Kubernetes if not in source).
- **Strict 1–2 Page Hard Cap (No 30+ Page Overflow)**: Engineered 2-column layout (matching Enhancv / NovoResume) that compresses vertical height by ~45%, keeping resumes strictly within 1 to 2 pages with vector-sharp print boundaries.
- **Built-in 9-Dimension Resume Score Checker**: Automated ATS quality audit evaluating Customization, Spelling & Grammar, Summary Statement, Measurable Results, Word Choice, Formatting, Optimal Length, Contact Info, and Comprehensiveness.
- **Zero-Hallucination Ground Truth Invariant**: Programmatic verification guarantees 100% invariance for past employers, job titles, employment dates, degrees, academic institutions, and technical skills.
- **Dual-Mode Output (Resume vs. Strategic CV)**:
  - **ATS Resume**: High-density, quantified metric-rich experience bullets tailored to job requirements.
  - **Curriculum Vitae & Statement of Strategic Alignment**: 1–2 page executive letter articulating motivation and strategic fit backed by real-time company research.
- **Company Research Intelligence**: Integrates real-time web search (DuckDuckGo / Tavily via LangChain) to discover company culture, engineering values, and tech stack nuances.
- **Anti-Recruitment-Noise Guardrail**: Explicit filter strips out HR boilerplate, hiring process timelines ("call with recruiter 30 mins", "technical review at office", etc.) from both research and generated documents.
- **Git-Style Diff Viewer**: Interactive side-by-side or inline diff viewer highlighting exactly which bullet points and skills were customized.
- **Automated Evaluation Suite with 5 Checkpoints & 6 Benchmarks**: Continuous evaluation engine with automated scoring across Truth Invariance, Noise Elimination, Competency Alignment, ATS Formatting, and Company Research Intelligence across 6 diverse real-world and adversarial test scenarios.

---

## 🏗️ Architectural Foundations

```
+---------------------------------------------------------------------------------------------------+
|                                      FRONTEND (Angular 22 + Signals)                              |
|  [ Job Spec / Target Title ]  [ HITL Mismatch Modal ]  [ Template Studio ]  [ Source of Truth ]    |
+---------------------------------------------------------------------------------------------------+
                             │                                              │
             POST /api/generate/preflight (JSON)              POST /api/generate/stream (SSE)
                             ▼                                              ▼
+---------------------------------------------------------------------------------------------------+
|                                   BACKEND ENGINE (FastAPI / ASGI)                                 |
|                                                                                                   |
|  0. Preflight Audit Gate        Honest match evaluation & HITL mismatch resolution trigger        |
|  1. Company Research Tool       LangChain DuckDuckGo / Tavily search with noise suppression       |
|  2. Job Deconstruction         Extracts essential skills, responsibilities & strategic focus      |
|  3. Ground Truth Invariant      Immutable candidate profile loaded from JSON store                |
|  4. Synthesis & Alignment       Reframes verified achievements incorporating candidate guidance   |
|  5. Noise Elimination Filter    Deterministic purge of HR recruitment process boilerplate         |
|  6. 7-Check Verifier Gate       Asserts 100% identity, employer, degree, dates & skills grounding  |
|  7. 9-Dimension Score Checker   Audits resume against official MyPerfectResume rubric             |
|  8. Template Engine             Renders responsive 2-column ATS HTML with @media print rules      |
+---------------------------------------------------------------------------------------------------+
                                                  │
                                                  ▼
+---------------------------------------------------------------------------------------------------+
|                                   EVALUATION SUITE (6 Benchmark Cases)                            |
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
|  📞 +1 (555) 019-2834  ✉ vishnut071@gmail.com  💻 https://github.com/TechieWithBeard  📍 India   |
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
- 1:1 screen preview synchronization matches physical PDF page layout, preventing text inflation or nested scrollbars.

---

## 🎨 Template Studio, Style Customizer & Design Tokens Guide

The built-in **Template Studio** (`🎨 Styling` button in the preview toolbar) allows candidate documents to be dynamically customized with real-time reactive preview:

### 1. Theming & Customization Controls
- **Curated Color Palettes**: Sapphire Tech (`#0284c7`), Emerald Enterprise (`#059669`), Executive Slate (`#1e293b`), Royal Indigo (`#4338ca`), Crimson Modern (`#dc2626`), and Midnight Charcoal (`#09090b`), plus custom hex color pickers.
- **Web Typography Engine**: Integrated Google Fonts preconnect with choices including **System Clean** (modern sans), **Inter** (clean Grotesk), **Merriweather** (executive serif), **JetBrains Mono** (technical/monospace), and **EB Garamond** (editorial serif).
- **Page Density & Spacing**: Three discrete modes—`Compact` (28px 36px padding), `Standard` (34px 40px), and `Spacious` (54px 58px) with calibrated line spacing (`1.28` to `1.50`).
- **Header Alignment Options**: `Left` aligned, `Center` stacked, or `Split` (name on left, contact items on right).
- **Section Visibility Toggles**: Granular toggles for tagline, contact icons, projects, certifications, and education.

### 2. Exposed CSS Design Tokens (`:root`)
Users can override any design token inside the **Custom CSS** editor:

| Token Variable | Category | Description & Purpose | Default / Example |
|---|---|---|---|
| `--primary-color` | Colors | Candidate name, section underlines, primary badges, headings | `#0284c7` |
| `--accent-color` | Colors | Company names, links, icons, job titles, secondary emphasis | `#0284c7` |
| `--text-primary` | Colors | Main paragraph text, summary statement, and bullet points | `#1e293b` |
| `--text-muted` | Colors | Dates, locations, institution names, and subtle metadata | `#64748b` |
| `--font-family` | Typography | Global font stack for body, headings, and lists | `system-ui`, `Inter`, `Merriweather` |
| `--font-size` | Typography | Base body text size (10.5px to 13px; calibrated for 1-2 page budget) | `11.5px` (~8.6pt) |
| `--line-height` | Typography | Vertical rhythm and paragraph line height ratio | `1.36` |
| `--border-color` | Structure | Light card borders and subtle dividers | `#cbd5e1` |
| `--divider-subtle` | Structure | Separators between experience items | `#f1f5f9` |
| `--diff-bg` | Diff / Badges | Background tint for tailored modifications in diff mode | `#f0fdf4` |
| `--diff-border` | Diff / Badges | Left accent border for modified bullet points | `#16a34a` |

### 3. Key Component Selectors
- `.resume-paper`: The printable document paper container sheet.
- `.header`: Top banner containing applicant name, title, and contact items.
- `.name`, `h1`: Candidate's full name.
- `.title-tagline`: Professional title and positioning tagline.
- `.section-title`: Main section headers (EXPERIENCE, SKILLS, etc.).
- `.exp-role`: Job position / title in experience entries.
- `.exp-company`: Employer / company name in experience entries.
- `.exp-meta`: Date range and location line.
- `.exp-highlights li`: Individual achievement bullet points.
- `.skill-pill`: Individual technical competency badge.
- `.skill-pill.matched`: Highlighted skill badge matching target job spec keywords.
- `.ats-banner`: Top ATS compliance verification badge.

### 4. Interactive 1-Click Quick Snippets
Template Studio provides instant one-click presets for common customizations:
- **Rounded Pill Badges**: Applies full pill border-radius and crisp border.
- **Left Accent Bar**: Converts section underlines into a modern vertical accent bar.
- **Underlined Roles**: Underlines job titles in accent color with text-underline offset.
- **Compact Bullets**: Tightens vertical margins to optimize content budget.
- **Hide ATS Banner**: Hides the top verification banner for a minimalist look.

### 5. Template Config API Endpoints
- `GET /api/template/config`: Retrieves currently persisted template configuration.
- `PUT /api/template/config`: Updates and persists custom colors, fonts, density, and CSS.
- `POST /api/template/config/reset`: Resets configuration back to system defaults.

---

## 🚀 Quickstart: Run in 1 Command

Anyone can clone this repository and run the full stack with **one command**. Everything needed to run locally—including the AI model, local server, and frontend—is configured automatically.

### Option A: Docker (Zero-Config, Self-Contained Ollama & Model Puller)

```bash
# Clone the repository
git clone https://github.com/TechieWithBeard/resume-generator.git
cd resume-generator

# Start the full stack (Ollama + llama3.2 auto-download + Frontend + Backend)
docker compose up --build
```
Open **[http://localhost:8000](http://localhost:8000)**.
- **Automated Ollama Provisioning**: Automatically downloads, starts, and caches `llama3.2` without manual host setup.
- **Model Customization**: To use a different model (e.g. `mistral` or `llama3.1:8b`):
  `OLLAMA_MODEL=mistral docker compose up --build`

---

### Option B: Turnkey Host Launcher (`./setup.sh`)

If you prefer running natively without Docker:

```bash
# Clone & run setup launcher
git clone https://github.com/TechieWithBeard/resume-generator.git
cd resume-generator
./setup.sh
```
The script creates an isolated virtualenv, installs all backend requirements, compiles the Angular frontend, verifies Ollama, and opens your default browser at **[http://localhost:8000](http://localhost:8000)**.

> 📖 For advanced configurations, environment variables, and GPU acceleration, read [INSTALLATION.md](INSTALLATION.md).

---

### Option C: Manual Developer Setup

#### 1. Backend Setup
```bash
# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt

# Run backend test suite
PYTHONPATH=. python -m unittest discover -s backend/tests -p "test_*.py" -v

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

## 🧪 Evaluation Suite & Continuous Benchmarking

The repository includes a standalone evaluation suite running 6 comprehensive benchmark test cases against 5 specialized checkpoints:

```bash
# Run evaluations in terminal format across all 6 cases
python backend/run_evals.py --format terminal

# Run a specific benchmark case (e.g. extreme mismatch HITL)
python backend/run_evals.py --case case_extreme_mismatch_hitl

# Or output markdown summary
python backend/run_evals.py --format markdown
```

### Benchmark Results (100.0% Pass Rate):
```
==============================================================================
  EVALUATION SUITE: Resume & CV Zero-Hallucination Alignment Benchmark
==============================================================================
  Total Cases: 6 | Passed: 6 | Failed: 0 | Pass Rate: 100.0% | Average Score: 95.3%
------------------------------------------------------------------------------
  CATEGORY BENCHMARK SCORES:
  • Truth Invariance             [████████████████████] 100.0%
  • Noise Elimination            [████████████████████] 100.0%
  • Competency Alignment         [████████████████░░░░] 81.2%
  • Ats Formatting               [████████████████████] 100.0%
  • Research Intelligence        [████████████████████] 100.0%
==============================================================================
```

### The 6 Benchmark Scenarios:
1. **Senior Frontend Architect (High Core Match)**: Validates high-density tailoring (97% match), quantifiable metric reframing, and ATS-tested 2-column rendering.
2. **Fullstack Cloud Engineer (Cross-Domain Pivot & Transferable Skills)**: Verifies transferable skills reasoning for fullstack cloud platforms without fabricating unverified technologies (e.g. Golang or Kubernetes).
3. **Adversarial Injection & Fake Credential Trap**: Injects deceptive prompts instructing the AI to fabricate MIT PhDs, Google Brain tenures, and recruitment interview schedules; asserts 100% rejection of synthetic facts.
4. **Rentman Executive CV (Bespoke European Alignment)**: Validates Executive CV generation for Rentman in Utrecht, Netherlands: authentic web intelligence, Dutch enterprise client preservation (Maistering B.V.), and recruitment noise stripping.
5. **Sparse Minimal Job Description**: Verifies graceful degradation and grounded synthesis when presented with a 1-sentence job posting without hallucinating out-of-scope technologies.
6. **Senior Embedded Firmware Engineer (Extreme Mismatch & HITL Gate)**: Adversarial test case with zero overlap (bare-metal C, FreeRTOS, ARM Cortex, CAN bus). Verifies that preflight flags extreme mismatch ($5\%$ match), prompts Human-in-the-Loop guidance, and strictly purges unverified skills.

### The 5 Checkpoints:
1. **Truth Invariance Checkpoint (Checks 1–5)**:
   - *Check 1 (Employers)*: 100% invariance for past companies.
   - *Check 2 (Education)*: 100% invariance for universities and degrees.
   - *Check 3 (Timelines)*: 100% invariance for employment date spans.
   - *Check 4 (Personal Identity)*: Name, phone, email, and location preserved verbatim.
   - *Check 5 (Skills Non-Fabrication Gate)*: Asserts that zero synthetic technical competencies are added to the candidate's skill taxonomy.
2. **Noise Elimination Checkpoint**: Flags and fails if any recruitment process boilerplate, phone screen duration, or interview schedules leak into generated documents.
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