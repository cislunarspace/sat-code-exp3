"""轨道阳光角约束检查（三次样条插值版本）。"""

from __future__ import annotations

from pathlib import Path

from .models import Task
from .solar_angle import SolarAngleModel


def JudgeSolarClash(
    schedule: dict[int, float],
    tasks: list[Task],
    solar_angle_path: Path | None = None,
) -> bool:
    task_map = {task.id: task for task in tasks}
    model = SolarAngleModel(solar_angle_path)
    for task_id, event_start in schedule.items():
        task = task_map[task_id]
        event_end = event_start + task.duration
        if not model.is_valid_for_task(
            event_start,
            event_end,
            task.min_angle,
            task.max_angle,
        ):
            return True
    return False
