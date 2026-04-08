from __future__ import annotations

import argparse
from pathlib import Path

from .engine import export_badge
from .project_io import load_project


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="离职厂牌制作助手")
    subparsers = parser.add_subparsers(dest="command")

    render_parser = subparsers.add_parser("render-project", help="读取 JSON 工程文件并批量导出")
    render_parser.add_argument("project", help="工程 JSON 路径")
    render_parser.add_argument("--output-dir", required=True, help="输出目录")

    subparsers.add_parser("gui", help="启动图形界面")
    return parser


def run_render_project(project_path: str, output_dir: str) -> int:
    records = load_project(project_path)
    root = Path(output_dir)
    for record in records:
        export_badge(record, root)
    print(f"已导出 {len(records)} 张图片到 {root}")
    return 0

