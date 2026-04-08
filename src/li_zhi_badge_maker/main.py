from __future__ import annotations

import sys

from .cli import build_parser, run_render_project


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command in (None, "gui"):
        from .gui import run_gui

        return run_gui()
    if args.command == "render-project":
        return run_render_project(args.project, args.output_dir)
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

