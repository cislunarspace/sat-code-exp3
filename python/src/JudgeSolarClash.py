from __future__ import annotations

from pathlib import Path

from data_io import read_solar_angles

DAY_SECONDS = 86_400


def _angle_range_for_segment(
    event_start: float,
    event_end: float,
    segment_start: float,
    start_angle: float,
    segment_end: float,
    end_angle: float,
) -> tuple[float, float] | None:
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
    if min_angle == 0:
        return angle_low < -max_angle or angle_high > max_angle
    in_negative_range = angle_low >= -max_angle and angle_high <= -min_angle
    in_positive_range = angle_low >= min_angle and angle_high <= max_angle
    return not (in_negative_range or in_positive_range)


def JudgeSolarClash(PlanningEvents: list[list[float]], solar_angle_path: Path | None = None) -> bool:
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
