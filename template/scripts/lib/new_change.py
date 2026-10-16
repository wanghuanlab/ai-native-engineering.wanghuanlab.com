#!/usr/bin/env python3
"""创建需求入库目录和变更包。

  new-change.sh <短名> --intake-only     只创建 docs/requirements/REQ-<日期>-<短名>/
  new-change.sh <短名> --level M|L       同时创建 docs/changes/REQ-<日期>-<短名>/（L 级含 design.md）

同一短名已入库时沿用已有编号。
"""
from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TEMPLATES = ROOT / "docs/_templates"
SHORT_NAME = re.compile(r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$")


def render(template: str, target: Path, values: dict[str, str]) -> None:
    if target.exists():
        print(f"  已存在，跳过 {target.relative_to(ROOT)}")
        return
    text = (TEMPLATES / template).read_text(encoding="utf-8")
    for key, value in values.items():
        text = text.replace(f"__{key}__", value)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    print(f"  创建 {target.relative_to(ROOT)}")


def find_existing(short: str) -> str | None:
    for base in ("docs/requirements", "docs/changes", "docs/changes/archive"):
        for path in sorted((ROOT / base).glob(f"REQ-*-{short}")):
            if re.fullmatch(rf"REQ-\d{{8}}-{re.escape(short)}", path.name):
                return path.name
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="创建需求入库目录和变更包")
    parser.add_argument("short", help="英文短名，小写加连字符，如 visitor-approval")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--intake-only", action="store_true")
    group.add_argument("--level", choices=["M", "L"])
    args = parser.parse_args()

    if not SHORT_NAME.match(args.short) or len(args.short) > 40:
        print("短名只能使用小写字母、数字和连字符，以字母开头，不超过 40 个字符", file=sys.stderr)
        return 2

    today = dt.date.today()
    req = find_existing(args.short) or f"REQ-{today:%Y%m%d}-{args.short}"
    if (ROOT / "docs/changes/archive" / req).exists():
        print(f"{req} 已归档。需求变更请用新的短名创建变更包", file=sys.stderr)
        return 1

    values = {"REQ_ID": req, "DATE": today.isoformat(), "LEVEL": args.level or "待判定"}
    print(f"需求编号：{req}")
    requirement = ROOT / "docs/requirements" / req
    (requirement / "raw").mkdir(parents=True, exist_ok=True)
    (requirement / "raw/.gitkeep").touch()
    render("intake.md", requirement / "intake.md", values)

    if args.level:
        change = ROOT / "docs/changes" / req
        render("proposal.md", change / "proposal.md", values)
        render("spec-delta.md", change / "spec-delta.md", values)
        if args.level == "L":
            render("design.md", change / "design.md", values)
        render("tasks.md", change / "tasks.md", values)
        render("acceptance.md", change / "acceptance.md", values)
    return 0


if __name__ == "__main__":
    sys.exit(main())
