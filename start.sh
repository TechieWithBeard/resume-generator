#!/usr/bin/env bash
# ==============================================================================
# One-Command Launcher for AI Resume Generator
# Automatically delegates to setup.sh for turnkey dependency management & execution.
# ==============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "$SCRIPT_DIR/setup.sh" "$@"
