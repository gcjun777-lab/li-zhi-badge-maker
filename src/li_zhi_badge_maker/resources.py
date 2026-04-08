from __future__ import annotations

from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_ROOT.parent.parent
ASSETS_DIR = PROJECT_ROOT / "assets"
TEMPLATES_DIR = ASSETS_DIR / "templates"
FONTS_DIR = ASSETS_DIR / "fonts"

LOWER_TEMPLATE = TEMPLATES_DIR / "lower.png"
UPPER_TEMPLATE = TEMPLATES_DIR / "upper.png"
DEFAULT_FONT = FONTS_DIR / "Alibaba-PuHuiTi-Medium.otf"


def resolve_path(raw_path: str | Path) -> Path:
    path = Path(raw_path)
    if path.is_absolute():
        return path
    return (PROJECT_ROOT / path).resolve()


def ensure_assets_exist() -> None:
    missing = [path for path in (LOWER_TEMPLATE, UPPER_TEMPLATE, DEFAULT_FONT) if not path.exists()]
    if missing:
        joined = ", ".join(str(path) for path in missing)
        raise FileNotFoundError(f"缺少必要资源文件: {joined}")

