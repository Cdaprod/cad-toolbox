#!/usr/bin/env bash
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$ROOT"

python3 -m venv .venv
source .venv/bin/activate

python -m pip install -U pip
python -m pip install -r recipes/finger-button-fixture/requirements.txt

echo
echo "Installed."
echo
echo "Try:"
echo "  source .venv/bin/activate"
echo "  python recipes/finger-button-fixture/generate_fixture.py --help"
echo "  python recipes/finger-button-fixture/generate_fixture.py"
