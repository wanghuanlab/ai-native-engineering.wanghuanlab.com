"""跨平台执行外部命令。Windows 上的 .cmd / pnpm 走 cmd /c。"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path


IS_WINDOWS = os.name == "nt"


def configure_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            try:
                reconfigure(line_buffering=True)
            except (OSError, ValueError):
                pass


def prepare_command(args: list[str], *, windows: bool) -> list[str]:
    """把命令整理成当前系统能直接执行的参数列表。"""
    if not args:
        return []
    if windows:
        head = Path(args[0]).name.lower()
        if head.endswith((".cmd", ".bat")) or head in {"pnpm", "npm", "npx", "pnpm.cmd", "npm.cmd"}:
            return ["cmd", "/c", *args]
    return list(args)


def maven_argv(goals: list[str], *, windows: bool) -> list[str]:
    executable = "mvnw.cmd" if windows else "./mvnw"
    return prepare_command([executable, "-B", "-q", *goals], windows=windows)


class CommandFailed(Exception):
    def __init__(self, args: list[str], returncode: int) -> None:
        super().__init__(f"{args[0] if args else '命令'} 退出码 {returncode}")
        self.args_list = args
        self.returncode = returncode


def run(args: list[str], *, cwd: Path | None = None, env: dict[str, str] | None = None) -> None:
    command = prepare_command(args, windows=IS_WINDOWS)
    try:
        result = subprocess.run(command, cwd=cwd, env=env)
    except FileNotFoundError as exc:
        print(f"✗ 找不到命令：{args[0]}", file=sys.stderr)
        raise CommandFailed(args, 127) from exc
    if result.returncode != 0:
        raise CommandFailed(args, result.returncode)


def which(name: str) -> str | None:
    return shutil.which(name)
