#!/usr/bin/env bash
# ==============================================================================
# One-Command Launcher for AI Resume Generator
# ==============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "============================================================"
echo "⚡ AI Resume Generator — Starting Unified Environment"
echo "============================================================"

# 1. Check Python environment
VENV_PATH=""
if [ -d "$SCRIPT_DIR/../../.venv" ]; then
    VENV_PATH="$SCRIPT_DIR/../../.venv"
elif [ -d "$SCRIPT_DIR/backend/venv" ]; then
    VENV_PATH="$SCRIPT_DIR/backend/venv"
elif [ -d "$SCRIPT_DIR/.venv" ]; then
    VENV_PATH="$SCRIPT_DIR/.venv"
fi

if [ -n "$VENV_PATH" ]; then
    echo "📦 Activating Python virtualenv at $VENV_PATH..."
    source "$VENV_PATH/bin/activate"
else
    echo "⚠️  No local virtualenv found. Using system python3."
fi

# 2. Check if frontend dist exists, if not build it
if [ ! -d "$SCRIPT_DIR/frontend/dist/frontend/browser" ]; then
    echo "🔨 Building Angular Frontend..."
    cd "$SCRIPT_DIR/frontend"
    NG_CLI_ANALYTICS=false ./node_modules/.bin/ng build
    cd "$SCRIPT_DIR"
fi

# 3. Launch unified server on port 8000
echo "🚀 Launching unified application server on http://localhost:8000"
echo "👉 Open your browser to: http://localhost:8000"
echo "Press Ctrl+C to stop."
echo "============================================================"

export PYTHONPATH="$SCRIPT_DIR"
python3 backend/run.py
