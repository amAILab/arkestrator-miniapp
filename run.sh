#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
export ARKESTRATOR_PORT="${ARKESTRATOR_PORT:-8791}"
python3 app.py
