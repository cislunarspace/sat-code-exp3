"""电能（功率）约束检查。"""

from __future__ import annotations

from .models import Task
from .power_check import check_power_overflow

MAX_POWER = 1000


def JudgeWelecClash(
    schedule: dict[int, float],
    tasks: list[Task],
    max_power: int = MAX_POWER,
) -> bool:
    return check_power_overflow(schedule, tasks, max_power)
