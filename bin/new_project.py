#!/usr/bin/env python3
"""用团队可访问的 Git 地址和固定引用创建项目。"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

BASELINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASELINE / "template" / "scripts"))

from lib.baseline_source import (  # noqa: E402
    copier_command,
    reachability_problem,
    resolve_create_ref,
    resolve_create_source,
)
from lib.proc import configure_stdio  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    configure_stdio()
    args = list(sys.argv[1:] if argv is None else argv)
    if not args:
        print(
            "用法：new-project <目标目录> [基线版本标签] [--source <Git URL>] [--ref <标签或提交>] [其他 copier 参数...]",
            file=sys.stderr,
        )
        return 2
    destination, ref_flag, source_flag, extra = parse_args(args)
    source = resolve_create_source(BASELINE, source_flag)
    ref = resolve_create_ref(BASELINE, ref_flag)
    problem = reachability_problem(source, ref)
    if problem:
        print(problem, file=sys.stderr)
        return 1
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


def parse_args(argv: list[str]) -> tuple[str, str | None, str | None, list[str]]:
    destination = argv[0]
    rest = argv[1:]
    ref = None
    source = None
    extra: list[str] = []
    index = 0
    if rest and not rest[0].startswith("-"):
        ref = rest[0]
        index = 1
    while index < len(rest):
        token = rest[index]
        if token in {"--source", "--ref", "--vcs-ref"}:
            if index + 1 >= len(rest):
                raise SystemExit(f"{token} 需要一个参数")
            if token == "--source":
                source = rest[index + 1]
            else:
                ref = rest[index + 1]
            index += 2
            continue
        extra.append(token)
        index += 1
    return destination, ref, source, extra


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit as exc:
        if isinstance(exc.code, str):
            print(exc.code, file=sys.stderr)
            sys.exit(1)
        raise
