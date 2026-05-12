from __future__ import annotations

import csv
from pathlib import Path

from JudgeAvoidAreaClash import JudgeAvoidAreaClash
from JudgeSolarClash import JudgeSolarClash
from JudgeWelecClash import JudgeWelecClash
import data_io
from data_io import find_csv_by_headers, read_avoid_area_windows, read_solar_angles


def write_csv(path: Path, rows: list[list[object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerows(rows)


def test_reads_avoid_area_windows_by_headers(tmp_path: Path) -> None:
    avoid_path = tmp_path / "misnamed_solar.csv"
    write_csv(
        avoid_path,
        [
            ["", "开始时间", "结束时间", "持续时间 (min)"],
            [1, "2021-10-02 14:47:00", "2021-10-02 14:59:00", 12],
        ],
    )

    windows = read_avoid_area_windows(avoid_path)

    assert windows == [(53220.0, 53940.0)]


def test_reads_solar_angles_by_headers(tmp_path: Path) -> None:
    solar_path = tmp_path / "misnamed_avoid.csv"
    write_csv(
        solar_path,
        [
            ["Time (LCLG)", "Beta Angle (deg)"],
            ["2021/10/2 0:00", 0],
            ["2021/10/2 8:00", 22.5],
        ],
    )

    solar_angles = read_solar_angles(solar_path)

    assert solar_angles == [(0.0, 0.0), (22.5, 28800.0)]


def test_find_csv_by_headers_detects_data_files() -> None:
    solar_path = find_csv_by_headers({"Time (LCLG)", "Beta Angle (deg)"})
    avoid_path = find_csv_by_headers({"开始时间", "持续时间 (min)"})

    assert solar_path.name == "SolarAngle.csv"
    assert avoid_path.name == "AvoidAeraWindow.csv"


def test_find_csv_by_headers_rejects_ambiguous_matches(tmp_path: Path) -> None:
    for name in ("a.csv", "b.csv"):
        write_csv(
            tmp_path / name,
            [
                ["Time (LCLG)", "Beta Angle (deg)"],
                ["2021/10/2 0:00", 0],
            ],
        )

    original_data_dir = data_io.DATA_DIR
    data_io.DATA_DIR = tmp_path
    try:
        try:
            find_csv_by_headers({"Time (LCLG)", "Beta Angle (deg)"})
        except ValueError as exc:
            assert "Multiple CSV files" in str(exc)
        else:
            raise AssertionError("ambiguous CSV files should raise ValueError")
    finally:
        data_io.DATA_DIR = original_data_dir


def test_judge_avoid_area_clash_detects_overlap(tmp_path: Path) -> None:
    avoid_path = tmp_path / "avoid.csv"
    write_csv(
        avoid_path,
        [
            ["", "开始时间", "结束时间", "持续时间 (min)"],
            [1, "2021-10-02 00:10:00", "2021-10-02 00:20:00", 10],
        ],
    )

    assert JudgeAvoidAreaClash([[1, 500, 700, 0, 20]], avoid_path) is True
    assert JudgeAvoidAreaClash([[1, 1300, 1400, 0, 20]], avoid_path) is False


def test_judge_solar_clash_detects_angle_violation(tmp_path: Path) -> None:
    solar_path = tmp_path / "solar.csv"
    write_csv(
        solar_path,
        [
            ["Time (LCLG)", "Beta Angle (deg)"],
            ["2021/10/2 0:00", 0],
            ["2021/10/2 8:00", 30],
        ],
    )

    assert JudgeSolarClash([[1, 0, 28800, 0, 20]], solar_path) is True
    assert JudgeSolarClash([[1, 0, 28800, 0, 40]], solar_path) is False


def test_judge_solar_clash_detects_uncovered_event_tail(tmp_path: Path) -> None:
    solar_path = tmp_path / "solar.csv"
    write_csv(
        solar_path,
        [
            ["Time (LCLG)", "Beta Angle (deg)"],
            ["2021/10/2 0:00", 0],
            ["2021/10/2 8:00", 10],
        ],
    )

    assert JudgeSolarClash([[1, 28000, 30000, 0, 40]], solar_path) is True


def test_judge_welec_clash_is_explicitly_unimplemented() -> None:
    try:
        JudgeWelecClash([[1, 0, 1]])
    except NotImplementedError as exc:
        assert "no algorithm" in str(exc)
    else:
        raise AssertionError("JudgeWelecClash should raise NotImplementedError")
