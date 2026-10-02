#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
# PYTHON_BIN can point to a dedicated Python 3.8-3.11 interpreter.
if [ -z "${PYTHON_BIN:-}" ]; then
  if [ -x "$HOME/miniconda3/envs/testidea/bin/python" ]; then
    PYTHON_BIN="$HOME/miniconda3/envs/testidea/bin/python"
  else
    PYTHON_BIN=python3
  fi
fi
if [ ! -x .venv/bin/python ]; then
  "$PYTHON_BIN" -m venv .venv
fi
.venv/bin/python -m pip --version >/dev/null || {
  echo 'Incomplete .venv: move it aside and recreate with Python 3.8-3.11 containing ensurepip.' >&2
  exit 1
}
if [ "${PIP_IPV4_ONLY:-0}" = "1" ]; then
  .venv/bin/python scripts/install_requirements.py
else
  .venv/bin/python -m pip install --timeout 15 --retries 1 -r requirements.txt
fi
.venv/bin/python -m unittest discover -s tests -v
run="outputs/smoke-$(date +%Y%m%d-%H%M%S)"
.venv/bin/python scripts/run_phase_a.py --config configs/smoke.json --output "$run"
.venv/bin/python scripts/plot_results.py "$run"
