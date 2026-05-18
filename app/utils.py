"""Cross-platform utility helpers for paths, bundled resources, and metadata."""

from __future__ import annotations

import json
import os
import platform
import shutil
import sys
from pathlib import Path
from typing import Any

from app import config
from app.sample_excel import generate_sample_xlsx


def resource_path(*parts: str) -> Path:
    """Return a path to a bundled resource in source or PyInstaller mode."""
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))
    return base.joinpath(*parts)


def get_cache_data_dir(system_name: str | None = None) -> Path:
    """Return the platform-specific writable cache data directory."""
    system = system_name or platform.system()
    if system == "Windows":
        local_app_data = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
        return Path(local_app_data) / config.CACHE_APP_DIR_NAME / config.DATA_DIR_NAME
    if system == "Darwin":
        return (
            Path.home()
            / "Library"
            / "Application Support"
            / config.CACHE_APP_DIR_NAME
            / config.DATA_DIR_NAME
        )
    xdg_data_home = os.environ.get("XDG_DATA_HOME")
    base = Path(xdg_data_home) if xdg_data_home else Path.home() / ".local" / "share"
    return base / config.CACHE_APP_DIR_NAME / config.DATA_DIR_NAME


def ensure_cache_files(cache_dir: Path | None = None) -> Path:
    """Ensure the cache directory and bundled fallback data files exist."""
    target_dir = cache_dir or get_cache_data_dir()
    target_dir.mkdir(parents=True, exist_ok=True)

    _ensure_cached_excel(target_dir)

    target_version = target_dir / config.VERSION_FILENAME
    if not target_version.exists():
        bundled_version = resource_path(config.DATA_DIR_NAME, config.VERSION_FILENAME)
        if not bundled_version.exists():
            raise FileNotFoundError(f"Bundled fallback file is missing: {bundled_version}")
        shutil.copy2(bundled_version, target_version)
    return target_dir


def _ensure_cached_excel(target_dir: Path) -> None:
    target_excel = target_dir / config.EXCEL_FILENAME
    if target_excel.exists():
        return

    bundled_excel = resource_path(config.DATA_DIR_NAME, config.EXCEL_FILENAME)
    if bundled_excel.exists():
        shutil.copy2(bundled_excel, target_excel)
        return

    bundled_csv = resource_path(config.DATA_DIR_NAME, config.CSV_SAMPLE_FILENAME)
    if bundled_csv.exists():
        generate_sample_xlsx(bundled_csv, target_excel)
        return

    raise FileNotFoundError(
        f"Bundled fallback data is missing: expected {bundled_excel} or {bundled_csv}"
    )


def load_json_file(path: Path) -> dict[str, Any]:
    """Load a JSON file, returning an empty dict if it is missing or invalid."""
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
            return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def readable_label(column_name: str) -> str:
    """Convert snake_case or machine-style column names into display labels."""
    return column_name.replace("_", " ").strip().title()


def is_probable_email(value: str) -> bool:
    return "@" in value and "." in value and " " not in value


def normalise_url(value: str) -> str:
    if value.startswith(("http://", "https://")):
        return value
    return f"https://{value}"
