"""轨道阳光角三次样条插值与约束判定工具。

本模块将离散的阳光角采样数据拟合为三次样条曲线，支持在任意时刻查询阳光角
并判定事件是否满足角度约束。与原有线性插值不同，这里使用三次多项式插值
（scipy.interpolate.CubicSpline），满足实验要求中“阳光角通过三次多项式插值
计算”的规定。
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import cast

import numpy as np
from scipy.interpolate import CubicSpline

from .data_io import read_solar_angles

# 规划窗口基准时间
BASE_TIME = datetime(2021, 10, 2, 0, 0)


class SolarAngleModel:
    """基于三次样条的阳光角插值模型。

    读取 CSV 中的离散采样点，构建 `CubicSpline` 插值器。模型在采样区间内部
    使用分段三次多项式精确插值，在区间外返回 NaN（避免外推导致错误判断）。
    """

    def __init__(self, solar_angle_path: Path | None = None) -> None:
        solar_angles = read_solar_angles(solar_angle_path)
        if len(solar_angles) < 2:
            raise ValueError(
                f"Need at least 2 sample points, got {len(solar_angles)}"
            )
        # solar_angles: list of (angle, relative_seconds)
        self._times = np.array([t for _, t in solar_angles], dtype=float)
        self._angles = np.array([a for a, _ in solar_angles], dtype=float)
        self._t_min = float(self._times[0])
        self._t_max = float(self._times[-1])

        # Use cubic spline when enough points, otherwise linear interpolation
        if len(solar_angles) >= 4:
            self._cs = CubicSpline(self._times, self._angles)
            self._interp_kind = "cubic"
        else:
            self._cs = None
            self._interp_kind = "linear"

    def angle_at(self, t: float | np.ndarray) -> float | np.ndarray:
        """查询相对秒数 ``t`` 处的阳光角（度）。

        若 ``t`` 超出采样范围，返回 NaN。
        """
        if isinstance(t, np.ndarray):
            valid = (t >= self._t_min) & (t <= self._t_max)
            if not np.any(valid):
                return np.full_like(t, np.nan, dtype=float)
            result = np.full_like(t, np.nan, dtype=float)
            valid_t = t[valid]
            if self._interp_kind == "cubic":
                result[valid] = self._cs(valid_t)
            else:
                result[valid] = np.interp(valid_t, self._times, self._angles)
            return result
        if t < self._t_min or t > self._t_max:
            return float("nan")
        if self._interp_kind == "cubic":
            return float(self._cs(t))
        return float(np.interp(t, self._times, self._angles))

    def min_max_in_interval(self, start: float, end: float, n_samples: int = 200) -> tuple[float, float]:
        """在闭区间 ``[start, end]`` 上近似求阳光角的最小值和最大值。

        采用均匀密集采样 + 边界点求值的方式。由于三次样条是光滑函数，
        200 个采样点对于典型任务时长（数分钟到数小时）已足够精确。
        返回 ``(min_angle, max_angle)``。
        """
        if end < start:
            raise ValueError("end must be >= start")
        # Include exact boundaries
        sample_times = np.linspace(start, end, n_samples)
        values = cast(np.ndarray, self.angle_at(sample_times))
        valid = ~np.isnan(values)
        if not np.any(valid):
            return float("nan"), float("nan")
        return float(np.min(values[valid])), float(np.max(values[valid]))

    def is_valid_for_task(
        self,
        start: float,
        end: float,
        min_angle: float,
        max_angle: float,
        n_samples: int = 200,
    ) -> bool:
        """判断任务时间区间 ``[start, end]`` 是否全程满足阳光角约束。

        约束定义与 MATLAB 版本一致：
        - ``min_angle == 0``：允许区间 ``[-max_angle, max_angle]``；
        - ``min_angle != 0``：允许区间 ``[-max_angle, -min_angle] ∪ [min_angle, max_angle]``。

        若区间任何部分超出采样范围，直接判定为不满足（返回 False）。
        """
        if end < start:
            return False
        if start < self._t_min or end > self._t_max:
            return False

        sample_times = np.linspace(start, end, n_samples)
        values = cast(np.ndarray, self.angle_at(sample_times))
        if np.any(np.isnan(values)):
            return False

        if min_angle == 0:
            return bool(np.all((values >= -max_angle) & (values <= max_angle)))

        neg_ok = (values >= -max_angle) & (values <= -min_angle)
        pos_ok = (values >= min_angle) & (values <= max_angle)
        return bool(np.all(neg_ok | pos_ok))


def create_default_model() -> SolarAngleModel:
    """使用默认数据文件创建阳光角模型。"""
    return SolarAngleModel()
