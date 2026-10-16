#!/usr/bin/env python3
"""门禁检查集合，由 Git 钩子和 verify.sh 调用。

  checks.py managed --staged             基线托管文件是否被修改
  checks.py migrations [--staged]        迁移脚本命名、方言一致、已合并脚本不可修改
  checks.py secrets --staged|--all       密钥泄露扫描
  checks.py commit-msg <文件>            提交说明格式
  checks.py test-guard                   与 main 相比是否删除、跳过或减少了测试
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MIGRATION_DIR = "db/migration"
MIGRATION_NAME = re.compile(r"^V(\d{12})__[a-z][a-z0-9]*_[a-z0-9_]+\.sql$")


def git(*args: str, check: bool = True) -> str:
    result = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True)
    if check and result.returncode != 0:
        raise SystemExit(f"git {' '.join(args)} 失败：{result.stderr.strip()}")
    return result.stdout


def fail(title: str, problems: list[str]) -> int:
    if not problems:
        return 0
    print(f"✗ {title}", file=sys.stderr)
    for p in problems:
        print(f"  - {p}", file=sys.stderr)
    return 1


def glob_to_regex(pattern: str) -> re.Pattern[str]:
    out, i = "", 0
    while i < len(pattern):
        if pattern.startswith("**/", i):
            out, i = out + "(?:.*/)?", i + 3
        elif pattern.startswith("**", i):
            out, i = out + ".*", i + 2
        elif pattern[i] == "*":
            out, i = out + "[^/]*", i + 1
        elif pattern[i] == "?":
            out, i = out + "[^/]", i + 1
        else:
            out, i = out + re.escape(pattern[i]), i + 1
    return re.compile(f"^{out}$")


def staged_files(filter_: str = "ACMRD") -> list[str]:
    return [f for f in git("diff", "--cached", "--name-only", f"--diff-filter={filter_}").splitlines() if f]


def base_ref() -> str | None:
    for ref in ("origin/main", "main"):
        if git("rev-parse", "--verify", "--quiet", ref, check=False).strip():
            return ref
    return None


# ---------------------------------------------------------------- managed
def check_managed() -> int:
    if os.environ.get("BASELINE_SYNC") == "1":
        return 0
    if not git("rev-parse", "--verify", "--quiet", "HEAD", check=False).strip():
        return 0
    patterns = [
        glob_to_regex(line.strip())
        for line in (ROOT / ".baseline/managed-files.txt").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]
    touched = [f for f in staged_files() if any(p.match(f) for p in patterns)]
    return fail(
        "以下文件由基线托管，项目内禁止修改（同步基线请用 scripts/sync-baseline.sh；项目规则写在 .ai/project/）",
        touched,
    )


# ---------------------------------------------------------------- migrations
def check_migrations(staged: bool) -> int:
    project = json.loads((ROOT / ".baseline/project.json").read_text(encoding="utf-8"))
    dialects: list[str] = project["dialects"]
    problems: list[str] = []
    files: dict[str, set[str]] = {}
    for dialect in dialects:
        directory = ROOT / MIGRATION_DIR / dialect
        names = {p.name for p in directory.glob("*.sql")} if directory.is_dir() else set()
        files[dialect] = names
        versions: dict[str, str] = {}
        for name in sorted(names):
            match = MIGRATION_NAME.match(name)
            if not match:
                problems.append(f"{dialect}/{name}：文件名不符合 V<年月日时分>__<模块>_<描述>.sql")
                continue
            if match.group(1) in versions:
                problems.append(f"{dialect}/{name}：版本号与 {versions[match.group(1)]} 重复")
            versions[match.group(1)] = name
    primary = dialects[0]
    for dialect in dialects[1:]:
        for name in sorted(files[primary] - files[dialect]):
            problems.append(f"{dialect}/ 缺少与 {primary}/{name} 对应的脚本")
        for name in sorted(files[dialect] - files[primary]):
            problems.append(f"{primary}/ 缺少与 {dialect}/{name} 对应的脚本")

    ref = base_ref()
    if ref:
        merged = [f for f in git("ls-tree", "-r", "--name-only", ref, "--", MIGRATION_DIR).splitlines() if f.endswith(".sql")]
        for path in merged:
            original = git("show", f"{ref}:{path}")
            if staged:
                current = git("show", f":{path}", check=False) if git("ls-files", "--", path).strip() else None
            else:
                p = ROOT / path
                current = p.read_text(encoding="utf-8") if p.exists() else None
            if current is None:
                problems.append(f"{path}：已合并到 {ref} 的迁移脚本不能删除")
            elif current != original:
                problems.append(f"{path}：已合并到 {ref} 的迁移脚本不能修改，请新增迁移脚本")
    return fail("迁移脚本检查未通过", problems)


# ---------------------------------------------------------------- secrets
SECRET_PATTERNS = [
    (re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH |ENCRYPTED )?PRIVATE KEY-----"), "私钥"),
    (re.compile(r"AKIA[0-9A-Z]{16}"), "云服务访问密钥"),
    (re.compile(r"(?i)\b(?:password|passwd|pwd|secret|token|api[_-]?key|access[_-]?key)\b\s*[:=]\s*['\"]?(?![$<{]|\*{3})[^\s'\"#,;]{8,}"), "疑似明文密码或令牌"),
]
SECRET_SKIP = re.compile(r"(?:^|/)(?:pnpm-lock\.yaml|package-lock\.json|.*\.(?:png|jpe?g|gif|ico|pdf|jar|zip|gz|woff2?|ttf))$")


def check_secrets(staged: bool) -> int:
    paths = staged_files("ACMR") if staged else [f for f in git("ls-files").splitlines() if f]
    problems = []
    for path in paths:
        if SECRET_SKIP.search(path) or path.startswith("scripts/lib/checks.py"):
            continue
        content = git("show", f":{path}", check=False) if staged else None
        if content is None:
            file = ROOT / path
            if not file.is_file():
                continue
            try:
                content = file.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
        for lineno, line in enumerate(content.splitlines(), 1):
            for pattern, label in SECRET_PATTERNS:
                if pattern.search(line):
                    problems.append(f"{path}:{lineno} {label}")
    return fail("发现疑似密钥，请改为环境变量注入（误报时调整写法，例如使用 ${ENV_NAME}）", problems)


# ---------------------------------------------------------------- commit-msg
COMMIT_TITLE = re.compile(r"^(feat|fix|refactor|perf|test|docs|build|chore|revert)(\([a-z0-9-]+\))?!?: \S.*")
REFS = re.compile(r"^Refs: ((REQ|BUG)-\d{8}-[a-z0-9-]+|BASELINE-v[\d.]+)(, ?((REQ|BUG)-\d{8}-[a-z0-9-]+))*\s*$", re.M)


def check_commit_msg(file: str) -> int:
    text = "\n".join(
        line for line in Path(file).read_text(encoding="utf-8").splitlines() if not line.startswith("#")
    ).strip()
    title = text.splitlines()[0] if text else ""
    if title.startswith(("Merge ", "Revert ")):
        return 0
    problems = []
    if not COMMIT_TITLE.match(title):
        problems.append("第一行格式应为 <类型>(<模块>): <中文描述>，类型为 feat/fix/refactor/perf/test/docs/build/chore/revert")
    if not REFS.search(text):
        problems.append("缺少关联编号行，例如 Refs: REQ-20261015-visitor-approval 或 Refs: BUG-20261016-passcode-expire")
    return fail("提交说明不符合规范", problems)


# ---------------------------------------------------------------- test-guard
TEST_FILE = re.compile(r"(?:src/test/.*\.java|tests/.*\.spec\.ts|\.spec\.ts)$")
TEST_COUNT = re.compile(r"@Test\b|@ParameterizedTest\b|^\s*(?:it|test)\(", re.M)
SKIP_MARK = re.compile(r"@Disabled\b|@Ignore\b|\b(?:it|test|describe)\.(?:skip|todo)\(|\bx(?:it|describe)\(")


def check_test_guard() -> int:
    if os.environ.get("ALLOW_TEST_CHANGE"):
        print(f"! 已通过 ALLOW_TEST_CHANGE 跳过测试删除检查：{os.environ['ALLOW_TEST_CHANGE']}", file=sys.stderr)
        return 0
    ref = base_ref()
    if not ref:
        return 0
    base = git("merge-base", ref, "HEAD", check=False).strip()
    if not base:
        return 0
    problems = []
    for line in git("diff", "--name-status", base, "--").splitlines():
        status, *paths = line.split("\t")
        path = paths[-1]
        old_path = paths[0]
        if not TEST_FILE.search(old_path):
            continue
        if status.startswith("D"):
            problems.append(f"{old_path}：删除了测试文件")
            continue
        old = git("show", f"{base}:{old_path}", check=False)
        new_file = ROOT / path
        new = new_file.read_text(encoding="utf-8") if new_file.exists() else ""
        if len(TEST_COUNT.findall(new)) < len(TEST_COUNT.findall(old)):
            problems.append(f"{path}：测试用例数量减少")
        if len(SKIP_MARK.findall(new)) > len(SKIP_MARK.findall(old)):
            problems.append(f"{path}：新增了跳过测试的标记")
    for path in git("ls-files", "--others", "--exclude-standard").splitlines():
        if TEST_FILE.search(path) and SKIP_MARK.search((ROOT / path).read_text(encoding="utf-8")):
            problems.append(f"{path}：新测试文件中有跳过测试的标记")
    return fail(
        "测试被删除、减少或跳过。确属业务变更时，须在 design.md 中说明并由 TL 设置 ALLOW_TEST_CHANGE=<需求编号> 后执行",
        problems,
    )


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2
    command, args = argv[0], argv[1:]
    if command == "managed":
        return check_managed()
    if command == "migrations":
        return check_migrations("--staged" in args)
    if command == "secrets":
        return check_secrets("--staged" in args)
    if command == "commit-msg":
        return check_commit_msg(args[0])
    if command == "test-guard":
        return check_test_guard()
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
