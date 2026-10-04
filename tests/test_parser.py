from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from guardian.data import parse_area_workbook


def _write_workbook(path: Path) -> None:
    shared = [
        "Tunniste",
        "VILPE Vantaa, Test Katto",
        "Sarjanumero",
        "TEST-1",
        "Tyyppi",
        "VILPE MCU-2",
        "Käyttötarkoitus",
        "Kattorakenteen tuuletus",
        "Rakennusmateriaali",
        "Betoni",
        "Viimeisin homeindeksi",
        "0.6",
        "Viimeisin rpm",
        "1000",
        "Aikaleima",
        "Rpm",
        "Ohjaava sisälähetin T (°C)",
        "Ohjaava sisälähetin H (%)",
        "Ohjaava sisälähetin g/m³",
        "Ohjaava ulkolähetin T (°C)",
        "Ohjaava ulkolähetin H (%)",
        "Ohjaava ulkolähetin g/m³",
    ]
    strings = "".join(f"<si><t>{value}</t></si>" for value in shared)

    def row(number: int, cells: list[tuple[str, str | int, bool]]) -> str:
        xml_cells = []
        for column, value, is_shared in cells:
            shared_attribute = ' t="s"' if is_shared else ""
            xml_cells.append(f'<c r="{column}{number}"{shared_attribute}><v>{value}</v></c>')
        return f'<row r="{number}">{"".join(xml_cells)}</row>'

    rows = []
    metadata = [
        ("Tunniste", "VILPE Vantaa, Test Katto"),
        ("Sarjanumero", "TEST-1"),
        ("Tyyppi", "VILPE MCU-2"),
        ("Käyttötarkoitus", "Kattorakenteen tuuletus"),
        ("Rakennusmateriaali", "Betoni"),
        ("Viimeisin homeindeksi", "0.6"),
        ("Viimeisin rpm", "1000"),
    ]
    for index, values in enumerate(metadata, start=1):
        rows.append(
            row(
                index,
                [("A", shared.index(values[0]), True), ("B", shared.index(values[1]), True)],
            )
        )
    rows.extend(
        [
            row(
                12,
                [
                    ("A", 14, True),
                    ("B", 15, True),
                    ("C", 16, True),
                    ("D", 17, True),
                    ("E", 18, True),
                    ("F", 19, True),
                    ("G", 20, True),
                    ("H", 21, True),
                ],
            ),
            row(
                13,
                [
                    ("A", 14, True),
                    ("B", 100, False),
                    ("C", 10, False),
                    ("D", 95, False),
                    ("E", 12, False),
                    ("F", 5, False),
                    ("G", 80, False),
                    ("H", 8, False),
                ],
            ),
            row(
                14,
                [
                    ("A", "2025/05/14 06:11:20", False),
                    ("B", 100, False),
                    ("C", 10, False),
                    ("D", 95, False),
                    ("E", 12, False),
                    ("F", 5, False),
                    ("G", 80, False),
                    ("H", 8, False),
                ],
            ),
            row(
                15,
                [
                    ("A", "2025/05/14 06:11:20", False),
                    ("B", 200, False),
                    ("D", 96, False),
                    ("E", 13, False),
                    ("F", 5, False),
                    ("G", 80, False),
                    ("H", 8, False),
                ],
            ),
        ]
    )
    content_types = (
        '<?xml version="1.0"?><Types '
        'xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Override PartName="/xl/workbook.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        '<Override PartName="/xl/worksheets/sheet1.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        "</Types>"
    )
    workbook = (
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        '<sheets><sheet name="Sheet1" sheetId="1" r:id="rId1"/></sheets></workbook>'
    )
    rels = (
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
        'Target="worksheets/sheet1.xml"/></Relationships>'
    )
    worksheet = f'<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>{"".join(rows)}</sheetData></worksheet>'
    with ZipFile(path, "w", ZIP_DEFLATED) as book:
        book.writestr("[Content_Types].xml", content_types)
        book.writestr("xl/workbook.xml", workbook)
        book.writestr("xl/_rels/workbook.xml.rels", rels)
        book.writestr(
            "xl/sharedStrings.xml",
            f'<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">{strings}</sst>',
        )
        book.writestr("xl/worksheets/sheet1.xml", worksheet)


def test_parser_normalizes_order_and_deduplicates(tmp_path: Path) -> None:
    path = tmp_path / "area.xlsx"
    _write_workbook(path)

    area = parse_area_workbook(path).area

    assert area.kind == "roof"
    assert area.latest_mould_index == 0.6
    assert len(area.readings) == 1
    assert area.readings[0].fan_rpm == 200
    assert area.readings[0].indoor_relative_humidity_pct == 96
    assert area.readings[0].outdoor_absolute_humidity_g_m3 == 8
    assert area.data_quality.duplicate_timestamps == 1
    assert area.data_quality.missing_values["indoor_temperature_c"] == 1
