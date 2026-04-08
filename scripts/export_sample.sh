#!/bin/zsh
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

if [ ! -x ".venv/bin/python" ]; then
  echo "未找到 .venv，请先运行 ./scripts/setup_local.sh"
  exit 1
fi

OUTPUT_DIR="examples/output/generated-local"
mkdir -p "$OUTPUT_DIR"

.venv/bin/python -m li_zhi_badge_maker render-project examples/sample_project.json --output-dir "$OUTPUT_DIR"

echo "示例输出目录: $ROOT_DIR/$OUTPUT_DIR"
