#!/usr/bin/env bash
# Install project deps, pytest, and the Claude Code CLI after the codespace is created.
# Runs as the non-root vscode user in a non-interactive shell.
set -euo pipefail

cd "$(dirname "$0")/.."

# The Python dev container image does not let vscode write the system site-packages.
python -m pip install --user --upgrade pip
python -m pip install --user -r requirements.txt
python -m pip install --user -e .
python -m pip install --user pytest

# The node feature puts npm on PATH via /usr/local/share/nvm/current/bin.
# Non-interactive shells still need nvm sourced when that symlink is absent.
if ! command -v npm >/dev/null 2>&1; then
  export NVM_DIR="${NVM_DIR:-/usr/local/share/nvm}"
  # shellcheck disable=SC1091
  . "${NVM_DIR}/nvm.sh"
fi
npm install -g @anthropic-ai/claude-code
