from __future__ import annotations

from app import config
import app.updater as updater
from app.updater import (
    _parse_latest_release,
    check_for_software_update,
    download_installer,
    is_newer_version,
)


class DummyResponse:
    def __init__(self, payload=None, content: bytes = b"", status_ok: bool = True, status_code: int = 200):
        self._payload = payload
        self.content = content
        self.status_ok = status_ok
        self.status_code = status_code

    def json(self):
        return self._payload

    def raise_for_status(self):
        if not self.status_ok:
            raise RuntimeError("http error")


def test_version_comparison_semver_ordering():
    assert is_newer_version("1.0.2", "1.0.1") is True
    assert is_newer_version("v1.2.0", "1.1.9") is True
    assert is_newer_version("1.0.2", "1.0.2") is False
    assert is_newer_version("1.0.1", "1.0.2") is False


def test_github_releases_url_not_placeholder():
    assert "OWNER" not in config.GITHUB_RELEASES_API_URL
    assert "REPOSITORY" not in config.GITHUB_RELEASES_API_URL


def test_release_parsing_windows_asset():
    payload = {
        "tag_name": "v1.2.0",
        "assets": [
            {
                "name": "SchoolInformationDashboardSetup.exe",
                "browser_download_url": "https://example.test/SchoolInformationDashboardSetup.exe",
            }
        ],
    }
    parsed = _parse_latest_release(payload, "Windows")
    assert parsed == {
        "version": "1.2.0",
        "name": "SchoolInformationDashboardSetup.exe",
        "url": "https://example.test/SchoolInformationDashboardSetup.exe",
    }


def test_release_parsing_returns_none_when_asset_missing():
    payload = {"tag_name": "v1.2.0", "assets": []}
    assert _parse_latest_release(payload, "Windows") is None


def test_software_update_check_handles_no_internet(monkeypatch):
    def offline_get(*_args, **_kwargs):
        raise updater.requests.exceptions.ConnectionError("network down")

    monkeypatch.setattr(updater.requests, "get", offline_get)
    result = check_for_software_update("1.2.0", "Windows")
    assert result.update_available is False
    assert "internet connection" in result.message.lower()


def test_software_update_check_current_equals_latest(monkeypatch):
    payload = {
        "tag_name": "v1.2.0",
        "assets": [{"name": "SchoolInformationDashboardSetup.exe", "browser_download_url": "https://example/v1.2.0.exe"}],
    }

    monkeypatch.setattr(updater.requests, "get", lambda *_args, **_kwargs: DummyResponse(payload=payload))
    result = check_for_software_update("1.2.0", "Windows")
    assert result.update_available is False
    assert "latest" in result.message.lower()


def test_software_update_check_newer_version_exists(monkeypatch):
    payload = {
        "tag_name": "v1.3.0",
        "assets": [{"name": "SchoolInformationDashboardSetup.exe", "browser_download_url": "https://example/v1.3.0.exe"}],
    }

    monkeypatch.setattr(updater.requests, "get", lambda *_args, **_kwargs: DummyResponse(payload=payload))
    result = check_for_software_update("1.2.0", "Windows")
    assert result.update_available is True
    assert result.latest_version == "1.3.0"
    assert result.installer_url == "https://example/v1.3.0.exe"


def test_software_update_check_when_asset_missing(monkeypatch):
    payload = {"tag_name": "v1.3.0", "assets": [{"name": "wrong.exe", "browser_download_url": "https://example/wrong.exe"}]}

    monkeypatch.setattr(updater.requests, "get", lambda *_args, **_kwargs: DummyResponse(payload=payload))
    result = check_for_software_update("1.2.0", "Windows")
    assert result.update_available is False
    assert "no compatible installer asset" in result.message.lower()


def test_software_update_check_invalid_placeholder_url():
    result = check_for_software_update(
        "1.2.2",
        "Windows",
        releases_api_url="https://api.github.com/repos/OWNER/REPOSITORY/releases/latest",
    )
    assert result.update_available is False
    assert "misconfigured" in result.message.lower()


def test_software_update_check_handles_rate_limiting(monkeypatch):
    monkeypatch.setattr(updater.requests, "get", lambda *_args, **_kwargs: DummyResponse(payload={}, status_code=403))
    result = check_for_software_update("1.2.2", "Windows")
    assert result.update_available is False
    assert "rate limit" in result.message.lower()


def test_download_installer_failure(monkeypatch, tmp_path):
    monkeypatch.setattr(updater.requests, "get", lambda *_args, **_kwargs: DummyResponse(status_ok=False))
    target = tmp_path / "setup.exe"
    try:
        download_installer("https://example/setup.exe", target)
    except RuntimeError as exc:
        assert "http error" in str(exc)
    else:
        raise AssertionError("Expected download_installer to fail")


def test_download_installer_success(monkeypatch, tmp_path):
    monkeypatch.setattr(updater.requests, "get", lambda *_args, **_kwargs: DummyResponse(content=b"binary"))
    target = tmp_path / "setup.exe"
    written = download_installer("https://example/setup.exe", target)
    assert written == target
    assert target.read_bytes() == b"binary"
