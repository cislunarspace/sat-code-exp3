"""航天任务贪心调度器。

将 71 个在轨任务按照优先级降序排序，逐个寻找最早可行的开始时间。
可行性要求同时满足：
1. 任务完全位于编排窗口内；
2. 不与任何地磁异常区窗口重叠；
3. 全程满足轨道阳光角约束（三次样条插值）；
4. 任意时刻总功率不超过 1000W。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import csv

import numpy as np

from .solar_angle import SolarAngleModel

# 规划窗口：2021-10-02 00:00 到 2021-10-08 00:00
WINDOW_START = 0.0
WINDOW_END = 6 * 86_400.0  # 6 天 = 518400 秒
# 任务最晚结束时间：不能超过阳光角采样末点（Oct 8 08:00）
LATEST_END = 6 * 86_400.0 + 8 * 3_600.0  # 547200 秒

# 搜索步长：1 分钟
SEARCH_STEP = 60

# 功率上限
MAX_POWER = 1000


@dataclass(frozen=True, slots=True)
class Task:
    id: int
    duration: int  # 秒
    power: int  # W
    min_angle: float
    max_angle: float
    priority: int


def read_tasks(path: Path | None = None) -> list[Task]:
    """从 event.csv 读取任务列表。"""
    if path is None:
        from .data_io import ROOT_DIR

        path = ROOT_DIR / "data" / "event.csv"

    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        next(reader)  # skip header
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


def read_anomaly_windows(path: Path | None = None) -> list[tuple[float, float]]:
    """读取异常区窗口并转换为相对秒数区间。"""
    from .data_io import read_avoid_area_windows

    return read_avoid_area_windows(path)


class PowerTracker:
    """基于分钟粒度的时间线功率追踪器。"""

    def __init__(self, window_end: float = LATEST_END) -> None:
        self.n_minutes = int(window_end) // 60 + 1
        self.timeline = np.zeros(self.n_minutes, dtype=int)

    def can_place(self, start: float, duration: int, power: int) -> bool:
        start_min = int(start) // 60
        end_min = int(start + duration + 59) // 60
        end_min = min(end_min, self.n_minutes)
        if start_min >= self.n_minutes:
            return False
        new_power = self.timeline[start_min:end_min] + power
        return bool(np.all(new_power <= MAX_POWER))

    def place(self, start: float, duration: int, power: int) -> None:
        start_min = int(start) // 60
        end_min = int(start + duration + 59) // 60
        end_min = min(end_min, self.n_minutes)
        self.timeline[start_min:end_min] += power


def schedule_tasks(
    tasks: list[Task] | None = None,
    solar_model: SolarAngleModel | None = None,
    anomaly_windows: list[tuple[float, float]] | None = None,
) -> tuple[list[Task], dict[int, float], list[Task]]:
    """执行贪心调度。

    Parameters
    ----------
    tasks :
        任务列表，默认从 ``data/event.csv`` 读取。
    solar_model :
        阳光角插值模型，默认新建。
    anomaly_windows :
        异常区窗口列表，默认从 CSV 读取。

    Returns
    -------
    scheduled_tasks :
        已安排的任务列表（按调度顺序）。
    schedule :
        任务 ID → 相对开始时间（秒）的映射。
    unscheduled :
        未能安排的任务列表。
    """
    if tasks is None:
        tasks = read_tasks()
    if solar_model is None:
        solar_model = SolarAngleModel()
    if anomaly_windows is None:
        anomaly_windows = read_anomaly_windows()

    # 按优先级降序排序；同优先级按时长升序（先排短任务，提高利用率）
    sorted_tasks = sorted(tasks, key=lambda t: (-t.priority, t.duration))

    tracker = PowerTracker()
    schedule: dict[int, float] = {}
    scheduled_tasks: list[Task] = []
    unscheduled: list[Task] = []

    for task in sorted_tasks:
        placed = False
        max_start = min(WINDOW_END, LATEST_END - task.duration)
        # 从窗口起点开始，以 1 分钟为步长搜索最早可行开始时间
        for start_sec in range(int(WINDOW_START), int(max_start) + 1, SEARCH_STEP):
            end_sec = start_sec + task.duration
            if end_sec > LATEST_END:
                break

            # 1. 异常区检查
            overlap = False
            for a_start, a_end in anomaly_windows:
                if end_sec > a_start and start_sec < a_end:
                    overlap = True
                    break
            if overlap:
                continue

            # 2. 阳光角检查
            if not solar_model.is_valid_for_task(
                start_sec, end_sec, task.min_angle, task.max_angle
            ):
                continue

            # 3. 功率检查
            if not tracker.can_place(start_sec, task.duration, task.power):
                continue

            # 安排任务
            tracker.place(start_sec, task.duration, task.power)
            schedule[task.id] = float(start_sec)
            scheduled_tasks.append(task)
            placed = True
            break

        if not placed:
            unscheduled.append(task)

    return scheduled_tasks, schedule, unscheduled
