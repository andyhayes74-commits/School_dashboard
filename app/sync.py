"""Offline-safe GitHub data synchronisation."""

from __future__ import annotations

import importlib
import importlib.util
import json
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

requests = importlib.import_module("requests") if importlib.util.find_spec("requests") else None

from app import config
from app.data_loader import DataValidationError, load_schools_excel
from app.utils import load_json_file


@dataclass(frozen=True)
class SyncResult:
    updated: bool
    message: str
    local_version: str | None = None
    remote_version: str | None = None


def check_for_updates(
    cache_dir: Path,
    remote_version_url: str = config.REMOTE_VERSION_URL,
    remote_excel_url: str = config.REMOTE_EXCEL_URL,
    timeout: int = 15,
) -> SyncResult:
    """Check GitHub for newer data and update cache only after validation."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    local_version_path = cache_dir / config.VERSION_FILENAME
    local_excel_path = cache_dir / config.EXCEL_FILENAME
    local_version = load_json_file(local_version_path)
    local_data_version = _version_value(local_version)

    if requests is None:
        return SyncResult(False, "Update failed, so cached data was kept. Details: requests is not installed", local_data_version)

    try:
        remote_version = _download_json(remote_version_url, timeout)
        remote_data_version = _version_value(remote_version)
        if not remote_data_version:
            return SyncResult(False, "Remote version information is invalid. Cached data was kept.", local_data_version)

        if remote_data_version == local_data_version:
            return SyncResult(False, "You already have the latest cached school data.", local_data_version, remote_data_version)

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            downloaded_excel = temp_path / config.EXCEL_FILENAME
            downloaded_version = temp_path / config.VERSION_FILENAME
            _download_file(remote_excel_url, downloaded_excel, timeout)
            load_schools_excel(downloaded_excel)
            downloaded_version.write_text(json.dumps(remote_version, indent=2), encoding="utf-8")
            shutil.copy2(downloaded_excel, local_excel_path)
            shutil.copy2(downloaded_version, local_version_path)

        return SyncResult(True, "School data was updated successfully.", local_data_version, remote_data_version)
    except (requests.RequestException, OSError, DataValidationError, json.JSONDecodeError) as exc:  # type: ignore[union-attr]
        return SyncResult(False, f"Update failed, so cached data was kept. Details: {exc}", local_data_version)


def _download_json(url: str, timeout: int) -> dict[str, Any]:
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    data = response.json()
    if not isinstance(data, dict):
        raise json.JSONDecodeError("Remote version JSON must be an object", response.text, 0)
    return data


def _download_file(url: str, destination: Path, timeout: int) -> None:
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    destination.write_bytes(response.content)


def _version_value(version_data: dict[str, Any]) -> str | None:
    value = version_data.get("data_version")
    return str(value) if value else None
