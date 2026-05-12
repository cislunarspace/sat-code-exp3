from __future__ import annotations

from datetime import datetime, timedelta

DAY_SECONDS = 86_400


def seconds_to_datetime(relative_seconds: float, base_time: datetime) -> datetime:
    """将相对秒数转换为以基准日期零点为起点的绝对时间。

    MATLAB 原脚本通过阳光角数据中的日期向量和事件相对时间计算事件实际时间。
    Python 版本把基准时间 `base_time` 归一化到当天 00:00:00，随后叠加
    `relative_seconds`。因此 0 秒对应基准日期零点，86400 秒对应次日零点，
    可以自然处理跨天事件。
    """
    base_day = base_time.replace(hour=0, minute=0, second=0, microsecond=0)
    return base_day + timedelta(seconds=relative_seconds)


def relativetimetodata(relative_times: list[float], base_time: datetime) -> list[datetime]:
    """批量转换事件相对时间。

    `relative_times` 中的每个元素都是相对于 `base_time` 所在日期零点的秒数。
    返回列表与输入顺序一一对应，可用于把规划事件的相对开始、结束时间恢复为
    便于展示或导出的 datetime 对象。
    """
    return [seconds_to_datetime(relative_time, base_time) for relative_time in relative_times]
