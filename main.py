"""航天任务规划实验入口。"""

import os
import subprocess
import sys

# Ensure python/ directory is on PYTHONPATH so that `import src` works
project_root = os.path.dirname(os.path.abspath(__file__))
python_dir = os.path.join(project_root, "python")
env = os.environ.copy()
env["PYTHONPATH"] = python_dir + os.pathsep + env.get("PYTHONPATH", "")

subprocess.run([sys.executable, "python/main.py"], cwd=project_root, env=env)
