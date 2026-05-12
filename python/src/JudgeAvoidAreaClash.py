from __future__ import annotations

from pathlib import Path

from .data_io import read_avoid_area_windows


def JudgeAvoidAreaClash(PlanningEvents: list[list[float]], avoid_area_path: Path | None = None) -> bool:
    """判断规划事件是否与异常区时间窗口发生冲突。

    PlanningEvents 沿用 MATLAB 版本的数据列约定：第 2 列为事件相对开始时间，
    第 3 列为事件相对结束时间，单位均为秒。异常区窗口来自 CSV 数据，
    `read_avoid_area_windows` 会将“开始时间”和“持续时间 (min)”转换为
    `[window_start, window_end]` 形式的相对秒数区间；窗口应按开始时间升序排列，
    因为判定逻辑会在当前事件早于后续窗口时提前结束内层遍历。

    只要任一事件与任一异常区窗口存在闭区间交集，即认为违反异常区约束并返回
    True；所有事件都没有交集时返回 False。与 MATLAB 版本累加重叠时长不同，
    Python 版本在发现首个交集后立即返回，结果等价但避免了不必要的遍历。
    """
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
