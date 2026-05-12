from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from typing import Iterable

ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "data"


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def _data_files() -> Iterable[Path]:
    return DATA_DIR.glob("*.csv")


def find_csv_by_headers(required_headers: set[str]) -> Path:
    matches: list[Path] = []
    for path in sorted(_data_files()):
        with path.open("r", encoding="utf-8-sig", newline="") as file:
            reader = csv.reader(file)
            try:
                headers = {header.strip() for header in next(reader)}
            except StopIteration:
                continue
        if required_headers.issubset(headers):
            matches.append(path)
    if not matches:
        raise FileNotFoundError(f"No CSV in {DATA_DIR} contains headers: {sorted(required_headers)}")
    if len(matches) > 1:
        names = ", ".join(path.name for path in matches)
        raise ValueError(f"Multiple CSV files contain headers {sorted(required_headers)}: {names}")
    return matches[0]


def parse_datetime(value: str) -> datetime:
    normalized = value.strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M", "%Y/%m/%d %H:%M:%S"):
        try:
            return datetime.strptime(normalized, fmt)
        except ValueError:
            pass
    raise ValueError(f"Unsupported datetime format: {value!r}")


def read_avoid_area_windows(path: Path | None = None) -> list[tuple[float, float]]:
    csv_path = path or find_csv_by_headers({"开始时间", "持续时间 (min)"})
    rows = _read_csv_rows(csv_path)
    if not rows:
        return []

    first_start = parse_datetime(rows[0]["开始时间"])
    windows: list[tuple[float, float]] = []
    for row in rows:
        start_at = parse_datetime(row["开始时间"])
        duration_minutes = float(row["持续时间 (min)"].strip())
        start_seconds = (start_at - first_start.replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds()
        end_seconds = start_seconds + duration_minutes * 60
        windows.append((start_seconds, end_seconds))
    return windows


def read_solar_angles(path: Path | None = None) -> list[tuple[float, float]]:
    csv_path = path or find_csv_by_headers({"Time (LCLG)", "Beta Angle (deg)"})
    rows = _read_csv_rows(csv_path)
    if not rows:
        return []

    first_time = parse_datetime(rows[0]["Time (LCLG)"])
    base_day = first_time.replace(hour=0, minute=0, second=0, microsecond=0)
    solar_angles: list[tuple[float, float]] = []
    for row in rows:
        timestamp = parse_datetime(row["Time (LCLG)"])
        angle = float(row["Beta Angle (deg)"].strip())
        relative_seconds = (timestamp - base_day).total_seconds()
        solar_angles.append((angle, relative_seconds))
    return solar_angles
