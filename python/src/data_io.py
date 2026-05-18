from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from typing import Iterable

from .models import Task

ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "data"


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def _data_files(data_dir: Path = DATA_DIR) -> Iterable[Path]:
    return data_dir.glob("*.csv")


def find_csv_by_headers(required_headers: set[str], data_dir: Path = DATA_DIR) -> Path:
    matches: list[Path] = []
    for path in sorted(_data_files(data_dir)):
        with path.open("r", encoding="utf-8-sig", newline="") as file:
            reader = csv.reader(file)
            try:
                headers = {header.strip() for header in next(reader)}
            except StopIteration:
                continue
        if required_headers.issubset(headers):
            matches.append(path)
    if not matches:
        raise FileNotFoundError(f"No CSV in {data_dir} contains headers: {sorted(required_headers)}")
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

    starts = [parse_datetime(row["开始时间"]) for row in rows]
    base_day = min(starts).replace(hour=0, minute=0, second=0, microsecond=0)
    windows: list[tuple[float, float]] = []
    for row, start_at in zip(rows, starts):
        duration_minutes = float(row["持续时间 (min)"].strip())
        start_seconds = (start_at - base_day).total_seconds()
        end_seconds = start_seconds + duration_minutes * 60
        windows.append((start_seconds, end_seconds))
    return sorted(windows)


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


def read_tasks(path: Path | None = None) -> list[Task]:
    if path is None:
        path = DATA_DIR / "event.csv"
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        next(reader)
        tasks: list[Task] = []
        for row in reader:
            if not row or not row[0]:
                continue
            tid, dur, power, min_a, max_a, prio = row[:6]
            tasks.append(
                Task(
                    id=int(tid),
                    duration=int(dur) * 60,
                    power=int(power),
                    min_angle=float(min_a),
                    max_angle=float(max_a),
                    priority=int(prio),
                )
            )
        return tasks


# Alias so callers can use either name
read_anomaly_windows = read_avoid_area_windows
