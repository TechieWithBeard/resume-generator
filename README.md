# AI-Powered Full-Fledged Resume Generator

[![Angular](https://img.shields.io/badge/Angular-22-dd0031.svg?logo=angular)](https://angular.dev)
[![Signals](https://img.shields.io/badge/State-Signals-purple.svg)](https://angular.dev/guide/signals)
[![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg?logo=python)](https://python.org)
[![LangChain](https://img.shields.io/badge/AI-LangChain-1c3c3c.svg)](https://langchain.com)
[![Streaming](https://img.shields.io/badge/Stream-SSE-0284c7.svg)](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

An end-to-end, production-grade, distributable AI Resume Generator that tailors a candidate's resume to target job descriptions or LinkedIn postings in real time—streaming every reasoning step and decision while deterministically preventing hallucinations.

---

## 🏗️ Architectural Foundations

### 1. The Ground Truth Invariant (Anti-Hallucination Policy)
In recruitment, fabricating experience or claiming unverified skills ruins candidate credibility. This generator enforces a **two-tier defense in depth**:
- **Tier 1 (Prompt Constraint Invariant)**: The LLM is strictly constrained to re-framing, prioritizing, and emphasizing verified achievements from the candidate's Base Resume.
- **Tier 2 (Deterministic Programmatic Verifier)**: A deterministic Python audit algorithm validates that 100% of companies, employment dates, degrees, and educational institutions match the Base Resume before any output is returned to the user.

### 2. Reactive Streaming (Server-Sent Events)
Rather than a traditional blocking spinner, the engine opens an HTTP Server-Sent Events (SSE) stream (`POST /api/generate/stream`) that broadcasts:
- **Phase Transitions**: Job Spec Deconstruction → Ground Truth & Competency Audit → Constrained Synthesis → Deterministic Verification.
- **Real-Time Reasoning Tokens**: Live internal thought chunks explaining keyword extraction, transferable competency mapping, and bullet-point tailoring.
- **Audit Reports**: Real-time competency match scores (0–100%) and direct vs. transferable skill matrices.

### 3. Open-Source Distributability & Privacy Separation
The package is completely decoupled from personal identifiable information (PII):
- The repository ships with an anonymized generic profile (`backend/data/sample_resume.json`).
- Personal resume data is loaded dynamically via `RESUME_DATA_PATH`, local file mounting, or in-app interactive editing.
- Strict `.gitignore` rules prevent personal data files (`*.personal.json`, `data/my_resume.json`, `.env`) from being committed.

---

## 🚀 Quickstart

### Option A: One-Command Local Startup (Fastest)

```bash
./start.sh
```
This script activates the Python environment, ensures the Angular frontend is built, and starts the unified ASGI server on [http://localhost:8000](http://localhost:8000).

---

### Option B: Docker / Docker Compose

Run the entire application in an isolated container:

```bash
# Build and run with docker compose
docker compose up --build
```
Navigate to [http://localhost:8000](http://localhost:8000).

---

### Option C: Manual Developer Setup

#### 1. Backend
```bash
# Install Python dependencies
pip install -r backend/requirements.txt

# Run backend test suite
PYTHONPATH=. python -m unittest backend/tests/test_backend.py
PYTHONPATH=. python -m unittest backend/tests/test_e2e.py

# Launch ASGI server
python backend/run.py
```

#### 2. Frontend
```bash
cd frontend

# Run development server with live reload
npm start

# Or build production bundle
npm run build
```

---

## ⚙️ Configurable LLM Providers

The generator supports multi-provider LLMs configurable via `.env` or dynamically in the in-app **LLM Settings Drawer**:

| Provider | Configuration | Ideal Use Case |
|---|---|---|
| **Local Ollama** | `OLLAMA_BASE_URL=http://localhost:11434`<br>`OLLAMA_MODEL=llama3` | Privacy-first, local offline development with zero cloud egress |
| **OpenAI** | `OPENAI_API_KEY=sk-...`<br>`OPENAI_MODEL=gpt-4o-mini` | High-velocity cloud intelligence |
| **Hugging Face** | `HUGGINGFACEHUB_API_TOKEN=hf_...` | Open-weight inference endpoints |
| **Intelligent Heuristic** | Zero config required | Deterministic high-precision fallback that works immediately out of the box |

---

## 🎨 Predefined ATS-Optimized HTML Templates

The template engine includes three distinct layout philosophies with embedded `@media print` CSS for vector-sharp PDF export:

1. **Modern Tech**: Clean sans-serif typography, accent section headers, skill badges, and 2-column contact header with LinkedIn/GitHub links.
2. **Executive Minimalist**: High-contrast, traditional serif/sans layout designed for 100% compliance across all enterprise ATS parsers (Workday, Greenhouse, Taleo).
3. **Compact Classic**: High-density 1-page engineering format.

### Export Capabilities
- **🖨️ PDF**: Native browser print formatting optimized for letter/A4 with automatic page-break avoidance on experience entries.
- **🌐 HTML**: Download standalone ATS-compliant `.html` file with embedded CSS.
- **{ } JSON**: Download raw structured resume data for programmatic processing.
- **🔍 Diff View**: Toggle real-time highlighting to inspect exactly which bullet points and skills were adapted for the target job.

---

## 📖 Senior Architect Documentation

Detailed engineering decisions and specifications are documented in `docs/`:
- [Architecture Decision Records (ADRs)](docs/ADR.md): Context, trade-offs, and decisions (ADR-001 to ADR-005).
- [Technical Architecture Specification](docs/ARCHITECTURE.md): System diagrams, component boundaries, and streaming protocols.
- [Implementation Plan](docs/IMPLEMENTATION_PLAN.md): Complete engineering blueprint and verification milestones.

---

## 🧪 Testing & Verification

Run the comprehensive unit and integration test suite:

```bash
# Run backend service tests (resume store, template renderer, anti-hallucination engine)
PYTHONPATH=. python -m unittest backend/tests/test_backend.py

# Run E2E HTTP and SSE streaming integration tests
PYTHONPATH=. python -m unittest backend/tests/test_e2e.py
```

---

## 📄 License
MIT License. Free to use, adapt, and distribute.