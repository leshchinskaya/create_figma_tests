#!/bin/bash

set -e

# Determine project root
ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Check if python3 is available
if command -v python3 > /dev/null 2>&1; then
    PYTHON=python3
else
    # Install Homebrew if missing
    if ! command -v brew > /dev/null 2>&1; then
        echo "Homebrew not found. Installing Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    fi

    echo "Installing Python via Homebrew..."
    brew install python
    PYTHON=python3
fi

VENV_DIR="$ROOT_DIR/venv"
if [ ! -d "$VENV_DIR" ]; then
    "$PYTHON" -m venv "$VENV_DIR"
fi

PIP="$VENV_DIR/bin/pip"
"$PIP" install -r "$ROOT_DIR/requirements.txt"

# Make the main scripts executable
chmod +x "$ROOT_DIR/send_figma_tests_all_tests.py" \
        "$ROOT_DIR/create_final_tests/create_final_promt.py" \
        "$ROOT_DIR/send_final_tests.py"

echo "✅ Environment setup complete."
