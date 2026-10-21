#!/usr/bin/env python3
"""新成员克隆项目后执行一次：检查工具、启用 Git 钩子、生成 AI 配置、安装前端依赖。"""
from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

from lib.proc import IS_WINDOWS, configure_stdio, run, which


ROOT = Path(__file__).resolve().parents[1]


def main(argv: list[str] | None = None) -> int:
    configure_stdio()
    del argv
    os.chdir(ROOT)
    missing = False
    checks = [
        ("Java 21", "java", "安装 JDK 21（如 Temurin 21）"),
        ("Docker", "docker", "集成测试、表结构摘要和升级路径测试需要 Docker"),
        ("Node.js", "node", "安装 Node.js 22 或更高版本"),
        ("pnpm", "pnpm", "执行 corepack enable，或 npm i -g pnpm@11"),
        ("Python 3", "python", "安装 Python 3.10 或更高版本"),
    ]
    for label, command, hint in checks:
        names = ["python3", "python", "py"] if command == "python" else [command]
        if any(which(name) for name in names):
            print(f"✓ {label}")
        else:
            print(f"✗ {label}：{hint}")
            missing = True
    if which("java"):
        major = java_major()
        if major is None or major < 21:
            print(f"✗ 当前 Java 版本为 {major or '未知'}，需要 21 或更高")
            missing = True
    if sys.version_info < (3, 10):
        print(f"✗ 当前 Python 版本为 {sys.version_info.major}.{sys.version_info.minor}，需要 3.10 或更高")
        missing = True
    if missing:
        print("请先安装缺失的工具")
        return 1

    subprocess.run(["git", "config", "core.hooksPath", ".githooks"], cwd=ROOT, check=True)
    from bootstrap import chmod_project_scripts

    chmod_project_scripts(ROOT)
    print("✓ 已启用 Git 钩子（.githooks/）")
    run([sys.executable, "scripts/build-ai-config.py"], cwd=ROOT)
    env = os.environ.copy()
    env["CI"] = "true"
    run(["pnpm", "install"], cwd=ROOT / "frontend", env=env)
    name = subprocess.run(["git", "config", "user.name"], cwd=ROOT, capture_output=True, text=True)
    if name.returncode != 0 or not name.stdout.strip():
        print("! 请设置 git user.name，需与 .baseline/project.json 中 techLeads 的写法一致（若你是技术负责人）")
    print()
    print("完成。下一步：scripts/verify（Windows 用 verify.cmd 或 verify.ps1，macOS/Linux 用 verify.sh）quick")
    print("协作流程见 docs/context/collaboration.md")
    return 0


def java_major() -> int | None:
    result = subprocess.run(
        ["java", "-XshowSettings:properties", "-version"],
        capture_output=True,
        text=True,
    )
    text = (result.stderr or "") + (result.stdout or "")
    match = re.search(r"java\.specification\.version\s*=\s*([0-9.]+)", text)
    if not match:
        return None
    raw = match.group(1)
    if raw.startswith("1."):
        return int(raw.split(".")[1])
    return int(raw.split(".")[0])


if __name__ == "__main__":
    from lib.proc import CommandFailed

    try:
        sys.exit(main())
    except CommandFailed as exc:
        sys.exit(exc.returncode or 1)
