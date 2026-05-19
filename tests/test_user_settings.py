from pathlib import Path

import requests

from app.user_settings import load_user_settings, save_user_settings
from app.updater import check_for_software_update
import app.updater as updater


class DummyResponse:
    def __init__(self, status_code: int):
        self.status_code = status_code

    def raise_for_status(self):
        err = requests.exceptions.HTTPError("not found")
        err.response = self
        raise err


def test_user_settings_defaults_when_missing(tmp_path: Path):
    assert load_user_settings(tmp_path / "user_settings.json") == {"dark_mode": False}


def test_user_settings_save_and_load_round_trip(tmp_path: Path):
    path = tmp_path / "user_settings.json"
    save_user_settings(path, {"dark_mode": True})
    assert load_user_settings(path) == {"dark_mode": True}


def test_user_settings_invalid_json_falls_back_to_default(tmp_path: Path):
    path = tmp_path / "user_settings.json"
    path.write_text("{bad", encoding="utf-8")
    assert load_user_settings(path) == {"dark_mode": False}


def test_software_update_check_404_message(monkeypatch):
    monkeypatch.setattr(updater.requests, "get", lambda *_args, **_kwargs: DummyResponse(status_code=404))
    result = check_for_software_update("1.2.4", "Windows")
    assert result.update_available is False
    assert "Update source not found" in result.message
