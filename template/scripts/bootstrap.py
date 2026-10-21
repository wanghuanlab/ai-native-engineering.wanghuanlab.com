#!/usr/bin/env python3
"""创建项目后的一次性初始化：Git 仓库、钩子、可执行位、AI 配置。由 Copier 任务调用。"""
from __future__ import annotations

import os
import stat
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def chmod_project_scripts(root: Path) -> None:
    if os.name == "nt":
        return
    patterns = (
        ".githooks/*",
        "scripts/*.sh",
        "scripts/_py.sh",
        "scripts/_py.ps1",
        "scripts/_py.cmd",
        "backend/mvnw",
    )
    for pattern in patterns:
        for path in root.glob(pattern):
            if path.is_file():
                path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def ensure_git(root: Path) -> None:
    if (root / ".git").exists():
        return
    result = subprocess.run(["git", "init", "-q", "-b", "main"], cwd=root)
    if result.returncode != 0:
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
        subprocess.run(["git", "symbolic-ref", "HEAD", "refs/heads/main"], cwd=root, check=True)


def main() -> int:
    ensure_git(ROOT)
    subprocess.run(["git", "config", "core.hooksPath", ".githooks"], cwd=ROOT, check=True)
    chmod_project_scripts(ROOT)
    subprocess.run([sys.executable, str(ROOT / "scripts" / "build-ai-config.py")], cwd=ROOT, check=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
