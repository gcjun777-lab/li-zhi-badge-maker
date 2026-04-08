from __future__ import annotations

from datetime import date
from dataclasses import asdict, dataclass, fields
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


def calculate_days_from_join_date(join_date: str, today: date | None = None) -> str:
    if not join_date:
        return ""
    current_day = today or date.today()
    try:
        start_day = date.fromisoformat(join_date)
    except ValueError:
        return ""
    if start_day > current_day:
        return "0"
    return str((current_day - start_day).days)


@dataclass
class BadgeRecord:
    image_path: str
    name: str
    join_date: str = ""
    days: str = ""
    output_name: str = ""
    scale_adjust: float = 1.0
    x_offset: int = 0
    y_offset: int = 0

    def ensure_defaults(self, index: int | None = None) -> None:
        if not self.name:
            self.name = infer_name_from_path(self.image_path)
        if not self.days and self.join_date:
            self.days = calculate_days_from_join_date(self.join_date)
        if not self.output_name:
            self.output_name = f"{self.name}-离职厂牌-.png"

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "BadgeRecord":
        valid_names = {field.name for field in fields(cls)}
        filtered = {key: value for key, value in data.items() if key in valid_names}
        record = cls(**filtered)
        record.ensure_defaults()
        return record
