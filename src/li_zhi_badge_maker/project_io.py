from __future__ import annotations

import json
from pathlib import Path

from .models import BadgeRecord


PROJECT_VERSION = "1.0"


def save_project(project_path: str | Path, records: list[BadgeRecord]) -> None:
    path = Path(project_path)
    payload = {
        "version": PROJECT_VERSION,
        "records": [record.to_dict() for record in records],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def load_project(project_path: str | Path) -> list[BadgeRecord]:
    path = Path(project_path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    records = [BadgeRecord.from_dict(item) for item in payload.get("records", [])]
    for index, record in enumerate(records):
        record.ensure_defaults(index=index)
    return records

