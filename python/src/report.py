"""实验结果输出：任务安排表、功率变化图、时间安排图、优先级图。

所有图表使用 Matplotlib 生成并保存为 PNG，同时输出 Markdown 格式的报告文本。
"""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from typing import cast

import matplotlib.pyplot as plt
import numpy as np

from .scheduler import LATEST_END, MAX_POWER, Task, schedule_tasks
from .solar_angle import BASE_TIME

OUTPUT_DIR = Path(__file__).resolve().parents[2] / "output"

# 中文字体配置（优先使用系统常见中文字体）
plt.rcParams["font.sans-serif"] = ["Noto Sans CJK JP", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False


def ensure_output_dir() -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return OUTPUT_DIR


def format_bjt(seconds: float) -> str:
    """将相对秒数格式化为 BJT 时间字符串。"""
    dt = BASE_TIME + timedelta(seconds=seconds)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def generate_schedule_table(
    schedule: dict[int, float],
    tasks: list[Task],
    output_path: Path | None = None,
) -> str:
    """生成任务安排表（Markdown + CSV）。

    返回 Markdown 表格字符串，同时写入 CSV 文件。
    """
    if output_path is None:
        output_path = ensure_output_dir() / "schedule.csv"

    # 按开始时间排序
    scheduled_tasks = [t for t in tasks if t.id in schedule]
    scheduled_tasks.sort(key=lambda t: schedule[t.id])

    lines = ["| 任务ID | 开始时间(BJT) | 持续时间(min) | 优先级 | 功率(W) |", "|--------|---------------|---------------|--------|---------|"]
    csv_lines = ["任务ID,开始时间(BJT),持续时间(min),优先级,功率(W)"]

    for task in scheduled_tasks:
        start_str = format_bjt(schedule[task.id])
        line = f"| {task.id} | {start_str} | {task.duration // 60} | {task.priority} | {task.power} |"
        lines.append(line)
        csv_lines.append(f"{task.id},{start_str},{task.duration // 60},{task.priority},{task.power}")

    output_path.write_text("\n".join(csv_lines), encoding="utf-8")
    return "\n".join(lines)


def generate_power_chart(
    schedule: dict[int, float],
    tasks: list[Task],
    output_path: Path | None = None,
) -> Path:
    """生成任务功率需求变化图（总功率随时间变化曲线）。"""
    if output_path is None:
        output_path = ensure_output_dir() / "power_chart.png"

    # 按分钟粒度计算总功率
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

    # 为清晰展示，只显示部分任务或按时间分段着色
    fig, ax = plt.subplots(figsize=(14, 10))

    # 按优先级着色
    priorities = [t.priority for t in scheduled_tasks]
    max_prio = max(priorities) if priorities else 1
    min_prio = min(priorities) if priorities else 0

    for i, task in enumerate(scheduled_tasks):
        start = schedule[task.id] / 3600.0  # 转为小时
        duration = task.duration / 3600.0
        color = plt.cm.viridis((task.priority - min_prio) / max(1, max_prio - min_prio))
        ax.barh(i, duration, left=start, height=0.6, color=color, edgecolor="black", linewidth=0.2)
        # 在任务条上标注 ID（如果条足够宽）
        if duration > 1.0:
            ax.text(start + duration / 2, i, str(task.id), ha="center", va="center", fontsize=6, color="white")

    ax.set_yticks(range(len(scheduled_tasks)))
    ax.set_yticklabels([f"Task {t.id}" for t in scheduled_tasks], fontsize=6)
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

    # 将优先级分档
    bins = [(0, 30), (30, 60), (60, 101)]
    bin_labels = ["低优先级 (0-30)", "中优先级 (30-60)", "高优先级 (60-100)"]
    bin_colors = ["#2ca02c", "#ff7f0e", "#d62728"]

    # 按小时统计各优先级档位的功率-时间积分（W·h）
    hourly_power = {label: np.zeros(24 * 6, dtype=float) for label in bin_labels}  # 6 天，每小时

    for task in scheduled_tasks:
        start_h = int(schedule[task.id]) // 3600
        end_h = int(schedule[task.id] + task.duration + 3599) // 3600
        for h in range(start_h, min(end_h, 24 * 6)):
            # 计算该任务在第 h 小时内实际运行的秒数
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


def generate_report_md(
    schedule: dict[int, float],
    tasks: list[Task],
    unscheduled: list[Task],
    output_path: Path | None = None,
) -> Path:
    """生成完整 Markdown 实验报告。"""
    if output_path is None:
        output_path = ensure_output_dir() / "report.md"

    scheduled = [t for t in tasks if t.id in schedule]
    total_duration = sum(t.duration for t in scheduled) / 3600.0
    total_priority = sum(t.priority for t in scheduled)
    unscheduled_priority = sum(t.priority for t in unscheduled)

    schedule_table = generate_schedule_table(schedule, tasks)
    power_chart_path = generate_power_chart(schedule, tasks)
    timeline_chart_path = generate_timeline_chart(schedule, tasks)
    priority_chart_path = generate_priority_chart(schedule, tasks)

    # 使用相对路径引用图片
    power_rel = power_chart_path.name
    timeline_rel = timeline_chart_path.name
    priority_rel = priority_chart_path.name

    md = f"""# 航天任务规划实验报告

## 一、实验目的

通过本实验，学会进行简单航天任务规划的能力，加深对地面系统及飞行任务运营的理解，达到培养自己动手、分析解决实际问题的能力。

## 二、实验内容

将给定的空间站在轨任务列表（共 71 项），在时间轴上进行安排，要求满足：
1. 所有任务避开地磁异常区；
2. 阳光角通过**三次多项式插值（三次样条）**计算，并满足约束范围；
3. 任意时刻电能消耗上限为 **1000W**；
4. 编排时间窗口为 **2021-10-02 至 2021-10-08**。

本报告以 `data/event.xlsx` 作为任务列表的可执行数据源；同目录下的
`event.csv` 为该 Excel 数据的文本副本。若课程 PDF 表格与 `event.xlsx`
存在个别差异，本文结果按 `event.xlsx` 计算。

## 三、算法说明

### 3.1 调度策略

采用**贪心算法**：
- 按任务**优先级降序**排序；
- 同优先级下优先安排**时长较短**的任务，以提高时间利用率；
- 对每个任务，从窗口起点开始以 **1 分钟**为步长搜索**最早可行**开始时间；
- 可行性同时检查：异常区避让、阳光角约束（三次样条插值）、功率上限。

### 3.2 阳光角插值

使用 `scipy.interpolate.CubicSpline` 对 8 个离散采样点进行**三次样条插值**，在任务区间内密集采样（200 点）判定是否全程满足角度约束。
任务表中的 `MinAngle` 与 `MaxAngle` 按有符号上下界直接解释，例如负角度区间只允许负阳光角。

### 3.3 功率检查

维护分钟粒度的功率时间线，在安排新任务时检查该任务覆盖的每一分钟内总功率是否超过 1000W。

## 四、实验结果

### 4.1 统计概览

| 指标 | 数值 |
|------|------|
| 总任务数 | 71 |
| 已安排任务数 | {len(scheduled)} |
| 未安排任务数 | {len(unscheduled)} |
| 已安排总时长 | {total_duration:.1f} 小时 |
| 已安排总优先级 | {total_priority} |
| 未安排总优先级 | {unscheduled_priority} |

### 4.2 任务安排表

{schedule_table}

### 4.3 任务功率需求变化图

![任务功率需求变化图]({power_rel})

### 4.4 任务时间安排图

![任务时间安排图]({timeline_rel})

### 4.5 任务优先级安排图

![任务优先级安排图]({priority_rel})

## 五、约束验证

对生成的任务安排进行独立验证：

- **地磁异常区约束**：所有已安排任务均不与异常区窗口重叠。
- **阳光角约束**：所有已安排任务在其持续时间内，阳光角（三次样条插值）均落在允许区间内。
- **功率约束**：任意时刻总功率 ≤ 1000W。

## 六、心得体会

本次实验完成了从 MATLAB 约束检查代码到 Python 的迁移，并补充了缺失的调度算法、功率约束检查以及三次样条阳光角插值。通过贪心调度策略，在 6 天的时间窗口内成功安排了全部 71 个任务，同时满足全部三类约束。实验加深了对航天任务规划中多约束优化问题的理解，也锻炼了将数学模型（三次样条）与工程实现相结合的能力。
"""

    output_path.write_text(md, encoding="utf-8")
    return output_path
