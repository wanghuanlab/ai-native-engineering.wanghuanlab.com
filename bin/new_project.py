#!/usr/bin/env python3
"""创建项目。两种方式：

- sync（方式 B，默认）：来源是团队可访问的 Git 地址并固定引用，项目以后可用 sync-baseline 升级。
- copy（方式 A）：从本机基线目录一次性拷贝，不访问网络，项目以后不跟随基线升级。
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

BASELINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASELINE / "template" / "scripts"))

from lib.baseline_source import (  # noqa: E402
    copier_command,
    git_stdout,
    mark_copy_mode,
    reachability_problem,
    resolve_create_ref,
    resolve_create_source,
)
from lib.proc import configure_stdio  # noqa: E402

MODES = ("sync", "copy")
USAGE = (
    "用法：new-project <目标目录> [基线版本标签] [--mode sync|copy] "
    "[--source <Git URL>] [--ref <标签或提交>] [其他 copier 参数...]\n"
    "  --mode sync  方式 B（默认）：可持续升级。来源必须是已推送的 Git 标签或提交，需要能访问远端\n"
    "  --mode copy  方式 A：一次性拷贝本机基线目录（含未提交改动），可离线，项目以后不能 sync-baseline"
)


def main(argv: list[str] | None = None) -> int:
    configure_stdio()
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] in {"-h", "--help"}:
        print(USAGE, file=sys.stderr)
        return 2
    destination, mode, ref_flag, source_flag, extra = parse_args(args)
    if mode == "copy":
        return create_copy(destination, ref_flag, source_flag, extra)
    return create_sync(destination, ref_flag, source_flag, extra)


def create_sync(destination: str, ref_flag: str | None, source_flag: str | None, extra: list[str]) -> int:
    source = resolve_create_source(BASELINE, source_flag)
    ref = resolve_create_ref(BASELINE, ref_flag)
    problem = reachability_problem(source, ref)
    if problem:
        print(problem, file=sys.stderr)
        print(
            "  只想离线生成一个不跟随基线升级的项目，可加 --mode copy（方式 A）。",
            file=sys.stderr,
        )
        return 1
    print("创建方式：可持续升级（方式 B）")
    print(f"基线来源：{source}")
    print(f"基线引用：{ref}")
    command = [*copier_command(), "copy", "--trust", "--vcs-ref", ref, *extra, source, str(destination)]
    result = subprocess.run(command)
    if result.returncode != 0:
        print(
            f"✗ copier copy 失败（退出码 {result.returncode}）。"
            "若引用是尚未推送的本地提交，请先推送或改用已发布的标签。",
            file=sys.stderr,
        )
        return result.returncode
    return 0


def create_copy(destination: str, ref_flag: str | None, source_flag: str | None, extra: list[str]) -> int:
    source = source_flag or str(BASELINE)
    vcs_ref = ref_flag
    if vcs_ref is None and Path(source).is_dir() and git_stdout(Path(source), "rev-parse", "HEAD"):
        # 不指定时 Copier 会取最新标签；HEAD 才是“当前文件”，且包含未提交的改动。
        vcs_ref = "HEAD"
    print("创建方式：一次性拷贝（方式 A），项目以后不跟随基线升级")
    print(f"拷贝来源：{source}")
    if vcs_ref:
        print(f"拷贝引用：{vcs_ref}")
    command = [*copier_command(), "copy", "--trust"]
    if vcs_ref:
        command += ["--vcs-ref", vcs_ref]
    command += [*extra, source, str(destination)]
    result = subprocess.run(command)
    if result.returncode != 0:
        print(f"✗ copier copy 失败（退出码 {result.returncode}）。", file=sys.stderr)
        return result.returncode
    answers = Path(destination) / ".baseline" / "copier-answers.yml"
    if answers.is_file():
        mark_copy_mode(answers)
    return 0


def parse_args(argv: list[str]) -> tuple[str, str, str | None, str | None, list[str]]:
    destination = argv[0]
    rest = argv[1:]
    mode = "sync"
    ref = None
    source = None
    extra: list[str] = []
    index = 0
    if rest and not rest[0].startswith("-"):
        ref = rest[0]
        index = 1
    while index < len(rest):
        token = rest[index]
        if token in {"--mode", "--source", "--ref", "--vcs-ref"}:
            if index + 1 >= len(rest):
                raise SystemExit(f"{token} 需要一个参数")
            value = rest[index + 1]
            if token == "--mode":
                if value not in MODES:
                    raise SystemExit(f"--mode 只能是 sync 或 copy，收到：{value}")
                mode = value
            elif token == "--source":
                source = value
            else:
                ref = value
            index += 2
            continue
        extra.append(token)
        index += 1
    return destination, mode, ref, source, extra


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit as exc:
        if isinstance(exc.code, str):
            print(exc.code, file=sys.stderr)
            sys.exit(1)
        raise
