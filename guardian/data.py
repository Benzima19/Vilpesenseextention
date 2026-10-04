"""Read and normalize the VILPE area workbooks."""

from __future__ import annotations

import re
import unicodedata
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any
from zipfile import ZipFile

from pydantic import BaseModel, ConfigDict, Field


class Reading(BaseModel):
    """A normalized measurement from one VILPE area."""

    timestamp: datetime
    indoor_temperature_c: float | None = None
    indoor_relative_humidity_pct: float | None = None
    indoor_absolute_humidity_g_m3: float | None = None
    outdoor_temperature_c: float | None = None
    outdoor_relative_humidity_pct: float | None = None
    outdoor_absolute_humidity_g_m3: float | None = None
    fan_rpm: float | None = None


class DataQuality(BaseModel):
    raw_readings: int
    normalized_readings: int
    duplicate_timestamps: int
    missing_values: dict[str, int]


class Area(BaseModel):
    id: str
    name: str
    kind: str
    usage: str | None = None
    material: str | None = None
    device_serial: str | None = None
    device_type: str | None = None
    controller_sensors: dict[str, str] = Field(default_factory=dict)
    readings: list[Reading] = Field(default_factory=list)
    latest_mould_index: float | None = None
    latest_rpm: float | None = None
    data_quality: DataQuality | None = None


class Building(BaseModel):
    id: str
    name: str
    location: str
    areas: list[Area] = Field(default_factory=list)


class HealthAssessment(BaseModel):
    status: str
    score: int
    reasons: list[str] = Field(default_factory=list)
    trend: str = "stable"


class ParsedWorkbook(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    area: Area
    source_file: str


_REL_NS = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
_AREA_PREFIX = "VILPE Vantaa, "


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _read_shared_strings(book: ZipFile) -> list[str]:
    try:
        root = ET.fromstring(book.read("xl/sharedStrings.xml"))
    except KeyError:
        return []

    strings = []
    for item in root:
        if _local_name(item.tag) == "si":
            strings.append(
                "".join(child.text or "" for child in item.iter() if _local_name(child.tag) == "t")
            )
    return strings


def _worksheet_path(book: ZipFile) -> str:
    workbook = ET.fromstring(book.read("xl/workbook.xml"))
    rels = ET.fromstring(book.read("xl/_rels/workbook.xml.rels"))
    targets = {
        relation.attrib["Id"]: relation.attrib["Target"]
        for relation in rels
        if relation.attrib.get("Type", "").endswith("/worksheet")
    }
    sheet = next(element for element in workbook.iter() if _local_name(element.tag) == "sheet")
    target = targets[sheet.attrib[f"{_REL_NS}id"]]
    return target if target.startswith("xl/") else f"xl/{target}"


def _cell_value(cell: ET.Element, shared_strings: list[str]) -> str | None:
    value = next((child.text for child in cell if _local_name(child.tag) == "v"), None)
    if value is None:
        return None
    if cell.attrib.get("t") == "s":
        return shared_strings[int(value)]
    return value


def _rows(book: ZipFile) -> list[dict[str, str | None]]:
    root = ET.fromstring(book.read(_worksheet_path(book)))
    shared_strings = _read_shared_strings(book)
    result = []
    for row in root.iter():
        if _local_name(row.tag) != "row":
            continue
        values: dict[str, str | None] = {}
        for cell in row:
            if _local_name(cell.tag) != "c":
                continue
            reference = cell.attrib.get("r", "")
            column = re.match(r"[A-Z]+", reference)
            if column:
                values[column.group()] = _cell_value(cell, shared_strings)
        result.append(values)
    return result


def _normalized(value: str | None) -> str:
    if not value:
        return ""
    return unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode().lower()


def _number(value: str | None) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except ValueError:
        return None


def _timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y/%m/%d %H:%M:%S")
    except ValueError:
        return None


def _area_kind(area_name: str) -> str:
    normalized = _normalized(area_name)
    if "viherkatto" in normalized:
        return "green_roof"
    if "katto" in normalized:
        return "roof"
    if "alapohja" in normalized:
        return "crawl_space"
    return "unknown"


def _measurement_field(header: str) -> str | None:
    normalized = _normalized(header)
    role = (
        "indoor"
        if "sisalahetin" in normalized
        else "outdoor"
        if "ulkolahetin" in normalized
        else ""
    )
    if not role:
        return None
    if "g/m" in normalized:
        measurement = "absolute_humidity_g_m3"
    elif "h (" in normalized:
        measurement = "relative_humidity_pct"
    elif "t (" in normalized:
        measurement = "temperature_c"
    else:
        return None
    return f"{role}_{measurement}"


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", _normalized(value)).strip("-")


def parse_area_workbook(path: Path) -> ParsedWorkbook:
    """Parse one VILPE MCU workbook, independent of column order."""

    with ZipFile(path) as book:
        rows = _rows(book)
    metadata = {str(row["A"]): row.get("B") for row in rows[:9] if row.get("A")}
    area_name = str(metadata.get("Tunniste") or path.stem.removeprefix(_AREA_PREFIX).split("_")[0])
    header_index = next(index for index, row in enumerate(rows) if row.get("A") == "Aikaleima")
    headers = rows[header_index]
    field_by_column = {
        column: field
        for column, header in headers.items()
        if (field := _measurement_field(str(header)))
    }
    field_by_column["B"] = "fan_rpm"

    raw_readings: list[Reading] = []
    for row in rows[header_index + 1 :]:
        timestamp = _timestamp(row.get("A"))
        if timestamp is None:
            continue
        values: dict[str, Any] = {
            field: _number(row.get(column)) for column, field in field_by_column.items()
        }
        raw_readings.append(Reading(timestamp=timestamp, **values))

    duplicate_count = sum(
        count - 1
        for count in Counter(reading.timestamp for reading in raw_readings).values()
        if count > 1
    )
    deduplicated: dict[datetime, Reading] = {}
    for reading in raw_readings:
        deduplicated[reading.timestamp] = reading
    readings = [deduplicated[timestamp] for timestamp in sorted(deduplicated)]
    missing_values = {
        field: sum(getattr(reading, field) is None for reading in readings)
        for field in Reading.model_fields
        if field != "timestamp"
    }
    controller_sensors = {}
    for row in rows:
        role = _normalized(row.get("A"))
        if "sisalahetin" in role:
            controller_sensors["indoor"] = str(row.get("C"))
        elif "ulkolahetin" in role:
            controller_sensors["outdoor"] = str(row.get("C"))

    area = Area(
        id=_slug(area_name.removeprefix(_AREA_PREFIX)),
        name=area_name,
        kind=_area_kind(area_name),
        usage=metadata.get("Käyttötarkoitus"),
        material=metadata.get("Rakennusmateriaali"),
        device_serial=metadata.get("Sarjanumero"),
        device_type=metadata.get("Tyyppi"),
        controller_sensors=controller_sensors,
        readings=readings,
        latest_mould_index=_number(metadata.get("Viimeisin homeindeksi")),
        latest_rpm=_number(metadata.get("Viimeisin rpm")),
        data_quality=DataQuality(
            raw_readings=len(raw_readings),
            normalized_readings=len(readings),
            duplicate_timestamps=duplicate_count,
            missing_values=missing_values,
        ),
    )
    return ParsedWorkbook(area=area, source_file=path.name)


def area_workbook_paths(data_dir: Path) -> list[Path]:
    """Return only the seven named Vantaa area workbooks."""

    return sorted(path for path in data_dir.glob("*.xlsx") if path.name.startswith(_AREA_PREFIX))


def load_vantaa_building(data_dir: Path) -> Building:
    paths = area_workbook_paths(data_dir)
    if len(paths) != 7:
        raise FileNotFoundError(
            f"Expected seven VILPE area workbooks in {data_dir}, found {len(paths)}"
        )
    parsed = [parse_area_workbook(path).area for path in paths]
    return Building(id="vantaa", name="VILPE Vantaa", location="Vantaa", areas=parsed)
