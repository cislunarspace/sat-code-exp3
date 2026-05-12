from __future__ import annotations

from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[2]
PYTHON_DIR = ROOT_DIR / "python"

# 让测试可以直接导入 python/src 下的被测模块。
if str(PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_DIR))
