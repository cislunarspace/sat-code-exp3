from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Task:
    id: int
    duration: int  # seconds
    power: int  # W
    min_angle: float
    max_angle: float
    priority: int
