#!/bin/bash
# Double-click this file on a Mac to start the project dashboard.
cd "$(dirname "$0")" || exit 1

PY=""
for candidate in python3 python; do
  if command -v "$candidate" >/dev/null 2>&1 && \
     "$candidate" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' 2>/dev/null; then
    PY="$candidate"; break
  fi
done
if [ -z "$PY" ]; then
  echo
  echo "Python 3.10 or newer is not installed."
  echo "Install it from https://www.python.org/downloads/ and double-click this file again."
  echo
  read -r -p "Press Enter to close this window."
  exit 1
fi

if [ ! -x ".venv/bin/python" ]; then
  echo "First start: setting things up. This takes a few minutes and needs the internet."
  "$PY" -m venv .venv || { read -r -p "Set-up failed. Press Enter to close."; exit 1; }
fi
if ! .venv/bin/python -c "import streamlit, pandas, openpyxl, yaml" 2>/dev/null; then
  .venv/bin/python -m pip install --quiet --upgrade pip
  .venv/bin/python -m pip install --quiet -r requirements.txt || {
    echo "Installing the required packages failed. Check the internet connection and try again."
    read -r -p "Press Enter to close this window."
    exit 1
  }
fi

.venv/bin/python run.py
