# 🚀 Installation & Running Guide

This guide describes how to run the **AI-Powered Resume & CV Generator** on any machine (macOS, Linux, Windows).

---

## ⚡ Option 1: Docker (Fastest & 100% Zero Configuration)

With Docker, the entire stack—including **Ollama**, the **AI model (`llama3.2`)**, the **FastAPI backend**, and the **Angular 22 frontend**—is downloaded, configured, and started with **one command**.

### 1. Clone & Run
```bash
git clone https://github.com/TechieWithBeard/resume-generator.git
cd resume-generator

# Start the full stack with automated Ollama & model setup
docker compose up --build
```

### What happens automatically:
1. **Ollama Container Starts**: Boots official Ollama service with persistent storage (`ollama_data`).
2. **Automated Model Provisioner Runs**: Checks whether the target model (`llama3.2`) is downloaded. If not, automatically downloads and caches it (~2.0 GB).
3. **App Container Builds & Starts**: Compiles the Angular frontend and spins up the FastAPI / LangChain backend on port `8000`.
4. **Browser Ready**: Open **[http://localhost:8000](http://localhost:8000)**.

> [!TIP]
> **Custom AI Models**: To run a different model (e.g., `mistral`, `llama3.1:8b`, or `phi3`), simply specify `OLLAMA_MODEL`:
> ```bash
> OLLAMA_MODEL=mistral docker compose up --build
> ```

---

## 💻 Option 2: Turnkey Host Script (`./setup.sh`)

If you prefer running natively without Docker, our turnkey launcher script handles environment checking, Python virtualenv creation, package installation, frontend building, and Ollama verification:

```bash
# Clone the repository
git clone https://github.com/TechieWithBeard/resume-generator.git
cd resume-generator

# Run the single-command setup
./setup.sh
```

### What the script does:
1. Detects Python 3.9+ and creates an isolated virtual environment (`.venv`) if not present.
2. Installs backend dependencies (`backend/requirements.txt`).
3. Compiles the Angular production bundle (if Node.js is present).
4. Detects Ollama on your system:
   - If installed and running, verifies `llama3.2` is downloaded (or pulls it).
   - If not installed, seamlessly falls back to hybrid mode (OpenAI API key or built-in zero-config heuristic engine).
5. Launches the server on **[http://localhost:8000](http://localhost:8000)** and opens your default browser.

---

## 🛡️ Step-by-Step Workflow: Using the Application

### 1. Load Your Source of Truth (Ground Truth)
- When opening the application for the first time, look at the **Source of Truth** card at the top of the input pane.
- Click **"Load Resume"** or **"Review"**.
- Upload your verified resume (PDF, DOCX, TXT, or JSON) or review the default profile.
- Verify your verified contact information, past roles, and skills.
- Click **"Save Ground Truth"**.

> [!IMPORTANT]
> The AI strictly obeys the **Zero-Hallucination Invariant**. It will **never** invent fake employers, fabricate degrees, or drop verified skills. Grounding your tailored application in factual data requires having your Source of Truth loaded first!

### 2. Enter Job Requirements
- Paste the target job description or requirements in the text area.
- (Optional) Paste a LinkedIn Job URL and click **"⚡ Extract"** to auto-fill the role title and requirements.

### 3. Generate Tailored Documents (with Preflight HITL Protection)
- Choose **"Targeted Resume"** (condensed 1–2 page ATS format) or **"Custom CV"** (bespoke executive curriculum vitae with company research).
- Click **"✨ Generate Tailored ATS Resume"**.
- **Human-in-the-Loop Mismatch Guard**: If the job requirements significantly diverge from your verified profile ($<40\%$ match), an interactive **Role Competency Gap Detected** dialog will appear.
  - Select your strategy: **Highlight Transferable Engineering Rigor** or **Strict Factual Alignment**.
  - (Optional) Provide custom guidance notes to direct the AI's emphasis.
  - Or click **Cancel & Update Source of Truth** to add verified skills you hadn't listed.
- Watch real-time streaming AI decisions as your achievements are realigned to job requirements!
- **Strict Skills Non-Fabrication Gate (Check 7)** ensures ungrounded technical skills are never hallucinated.

### 4. Customize Styling & Export
- Open **Template Studio** to toggle layouts, color palettes, fonts, density, or custom CSS.
- Check the **9-Dimension Resume Score** to ensure your resume scores an **A+ (95–100%)**.
- Click **"Download PDF"** for clean vector printing.

---

## ⚙️ Environment Variables (Optional)

You can customize runtime behavior by creating a `.env` file in the root directory:

| Variable | Default | Description |
|---|---|---|
| `PORT` | `8000` | Port for the unified web server |
| `OLLAMA_BASE_URL` | `http://localhost:11434` (or `http://ollama:11434` in Docker) | Ollama API endpoint |
| `OLLAMA_MODEL` | `llama3.2` | Local LLM model name |
| `OPENAI_API_KEY` | `""` | (Optional) OpenAI API key for GPT-4o / GPT-4o-mini |
| `RESUME_DATA_PATH` | `backend/data/my_resume.json` | Path to candidate Ground Truth JSON profile |

---

## 🧪 Running Verification Tests & Continuous Evals

To verify that the entire backend engine, preflight guards, and evaluation benchmarks pass:

```bash
# Run all 46 backend unit, E2E, and regression tests
PYTHONPATH=. python -m unittest discover -s backend/tests -p "test_*.py" -v

# Run 6-case evaluation benchmark suite across all 5 checkpoints
python backend/run_evals.py --format terminal

# Run evaluation suite unit tests
python -m unittest backend/tests/test_evals.py -v
```

