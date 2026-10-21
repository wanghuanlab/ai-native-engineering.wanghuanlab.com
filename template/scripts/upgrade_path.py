#!/usr/bin/env python3
"""对客户在用版本执行升级路径测试。只验证 PostgreSQL；信创方言在客户环境验证。"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

from lib.postgres import Postgres
from lib.proc import configure_stdio


ROOT = Path(__file__).resolve().parents[1]
MIGRATION = Path("db/migration/postgresql")
VERSION_LINE = re.compile(r"^- (v\d+\.\d+\.\d+)\b")


def versions_in_use(text: str) -> list[str]:
    found: list[str] = []
    in_section = False
    for line in text.splitlines():
        if line.startswith("## 在用版本"):
            in_section = True
            continue
        if line.startswith("## "):
            in_section = False
            continue
        if not in_section:
            continue
        match = VERSION_LINE.match(line)
        if match:
            found.append(match.group(1))
    return sorted(set(found))


def git_bytes(*args: str) -> bytes:
    result = subprocess.run(["git", *args], cwd=ROOT, capture_output=True)
    if result.returncode != 0:
        raise SystemExit(result.returncode)
    return result.stdout


def sql_names(ref: str | None) -> list[str]:
    directory = ROOT / MIGRATION
    if ref is None:
        return sorted(path.name for path in directory.glob("V*.sql"))
    listing = subprocess.run(
        ["git", "ls-tree", "--name-only", ref, f"{MIGRATION.as_posix()}/"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    names = []
    for line in listing.stdout.splitlines():
        name = Path(line).name
        if name.startswith("V") and name.endswith(".sql"):
            names.append(name)
    return sorted(names)


def main(argv: list[str] | None = None) -> int:
    configure_stdio()
    del argv
    text = (ROOT / "docs" / "releases" / "deployments.md").read_text(encoding="utf-8")
    versions = versions_in_use(text)
    if not versions:
        print("deployments.md 中没有在用版本，跳过升级路径测试")
        return 0
    with Postgres() as pg:
        current = sql_names(None)
        for version in versions:
            probe = subprocess.run(
                ["git", "rev-parse", "--verify", "--quiet", f"{version}^{{commit}}"],
                cwd=ROOT,
                capture_output=True,
            )
            if probe.returncode != 0:
                print(f"✗ 找不到版本标签 {version}，发布时必须打标签", file=sys.stderr)
                return 1
            print(f"· 从 {version} 升级")
            pg.reset()
            old = sql_names(version)
            for name in old:
                pg.execute(git_bytes("show", f"{version}:{MIGRATION.as_posix()}/{name}"))
            for name in current:
                if name in old:
                    continue
                print(f"  执行 {name}")
                pg.execute_file(ROOT / MIGRATION / name)
    print(f"升级路径测试通过：{', '.join(versions)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
