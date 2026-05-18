"""实验图表生成：功率变化图、时间安排图、优先级图。

所有图表使用 Matplotlib 生成并保存为 PNG。
"""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from .scheduler import LATEST_END, MAX_POWER, Task
from .solar_angle import BASE_TIME

OUTPUT_DIR = Path(__file__).resolve().parents[2] / "output"

# ── 字体与字号配置（集中调节区） ──────────────────────────────
plt.rcParams["font.family"] = "serif"
plt.rcParams["font.serif"] = ["Times New Roman", "SimSun", "STSong"]
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["font.size"] = 12
plt.rcParams["axes.titlesize"] = 14
plt.rcParams["axes.labelsize"] = 12
plt.rcParams["legend.fontsize"] = 10
plt.rcParams["xtick.labelsize"] = 10
plt.rcParams["ytick.labelsize"] = 10

# 甘特图局部字号
GANTT_BAR_TEXT_SIZE = 6
GANTT_YTICK_SIZE = 6
# ───────────────────────────────────────────────────────────────


def ensure_output_dir() -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return OUTPUT_DIR


def format_bjt(seconds: float) -> str:
    """将相对秒数格式化为 BJT 时间字符串。"""
    dt = BASE_TIME + timedelta(seconds=seconds)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def generate_power_chart(
    schedule: dict[int, float],
    tasks: list[Task],
    output_path: Path | None = None,
) -> Path:
    """生成任务功率需求变化图（总功率随时间变化曲线）。"""
    if output_path is None:
        output_path = ensure_output_dir() / "power_chart.png"

    n_minutes = int(LATEST_END) // 60 + 1
    timeline = np.zeros(n_minutes, dtype=int)
    for task in tasks:
        if task.id not in schedule:
            continue
        start_min = int(schedule[task.id]) // 60
        end_min = int(schedule[task.id] + task.duration + 59) // 60
        end_min = min(end_min, n_minutes)
        timeline[start_min:end_min] += task.power

    hours = np.arange(n_minutes) / 60.0
    fig, ax = plt.subplots(figsize=(14, 5))
    ax.fill_between(hours, timeline, alpha=0.3, color="tab:blue")
    ax.plot(hours, timeline, color="tab:blue", linewidth=0.8, label="总功率")
    ax.axhline(MAX_POWER, color="red", linestyle="--", linewidth=1.5, label=f"功率上限 {MAX_POWER}W")
    ax.set_xlabel("时间（小时，自 2021-10-02 00:00 起）")
    ax.set_ylabel("功率 (W)")
    ax.set_title("任务功率需求变化图")
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_xlim(0, hours[-1])
    fig.tight_layout()
    fig.savefig(output_path, dpi=200)
    plt.close(fig)
    return output_path


def generate_timeline_chart(
    schedule: dict[int, float],
    tasks: list[Task],
    output_path: Path | None = None,
) -> Path:
    """生成任务时间安排图（Gantt 图）。"""
    if output_path is None:
        output_path = ensure_output_dir() / "timeline_chart.png"

    scheduled_tasks = [t for t in tasks if t.id in schedule]
    scheduled_tasks.sort(key=lambda t: schedule[t.id])

    fig, ax = plt.subplots(figsize=(14, 10))

    priorities = [t.priority for t in scheduled_tasks]
    max_prio = max(priorities) if priorities else 1
    min_prio = min(priorities) if priorities else 0

    for i, task in enumerate(scheduled_tasks):
        start = schedule[task.id] / 3600.0
        duration = task.duration / 3600.0
        color = plt.cm.viridis((task.priority - min_prio) / max(1, max_prio - min_prio))
        ax.barh(i, duration, left=start, height=0.6, color=color, edgecolor="black", linewidth=0.2)
        if duration > 1.0:
            ax.text(start + duration / 2, i, str(task.id), ha="center", va="center", fontsize=GANTT_BAR_TEXT_SIZE, color="white")

    ax.set_yticks(range(len(scheduled_tasks)))
    ax.set_yticklabels([f"Task {t.id}" for t in scheduled_tasks], fontsize=GANTT_YTICK_SIZE)
    ax.set_xlabel("时间（小时，自 2021-10-02 00:00 起）")
    ax.set_title("任务时间安排图")
    ax.grid(True, alpha=0.3, axis="x")
    fig.tight_layout()
    fig.savefig(output_path, dpi=200)
    plt.close(fig)
    return output_path


def generate_priority_chart(
    schedule: dict[int, float],
    tasks: list[Task],
    output_path: Path | None = None,
) -> Path:
    """生成任务优先级安排图（按优先级的堆叠功率柱状图）。"""
    if output_path is None:
        output_path = ensure_output_dir() / "priority_chart.png"

    scheduled_tasks = [t for t in tasks if t.id in schedule]

    bins = [(0, 30), (30, 60), (60, 101)]
    bin_labels = ["低优先级 (0-30)", "中优先级 (30-60)", "高优先级 (60-100)"]
    bin_colors = ["#2ca02c", "#ff7f0e", "#d62728"]

    hourly_power = {label: np.zeros(24 * 6, dtype=float) for label in bin_labels}

    for task in scheduled_tasks:
        start_h = int(schedule[task.id]) // 3600
        end_h = int(schedule[task.id] + task.duration + 3599) // 3600
        for h in range(start_h, min(end_h, 24 * 6)):
            h_start = h * 3600
            h_end = (h + 1) * 3600
            overlap_start = max(schedule[task.id], h_start)
            overlap_end = min(schedule[task.id] + task.duration, h_end)
            if overlap_end > overlap_start:
                overlap_hours = (overlap_end - overlap_start) / 3600.0
                for (low, high), label in zip(bins, bin_labels):
                    if low <= task.priority < high:
                        hourly_power[label][h] += task.power * overlap_hours
                        break

    hours = np.arange(24 * 6)
    fig, ax = plt.subplots(figsize=(14, 5))
    bottom = np.zeros(24 * 6)
    for label, color in zip(bin_labels, bin_colors):
        ax.bar(hours, hourly_power[label], bottom=bottom, width=1.0, color=color, label=label, edgecolor="none")
        bottom += hourly_power[label]

    ax.axhline(MAX_POWER, color="black", linestyle="--", linewidth=1.5, label=f"功率上限 {MAX_POWER}W")
    ax.set_xlabel("时间（小时，自 2021-10-02 00:00 起）")
    ax.set_ylabel("功率 (W)")
    ax.set_title("任务优先级安排图（按优先级分色的功率堆叠图）")
    ax.legend()
    ax.grid(True, alpha=0.3, axis="y")
    fig.tight_layout()
    fig.savefig(output_path, dpi=200)
    plt.close(fig)
    return output_path
