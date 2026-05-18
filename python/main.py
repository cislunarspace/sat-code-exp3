"""航天任务规划约束检查与调度入口。

本脚本执行完整的实验流程：
1. 读取任务列表、异常区窗口、阳光角采样数据；
2. 使用贪心算法安排任务（满足异常区、阳光角、功率约束）；
3. 对生成的安排进行三类约束验证；
4. 生成实验报告（Markdown + 图表 + CSV）。
"""

from __future__ import annotations

from pathlib import Path

import csv

from src.JudgeAvoidAreaClash import JudgeAvoidAreaClash
from src.JudgeSolarClash import JudgeSolarClash
from src.JudgeWelecClash import JudgeWelecClash
from src.report import generate_report_md
from src.scheduler import Task, schedule_tasks

ROOT_DIR = Path(__file__).resolve().parents[1]


def read_planning_events(path: Path | None = None) -> list[list[float]]:
    """读取规划事件表并转换为约束检查所需的数值矩阵。

    默认读取 `data/planningevents.csv`，也可以通过 `path` 指定其他 CSV 文件。
    表格第 1 行视为表头，从第 2 行开始读取；空行或首列为空的行会被跳过。
    每条事件只取前 5 列并转为 float，保持与 MATLAB 版本 PlanningEvents 矩阵一致。
    """
    csv_path = path or ROOT_DIR / "data" / "planningevents.csv"
    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        rows: list[list[float]] = []
        next(reader)  # skip header
        for row in reader:
            if not row or not row[0]:
                continue
            rows.append([float(v) for v in row[:5]])
        return rows


def convert_schedule_to_events(schedule: dict[int, float], tasks: list[Task]) -> list[list[float]]:
    """将调度结果转换为 PlanningEvents 矩阵格式。"""
    task_map = {t.id: t for t in tasks}
    events: list[list[float]] = []
    for tid, start in sorted(schedule.items(), key=lambda x: x[1]):
        task = task_map[tid]
        events.append([
            float(tid),
            float(start),
            float(start + task.duration),
            float(task.min_angle),
            float(task.max_angle),
        ])
    return events


def main() -> None:
    """执行完整实验流程并打印结果摘要。"""
    print("=" * 60)
    print("航天任务规划实验")
    print("=" * 60)

    # 1. 读取已有规划（用于对比/验证）
    planning_events = read_planning_events()
    print(f"\n[1] 已有规划事件数: {len(planning_events)}")
    if planning_events:
        avoid_area_clash = JudgeAvoidAreaClash(planning_events)
        solar_clash = JudgeSolarClash(planning_events)
        print(f"    异常区冲突: {avoid_area_clash}")
        print(f"    阳光角冲突: {solar_clash}")

    # 2. 执行贪心调度
    print("\n[2] 正在执行贪心调度...")
    scheduled_tasks, schedule, unscheduled = schedule_tasks()
    print(f"    已安排: {len(schedule)}/71")
    print(f"    未安排: {len(unscheduled)}")
    if unscheduled:
        print(f"    未安排任务 ID: {[t.id for t in unscheduled]}")

    # 3. 将调度结果转为 PlanningEvents 并验证
    scheduled_events = convert_schedule_to_events(schedule, scheduled_tasks)
    print(f"\n[3] 对调度结果进行约束验证...")
    avoid_clash = JudgeAvoidAreaClash(scheduled_events)
    solar_clash = JudgeSolarClash(scheduled_events)
    power_clash = JudgeWelecClash(scheduled_events)
    print(f"    异常区冲突: {avoid_clash}")
    print(f"    阳光角冲突: {solar_clash}")
    print(f"    功率冲突:   {power_clash}")

    assert not avoid_clash, "调度结果不应存在异常区冲突"
    assert not solar_clash, "调度结果不应存在阳光角冲突"
    assert not power_clash, "调度结果不应存在功率冲突"

    # 4. 生成报告
    print("\n[4] 正在生成实验报告...")
    report_path = generate_report_md(schedule, scheduled_tasks, unscheduled)
    print(f"    报告已保存: {report_path}")

    print("\n" + "=" * 60)
    print("实验完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
