"""功率约束检查——事件驱动扫描算法。"""

from __future__ import annotations

from .models import Task


def check_power_overflow(
    schedule: dict[int, float],
    tasks: list[Task],
    max_power: int = 1000,
) -> bool:
    if not schedule:
        return False

    task_map = {task.id: task for task in tasks}
    events: list[tuple[float, int]] = []
    for task_id, start in schedule.items():
        task = task_map[task_id]
        end = start + task.duration
        events.append((start, task.power))
        events.append((end, -task.power))

    events.sort(key=lambda item: (item[0], item[1] > 0))

    current = 0
    for _, delta in events:
        current += delta
        if current > max_power:
            return True
    return False
