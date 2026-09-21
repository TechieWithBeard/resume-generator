#!/usr/bin/env bash
# ==============================================================================
# AI-Powered Resume Generator — Turnkey 1-Command Setup & Runner
# Anyone can clone this repository and run this single command.
# Everything needed to run locally will be installed and configured automatically.
# ==============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

MODE="auto"
MODEL="${OLLAMA_MODEL:-llama3.2}"

# Parse optional arguments
for arg in "$@"; do
  case $arg in
    --docker)
      MODE="docker"
      shift
      ;;
    --native)
      MODE="native"
      shift
      ;;
    --model=*)
      MODEL="${arg#*=}"
      shift
      ;;
    --help|-h)
      echo "Usage: ./setup.sh [OPTIONS]"
      echo ""
      echo "Options:"
      echo "  --docker      Run using Docker Compose (includes automated Ollama + model puller)"
      echo "  --native      Run directly on host using Python venv & Node.js"
      echo "  --model=NAME  Specify Ollama model (default: llama3.2)"
      echo "  -h, --help    Show this help message"
      exit 0
      ;;
  esac
done

echo ""
echo "=============================================================================="
echo "✨ AI-Powered Resume Generator — Turnkey Launcher"
echo "=============================================================================="

# ------------------------------------------------------------------------------
# 1. Docker Mode Execution
# ------------------------------------------------------------------------------
if [ "$MODE" = "docker" ]; then
  echo "🐳 Launching via Docker Compose (Isolated Ollama + Model Puller + App)..."
  if ! command -v docker >/dev/null 2>&1; then
    echo "❌ Error: Docker is not installed or not in PATH."
    exit 1
  fi
  export OLLAMA_MODEL="$MODEL"
  exec docker compose up --build
fi

# In Auto mode, if user explicitly has docker running and no python/node, suggest or allow docker
if [ "$MODE" = "auto" ] && [ "$1" = "--docker" ]; then
  export OLLAMA_MODEL="$MODEL"
  exec docker compose up --build
fi

# ------------------------------------------------------------------------------
# 2. Native Host Setup & Run
# ------------------------------------------------------------------------------
echo "💻 Setting up local native environment..."

# A. Check & Prepare Ground Truth Resume File
mkdir -p "$SCRIPT_DIR/backend/data"
if [ ! -f "$SCRIPT_DIR/backend/data/my_resume.json" ]; then
  if [ -f "$SCRIPT_DIR/backend/data/default_base_resume.json" ]; then
    echo "📋 Initializing backend/data/my_resume.json from default base profile..."
    cp "$SCRIPT_DIR/backend/data/default_base_resume.json" "$SCRIPT_DIR/backend/data/my_resume.json"
  elif [ -f "$SCRIPT_DIR/backend/data/sample_resume.json" ]; then
    echo "📋 Initializing backend/data/my_resume.json from sample profile..."
    cp "$SCRIPT_DIR/backend/data/sample_resume.json" "$SCRIPT_DIR/backend/data/my_resume.json"
  fi
fi

# B. Check Python
PYTHON_BIN=""
for py in python3.11 python3.10 python3.9 python3; do
  if command -v $py >/dev/null 2>&1; then
    PY_VER=$($py -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    PY_MAJOR=$(echo "$PY_VER" | cut -d. -f1)
    PY_MINOR=$(echo "$PY_VER" | cut -d. -f2)
    if [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -ge 9 ]; then
      PYTHON_BIN="$py"
      break
    fi
  fi
done

if [ -z "$PYTHON_BIN" ]; then
  echo "❌ Error: Python 3.9 or higher is required. Please install Python 3.9+."
  exit 1
fi
echo "✓ Found Python: $($PYTHON_BIN --version)"

# C. Setup Virtual Environment
VENV_DIR=""
if [ -d "$SCRIPT_DIR/.venv" ]; then
  VENV_DIR="$SCRIPT_DIR/.venv"
elif [ -d "$SCRIPT_DIR/backend/venv" ]; then
  VENV_DIR="$SCRIPT_DIR/backend/venv"
elif [ -d "$SCRIPT_DIR/../../.venv" ]; then
  VENV_DIR="$SCRIPT_DIR/../../.venv"
else
  echo "📦 Creating Python virtual environment in .venv..."
  $PYTHON_BIN -m venv "$SCRIPT_DIR/.venv"
  VENV_DIR="$SCRIPT_DIR/.venv"
fi

echo "📦 Activating Python virtual environment ($VENV_DIR)..."
source "$VENV_DIR/bin/activate"

# D. Install Python Dependencies
echo "📥 Checking Python dependencies (backend/requirements.txt)..."
pip install -q --disable-pip-version-check -r "$SCRIPT_DIR/backend/requirements.txt"
echo "✓ Python dependencies verified."

# E. Check Node.js & Build Frontend
if [ ! -d "$SCRIPT_DIR/frontend/dist/frontend/browser" ]; then
  echo "🎨 Building Angular Frontend..."
  if ! command -v node >/dev/null 2>&1 || ! command -v npm >/dev/null 2>&1; then
    echo "⚠️ Node.js / npm not detected. Looking for pre-built frontend distribution..."
    if [ ! -d "$SCRIPT_DIR/frontend/dist" ]; then
      echo "❌ Error: Node.js and npm are required to build the frontend. Please install Node.js 18+."
      exit 1
    fi
  else
    cd "$SCRIPT_DIR/frontend"
    if [ ! -d "node_modules" ]; then
      echo "📥 Installing frontend dependencies..."
      npm install --silent
    fi
    echo "🔨 Compiling Angular production bundle..."
    npm run build
    cd "$SCRIPT_DIR"
  fi
else
  echo "✓ Angular frontend build verified."
fi

# F. Check Ollama (Local AI Model)
if command -v ollama >/dev/null 2>&1; then
  echo "🦙 Ollama detected on host system."
  # Check if Ollama daemon is running
  if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
    echo "✓ Ollama server is active on http://localhost:11434."
    if ! ollama list | grep -q "$MODEL"; then
      echo "📥 Pulling recommended local model '$MODEL' into Ollama (one-time setup)..."
      ollama pull "$MODEL"
    else
      echo "✓ Model '$MODEL' is already downloaded and ready in Ollama."
    fi
  else
    echo "ℹ️ Ollama is installed but not currently running. Starting Ollama in background..."
    (ollama serve >/dev/null 2>&1 &) || true
    sleep 2
    if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
      echo "✓ Ollama server started."
      if ! ollama list | grep -q "$MODEL"; then
        echo "📥 Pulling model '$MODEL'..."
        ollama pull "$MODEL" || true
      fi
    fi
  fi
else
  echo "ℹ️ Ollama not found on host. The app will run in hybrid mode (OpenAI key or built-in heuristic engine)."
  echo "💡 To use 100% offline local AI models anytime, install Ollama from https://ollama.com"
fi

# G. Launch Server and Open Browser
echo ""
echo "=============================================================================="
echo "🚀 Starting AI Resume Generator on http://localhost:8000"
echo "👉 Open your browser: http://localhost:8000"
echo "=============================================================================="

# Launch browser asynchronously after 1 second
(
  sleep 1.5
  if command -v open >/dev/null 2>&1; then
    open "http://localhost:8000"
  elif command -v xdg-open >/dev/null 2>&1; then
    xdg-open "http://localhost:8000"
  fi
) >/dev/null 2>&1 &

export PYTHONPATH="$SCRIPT_DIR"
export PORT="${PORT:-8000}"
export OLLAMA_MODEL="$MODEL"
exec python3 backend/run.py
