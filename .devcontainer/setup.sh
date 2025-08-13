#!/usr/bin/env bash
set -euo pipefail

echo "▶ Setting up Python environment"

# Resolve repo root relative to this script to avoid hardcoded paths
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
SRC_DIR="${REPO_ROOT}/src"

cd "${SRC_DIR}"

# Create venv if it doesn't exist (non-interactive)
if [[ ! -d .venv ]]; then
	echo "▶ Creating venv at ${SRC_DIR}/.venv"
	python3 -m venv .venv
fi

# Activate venv
source .venv/bin/activate

# Ensure pip exists in the venv
if ! python -m pip --version >/dev/null 2>&1; then
	echo "▶ Bootstrapping pip in venv"
	if ! python -m ensurepip --upgrade >/dev/null 2>&1; then
		echo "⚠ ensurepip not available; using get-pip.py"
		curl -fsSL https://bootstrap.pypa.io/get-pip.py -o /tmp/get-pip.py
		python /tmp/get-pip.py
		rm -f /tmp/get-pip.py
	fi
fi

# Ensure modern tooling
python -m pip install --upgrade pip setuptools wheel

echo "▶ Installing dependencies with pip"
pip install -r requirements.txt

echo "✅ Python environment ready"
