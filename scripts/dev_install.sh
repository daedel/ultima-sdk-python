#!/usr/bin/env bash
VENV_PATH="${1:-.venv}"

if [ ! -d "$VENV_PATH" ]; then
  echo "Virtualenv not found at $VENV_PATH — creating..."
  python -m venv "$VENV_PATH"
fi

echo "Activating virtualenv from $VENV_PATH"
# shellcheck source=/dev/null
source "$VENV_PATH/bin/activate"

echo "Upgrading pip and installing package in editable mode..."
python -m pip install --upgrade pip
python -m pip install -e .

echo "Done. Run 'pytest -q' to run tests."
