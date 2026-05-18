from __future__ import annotations

import csv
from pathlib import Path

from src.JudgeAvoidAreaClash import JudgeAvoidAreaClash
from src.JudgeSolarClash import JudgeSolarClash
from src.JudgeWelecClash import JudgeWelecClash
from src.data_io import find_csv_by_headers, read_avoid_area_windows, read_solar_angles
from src.models import Task


def write_csv(path: Path, rows: list[list[object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerows(rows)


def make_task(
    task_id: int,
    duration: int,
    power: int = 100,
    min_angle: float = 0,
    max_angle: float = 20,
    priority: int = 1,
) -> Task:
    return Task(
        id=task_id,
        duration=duration,
        power=power,
        min_angle=min_angle,
        max_angle=max_angle,
        priority=priority,
    )


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

    try:
        find_csv_by_headers({"Time (LCLG)", "Beta Angle (deg)"}, tmp_path)
    except ValueError as exc:
        assert "Multiple CSV files" in str(exc)
    else:
        raise AssertionError("ambiguous CSV files should raise ValueError")


def test_judge_avoid_area_clash_detects_overlap(tmp_path: Path) -> None:
    avoid_path = tmp_path / "avoid.csv"
    write_csv(
        avoid_path,
        [
            ["", "开始时间", "结束时间", "持续时间 (min)"],
            [1, "2021-10-02 00:10:00", "2021-10-02 00:20:00", 10],
        ],
    )

    tasks = [make_task(1, 200)]

    assert JudgeAvoidAreaClash({1: 500}, tasks, avoid_path) is True
    assert JudgeAvoidAreaClash({1: 1300}, tasks, avoid_path) is False


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

    assert JudgeAvoidAreaClash({1: 500}, [make_task(1, 200)], avoid_path) is True


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

    assert JudgeSolarClash({1: 0}, [make_task(1, 28800, min_angle=0, max_angle=20)], solar_path) is True
    assert JudgeSolarClash({1: 0}, [make_task(1, 28800, min_angle=0, max_angle=40)], solar_path) is False


def test_judge_solar_clash_treats_signed_ranges_literally(tmp_path: Path) -> None:
    solar_path = tmp_path / "solar.csv"
    write_csv(
        solar_path,
        [
            ["Time (LCLG)", "Beta Angle (deg)"],
            ["2021/10/2 0:00", 10],
            ["2021/10/2 8:00", 12],
        ],
    )

    assert JudgeSolarClash({1: 0}, [make_task(1, 28800, min_angle=-20, max_angle=-2)], solar_path) is True
    assert JudgeSolarClash({1: 0}, [make_task(1, 28800, min_angle=2, max_angle=20)], solar_path) is False


def test_judge_solar_clash_accepts_negative_signed_ranges(tmp_path: Path) -> None:
    solar_path = tmp_path / "solar.csv"
    write_csv(
        solar_path,
        [
            ["Time (LCLG)", "Beta Angle (deg)"],
            ["2021/10/2 0:00", -12],
            ["2021/10/2 8:00", -10],
        ],
    )

    assert JudgeSolarClash({1: 0}, [make_task(1, 28800, min_angle=-20, max_angle=-2)], solar_path) is False


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

    assert JudgeSolarClash({1: 28000}, [make_task(1, 2000, min_angle=0, max_angle=40)], solar_path) is True


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

    assert JudgeSolarClash({1: 0}, [make_task(1, 4000, min_angle=0, max_angle=40)], solar_path) is True


def test_judge_welec_clash_no_conflict_for_low_power() -> None:
    result = JudgeWelecClash({1: 0}, [make_task(1, 3600, power=200)])
    assert result is False


def test_judge_welec_clash_detects_power_overflow() -> None:
    result = JudgeWelecClash(
        {13: 0, 49: 0},
        [make_task(13, 3600, power=800), make_task(49, 3600, power=800)],
    )
    assert result is True


def test_judge_welec_clash_allows_exact_limit() -> None:
    result = JudgeWelecClash(
        {13: 0, 1: 0},
        [make_task(13, 3600, power=800), make_task(1, 3600, power=200)],
    )
    assert result is False


def test_judge_welec_clash_rejects_unknown_task_id() -> None:
    try:
        JudgeWelecClash({999: 0}, [make_task(1, 3600)])
    except KeyError as exc:
        assert "999" in str(exc)
    else:
        raise AssertionError("unknown task ID should raise KeyError")


def test_judge_welec_clash_allows_back_to_back_tasks_at_limit() -> None:
    result = JudgeWelecClash(
        {13: 0, 49: 3600},
        [make_task(13, 3600, power=800), make_task(49, 3600, power=800)],
    )
    assert result is False


def test_power_tracker_matches_sweep_algorithm() -> None:
    """交叉验证：PowerTracker 和事件扫描算法对相同输入判定一致。"""
    from src.power_check import check_power_overflow
    from src.scheduler import PowerTracker

    tasks = [make_task(1, 3600, power=600), make_task(2, 3600, power=600)]

    # 场景 A：两任务不重叠 → 均应返回 False
    schedule_a = {1: 0, 2: 3600}
    tracker_a = PowerTracker()
    for t in tasks:
        tracker_a.place(schedule_a[t.id], t.duration, t.power)
    sweep_a = check_power_overflow(schedule_a, tasks)
    tracker_a_overflow = bool((tracker_a.timeline > 1000).any())
    assert sweep_a == tracker_a_overflow == False

    # 场景 B：两任务重叠 → 均应返回 True
    schedule_b = {1: 0, 2: 0}
    sweep_b = check_power_overflow(schedule_b, tasks)
    tracker_b = PowerTracker()
    tracker_b.place(0, 3600, 600)
    tracker_b.place(0, 3600, 600)
    tracker_b_ok = bool((tracker_b.timeline > 1000).any())
    assert sweep_b == tracker_b_ok == True

    # 场景 C：总功率恰好等于上限 → 均应返回 False
    schedule_c = {1: 0, 2: 0}
    tasks_c = [make_task(1, 3600, power=600), make_task(2, 3600, power=400)]
    sweep_c = check_power_overflow(schedule_c, tasks_c)
    tracker_c = PowerTracker()
    tracker_c.place(0, 3600, 600)
    tracker_c.place(0, 3600, 400)
    tracker_c_overflow = bool((tracker_c.timeline > 1000).any())
    assert sweep_c == tracker_c_overflow == False
