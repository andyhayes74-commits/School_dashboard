from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from app import config
from app.data_loader import DataValidationError, dataframe_to_school_records, load_schools_excel, validate_school_records
from app.sample_excel import generate_sample_xlsx
from app.sync import check_for_updates
from app.utils import ensure_cache_files, get_cache_data_dir


ROOT = Path(__file__).resolve().parents[1]
SAMPLE_CSV = ROOT / "data" / "schools.csv"


@pytest.fixture()
def sample_excel(tmp_path: Path) -> Path:
    return generate_sample_xlsx(SAMPLE_CSV, tmp_path / config.EXCEL_FILENAME)


def test_valid_sample_excel_loads(sample_excel: Path):
    data = load_schools_excel(sample_excel)
    records = dataframe_to_school_records(data)
    assert len(records) >= 3
    assert records[0]["school_id"] == "SCH001"
    assert records[0]["school_name"] == "Bluewater Primary School"


def test_required_columns_are_detected(sample_excel: Path):
    data = load_schools_excel(sample_excel)
    records = dataframe_to_school_records(data)
    assert set(config.REQUIRED_COLUMNS).issubset(records[0].keys())


def test_missing_required_columns_raises_friendly_validation_error():
    with pytest.raises(DataValidationError, match="missing required column"):
        validate_school_records(["school_id", "address"], [{"school_id": "SCH001", "address": "Somewhere"}])


def test_blank_values_are_normalised_to_not_provided():
    table = validate_school_records(
        ["school_id", "school_name", "email", "notes"],
        [{"school_id": "SCH001", "school_name": "Test School", "email": "", "notes": None}],
    )
    assert table.rows[0]["email"] == config.NOT_PROVIDED
    assert table.rows[0]["notes"] == config.NOT_PROVIDED


def test_extra_columns_are_preserved():
    table = validate_school_records(
        ["school_id", "school_name", "custom_field"],
        [{"school_id": "SCH001", "school_name": "Test School", "custom_field": "Custom value"}],
    )
    assert "custom_field" in table.columns
    assert table.rows[0]["custom_field"] == "Custom value"


def test_cache_path_function_for_supported_platforms(monkeypatch, tmp_path):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "LocalAppData"))
    assert get_cache_data_dir("Windows") == tmp_path / "LocalAppData" / "SchoolInfoDashboard" / "data"
    assert "Library/Application Support/SchoolInfoDashboard/data" in str(get_cache_data_dir("Darwin"))
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "xdg"))
    assert get_cache_data_dir("Linux") == tmp_path / "xdg" / "SchoolInfoDashboard" / "data"


def test_cache_setup_generates_excel_from_committed_csv(tmp_path, monkeypatch):
    monkeypatch.chdir(ROOT)
    cache_dir = ensure_cache_files(tmp_path / "cache")
    assert (cache_dir / config.EXCEL_FILENAME).exists()
    assert (cache_dir / config.VERSION_FILENAME).exists()
    records = dataframe_to_school_records(load_schools_excel(cache_dir / config.EXCEL_FILENAME))
    assert records[0]["school_name"] == "Bluewater Primary School"


def test_sync_failure_does_not_delete_existing_cached_data(tmp_path, sample_excel: Path):
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    excel_path = cache_dir / config.EXCEL_FILENAME
    version_path = cache_dir / config.VERSION_FILENAME
    shutil.copy2(sample_excel, excel_path)
    version_path.write_text(json.dumps({"data_version": "local", "updated_at": "2026-05-18"}), encoding="utf-8")

    result = check_for_updates(cache_dir, remote_version_url="https://127.0.0.1:1/version.json", timeout=1)

    assert result.updated is False
    assert excel_path.exists()
    assert version_path.exists()
    assert json.loads(version_path.read_text(encoding="utf-8"))["data_version"] == "local"


def test_valid_sample_csv_loads():
    from app.data_loader import load_schools_csv

    data = load_schools_csv(SAMPLE_CSV)
    records = dataframe_to_school_records(data)
    assert len(records) >= 3
    assert records[0]["school_id"] == "SCH001"
    assert records[0]["school_name"] == "Bluewater Primary School"


def test_sync_downloads_csv_and_generates_cached_excel(tmp_path, sample_excel: Path, monkeypatch):
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    excel_path = cache_dir / config.EXCEL_FILENAME
    version_path = cache_dir / config.VERSION_FILENAME
    shutil.copy2(sample_excel, excel_path)
    version_path.write_text(json.dumps({"data_version": "local", "updated_at": "2026-05-18"}), encoding="utf-8")

    remote_version = {"data_version": "remote", "updated_at": "2026-05-19", "data_file": "schools.csv"}
    csv_bytes = SAMPLE_CSV.read_bytes()

    class DummyResponse:
        def __init__(self, *, json_data=None, content=b"", text=""):
            self._json_data = json_data
            self.content = content
            self.text = text

        def raise_for_status(self):
            return None

        def json(self):
            return self._json_data

    class DummyRequests:
        class RequestException(Exception):
            pass

        def get(self, url, timeout):
            if url.endswith("version.json"):
                return DummyResponse(json_data=remote_version, text=json.dumps(remote_version))
            if url.endswith("schools.csv"):
                return DummyResponse(content=csv_bytes, text=csv_bytes.decode("utf-8"))
            raise AssertionError(f"unexpected URL: {url}")

    import app.sync as sync_module

    monkeypatch.setattr(sync_module, "requests", DummyRequests())

    result = check_for_updates(
        cache_dir,
        remote_version_url="https://example.test/data/version.json",
        remote_data_url="https://example.test/data/schools.csv",
    )

    assert result.updated is True
    assert json.loads(version_path.read_text(encoding="utf-8"))["data_file"] == "schools.csv"
    records = dataframe_to_school_records(load_schools_excel(excel_path))
    assert records[0]["school_name"] == "Bluewater Primary School"
