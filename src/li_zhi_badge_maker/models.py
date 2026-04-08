from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path


DEFAULT_SUBHEADLINE = "感恩有您  前程似锦"


def infer_name_from_path(image_path: str | Path) -> str:
    stem = Path(image_path).stem.strip()
    stem = stem.lstrip("0123456789-_ ")
    if not stem:
        return "未命名"
    return stem


def build_headline(days: str | int) -> str:
    return f"和奥马一起走过{days}天"


@dataclass
class BadgeRecord:
    image_path: str
    name: str
    days: str = ""
    headline: str = ""
    subheadline: str = DEFAULT_SUBHEADLINE
    output_name: str = ""
    scale_adjust: float = 1.0
    x_offset: int = 0
    y_offset: int = 0

    def ensure_defaults(self, index: int | None = None) -> None:
        if not self.name:
            self.name = infer_name_from_path(self.image_path)
        if not self.headline:
            self.headline = build_headline(self.days or "")
        if not self.output_name:
            prefix = f"{index + 1:02d} " if index is not None else ""
            self.output_name = f"{prefix}{self.name}-离职厂牌-.png"

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "BadgeRecord":
        record = cls(**data)
        record.ensure_defaults()
        return record

