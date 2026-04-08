#!/bin/zsh
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR"

if [ ! -x ".venv/bin/python" ]; then
  ./scripts/setup_local.sh
fi

exec ./scripts/run_gui.sh

