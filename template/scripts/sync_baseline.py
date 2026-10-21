#!/usr/bin/env python3
"""把基线同步到指定版本。来源必须是团队可访问的 Git 地址。"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from lib.baseline_source import (
    copier_command,
    reachability_problem,
    read_src_path,
    sanitize_git_url,
    source_problem,
    write_src_path,
)
from lib.proc import configure_stdio


ROOT = Path(__file__).resolve().parents[1]
ANSWERS = ROOT / ".baseline" / "copier-answers.yml"


def main(argv: list[str] | None = None) -> int:
    configure_stdio()
    args = list(sys.argv[1:] if argv is None else argv)
    version, source_flag = parse_args(args)
    os.chdir(ROOT)
    if not ANSWERS.is_file():
        print(f"✗ 找不到 {ANSWERS.relative_to(ROOT)}，这不是由基线创建的项目。", file=sys.stderr)
        return 1
    status = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True)
    if status.stdout.strip():
        print("工作区有未提交的改动，请先提交或暂存", file=sys.stderr)
        return 1

    recorded = read_src_path(ANSWERS.read_text(encoding="utf-8"))
    if recorded is None:
        print(f"✗ {ANSWERS.relative_to(ROOT)} 缺少 _src_path。", file=sys.stderr)
        return 1
    chosen = source_flag or os.environ.get("BASELINE_SOURCE") or recorded
    cleaned = sanitize_git_url(chosen.strip())
    if cleaned != chosen.strip():
        print("已去掉基线来源中的凭据。", file=sys.stderr)
    problem = source_problem(cleaned)
    if problem:
        print(problem, file=sys.stderr)
        return 1
    unreachable = reachability_problem(cleaned, version)
    if unreachable:
        print(unreachable, file=sys.stderr)
        return 1
    if cleaned != recorded:
        write_src_path(ANSWERS, cleaned)
        commit_source_change(version)

    command = [
        *copier_command(),
        "update",
        "--trust",
        "--defaults",
        "--vcs-ref",
        version,
        "--answers-file",
        ".baseline/copier-answers.yml",
    ]
    result = subprocess.run(command, cwd=ROOT)
    if result.returncode != 0:
        print(
            f"✗ copier update 失败（退出码 {result.returncode}）。"
            "请确认版本标签已推送到基线来源，且高于当前项目记录的版本。",
            file=sys.stderr,
        )
        return result.returncode
    subprocess.run([sys.executable, "scripts/build-ai-config.py"], cwd=ROOT, check=True)
    print()
    print(f"已同步到基线 {version}。请检查改动（git diff），处理冲突标记后执行：")
    print("  scripts/verify.sh full    （Windows：scripts\\verify.cmd full）")
    print(
        "  git add -A && BASELINE_SYNC=1 git commit "
        f'-m "chore(baseline): 同步基线 {version}" -m "Refs: BASELINE-{version}"'
    )
    return 0


def parse_args(argv: list[str]) -> tuple[str, str | None]:
    if not argv or argv[0].startswith("-"):
        raise SystemExit("用法：sync-baseline <版本，如 v0.2.0> [--source <Git URL>]")
    version = argv[0]
    source = None
    index = 1
    while index < len(argv):
        if argv[index] == "--source" and index + 1 < len(argv):
            source = argv[index + 1]
            index += 2
            continue
        raise SystemExit("用法：sync-baseline <版本，如 v0.2.0> [--source <Git URL>]")
    return version, source


def commit_source_change(version: str) -> None:
    """Copier 拒绝脏工作区。来源地址变化时先单独提交，钩子用 BASELINE_SYNC 放行。"""
    env = os.environ.copy()
    env["BASELINE_SYNC"] = "1"
    subprocess.run(["git", "add", "--", ".baseline/copier-answers.yml"], cwd=ROOT, check=True, env=env)
    message = f"chore(baseline): 更新基线来源地址\n\nRefs: BASELINE-{version}\n"
    result = subprocess.run(
        ["git", "commit", "-q", "-F", "-"],
        cwd=ROOT,
        input=message,
        text=True,
        env=env,
    )
    if result.returncode != 0:
        raise SystemExit("✗ 无法提交更新后的基线来源地址。请查看上面的钩子输出。")
    print("已提交基线来源地址变更（Copier 要求同步前工作区干净）。")


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit as exc:
        if isinstance(exc.code, str):
            print(exc.code, file=sys.stderr)
            sys.exit(1)
        raise
