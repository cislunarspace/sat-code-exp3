from __future__ import annotations

from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[2]
PYTHON_DIR = ROOT_DIR / "python"

# 让测试优先导入 python/src 和 python/main.py 下的被测模块。
python_dir = str(PYTHON_DIR)
if python_dir in sys.path:
    sys.path.remove(python_dir)
sys.path.insert(0, python_dir)
