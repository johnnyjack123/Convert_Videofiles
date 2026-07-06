#!/usr/bin/env bash
set -e

cd "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

VENV_DIR="venv"

PYTHON=python3
if ! command -v python3 >/dev/null 2>&1; then
    PYTHON=python
fi

if [ ! -f "$VENV_DIR/bin/activate" ]; then
    echo "Creating virtual environment..."
    "$PYTHON" -m venv "$VENV_DIR"

    source "$VENV_DIR/bin/activate"

    echo "Installing requirements..."
    pip install -r requirements.txt
else
    source "$VENV_DIR/bin/activate"
fi

python main.py "$@"
