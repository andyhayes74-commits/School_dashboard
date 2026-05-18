"""School data loading and validation helpers.

The runtime cache remains an Excel workbook, while GitHub-hosted source data is
CSV. The production dependency set uses pandas/openpyxl where available. Small
stdlib fallback parsers are included so validation and cache-safety tests can run
in constrained environments.
"""

from __future__ import annotations

from dataclasses import dataclass
import csv
import importlib
import importlib.util
from pathlib import Path
from typing import Any, Iterable
from xml.etree import ElementTree as ET
from zipfile import ZipFile

from app import config


class DataValidationError(ValueError):
    """Friendly validation error suitable for display to non-technical users."""


@dataclass
class SchoolTable:
    columns: list[str]
    rows: list[dict[str, str]]

    @property
    def empty(self) -> bool:
        return not self.rows


def _normalise_headers(columns: Iterable[object]) -> list[str]:
    headers: list[str] = []
    for column in columns:
        header = "" if column is None else str(column).strip()
        if not header or header.lower().startswith("unnamed:"):
            raise DataValidationError("The school data file has a blank column header. Please fill every header cell.")
        headers.append(header)
    return headers


def _normalise_cell_value(value: object) -> str:
    if value is None:
        return config.NOT_PROVIDED
    text = str(value).strip()
    if not text or text.lower() == "nan":
        return config.NOT_PROVIDED
    return text


def validate_school_records(columns: Iterable[object], rows: Iterable[dict[str, Any]]) -> SchoolTable:
    """Validate school records and return display-safe string data."""
    headers = _normalise_headers(columns)
    missing = [column for column in config.REQUIRED_COLUMNS if column not in headers]
    if missing:
        missing_text = ", ".join(missing)
        raise DataValidationError(f"The school data file is missing required column(s): {missing_text}.")

    normalised_rows: list[dict[str, str]] = []
    for source_row in rows:
        row = {column: _normalise_cell_value(source_row.get(column)) for column in headers}
        for required in config.REQUIRED_COLUMNS:
            if row[required] == config.NOT_PROVIDED:
                raise DataValidationError(f"The required column '{required}' contains blank values.")
        normalised_rows.append(row)

    if not normalised_rows:
        raise DataValidationError("The school data file does not contain any school rows.")
    return SchoolTable(headers, normalised_rows)


def validate_school_dataframe(df: Any) -> Any:
    """Validate a pandas dataframe when pandas is available."""
    # Kept as a public helper because pandas/openpyxl are the intended runtime
    # stack and tests/users may call it directly with a dataframe.
    df = df.copy()
    df.columns = _normalise_headers(list(df.columns))
    table = validate_school_records(df.columns, df.to_dict(orient="records"))
    if importlib.util.find_spec("pandas") is None:
        return table
    pd = importlib.import_module("pandas")
    return pd.DataFrame(table.rows, columns=table.columns)


def load_schools_csv(path: str | Path) -> Any:
    """Load and validate source-controlled school data from a CSV file."""
    csv_path = Path(path)
    if not csv_path.exists():
        raise DataValidationError(f"The school data file could not be found: {csv_path}")

    if importlib.util.find_spec("pandas") is not None:
        pd = importlib.import_module("pandas")
        try:
            df = pd.read_csv(csv_path, dtype=object, keep_default_na=False)
            return validate_school_dataframe(df)
        except DataValidationError:
            raise
        except Exception as exc:
            raise DataValidationError(f"The CSV file could not be read: {exc}") from exc

    try:
        with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames is None:
                raise DataValidationError("The school data file does not contain a header row.")
            return validate_school_records(reader.fieldnames, reader)
    except DataValidationError:
        raise
    except csv.Error as exc:
        raise DataValidationError(f"The CSV file could not be read: {exc}") from exc
    except OSError as exc:
        raise DataValidationError(f"The CSV file could not be read: {exc}") from exc


def load_schools_excel(path: str | Path) -> Any:
    """Load and validate the schools sheet from an Excel workbook."""
    excel_path = Path(path)
    if not excel_path.exists():
        raise DataValidationError(f"The school data file could not be found: {excel_path}")

    if importlib.util.find_spec("pandas") is None or importlib.util.find_spec("openpyxl") is None:
        return _load_xlsx_with_stdlib(excel_path)

    pd = importlib.import_module("pandas")
    try:
        df = pd.read_excel(excel_path, sheet_name=config.SCHOOLS_SHEET_NAME, dtype=object, engine="openpyxl")
        return validate_school_dataframe(df)
    except ValueError as exc:
        raise DataValidationError("The Excel file must contain a sheet named 'schools'.") from exc
    except DataValidationError:
        raise
    except Exception as exc:
        # If pandas/openpyxl is installed but cannot read the workbook, report a
        # friendly message rather than exposing a traceback.
        raise DataValidationError(f"The Excel file could not be read: {exc}") from exc


def dataframe_to_school_records(data: Any) -> list[dict[str, str]]:
    """Convert validated school data to row dictionaries for UI display."""
    if isinstance(data, SchoolTable):
        return data.rows
    if hasattr(data, "iterrows") and hasattr(data, "columns"):
        return [{column: str(row[column]) for column in data.columns} for _, row in data.iterrows()]
    return list(data)


def _load_xlsx_with_stdlib(path: Path) -> SchoolTable:
    try:
        with ZipFile(path) as archive:
            sheet_path = _find_sheet_path(archive, config.SCHOOLS_SHEET_NAME)
            shared_strings = _read_shared_strings(archive)
            rows = _read_sheet_rows(archive, sheet_path, shared_strings)
    except KeyError as exc:
        raise DataValidationError("The Excel file must contain a sheet named 'schools'.") from exc
    except Exception as exc:
        raise DataValidationError(f"The Excel file could not be read: {exc}") from exc

    if not rows:
        raise DataValidationError("The school data file does not contain any school rows.")
    headers = rows[0]
    record_rows = [dict(zip(headers, row + [None] * (len(headers) - len(row)))) for row in rows[1:]]
    return validate_school_records(headers, record_rows)


def _find_sheet_path(archive: ZipFile, sheet_name: str) -> str:
    ns = {
        "main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
        "rel": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
        "pkg": "http://schemas.openxmlformats.org/package/2006/relationships",
    }
    workbook = ET.fromstring(archive.read("xl/workbook.xml"))
    rels = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
    rel_targets = {rel.attrib["Id"]: rel.attrib["Target"] for rel in rels.findall("pkg:Relationship", ns)}
    for sheet in workbook.findall("main:sheets/main:sheet", ns):
        if sheet.attrib.get("name") == sheet_name:
            rel_id = sheet.attrib.get(f"{{{ns['rel']}}}id")
            target = rel_targets[rel_id]
            return "xl/" + target.lstrip("/") if not target.startswith("xl/") else target
    raise KeyError(sheet_name)


def _read_shared_strings(archive: ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in archive.namelist():
        return []
    ns = {"main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
    values: list[str] = []
    for item in root.findall("main:si", ns):
        texts = [node.text or "" for node in item.findall(".//main:t", ns)]
        values.append("".join(texts))
    return values


def _read_sheet_rows(archive: ZipFile, sheet_path: str, shared_strings: list[str]) -> list[list[str | None]]:
    ns = {"main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    root = ET.fromstring(archive.read(sheet_path))
    parsed_rows: list[list[str | None]] = []
    for row in root.findall(".//main:sheetData/main:row", ns):
        values: list[str | None] = []
        for cell in row.findall("main:c", ns):
            index = _column_index(cell.attrib.get("r", "A1"))
            while len(values) < index:
                values.append(None)
            values.append(_cell_value(cell, shared_strings, ns))
        parsed_rows.append(values)
    return parsed_rows


def _cell_value(cell: ET.Element, shared_strings: list[str], ns: dict[str, str]) -> str | None:
    cell_type = cell.attrib.get("t")
    if cell_type == "inlineStr":
        texts = [node.text or "" for node in cell.findall(".//main:t", ns)]
        return "".join(texts)
    value_node = cell.find("main:v", ns)
    if value_node is None or value_node.text is None:
        return None
    if cell_type == "s":
        return shared_strings[int(value_node.text)]
    return value_node.text


def _column_index(cell_ref: str) -> int:
    letters = "".join(character for character in cell_ref if character.isalpha()).upper()
    total = 0
    for character in letters:
        total = total * 26 + (ord(character) - ord("A") + 1)
    return max(total - 1, 0)
