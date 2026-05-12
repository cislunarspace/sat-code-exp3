from __future__ import annotations

from pathlib import Path

from data_io import read_avoid_area_windows


def JudgeAvoidAreaClash(PlanningEvents: list[list[float]], avoid_area_path: Path | None = None) -> bool:
    windows = read_avoid_area_windows(avoid_area_path)
    for event in PlanningEvents:
        start_time = float(event[1])
        end_time = float(event[2])
        for window_start, window_end in windows:
            if end_time < window_start:
                break
            if start_time > window_end:
                continue
            overlap_start = max(start_time, window_start)
            overlap_end = min(end_time, window_end)
            if overlap_start <= overlap_end:
                return True
    return False
