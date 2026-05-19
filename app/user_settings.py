from __future__ import annotations

import json
from pathlib import Path


def load_user_settings(path: Path) -> dict[str, bool]:
    defaults = {"dark_mode": False}
    try:
        if not path.exists():
            return defaults
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            return {"dark_mode": bool(payload.get("dark_mode", False))}
    except Exception:
        pass
    return defaults


def save_user_settings(path: Path, settings: dict[str, bool]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(settings, indent=2), encoding="utf-8")
