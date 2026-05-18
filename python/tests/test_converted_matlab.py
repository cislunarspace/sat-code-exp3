from __future__ import annotations

import csv
from pathlib import Path

import main as planning_main
from src import data_io
from src.JudgeAvoidAreaClash import JudgeAvoidAreaClash
from src.JudgeSolarClash import JudgeSolarClash
from src.JudgeWelecClash import JudgeWelecClash
from src.data_io import find_csv_by_headers, read_avoid_area_windows, read_solar_angles


def write_csv(path: Path, rows: list[list[object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerows(rows)


# 验证规避区域窗口读取逻辑只依赖表头，不依赖文件名。
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


# 验证太阳角读取逻辑按表头识别数据，并把时间转换为相对秒数。
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


# 验证真实数据目录中能通过表头找到对应 CSV 文件。
def test_find_csv_by_headers_detects_data_files() -> None:
    solar_path = find_csv_by_headers({"Time (LCLG)", "Beta Angle (deg)"})
    avoid_path = find_csv_by_headers({"开始时间", "持续时间 (min)"})

    assert solar_path.name == "SolarAngle.csv"
    assert avoid_path.name == "AvoidAeraWindow.csv"


# 验证表头匹配到多个 CSV 时会显式报错，避免静默选错数据源。
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


# 验证任务时间窗与规避区域窗口重叠时会判定冲突。
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


# 验证异常区窗口即使在 CSV 中乱序，也不会漏报后续重叠窗口。
def test_judge_avoid_area_clash_handles_unsorted_windows(tmp_path: Path) -> None:
    avoid_path = tmp_path / "avoid.csv"
    write_csv(
        avoid_path,
        [
            ["", "开始时间", "结束时间", "持续时间 (min)"],
            [1, "2021-10-02 01:00:00", "2021-10-02 01:10:00", 10],
            [2, "2021-10-02 00:10:00", "2021-10-02 00:20:00", 10],
        ],
    )

    assert JudgeAvoidAreaClash([[1, 500, 700, 0, 20]], avoid_path) is True


# 验证异常区窗口即使跨天乱序，也以最早窗口日期作为相对时间基准。
def test_read_avoid_area_windows_uses_earliest_day_for_unsorted_rows(tmp_path: Path) -> None:
    avoid_path = tmp_path / "avoid.csv"
    write_csv(
        avoid_path,
        [
            ["", "开始时间", "结束时间", "持续时间 (min)"],
            [1, "2021-10-03 00:10:00", "2021-10-03 00:20:00", 10],
            [2, "2021-10-02 23:50:00", "2021-10-03 00:00:00", 10],
        ],
    )

    assert read_avoid_area_windows(avoid_path) == [(85800.0, 86400.0), (87000.0, 87600.0)]


# 验证任务期间太阳 Beta 角低于阈值时会判定冲突。
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


# 验证任务尾段超出太阳角数据覆盖范围时按冲突处理。
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


# 验证任务头段早于太阳角数据覆盖范围时按冲突处理。
def test_judge_solar_clash_detects_uncovered_event_head(tmp_path: Path) -> None:
    solar_path = tmp_path / "solar.csv"
    write_csv(
        solar_path,
        [
            ["Time (LCLG)", "Beta Angle (deg)"],
            ["2021/10/2 1:00", 0],
            ["2021/10/2 8:00", 10],
        ],
    )

    assert JudgeSolarClash([[1, 0, 4000, 0, 40]], solar_path) is True


# 验证读取规划事件 CSV 能正确解析数据并跳过表头。
def test_read_planning_events_parses_csv(tmp_path: Path) -> None:
    csv_path = tmp_path / "planningevents.csv"
    write_csv(
        csv_path,
        [
            ["事件ID", "StartTime", "EndTime", "MinAngle", "MaxAngle"],
            [1, 10, 20, 0, 23],
            [2, 30, 40, 5, 25],
        ],
    )

    result = planning_main.read_planning_events(csv_path)
    assert result == [[1.0, 10.0, 20.0, 0.0, 23.0], [2.0, 30.0, 40.0, 5.0, 25.0]]


# 验证功率约束检查：单任务功率低于上限时不应冲突。
def test_judge_welec_clash_no_conflict_for_low_power() -> None:
    # Task 1 in event.xlsx has power 200W, well below 1000W
    result = JudgeWelecClash([[1, 0, 3600]])
    assert result is False


# 验证功率约束检查：并发任务总功率超过 1000W 时应判定冲突。
def test_judge_welec_clash_detects_power_overflow() -> None:
    # Task 13 (800W) + Task 49 (800W) overlapping → 1600W > 1000W
    result = JudgeWelecClash([
        [13, 0, 3600],
        [49, 0, 3600],
    ])
    assert result is True


# 验证功率约束检查：并发任务总功率恰好等于上限时不应冲突。
def test_judge_welec_clash_allows_exact_limit() -> None:
    # Task 13 (800W) + Task 1 (200W) = 1000W exactly
    result = JudgeWelecClash([
        [13, 0, 3600],
        [1, 0, 3600],
    ])
    assert result is False
