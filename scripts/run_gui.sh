#!/bin/zsh
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

if [ ! -x ".venv/bin/python" ]; then
  echo "未找到 .venv，请先运行 ./scripts/setup_local.sh"
  exit 1
fi

exec .venv/bin/python -m li_zhi_badge_maker gui

