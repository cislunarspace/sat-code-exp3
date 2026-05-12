from __future__ import annotations

from pathlib import Path

from .data_io import read_solar_angles

DAY_SECONDS = 86_400


def _angle_range_for_segment(
    event_start: float,
    event_end: float,
    segment_start: float,
    start_angle: float,
    segment_end: float,
    end_angle: float,
) -> tuple[float, float] | None:
    """计算事件与单个阳光角采样分段重叠部分的角度范围。

    阳光角 CSV 提供离散采样点，每两个相邻采样点构成一个线性变化分段。
    本函数先求事件时间区间与该分段时间区间的交集，再按交集端点在分段中的
    相对位置做线性插值，得到交集开始和结束时刻的阳光角。返回值始终按
    `(较小角度, 较大角度)` 排序，便于后续只用范围边界判断是否满足约束。

    如果事件与该分段没有时间重叠，或分段时长无效，则返回 None。
    """
    overlap_start = max(event_start, segment_start)
    overlap_end = min(event_end, segment_end)
    if overlap_start > overlap_end:
        return None

    duration = segment_end - segment_start
    if duration <= 0:
        return None

    start_ratio = (overlap_start - segment_start) / duration
    end_ratio = (overlap_end - segment_start) / duration
    angle_at_start = start_angle + (end_angle - start_angle) * start_ratio
    angle_at_end = start_angle + (end_angle - start_angle) * end_ratio
    return min(angle_at_start, angle_at_end), max(angle_at_start, angle_at_end)


def _violates_angle_constraint(min_angle: float, max_angle: float, angle_low: float, angle_high: float) -> bool:
    """判断某段阳光角范围是否超出事件允许的角度约束。

    PlanningEvents 的第 4、5 列分别表示允许阳光角绝对值的最小值和最大值。
    当最小值为 0 时，允许区间是连续的 `[-max_angle, max_angle]`。
    当最小值不为 0 时，允许区间分裂为负向区间
    `[-max_angle, -min_angle]` 和正向区间 `[min_angle, max_angle]`，
    角度范围必须完整落在其中一个区间内才算满足约束。

    返回 True 表示该角度范围违反约束，返回 False 表示满足约束。
    """
    if min_angle == 0:
        return angle_low < -max_angle or angle_high > max_angle
    in_negative_range = angle_low >= -max_angle and angle_high <= -min_angle
    in_positive_range = angle_low >= min_angle and angle_high <= max_angle
    return not (in_negative_range or in_positive_range)


def JudgeSolarClash(PlanningEvents: list[list[float]], solar_angle_path: Path | None = None) -> bool:
    """判断规划事件是否违反轨道阳光角约束。

    PlanningEvents 沿用 MATLAB 版本的数据列约定：第 2、3 列为事件相对开始、
    结束时间，第 4、5 列为该事件允许的最小和最大阳光角绝对值，时间单位为秒，
    角度单位为度。阳光角数据来自 CSV 的 `Time (LCLG)` 与
    `Beta Angle (deg)` 列，读取后转换为 `(阳光角, 相对秒数)` 采样序列。

    Python 版本不再假设相邻阳光角采样一定相隔 86400 秒，而是按 CSV 中实际
    时间形成分段，并对事件与每个分段的重叠部分做线性插值。只要某个事件的
    任一重叠角度范围超出允许区间，或事件时间超出最后一个阳光角采样点，
    即返回 True；全部事件均满足约束时返回 False。
    """
    solar_angles = read_solar_angles(solar_angle_path)
    if len(solar_angles) < 2:
        return bool(PlanningEvents)

    last_time = solar_angles[-1][1]
    for event in PlanningEvents:
        event_start = float(event[1])
        event_end = float(event[2])
        min_angle = float(event[3])
        max_angle = float(event[4])
        if event_start > last_time or event_end > last_time:
            return True

        for (start_angle, segment_start), (end_angle, segment_end) in zip(solar_angles, solar_angles[1:]):
            angle_range = _angle_range_for_segment(
                event_start,
                event_end,
                segment_start,
                start_angle,
                segment_end,
                end_angle,
            )
            if angle_range is None:
                continue
            angle_low, angle_high = angle_range
            if _violates_angle_constraint(min_angle, max_angle, angle_low, angle_high):
                return True
    return False
