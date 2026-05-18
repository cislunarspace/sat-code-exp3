from __future__ import annotations

from pathlib import Path

from .data_io import read_avoid_area_windows
from .models import Task


def JudgeAvoidAreaClash(
    schedule: dict[int, float],
    tasks: list[Task],
    avoid_area_path: Path | None = None,
) -> bool:
    """判断已安排任务是否与异常区时间窗口发生冲突。"""
    task_map = {task.id: task for task in tasks}
    windows = read_avoid_area_windows(avoid_area_path)
    for task_id, start_time in schedule.items():
        task = task_map[task_id]
        end_time = start_time + task.duration
        for window_start, window_end in windows:
            if end_time < window_start:
                break
            if start_time > window_end:
                continue
            overlap_start = max(start_time, window_start)
            overlap_end = min(end_time, window_end)
            if overlap_start < overlap_end:
                return True
    return False
