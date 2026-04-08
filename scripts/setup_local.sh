#!/bin/zsh
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi

.venv/bin/pip install --upgrade pip setuptools wheel
.venv/bin/pip install --no-build-isolation -r requirements.txt -e .

echo "本地环境准备完成。"
echo "启动 GUI: ./scripts/run_gui.sh"
echo "导出示例: ./scripts/export_sample.sh"

