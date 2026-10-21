#!/usr/bin/env python3
"""统一校验入口。每条命令单独检查退出码，前面的失败不会被后面的成功掩盖。"""
from __future__ import annotations

import os
import sys
from pathlib import Path

from lib.proc import IS_WINDOWS, CommandFailed, configure_stdio, maven_argv, prepare_command, run


ROOT = Path(__file__).resolve().parents[1]


def main(argv: list[str] | None = None) -> int:
    configure_stdio()
    os.chdir(ROOT)
    args = list(sys.argv[1:] if argv is None else argv)
    mode = args[0] if args else "quick"
    steps: list[tuple[str, str]]
    if mode == "ai":
        steps = [("AI 配置一致性", "ai")]
    elif mode == "db":
        steps = [("迁移脚本", "db")]
    elif mode == "backend":
        steps = [("后端格式与单元测试", "backend-test")]
    elif mode == "frontend":
        steps = [("前端检查", "frontend")]
    elif mode == "upgrade":
        steps = [("升级路径", "upgrade")]
    elif mode == "quick":
        steps = [
            ("AI 配置一致性", "ai"),
            ("迁移脚本", "db"),
            ("后端格式与单元测试", "backend-test"),
            ("前端检查", "frontend"),
        ]
    elif mode == "full":
        steps = [
            ("AI 配置一致性", "ai"),
            ("迁移脚本", "db"),
            ("测试删除检查", "test-guard"),
            ("密钥扫描", "secrets"),
            ("后端格式、单元测试与集成测试", "backend-verify"),
            ("前端检查与构建", "frontend-build"),
            ("升级路径", "upgrade"),
        ]
    else:
        print("用法：verify.py [quick|full|ai|db|backend|frontend|upgrade]", file=sys.stderr)
        return 2

    results: list[str] = []
    for name, kind in steps:
        print(f"▶ {name}", flush=True)
        try:
            run_kind(kind)
        except (CommandFailed, SystemExit) as exc:
            if isinstance(exc, SystemExit) and exc.code in (0, None):
                results.append(f"✓ {name}")
                continue
            if isinstance(exc, SystemExit) and isinstance(exc.code, str):
                print(exc.code, file=sys.stderr)
            results.append(f"✗ {name}")
            summary(mode, results)
            return 1
        results.append(f"✓ {name}")
    summary(mode, results)
    return 0


def summary(mode: str, results: list[str]) -> None:
    print()
    print(f"──────── 校验结果（{mode}）")
    print("\n".join(results))


def run_kind(kind: str) -> None:
    if kind == "ai":
        run([sys.executable, "scripts/build-ai-config.py", "--check"], cwd=ROOT)
    elif kind == "db":
        run([sys.executable, "scripts/lib/checks.py", "migrations"], cwd=ROOT)
    elif kind == "test-guard":
        run([sys.executable, "scripts/lib/checks.py", "test-guard"], cwd=ROOT)
    elif kind == "secrets":
        run([sys.executable, "scripts/lib/checks.py", "secrets", "--all"], cwd=ROOT)
    elif kind == "backend-test":
        run(maven_argv(["spotless:check", "test"], windows=IS_WINDOWS), cwd=ROOT / "backend")
    elif kind == "backend-verify":
        run(maven_argv(["spotless:check", "verify"], windows=IS_WINDOWS), cwd=ROOT / "backend")
    elif kind == "frontend":
        frontend(build=False)
    elif kind == "frontend-build":
        frontend(build=True)
    elif kind == "upgrade":
        from upgrade_path import main as upgrade_main

        code = upgrade_main([])
        if code:
            raise SystemExit(code)
    else:
        raise SystemExit(2)


def frontend(build: bool) -> None:
    frontend_dir = ROOT / "frontend"
    env = os.environ.copy()
    env["CI"] = "true"
    if not (frontend_dir / "node_modules").is_dir():
        if (frontend_dir / "pnpm-lock.yaml").is_file():
            run(["pnpm", "install", "--frozen-lockfile"], cwd=frontend_dir, env=env)
        else:
            run(["pnpm", "install"], cwd=frontend_dir, env=env)
    for script in ("gen:api", "typecheck", "lint", "format:check", "test"):
        run(["pnpm", "-s", script], cwd=frontend_dir, env=env)
    if build:
        run(["pnpm", "-s", "build"], cwd=frontend_dir, env=env)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except CommandFailed:
        sys.exit(1)
