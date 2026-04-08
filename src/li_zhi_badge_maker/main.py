from __future__ import annotations

import sys
from pathlib import Path


if __package__ in (None, ""):
    # Support running as a plain script inside a PyInstaller bundle.
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from li_zhi_badge_maker.cli import build_parser, run_render_project
else:
    from .cli import build_parser, run_render_project


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command in (None, "gui"):
        if __package__ in (None, ""):
            from li_zhi_badge_maker.gui import run_gui
        else:
            from .gui import run_gui

        return run_gui()
    if args.command == "render-project":
        return run_render_project(args.project, args.output_dir)
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
