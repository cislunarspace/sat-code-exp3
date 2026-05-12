from __future__ import annotations

from pathlib import Path
import sys

from openpyxl import load_workbook

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = Path(__file__).resolve().parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from JudgeAvoidAreaClash import JudgeAvoidAreaClash
from JudgeSolarClash import JudgeSolarClash


def read_planning_events(path: Path | None = None) -> list[list[float]]:
    workbook_path = path or ROOT_DIR / "data" / "planningevents.xlsx"
    workbook = load_workbook(workbook_path, data_only=True, read_only=True)
    sheet = workbook.active
    rows: list[list[float]] = []
    for row in sheet.iter_rows(min_row=2, values_only=True):
        if row is None or row[0] is None:
            continue
        rows.append([float(value) for value in row[:5]])
    return rows


def main() -> tuple[bool, bool]:
    planning_events = read_planning_events()
    avoid_area_clash = JudgeAvoidAreaClash(planning_events)
    solar_clash = JudgeSolarClash(planning_events)
    print(f"AvoidAreaClash: {avoid_area_clash}")
    print(f"SolarClash: {solar_clash}")
    return avoid_area_clash, solar_clash


if __name__ == "__main__":
    main()
