"""项目入口脚本。

通过子进程运行 python/main.py，并自动将 python/ 目录加入 PYTHONPATH，
使 python/src 下的模块可以被正确 import。

用法：uv run python main.py
"""

import os
import subprocess
import sys

project_root = os.path.dirname(os.path.abspath(__file__))
python_dir = os.path.join(project_root, "python")

env = os.environ.copy()
env["PYTHONPATH"] = python_dir + os.pathsep + env.get("PYTHONPATH", "")

subprocess.run([sys.executable, os.path.join("python", "main.py")], cwd=project_root, env=env)
