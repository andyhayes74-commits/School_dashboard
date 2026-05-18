"""Software update checks and installer download helpers."""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests
from app import config


@dataclass(frozen=True)
class SoftwareUpdateResult:
    update_available: bool
    message: str
    current_version: str
    latest_version: str | None = None
    installer_url: str | None = None
    installer_name: str | None = None


def check_for_software_update(
    current_version: str,
    platform_name: str,
    releases_api_url: str = config.GITHUB_RELEASES_API_URL,
    timeout: int = 15,
) -> SoftwareUpdateResult:
    if not config.AUTO_CHECK_SOFTWARE_UPDATES:
        return SoftwareUpdateResult(False, "Automatic software update checks are disabled.", current_version)
    if "OWNER" in releases_api_url or "REPOSITORY" in releases_api_url:
        return SoftwareUpdateResult(
            False,
            "Software update check is misconfigured: invalid GitHub Releases URL placeholder.",
            current_version,
        )

    try:
        response = requests.get(releases_api_url, timeout=timeout)
        if response.status_code == 403:
            return SoftwareUpdateResult(
                False,
                "GitHub API rate limit reached. Please try again later.",
                current_version,
            )
        response.raise_for_status()
        release = _parse_latest_release(response.json(), platform_name)
        if not release:
            return SoftwareUpdateResult(False, "No compatible installer asset found for this platform in the latest release.", current_version)

        latest_version = release["version"]
        if not is_newer_version(latest_version, current_version):
            return SoftwareUpdateResult(False, "You already have the latest software version.", current_version, latest_version)

        return SoftwareUpdateResult(
            True,
            f"Update available: v{latest_version}. Download ready when requested.",
            current_version,
            latest_version,
            release["url"],
            release["name"],
        )
    except requests.exceptions.ConnectionError as exc:
        return SoftwareUpdateResult(False, f"No internet connection for software update check. Details: {exc}", current_version)
    except requests.exceptions.Timeout as exc:
        return SoftwareUpdateResult(False, f"GitHub API request timed out. Details: {exc}", current_version)
    except requests.exceptions.HTTPError as exc:
        return SoftwareUpdateResult(False, f"GitHub API request failed. Details: {exc}", current_version)
    except ValueError as exc:
        return SoftwareUpdateResult(False, f"GitHub API response could not be parsed. Details: {exc}", current_version)
    except requests.exceptions.RequestException as exc:
        return SoftwareUpdateResult(False, f"Software update check request failed. Details: {exc}", current_version)
    except Exception as exc:
        return SoftwareUpdateResult(False, f"Software update check failed unexpectedly. Details: {exc}", current_version)


def _parse_latest_release(payload: Any, platform_name: str) -> dict[str, str] | None:
    if not isinstance(payload, dict):
        return None
    tag = str(payload.get("tag_name") or "").strip()
    version = _normalise_version(tag)
    assets = payload.get("assets")
    if not version or not isinstance(assets, list):
        return None

    if platform_name not in {"Windows", "Darwin"}:
        return None

    windows_installer_asset: dict[str, str] | None = None
    windows_portable_asset: dict[str, str] | None = None
    macos_asset: dict[str, str] | None = None

    for asset in assets:
        if not isinstance(asset, dict):
            continue
        name = asset.get("name")
        url = asset.get("browser_download_url")
        if not isinstance(name, str) or not isinstance(url, str):
            continue

        if platform_name == "Windows":
            if name == config.WINDOWS_INSTALLER_NAME:
                windows_installer_asset = {"version": version, "name": name, "url": url}
            elif name.startswith("SchoolDashboard-v") and name.endswith("-portable.zip"):
                windows_portable_asset = {"version": version, "name": name, "url": url}
        elif platform_name == "Darwin" and name == config.MACOS_INSTALLER_NAME:
            macos_asset = {"version": version, "name": name, "url": url}

    if platform_name == "Windows":
        return windows_installer_asset or windows_portable_asset
    return macos_asset


def _normalise_version(tag: str) -> str | None:
    m = re.fullmatch(r"v?(\d+)\.(\d+)\.(\d+)", tag)
    if not m:
        return None
    return ".".join(m.groups())


def is_newer_version(candidate: str, installed: str) -> bool:
    return _version_tuple(candidate) > _version_tuple(installed)


def _version_tuple(version: str) -> tuple[int, int, int]:
    clean = _normalise_version(version) or "0.0.0"
    return tuple(int(p) for p in clean.split("."))  # type: ignore[return-value]


def download_installer(installer_url: str, destination: Path, timeout: int = 30) -> Path:
    response = requests.get(installer_url, timeout=timeout)
    response.raise_for_status()
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(response.content)
    return destination


def install_downloaded_update(platform_name: str, installer_path: Path) -> str:
    if platform_name == "Windows":
        subprocess.Popen([str(installer_path)], shell=True)
        return "Installer launched. The app will now close so you can complete the update."
    if platform_name == "Darwin":
        subprocess.Popen(["open", str(installer_path)])
        return "DMG opened. Install the app from the mounted image, then reopen the dashboard."
    raise RuntimeError("Software updates are supported only on Windows and macOS.")
