"""Generate a minimal .xlsx workbook from source-controlled CSV sample data."""

from __future__ import annotations

import csv
import re
from pathlib import Path
from xml.sax.saxutils import escape
from zipfile import ZIP_DEFLATED, ZipFile

from app import config


INLINE_STRING_RE = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F]")


def generate_sample_xlsx(csv_path: Path, xlsx_path: Path) -> Path:
    """Generate a local Excel workbook with a `schools` sheet from a CSV file."""
    if not csv_path.exists():
        raise FileNotFoundError(f"Sample CSV file is missing: {csv_path}")

    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.reader(handle))

    if not rows:
        raise ValueError(f"Sample CSV file is empty: {csv_path}")

    xlsx_path.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(xlsx_path, "w", ZIP_DEFLATED) as archive:
        for name, content in _xlsx_parts(rows).items():
            archive.writestr(name, content)
    return xlsx_path


def _xlsx_parts(rows: list[list[str]]) -> dict[str, str]:
    return {
        "[Content_Types].xml": _content_types_xml(),
        "_rels/.rels": _root_rels_xml(),
        "xl/workbook.xml": _workbook_xml(),
        "xl/_rels/workbook.xml.rels": _workbook_rels_xml(),
        "xl/worksheets/sheet1.xml": _worksheet_xml(rows),
    }


def _worksheet_xml(rows: list[list[str]]) -> str:
    row_xml: list[str] = []
    for row_index, row in enumerate(rows, start=1):
        cells: list[str] = []
        for column_index, value in enumerate(row, start=1):
            reference = f"{_column_name(column_index)}{row_index}"
            clean_value = INLINE_STRING_RE.sub("", value or "")
            if clean_value == "":
                cells.append(f'<c r="{reference}"/>')
            else:
                cells.append(
                    f'<c r="{reference}" t="inlineStr"><is><t>{escape(clean_value)}</t></is></c>'
                )
        row_xml.append(f'<row r="{row_index}">{"".join(cells)}</row>')

    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f'<sheetData>{"".join(row_xml)}</sheetData>'
        "</worksheet>"
    )


def _column_name(column_index: int) -> str:
    name = ""
    while column_index:
        column_index, remainder = divmod(column_index - 1, 26)
        name = chr(65 + remainder) + name
    return name


def _content_types_xml() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/xl/workbook.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        '<Override PartName="/xl/worksheets/sheet1.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        "</Types>"
    )


def _root_rels_xml() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
        'Target="xl/workbook.xml"/>'
        "</Relationships>"
    )


def _workbook_xml() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        f'<sheets><sheet name="{config.SCHOOLS_SHEET_NAME}" sheetId="1" r:id="rId1"/></sheets>'
        "</workbook>"
    )


def _workbook_rels_xml() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
        'Target="worksheets/sheet1.xml"/>'
        "</Relationships>"
    )


def main() -> int:
    generate_sample_xlsx(
        Path(config.DATA_DIR_NAME) / "schools.csv",
        Path(config.DATA_DIR_NAME) / config.EXCEL_FILENAME,
    )
    print(f"Generated {Path(config.DATA_DIR_NAME) / config.EXCEL_FILENAME}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
