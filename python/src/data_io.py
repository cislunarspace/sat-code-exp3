from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from typing import Iterable

ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "data"


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    """按表头读取 CSV，并兼容 UTF-8 BOM 文件。"""
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def _data_files() -> Iterable[Path]:
    return DATA_DIR.glob("*.csv")


def find_csv_by_headers(required_headers: set[str]) -> Path:
    """在 data 目录中查找唯一一个包含指定表头集合的 CSV 文件。

    MATLAB 版本在函数中写死了 AvoidAeraWindow.csv、SolarAngle.csv 等绝对路径。
    Python 版本改为按必要表头识别数据文件，使文件名变化时仍能读取正确数据。
    如果没有匹配文件或匹配到多个文件，会显式报错，避免静默使用错误数据。
    """
    matches: list[Path] = []
    for path in sorted(_data_files()):
        with path.open("r", encoding="utf-8-sig", newline="") as file:
            reader = csv.reader(file)
            try:
                headers = {header.strip() for header in next(reader)}
            except StopIteration:
                continue
        if required_headers.issubset(headers):
            matches.append(path)
    if not matches:
        raise FileNotFoundError(f"No CSV in {DATA_DIR} contains headers: {sorted(required_headers)}")
    if len(matches) > 1:
        names = ", ".join(path.name for path in matches)
        raise ValueError(f"Multiple CSV files contain headers {sorted(required_headers)}: {names}")
    return matches[0]


def parse_datetime(value: str) -> datetime:
    """解析项目 CSV 中出现的日期时间字符串。

    当前数据同时可能使用 `YYYY-MM-DD HH:MM:SS`、`YYYY/MM/DD HH:MM` 和
    `YYYY/MM/DD HH:MM:SS` 格式。解析失败时抛出 ValueError，便于尽早发现
    数据格式与预期不一致的问题。
    """
    normalized = value.strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M", "%Y/%m/%d %H:%M:%S"):
        try:
            return datetime.strptime(normalized, fmt)
        except ValueError:
            pass
    raise ValueError(f"Unsupported datetime format: {value!r}")


def read_avoid_area_windows(path: Path | None = None) -> list[tuple[float, float]]:
    """读取异常区时间窗口并转换为相对秒数区间。

    CSV 需要包含“开始时间”和“持续时间 (min)”两列。每行的开始时间先转换为
    datetime，再减去首个异常区开始日期的当天零点，得到相对开始秒数；持续时间
    从分钟转换为秒后叠加得到相对结束秒数。返回列表中的每个元组均为
    `(window_start_seconds, window_end_seconds)`。

    该实现修正了 MATLAB 版本中分钟差计算误用小时字段的问题，并直接使用
    datetime 差值处理跨日窗口。
    """
    csv_path = path or find_csv_by_headers({"开始时间", "持续时间 (min)"})
    rows = _read_csv_rows(csv_path)
    if not rows:
        return []

    starts = [parse_datetime(row["开始时间"]) for row in rows]
    base_day = min(starts).replace(hour=0, minute=0, second=0, microsecond=0)
    windows: list[tuple[float, float]] = []
    for row, start_at in zip(rows, starts):
        duration_minutes = float(row["持续时间 (min)"].strip())
        start_seconds = (start_at - base_day).total_seconds()
        end_seconds = start_seconds + duration_minutes * 60
        windows.append((start_seconds, end_seconds))
    return sorted(windows)


def read_solar_angles(path: Path | None = None) -> list[tuple[float, float]]:
    """读取轨道阳光角采样点并转换为相对秒数序列。

    CSV 需要包含 `Time (LCLG)` 和 `Beta Angle (deg)` 两列。时间列以首个采样点
    所在日期的零点为基准转换为相对秒数，角度列按度读取。返回列表中的每个
    元组为 `(beta_angle_degrees, relative_seconds)`，供阳光角约束判定函数按
    相邻采样点进行线性插值。

    与 MATLAB 版本不同，这里不硬编码第二个采样点为 8 小时、后续采样点每天
    间隔 86400 秒，而是完全采用 CSV 中的实际时间戳，避免数据采样间隔变化时
    注释和算法失真。
    """
    csv_path = path or find_csv_by_headers({"Time (LCLG)", "Beta Angle (deg)"})
    rows = _read_csv_rows(csv_path)
    if not rows:
        return []

    first_time = parse_datetime(rows[0]["Time (LCLG)"])
    base_day = first_time.replace(hour=0, minute=0, second=0, microsecond=0)
    solar_angles: list[tuple[float, float]] = []
    for row in rows:
        timestamp = parse_datetime(row["Time (LCLG)"])
        angle = float(row["Beta Angle (deg)"].strip())
        relative_seconds = (timestamp - base_day).total_seconds()
        solar_angles.append((angle, relative_seconds))
    return solar_angles
