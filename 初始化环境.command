#!/bin/zsh
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR"

./scripts/setup_local.sh

echo
echo "环境初始化完成，按任意键退出。"
read -n 1

