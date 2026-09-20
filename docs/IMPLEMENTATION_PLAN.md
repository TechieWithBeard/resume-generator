# Implementation Plan: AI-Powered Full-Fledged Resume Generator

This document contains the execution plan for building the AI-Powered Resume Generator.

---

## 1. Objectives & Scope

1. **Predefined ATS HTML Templates**: Clean, professional, ATS-optimized templates with responsive layouts and dedicated print stylesheets (`@media print`).
2. **Base Resume as Ground Truth**: Seeded with verified profile data, but architecturally decoupled so personal data is never hardcoded into distributable releases.
3. **Dual Job Input**: Support for LinkedIn job URLs (with automated extraction and polite fallbacks) as well as direct job description pasting.
4. **Constrained AI Tailoring & Anti-Hallucination Guardrails**: Re-frames, highlights, and prioritizes existing achievements to match the job without fabricating skills, companies, or degrees.
5. **Real-Time Decision Streaming**: Streams the AI's internal reasoning, keyword audits, and thought process via Server-Sent Events (SSE).
6. **Modern Angular Frontend**: Powered by Angular Signals for fine-grained reactivity, live preview, diff comparison, and export to PDF/HTML/JSON.
7. **Modular & Distributable**: Clean packaging, Docker support, and an offline heuristic fallback mode so anyone can download and use the application immediately.

---

## 2. Technical Stack

| Layer | Technology | Rationale |
|---|---|---|
| Backend Server | Python 3.9+ / ASGI (FastAPI/Starlette) | High-performance async I/O, native SSE streaming support |
| AI / LLM Framework | LangChain (`langchain-core`, `langchain-community`, `langchain-ollama`, `langchain-openai`) | Unified interface for local Ollama, OpenAI, and Hugging Face |
| Frontend Framework | Modern Angular (Standalone Components) | Strict typing, robust component architecture |
| State Management | Angular Signals (`signal`, `computed`, `effect`) | Zero-overhead, granular DOM updates during high-frequency streaming |
| Styling & Print | Modern CSS with Glassmorphism & `@media print` | Beautiful web UI with vector-sharp PDF export capability |
| Packaging | Docker, Docker Compose, standalone scripts | Easy distribution for individual or enterprise use |

---

## 3. Implementation Phases

### Phase 1: Foundation & Senior Architect Documentation (Complete)
- Architecture Decision Records (`docs/ADR.md`)
- Technical Architecture Specification (`docs/ARCHITECTURE.md`)
- Plan Specification (`docs/IMPLEMENTATION_PLAN.md`)

### Phase 2: Python Backend Engine
- Pydantic models for resume schema, job inputs, and stream events (`backend/app/models/resume.py`).
- Generic sample resume for package distribution (`backend/data/sample_resume.json`).
- Pre-loaded local base resume (`backend/data/default_base_resume.json`).
- LinkedIn job scraper & extractor (`backend/app/services/linkedin_extractor.py`).
- Predefined HTML template engine (`backend/app/services/template_engine.py`).
- LangChain multi-provider generation chain with anti-hallucination verification (`backend/app/services/generator_chain.py`).
- Main ASGI / FastAPI server with SSE streaming endpoint (`backend/app/main.py`).
- Automated tests verifying anti-hallucination and extraction logic (`backend/tests/test_backend.py`).

### Phase 3: Modern Angular Frontend
- Angular project scaffolding with Signals.
- Streaming service consuming SSE endpoint (`src/app/services/resume-generator.service.ts`).
- Job input component with LinkedIn URL and JD paste tabs (`src/app/components/job-input/`).
- AI decision-making console with typewriter thought log (`src/app/components/stream-console/`).
- Interactive resume preview with template switcher and diff toggle (`src/app/components/resume-preview/`).
- Source of Truth viewer/editor modal (`src/app/components/base-resume-modal/`).
- LLM provider settings drawer (`src/app/components/settings-drawer/`).

### Phase 4: Packaging & Launch Orchestration
- Multi-stage `Dockerfile` and `docker-compose.yml`.
- Convenient launch script (`start.sh`).
- `.gitignore` ensuring private personal resumes are excluded from commits.
- Comprehensive `README.md` with setup and usage instructions.

### Phase 5: Verification & End-to-End Testing
- Automated test runs.
- End-to-end flow testing (Input -> Stream -> Audit -> Render -> Export).
- Walkthrough documentation (`walkthrough.md`).
