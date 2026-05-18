"""轨道阳光角约束检查（三次样条插值版本）。

本模块将原有的线性插值升级为三次多项式插值，满足实验要求：
“阳光角通过三次多项式插值计算，满足在约束范围内”。
"""

from __future__ import annotations

from pathlib import Path

from .solar_angle import SolarAngleModel


def JudgeSolarClash(PlanningEvents: list[list[float]], solar_angle_path: Path | None = None) -> bool:
    """判断规划事件是否违反轨道阳光角约束。

    PlanningEvents 沿用任务表的数据列约定：第 2、3 列为事件相对开始、
    结束时间，第 4、5 列为该事件允许的有符号最小和最大阳光角，时间单位为秒，
    角度单位为度。阳光角数据来自 CSV，经 ``SolarAngleModel`` 三次样条插值后
    进行约束判定。

    只要某个事件的任一时刻超出允许区间，或事件时间超出阳光角采样覆盖范围，
    即返回 True；全部事件均满足约束时返回 False。
    """
    model = SolarAngleModel(solar_angle_path)
    for event in PlanningEvents:
        event_start = float(event[1])
        event_end = float(event[2])
        min_angle = float(event[3])
        max_angle = float(event[4])
        if not model.is_valid_for_task(event_start, event_end, min_angle, max_angle):
            return True
    return False
