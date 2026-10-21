#!/usr/bin/env python3
"""推送前检查。由 .githooks/pre-push 调用，逻辑不依赖 bash。"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ZERO = "0000000000000000000000000000000000000000"


def main() -> int:
    os.chdir(ROOT)
    pushing_main = False
    for line in sys.stdin:
        parts = line.split()
        if len(parts) < 3:
            continue
        local_sha, remote_ref = parts[1], parts[2]
        if remote_ref == "refs/heads/main" and local_sha != ZERO:
            pushing_main = True
    if pushing_main and not is_tech_lead():
        name = git_user_name() or "未设置"
        print("✗ 只有技术负责人可以推送 main。请推送功能分支（feat/<需求编号> 或 fix/<缺陷编号>），由技术负责人合并。", file=sys.stderr)
        print(f"  当前 git user.name：{name}", file=sys.stderr)
        return 1
    if os.environ.get("SKIP_VERIFY") == "1":
        print("! 已跳过推送前校验（SKIP_VERIFY=1）", file=sys.stderr)
        return 0
    from verify import main as verify_main

    return verify_main(["quick"])


def git_user_name() -> str:
    result = subprocess.run(["git", "config", "user.name"], cwd=ROOT, capture_output=True, text=True)
    return result.stdout.strip() if result.returncode == 0 else ""


def is_tech_lead() -> bool:
    name = git_user_name()
    data = json.loads((ROOT / ".baseline" / "project.json").read_text(encoding="utf-8"))
    return name in data.get("techLeads", [])


if __name__ == "__main__":
    sys.exit(main())
