#!/usr/bin/env python3
"""
Launcher script for AI Resume Generator Backend.
Runs Uvicorn on port 8000.
"""

import sys
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import uvicorn

if __name__ == "__main__":
    port = 8000
    print(f"🚀 Starting AI Resume Generator Engine on http://localhost:{port}")
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=port, reload=True)
