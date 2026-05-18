"""航天任务规划约束检查与调度入口。

本脚本执行完整的实验流程：
1. 使用贪心算法安排任务（满足异常区、阳光角、功率约束）；
2. 对生成的安排进行三类约束验证；
3. 生成图表和任务安排表（CSV）。
"""

from __future__ import annotations

from pathlib import Path

from src.JudgeAvoidAreaClash import JudgeAvoidAreaClash
from src.JudgeSolarClash import JudgeSolarClash
from src.JudgeWelecClash import JudgeWelecClash
from src.models import Task
from src.plot import ensure_output_dir, format_bjt, generate_power_chart, generate_priority_chart, generate_timeline_chart
from src.scheduler import schedule_tasks


def save_schedule_csv(schedule: dict[int, float], tasks: list[Task], output_path: Path | None = None) -> Path:
    """将任务安排写入 CSV 文件。"""
    if output_path is None:
        output_path = ensure_output_dir() / "schedule.csv"

    scheduled_tasks = [t for t in tasks if t.id in schedule]
    scheduled_tasks.sort(key=lambda t: schedule[t.id])

    csv_lines = ["开始时间(BJT),任务ID,持续时间(min),优先级"]
    for task in scheduled_tasks:
        start_str = format_bjt(schedule[task.id])
        csv_lines.append(f"\t{start_str},{task.id},{task.duration // 60},{task.priority}")

    output_path.write_bytes(b"\xef\xbb\xbf" + "\n".join(csv_lines).encode("utf-8"))
    return output_path


def main() -> None:
    """执行完整实验流程并打印结果摘要。"""
    print("=" * 60)
    print("航天任务规划实验")
    print("=" * 60)

    print("\n[1] 正在执行贪心调度...")
    scheduled_tasks, schedule, unscheduled = schedule_tasks()
    print(f"    已安排: {len(schedule)}/71")
    print(f"    未安排: {len(unscheduled)}")
    if unscheduled:
        print(f"    未安排任务 ID: {[t.id for t in unscheduled]}")

    print(f"\n[2] 对调度结果进行约束验证...")
    avoid_clash = JudgeAvoidAreaClash(schedule, scheduled_tasks)
    solar_clash = JudgeSolarClash(schedule, scheduled_tasks)
    power_clash = JudgeWelecClash(schedule, scheduled_tasks)
    print(f"    异常区冲突: {avoid_clash}")
    print(f"    阳光角冲突: {solar_clash}")
    print(f"    功率冲突:   {power_clash}")

    assert not avoid_clash, "调度结果不应存在异常区冲突"
    assert not solar_clash, "调度结果不应存在阳光角冲突"
    assert not power_clash, "调度结果不应存在功率冲突"

    print("\n[3] 正在生成图表和任务安排表...")
    schedule_path = save_schedule_csv(schedule, scheduled_tasks)
    power_path = generate_power_chart(schedule, scheduled_tasks)
    timeline_path = generate_timeline_chart(schedule, scheduled_tasks)
    priority_path = generate_priority_chart(schedule, scheduled_tasks)

    print("    已保存:")
    print(f"    - {schedule_path}")
    print(f"    - {power_path}")
    print(f"    - {timeline_path}")
    print(f"    - {priority_path}")

    print("\n" + "=" * 60)
    print("实验完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
