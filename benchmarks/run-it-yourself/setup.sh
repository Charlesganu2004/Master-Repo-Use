#!/usr/bin/env bash
# Set up the 600-token harness test on macOS or Linux.
#
#   bash benchmarks/run-it-yourself/setup.sh
#
# Installs graphify into its own virtual environment under your home folder,
# indexes this repository locally (no API key, nothing leaves the machine), and
# writes the eight prompts.
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo="$(cd "$here/../.." && pwd)"
venv="$HOME/.graphify/venv"
exe="$venv/bin/graphify"

echo "1. graphify"
if [ -x "$exe" ]; then
  echo "   already installed: $("$exe" --version)"
else
  mkdir -p "$HOME/.graphify"
  python3 -m venv "$venv"
  "$venv/bin/python" -m pip install --quiet --disable-pip-version-check graphifyy
  echo "   installed: $("$exe" --version)"
fi

if [ -d "$HOME/.local/bin" ]; then
  ln -sf "$exe" "$HOME/.local/bin/graphify"
  echo "   linked into ~/.local/bin"
fi

echo "2. index this repository (local AST only, no model)"
"$exe" extract "$repo" --code-only --no-cluster | tail -2

echo "3. write the prompts"
python3 "$here/harness/build_arms.py"

cat <<'NEXT'

Ready. Next:
  - paste any file from benchmarks/run-it-yourself/arms/<task>/<arm>.prompt.md into your assistant
  - save each reply as benchmarks/run-it-yourself/answers/<task>/<arm>.md
  - python3 benchmarks/run-it-yourself/harness/score.py
NEXT
