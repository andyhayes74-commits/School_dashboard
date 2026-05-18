from __future__ import annotations

from app.updater import _parse_latest_release, is_newer_version


def test_version_comparison_semver_ordering():
    assert is_newer_version("1.0.2", "1.0.1") is True
    assert is_newer_version("v1.2.0", "1.1.9") is True
    assert is_newer_version("1.0.2", "1.0.2") is False
    assert is_newer_version("1.0.1", "1.0.2") is False


def test_release_parsing_windows_asset():
    payload = {
        "tag_name": "v1.0.3",
        "assets": [
            {
                "name": "SchoolInformationDashboardSetup.exe",
                "browser_download_url": "https://example.test/SchoolInformationDashboardSetup.exe",
            }
        ],
    }
    parsed = _parse_latest_release(payload, "Windows")
    assert parsed == {
        "version": "1.0.3",
        "name": "SchoolInformationDashboardSetup.exe",
        "url": "https://example.test/SchoolInformationDashboardSetup.exe",
    }


def test_release_parsing_macos_asset():
    payload = {
        "tag_name": "v1.0.3",
        "assets": [
            {
                "name": "SchoolInformationDashboard-macOS.dmg",
                "browser_download_url": "https://example.test/SchoolInformationDashboard-macOS.dmg",
            }
        ],
    }
    parsed = _parse_latest_release(payload, "Darwin")
    assert parsed and parsed["name"].endswith(".dmg")


def test_release_parsing_returns_none_when_asset_missing():
    payload = {"tag_name": "v1.0.3", "assets": []}
    assert _parse_latest_release(payload, "Windows") is None
