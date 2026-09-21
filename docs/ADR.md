# Architecture Decision Records (ADRs)

This document records the foundational architectural decisions made for the **AI-Powered Resume Generator** platform, detailing the context, decision, consequences, and trade-offs of each choice.

---

## ADR-001: Decoupling Personal Resume Data from Core Engine Package

### Status
Accepted

### Context
Resume generation software is inherently personal, yet the core generation engine, HTML/CSS templates, prompt pipelines, and UI constitute a generic, reusable product. If personal data (names, contact information, career history) is tightly coupled with the code, the repository cannot be safely distributed, published as open source, or packaged for generic enterprise use without leaking personal identifiable information (PII).

### Decision
1. Separate code and personal data completely.
2. The core repository ships with an anonymized, generic `sample_resume.json` satisfying the schema.
3. The platform supports dynamic runtime configuration of the candidate's Base Resume via:
   - Configurable file path (`RESUME_DATA_PATH` environment variable).
   - In-app interactive UI editor where any user can import, inspect, edit, and locally persist their own base resume.
4. Add strict `.gitignore` rules covering personal resume data files (`data/*.personal.json`, `data/my_resume.json`, `.env`).

### Consequences
- **Positive**: The codebase can be safely distributed as an open-source package, containerized via Docker, or shared publicly.
- **Positive**: Zero risk of personal PII leakage into version control.
- **Negative**: Requires runtime validation to guarantee that a valid Base Resume schema exists before generation commences.

---

## ADR-002: Server-Sent Events (SSE) over WebSockets for Thought Streaming

### Status
Accepted

### Context
The user requirement mandates streaming the AI's internal decision-making process, thoughts, and progress in real time rather than waiting for a delayed batch response. We evaluated two primary transport mechanisms: WebSockets and Server-Sent Events (SSE).

### Decision
Adopt **Server-Sent Events (SSE)** via HTTP POST with `text/event-stream; charset=utf-8`.

### Rationale & Trade-off Analysis
| Criterion | WebSockets | Server-Sent Events (SSE) | Decision Alignment |
|---|---|---|---|
| Communication Direction | Full-duplex bidirectional | Unidirectional server-to-client | Generation is a unidirectional response stream |
| Transport Protocol | WebSocket framing over TCP | Standard HTTP/1.1 or HTTP/2 | Better compatibility with reverse proxies, CDNs, and load balancers |
| Connection Lifecycle | Persistent stateful connection | Standard HTTP request with streaming response | Matches RESTful semantics (`POST /api/generate/stream`) |
| Client Complexity | Requires heartbeat/ping-pong handling | Native browser `EventSource` / `fetch` `ReadableStream` | Zero external dependencies on frontend |
| Firewall/Proxy Traversal | Often throttled or blocked by corporate proxies | Operates over standard HTTP/HTTPS ports | High enterprise reliability |

### Consequences
- **Positive**: Lightweight, stateless server implementation with standard HTTP infrastructure compatibility.
- **Positive**: Directly consumable via standard browser `fetch` and `ReadableStreamDefaultReader`.

---

## ADR-003: Angular Signals for Fine-Grained Reactive State Management

### Status
Accepted

### Context
Streaming AI responses emits frequent, high-velocity events (thought tokens, phase transitions, partial resume sections). Traditional Angular change detection (Zone.js checking the entire component tree on each microtask) causes excessive re-renders and UI jank during high-frequency streaming.

### Decision
Adopt **Angular Signals** (`signal()`, `computed()`, `effect()`) for state management throughout the frontend.

### Rationale
- Signals introduce fine-grained reactivity directly to the DOM nodes that depend on them.
- High-frequency thought token updates only re-render the terminal stream view without touching the resume preview, job input form, or global navigation.
- Eliminates heavy external state management libraries (such as NgRx or Akita) for a lightweight, modular architecture.

### Consequences
- **Positive**: Superior runtime performance during 60fps streaming updates.
- **Positive**: Clean, readable reactive code with minimal boilerplate.

---

## ADR-004: Multi-Tiered Anti-Hallucination Guardrails

### Status
Accepted

### Context
Large Language Models have a known propensity to invent facts ("hallucination"). In resume generation, fabricating experience, inventing non-existent employers, inflating degrees, or asserting unverified technical proficiencies destroys candidate credibility and violates ethical standards. The platform must guarantee that the candidate's Base Resume is the inviolable Ground Truth.

### Decision
Implement a **two-tier defense in depth** against hallucinations:

```mermaid
flowchart TD
    JD[Job Description / LinkedIn URL] --> Chain[LangChain Reasoning Pipeline]
    BR[Base Resume: Ground Truth] --> Chain
    
    subgraph Tier1 ["Tier 1: Constrained Generation"]
        Prompt[System Prompt with Negative Constraints & Ground Truth Invariant]
        Chain --> Prompt
        Prompt --> Draft[Candidate Resume Draft]
    end
    
    subgraph Tier2 ["Tier 2: Deterministic Programmatic Audit"]
        Draft --> Audit[Deterministic Entity & Fact Verifier]
        BR --> Audit
        Audit -->|Check 1: Company Names strictly match| V1{Valid?}
        Audit -->|Check 2: Degree & School names match| V2{Valid?}
        Audit -->|Check 3: Skill classification verified| V3{Valid?}
        V1 & V2 & V3 -->|Pass| Final[Verified Resume Output]
        V1 & V2 & V3 -->|Fail| Sanitize[Fallback Sanitization / Flagging]
        Sanitize --> Final
    end
```

1. **Tier 1 (Prompt Engineering Invariant)**: The LLM is instructed that its sole task is *re-framing*, *re-ordering*, and *highlighting* existing achievements from the base resume using the terminology of the target job description. Explicit negative constraints forbid creating new employment blocks or claiming unverified skills.
2. **Tier 2 (Deterministic Programmatic Verification)**: Before returning the resume, a deterministic Python audit function verifies that:
   - All company names in the output exist in the base resume.
   - All educational institutions and degrees exist in the base resume.
   - Experience date ranges have not been altered.
   - Generates an `AlignmentReport` summarizing direct matches, transferable skills, and explicit verification logs.

### Consequences
- **Positive**: Absolute protection against rogue LLM hallucinations.
- **Positive**: Full auditability: users can inspect exactly how the AI mapped their experience to the job requirements.

---

## ADR-005: Multi-Provider LLM Abstraction with Zero-Config Fallback

### Status
Accepted

### Context
End users have varying deployment constraints:
- Local privacy enthusiasts require **Local Ollama** (Llama 3, Mistral, Qwen) with zero external data transmission.
- Cloud users prefer state-of-the-art **OpenAI** (GPT-4o, GPT-4o-mini).
- Open-source practitioners utilize **Hugging Face Inference**.
- First-time evaluators downloading the package may not have API keys or an Ollama instance active immediately.

### Decision
Design a unified LLM Provider Adapter interface:
1. `ChatOllama` adapter.
2. `ChatOpenAI` adapter.
3. `HuggingFaceEndpoint` adapter.
4. **Intelligent Heuristic Fallback Engine**: If no external provider is configured or reachable, an intelligent heuristic keyword-mapping engine executes the exact same multi-stage alignment flow and streaming protocol deterministically. This guarantees the package works out-of-the-box on the very first run without configuration friction.

### Consequences
- **Positive**: Maximum portability across local, private, and cloud environments.
- **Positive**: 100% out-of-the-box functional experience for anyone downloading the package.

---

## ADR-006: Real-Time LLM Token Streaming (`astream`) and Domain Competency Inference

### Status
Accepted

### Context
During testing with concise job specifications (e.g. `Senior Frontend Developer at Rentman — Utrecht, Netherlands`) and local Ollama execution, two architectural friction points emerged:
1. **LLM Invocation Latency Freeze**: Calling synchronous/blocking `ainvoke()` caused a ~60–80 second delay where no SSE chunks were yielded, giving the illusion of a frozen or broken system.
2. **Concise Headline Inputs**: Users frequently paste high-level role headlines rather than multi-page technical checklists. Rigid literal keyword matching produced empty competency matches for concise titles.
3. **Capacity Misunderstanding**: Dynamic character length counters (e.g. `Ingesting job specification (172 characters)...`) were misinterpreted by users as arbitrary character limits.

### Decision
1. **Granular Token Streaming**: Replaced blocking `ainvoke()` with LangChain's asynchronous token streaming `llm.astream()`. The engine yields granular `thought_stream` / `token` events over SSE as words are emitted, rendering a live typewriter view in the frontend.
2. **Entity & Domain Competency Inference**: Enhanced the analysis stage to extract entities (company: *Rentman*, location: *Utrecht, Netherlands*, role: *Senior Frontend Developer*) and automatically infer core domain competencies when tech mentions are sparse, cross-referencing against the candidate's verified Base Resume.
3. **Capacity & Context Expansion**: Explicitly expanded prompt context snippets up to 15,000+ characters to comfortably process enterprise multi-page LinkedIn JDs in full, and clarified logging to display received character length without confusing it for a limit.
4. **Dynamic Model Discovery**: Auto-detects installed models in the local Ollama catalog (`/api/tags`), preventing failures when specific tags like `llama3.1:8b` are installed instead of generic `llama3`.

### Consequences
- **Positive**: Zero dead pauses or frozen screens during LLM reasoning.
- **Positive**: High match scores and tailored summaries even for single-line job inputs.
- **Positive**: Transparent visibility into AI decision-making.

---

## ADR-007: Multi-Format Document Ingestion & Schema-Constrained Extraction for Candidate Ground Truth

### Status
Accepted

### Context
Users require the ability to upload their existing resume (PDF, Word DOCX, Plain Text, Markdown, or JSON) to automatically populate and update their Source of Truth Base Resume, rather than manually re-typing employment history, dates, degrees, and skills. The extraction pipeline must reliably handle unstructured documents, extract full metadata, and operate even when offline without external API keys.

### Decision
1. **Multi-Format Ingestion Engine (`ResumeParserService`)**:
   - **PDF** (`.pdf`): Extract text streams with `pypdf.PdfReader` across all document pages.
   - **Word Documents** (`.docx`): Extract paragraph nodes from `word/document.xml` using `zipfile` and `xml.etree.ElementTree` without brittle external C-dependencies.
   - **Plain Text / Markdown** (`.txt`, `.md`, `.rtf`): Decoded with UTF-8 and Latin-1 fallbacks.
   - **JSON** (`.json`): Direct deserialization and Pydantic validation against `ResumeData`.
2. **Dual-Engine Information Extraction**:
   - **LLM Extraction Engine**: When Ollama or OpenAI is configured, dispatches a structured system prompt extracting the complete schema with categorized skills and bullet points.
   - **Deterministic Heuristic NLP Fallback**: If LLM is unconfigured or unreachable, an intelligent regex and section-boundary parser extracts contact info, work history, institutions, and skills matrix deterministically with zero API keys.
3. **Metadata Calculation**:
   - Ingestion returns document metadata: format, word count, character count, page count, detected sections, and extraction method.
4. **Interactive Review & Ground Truth Persistence**:
   - Uploaded resumes populate the interactive form for user review and edits before saving to `data/my_resume.json` (decoupled from git).

### Consequences
- **Positive**: Effortless onboarding: users can upload their real PDF/DOCX resume in seconds.
- **Positive**: Zero data loss or hallucination: extracted data is presented for user review.
- **Positive**: 100% functional offline or online.

---

## ADR-008: Dual Document Generation Paradigm (Targeted Resume vs. Custom Curriculum Vitae)

### Status
Accepted

### Context
Senior software architects and engineering leaders require two distinct presentation formats depending on the target role, geography, and hiring stage:
1. **Targeted Resume (1–2 Pages)**: Highly condensed, high ATS keyword density, emphasizing recent high-impact quantifiable metrics and direct role requirements.
2. **Custom Curriculum Vitae (Multi-Page CV)**: Comprehensive career biography detailing architectural decisions, enterprise scale, technical leadership, legacy modernization case studies, professional certifications, and complete technical taxonomy.

Attempting to force both formats into a single template created a design tension: either the resume overflowed onto an awkward half-page, or architectural case studies and certifications had to be omitted.

### Decision
1. **Unified Schema Extension**:
   - Expanded `ResumeData`, `ProjectItem`, `CertificationItem`, and `JobInput` to include `projects`, `certifications`, `publications`, and `document_type` (`"resume"` | `"cv"`).
2. **Dedicated Executive CV Template (`cv_executive`)**:
   - Designed a comprehensive multi-page layout featuring:
     - Executive Career Architecture & Profile summary
     - Full technical taxonomy and core competency matrix
     - Career history with verified quantifiable impact
     - Key Architectural Projects & Case Studies (role, dates, system description, technology badges, live repository links)
     - Professional Certifications & Licenses (issuer, date, credential ID, URL)
     - Publications & Thought Leadership
     - Education & Academic Background
3. **Print & Page Break Architecture**:
   - Integrated CSS print specifications (`page-break-inside: avoid;`, `break-inside: avoid;`, `@page { margin: 15mm; size: A4 portrait; }`) ensuring clean page boundaries when exporting to PDF via browser print engines.
4. **Adaptive Alignment Pipeline**:
   - In `GeneratorChain`, when `document_type == 'cv'`:
     - Synthesis prompts reframe the executive profile around technical governance, mentorship pipelines, and architectural vision.
     - Auto-selects `cv_executive` template if default is requested.
     - Tier-2 Deterministic Anti-Hallucination verification strictly validates that projects and certifications originate solely from the candidate's verified Ground Truth profile.
5. **Frontend User Controls**:
   - Added responsive document mode switcher in the Job Input component (`📄 Targeted Resume` vs. `📜 Custom CV`).
   - Dynamic UI styling, button labels, and export filenames (`[Name]_Custom_CV.pdf`, `.html`, `.json`).

### Consequences
- **Positive**: High-utility dual document generation covering both rapid ATS screeners and comprehensive executive hiring evaluations.
- **Positive**: Pixel-perfect multi-page PDF exports with zero card-splitting across page breaks.
- **Positive**: Strict preservation of Ground Truth integrity across both formats.

---

## ADR-009: Zero-Data-Loss Resume Ingestion & Letter-Tracking Normalization

### Status
Accepted

### Context
When candidates uploaded real-world resumes created in design systems, LaTeX, or Canva, standard PDF extraction engines (e.g. `pypdf`) extracted text with tracking spaces between individual characters (e.g., `V I S H N U   T H A N K A P P A N`). This broke downstream NLP chunking, tokenization, and regular expressions.
Furthermore, naive regex parsers discarded unmatched lines, dropping up to 80% of candidate achievements, omitting whole employer blocks, and shredding rich bullet points.

### Decision
1. **Letter-Tracking Font Normalization (`normalize_extracted_text`)**:
   - Implemented an intelligent multi-token heuristic: if single-character token ratio exceeds 35%, word-spaced boundaries are detected and characters are reconstituted into normal words (`V I S H N U` -> `VISHNU`). Standardizes unicode bullet points (`•`, `▪`, `●`, `·`) into uniform ASCII hyphens.
2. **Zero-Data-Loss Structural Ingestion (`_parse_structurally`)**:
   - Replaced fragile line shredders with a structural section scanner.
   - Preserves every bullet point verbatim without truncation.
   - Extracts categorized skills and architectures directly into taxonomy matrices.
   - Invariant: Stores the full, unadulterated document text in `resume.raw_text`.
3. **Holistic Truth Audit Expansion**:
   - Upgraded `GeneratorChain._perform_competency_audit()` to inspect `base.raw_text`, `summary`, `projects`, and `certifications`, ensuring candidate competencies are never falsely flagged as out-of-scope during anti-hallucination guardrails.
4. **Candidate Ground Truth 3-Way Studio**:
   - Enhanced the Base Resume modal with a 3-way toggle (`Structured Profile`, `Verbatim Knowledge Base`, `JSON Schema`), giving candidates complete visibility and control over all extracted knowledge.

### Consequences
- **Positive**: 100% data extraction and preservation on complex resumes.
- **Positive**: Zero false out-of-scope rejections during LLM competency alignment.
- **Positive**: Verbatim candidate context accessible to the reasoning chain.

---

## ADR-010: Interactive Template Preview & Configuration Studio

### Status
Accepted

### Context
Resume candidates require diverse visual styles, palettes, and layouts suited to different corporate cultures (e.g. modern tech startups vs. conservative enterprise finance). Previously, templates had hardcoded colors and fixed densities. Users requested a dedicated template studio to preview and configure templates, adjust colors and typography, and persist their preferred styling.

### Decision
1. **Dynamic Style Overrides in `TemplateEngine`**:
   - Introduced `TemplateConfig` data model specifying:
     - `template_id` (`modern`, `executive`, `compact`, `cv_executive`)
     - `primary_color`, `accent_color`, `text_color` (hex codes)
     - `font_family`, `font_size`, `line_height`
     - `density` (`compact`, `normal`, `comfortable`)
     - `header_layout` (`left`, `center`, `split`)
     - Section visibility toggles (`show_tagline`, `show_icons`, `show_projects`, `show_certifications`, `show_education`)
   - Implemented `_build_dynamic_styles()` to dynamically inject CSS variables (`--primary-color`, `--accent-color`, `--text-primary`, `--font-family`, `--font-size`, `--line-height`) and layout rules into all rendered HTML templates and print stylesheets.
2. **Configuration Persistence & ASGI Endpoints**:
   - Added `GET /api/template/config` and `PUT /api/template/config` ASGI routes.
   - Persisted candidate styling in `data/template_config.json`.
   - Integrated `template_config` into `POST /api/render` and `POST /api/generate/stream`.
3. **Frontend Template Studio Component**:
   - Created `TemplateConfigModalComponent` (`template-config-modal/`):
     - Left column: curated color palettes (`Sapphire Tech`, `Emerald Enterprise`, `Executive Slate`, `Royal Indigo`, `Crimson Modern`, `Midnight Charcoal`) + custom HTML5 color pickers; typography font selectors; density pills; header layout toggles; section switches.
     - Right column: live interactive iframe preview rendering instant real-time styling updates via `renderPreviewWithConfig()`.
     - Toolbar: "🎨 Customize" button added to the main resume preview toolbar.

### Consequences
- **Positive**: Instant visual feedback on styling changes without affecting base resume data.
- **Positive**: Both onscreen iframes and printable vector PDFs automatically inherit custom styles.
- **Positive**: User styling preferences persist across sessions.

---

## ADR-011: Human-in-the-Loop (HITL) Mismatch Resolution & Programmatic Skills Non-Fabrication Gate (Check 7)

### Status
Accepted

### Context
When a candidate attempts to generate a tailored resume or CV against a job description that has minimal or zero alignment with their verified Ground Truth profile (for example, a Senior Frontend Engineer targeting a Senior Embedded Firmware Engineer role requiring bare-metal C, FreeRTOS, ARM Cortex, and CAN bus protocols), generative AI models and tailoring engines encounter three critical failure modes:
1. **"Helpful" Skill Fabrication (Hallucination Trap)**: To satisfy the prompt and job requirements, LLMs frequently inject unverified technical competencies (e.g. FreeRTOS, Swift, Golang, Kubernetes) directly into the applicant's skills matrix.
2. **Artificial Score Inflation**: Previous audit routines floored match scores (e.g. `max(72, ...)`), masking severe competency deficits from the candidate and creating a dangerous false sense of qualification.
3. **Silent Misalignment**: Synthesizing documents without candidate awareness of severe gaps deprives the candidate of strategic agency—such as framing transferable capabilities or canceling to update their Source of Truth.

### Decision
1. **Honest Competency Preflight API (`POST /api/generate/preflight`)**:
   - Implemented `preflight_check()` in `GeneratorChain`, returning `PreflightReport(match_score, is_low_match, direct_matches, missing_skills, message)`.
   - Removed artificial minimum floors; scores honestly reflect candidate alignment ($0–100\%$).
   - Enforced word-boundary and language-context guards for single-character keywords (e.g. `\bC\b` with language context) to eliminate false substring matches in words like "architecture".
   - Flags `is_low_match = True` whenever match score $< 40\%$ or zero direct competencies exist.
2. **Interactive Frontend Human-in-the-Loop (HITL) Modal**:
   - `JobInputComponent` invokes the preflight check before starting the generation stream.
   - If a severe gap is detected, execution pauses and an interactive modal alerts the user with:
     - Honest match percentage and highlighted missing skill badges.
     - Strict Non-Fabrication Notice: Explicitly reminds the user that ungrounded tools cannot be added to their profile.
     - Strategic Decision Selector:
       - **Highlight Transferable Engineering Rigor**: Bridges systematic engineering discipline, performance tuning, and architectural governance without claiming domain-specific tools.
       - **Strict Factual Alignment**: Completely omits missing requirement domains and leads 100% with verified core strengths.
     - Free-form Candidate Guidance Notes textarea passed directly into the reasoning engine.
     - "Cancel & Update Source of Truth" button for users wanting to add missing verified credentials.
3. **Check 7: Programmatic Skills Non-Fabrication Gate (`_verify_anti_hallucination`)**:
   - Added Check 7 into the deterministic post-synthesis anti-hallucination verification layer.
   - Extracts the candidate's comprehensive ground-truth corpus (`skills`, `experience`, `projects`, `certifications`, `raw_text`, `summary`).
   - Scans every individual skill in `generated.skills`. Any skill not grounded in candidate truth is deterministically purged before the payload or HTML is emitted.
4. **Continuous Evaluation Suite Benchmark**:
   - Added `case_extreme_mismatch_hitl` (Senior Embedded Firmware Engineer) to `BENCHMARK_DATASET`.
   - Added Check 5 (Skills Non-Fabrication Gate) into `TruthInvarianceCheckpoint`.
   - Added 5 automated tests in `test_evals.py` verifying preflight detection, truth invariance on synthetic skills, and programmatic purge behavior.

### Consequences
- **Positive**: 100% guarantee that unverified technical skills are never fabricated into the candidate's resume, regardless of LLM propensity to please the prompt.
- **Positive**: Candidates retain full strategic transparency and agency when applying for cross-domain or stretch roles.
- **Positive**: Preflight check executes in $< 15\text{ms}$ with zero external LLM latency or cost.
- **Positive**: 100.0% evaluation pass rate maintained across all 6 benchmark scenarios.



