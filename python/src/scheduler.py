"""航天任务贪心调度器。"""

from __future__ import annotations

import numpy as np

from .data_io import read_anomaly_windows, read_tasks
from .models import Task
from .solar_angle import SolarAngleModel

WINDOW_START = 0.0
WINDOW_END = 6 * 86_400.0
LATEST_END = 6 * 86_400.0 + 8 * 3_600.0
SEARCH_STEP = 60
MAX_POWER = 1000


class PowerTracker:
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
    if tasks is None:
        tasks = read_tasks()
    if solar_model is None:
        solar_model = SolarAngleModel()
    if anomaly_windows is None:
        anomaly_windows = read_anomaly_windows()

    sorted_tasks = sorted(tasks, key=lambda t: (-t.priority, t.duration))

    tracker = PowerTracker()
    schedule: dict[int, float] = {}
    scheduled_tasks: list[Task] = []
    unscheduled: list[Task] = []

    for task in sorted_tasks:
        placed = False
        max_start = min(WINDOW_END, LATEST_END - task.duration)
        for start_sec in range(int(WINDOW_START), int(max_start) + 1, SEARCH_STEP):
            end_sec = start_sec + task.duration
            if end_sec > LATEST_END:
                break

            overlap = False
            for a_start, a_end in anomaly_windows:
                if end_sec > a_start and start_sec < a_end:
                    overlap = True
                    break
            if overlap:
                continue

            if not solar_model.is_valid_for_task(
                start_sec, end_sec, task.min_angle, task.max_angle
            ):
                continue

            if not tracker.can_place(start_sec, task.duration, task.power):
                continue

            tracker.place(start_sec, task.duration, task.power)
            schedule[task.id] = float(start_sec)
            scheduled_tasks.append(task)
            placed = True
            break

        if not placed:
            unscheduled.append(task)

    return scheduled_tasks, schedule, unscheduled
