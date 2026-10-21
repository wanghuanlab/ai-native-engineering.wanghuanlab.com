#!/usr/bin/env bash
# 基线自测：用多种画像生成项目，跑完整校验，并验证门禁确实会拦截违规操作。
# 用法：bin/selftest.sh [all|default|minimal|xinchuang|source]
#   source  只跑基线来源与 copier update（不需要 Docker / JDK / pnpm）
#   其余    需要 Docker、JDK 21、Node.js、pnpm、Python 3、uv 或 copier
# 发布基线版本前必须全部通过。
set -euo pipefail

BASELINE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
WORK="${BASELINE_DIR}/.selftest"
TARGET="${1:-all}"
export CI=true

if command -v copier >/dev/null 2>&1; then COPIER=(copier); else COPIER=(uvx copier); fi

pass() { echo "  ✓ $*"; }
die() { echo "  ✗ $*" >&2; exit 1; }
expect_fail() {
  local name="$1"
  shift
  if "$@" >/dev/null 2>&1; then die "${name}：应当被拦截，实际通过"; else pass "${name}：已拦截"; fi
}

# 反向门禁。兼容 macOS Bash 3.2 与 set -u：不用空数组展开，赋值与 local 分开写。
check_frontend_fails_closed() {
  local mock_dir out status
  mock_dir="$(mktemp -d "${TMPDIR:-/tmp}/baseline-gate.XXXXXX")"
  cat > "${mock_dir}/pnpm" <<'EOF'
#!/bin/sh
for arg in "$@"; do
  case "$arg" in
    typecheck)
      echo "SIMULATED TYPECHECK FAILURE" >&2
      exit 23
      ;;
  esac
done
exit 0
EOF
  chmod +x "${mock_dir}/pnpm"
  set +e
  out="$(PATH="${mock_dir}:${PATH}" ./scripts/verify.sh frontend 2>&1)"
  status=$?
  set -e
  rm -rf "${mock_dir}"
  if [ "${status}" -eq 0 ]; then
    die "非末条前端命令失败：应当失败，实际通过"
  fi
  case "${out}" in
    *"SIMULATED TYPECHECK FAILURE"*) ;;
    *) die "非末条前端命令失败：没有执行到模拟的 typecheck" ;;
  esac
  case "${out}" in
    *"✓ 前端检查"*) die "非末条前端命令失败：步骤被记为通过" ;;
  esac
  case "${out}" in
    *"✗ 前端检查"*) pass "非末条前端命令失败：校验返回非零" ;;
    *) die "非末条前端命令失败：未标记步骤失败" ;;
  esac
}

check_secret_scan_binary_and_text() {
  local out status
  python3 -c 'from pathlib import Path
blob = b"BIN\x00\xff\xfe\xfd"
for name in ("model.glb", "photo.webp", "sheet.xlsx", "cache.pyc", "payload.bin"):
    Path(name).write_bytes(blob)
Path("notes.txt").write_text("普通说明，没有密钥\n", encoding="utf-8")'
  git add model.glb photo.webp sheet.xlsx cache.pyc payload.bin notes.txt
  set +e
  out="$(python3 scripts/lib/checks.py secrets --staged 2>&1)"
  status=$?
  set -e
  git reset -q -- model.glb photo.webp sheet.xlsx cache.pyc payload.bin notes.txt
  rm -f model.glb photo.webp sheet.xlsx cache.pyc payload.bin notes.txt
  if [ "${status}" -ne 0 ]; then
    printf '%s\n' "${out}" >&2
    die "暂存二进制文件：密钥扫描应当通过，实际失败（退出码 ${status}）"
  fi
  case "${out}" in
    *UnicodeDecodeError*|*Traceback*) die "暂存二进制文件：密钥扫描崩溃" ;;
  esac
  pass "暂存二进制文件：密钥扫描未崩溃"

  printf '%s\n' 'access_key = AKIAIOSFODNN7EXAMPLE' > leak.txt
  python3 -c 'from pathlib import Path; Path("payload.bin").write_bytes(b"BIN\x00\xff\xfe\xfd")'
  git add leak.txt payload.bin
  set +e
  out="$(python3 scripts/lib/checks.py secrets --staged 2>&1)"
  status=$?
  set -e
  git reset -q -- leak.txt payload.bin
  rm -f leak.txt payload.bin
  if [ "${status}" -eq 0 ]; then
    die "文本文件中的密钥：应当被拦截，实际通过"
  fi
  case "${out}" in
    *UnicodeDecodeError*|*Traceback*) die "文本文件中的密钥：扫描崩溃而非拦截" ;;
  esac
  case "${out}" in
    *发现疑似密钥*) ;;
    *) die "文本文件中的密钥：未报告疑似密钥" ;;
  esac
  case "${out}" in
    *leak.txt*) pass "文本文件中的密钥：已拦截" ;;
    *) die "文本文件中的密钥：未指向文本文件" ;;
  esac
}

# 维护者自测仍把本地检出目录交给 Copier，这样未提交的模板改动也会进生成结果。
# 因此 generate 写进项目的 _src_path 是本机路径。团队创建项目必须走 bin/new-project，
# 来源地址的行为由 source 目标覆盖。
generate() {
  local name="$1"
  shift
  local dest="${WORK}/${name}"
  rm -rf "${dest}"
  echo "▶ 生成 ${name}"
  "${COPIER[@]}" copy --trust --defaults --quiet -d project_code=park -d project_name=智慧园区 \
    -d tech_lead=selftest "$@" "${BASELINE_DIR}" "${dest}"
  cd "${dest}"
  git config user.name selftest
  git config user.email selftest@example.com
  if find . -name '*.jinja' -not -path './node_modules/*' | grep -q .; then die "存在未渲染的 .jinja 文件"; fi
  if grep -rIl --exclude-dir=node_modules --exclude-dir=.git -e '{{ *project_' -e '{%' . | grep -v '^./docs/_templates/' | grep -q .; then
    die "存在未渲染的模板语法"
  fi
  pass "渲染完整"
  (cd frontend && pnpm install --silent)
  git add -A
  git commit -q -m "chore(baseline): 初始化项目" -m "Refs: BASELINE-v0.0.0"
  pass "初始提交通过钩子"
}

verify_full() {
  echo "▶ verify.sh full"
  ./scripts/verify.sh full
}

gate_tests() {
  echo "▶ 门禁拦截测试"
  local sql
  sql=$(ls db/migration/postgresql/V*.sql | head -1)

  echo "-- 改动" >>"${sql}"
  expect_fail "修改已合并的迁移脚本" python3 scripts/lib/checks.py migrations
  git checkout -q -- "${sql}"

  echo "SELECT 1;" >db/migration/postgresql/V209901010000__example_bad.sql
  if [ "$(python3 -c 'import json;print(len(json.load(open(".baseline/project.json"))["dialects"]))')" -gt 1 ]; then
    expect_fail "缺少对应方言的迁移脚本" python3 scripts/lib/checks.py migrations
  fi
  echo "SELECT 1;" >db/migration/postgresql/v1_bad_name.sql
  expect_fail "迁移脚本命名不规范" python3 scripts/lib/checks.py migrations
  rm -f db/migration/postgresql/V209901010000__example_bad.sql db/migration/postgresql/v1_bad_name.sql

  echo "# 改动" >>scripts/verify.sh
  git add scripts/verify.sh
  expect_fail "修改基线托管文件" python3 scripts/lib/checks.py managed --staged
  git reset -q && git checkout -q -- scripts/verify.sh

  echo 'db.password = "Sup3rS3cretValue"' >leak.properties
  git add leak.properties
  expect_fail "提交明文密码" python3 scripts/lib/checks.py secrets --staged
  git reset -q && rm leak.properties

  check_frontend_fails_closed
  check_secret_scan_binary_and_text

  printf 'update stuff\n' >/tmp/selftest-msg
  expect_fail "提交说明不规范" python3 scripts/lib/checks.py commit-msg /tmp/selftest-msg
  printf 'feat(core): 新功能\n\nRefs: REQ-20261015-demo\n' >/tmp/selftest-msg
  python3 scripts/lib/checks.py commit-msg /tmp/selftest-msg && pass "规范的提交说明通过"

  echo "<!-- 手改 -->" >>AGENTS.md
  expect_fail "手改生成的 AI 配置" python3 scripts/build-ai-config.py --check
  git checkout -q -- AGENTS.md

  git switch -q -c feat/selftest
  local test_file
  test_file=$(git ls-files 'backend/**/src/test/**/*Test.java' | head -1)
  git rm -q "${test_file}" && git commit -q --no-verify -m "test: 删除测试" -m "Refs: REQ-20261015-demo"
  expect_fail "删除测试" python3 scripts/lib/checks.py test-guard
  git switch -q main && git branch -q -D feat/selftest
}

scaffold_tests() {
  echo "▶ 脚手架测试"
  ./scripts/new-change.sh demo-flow --intake-only >/dev/null
  ./scripts/new-change.sh demo-flow --level L >/dev/null
  local req
  req=$(ls docs/changes | grep demo-flow)
  for f in proposal spec-delta design tasks acceptance; do
    [ -f "docs/changes/${req}/${f}.md" ] || die "变更包缺少 ${f}.md"
  done
  grep -q "${req}" "docs/changes/${req}/tasks.md" || die "变更包未替换需求编号"
  pass "变更包 ${req}"

  ./scripts/new-module.sh visitor --title 访客 >/dev/null
  grep -q "modules/visitor" backend/pom.xml || die "新模块未登记到父 POM"
  grep -q "| \`visitor\`" docs/context/architecture.md || die "新模块未登记到架构文档"
  ./scripts/verify.sh backend >/dev/null && pass "新模块 visitor 构建与架构测试通过"
  ./scripts/verify.sh frontend >/dev/null && pass "空契约不影响前端生成"

  ./scripts/db-schema.sh >/dev/null
  grep -q "^## " docs/context/db-schema.md && pass "表结构摘要已生成"
  git reset -q --hard && git clean -qfd -e node_modules
}

upgrade_tests() {
  echo "▶ 升级路径测试"
  git tag v0.1.0
  python3 - <<'EOF'
from pathlib import Path
p = Path("docs/releases/deployments.md")
p.write_text(p.read_text(encoding="utf-8").replace("## 在用版本\n", "## 在用版本\n\n- v0.1.0（自测现场）\n"), encoding="utf-8")
EOF
  for d in $(python3 -c 'import json;print(" ".join(json.load(open(".baseline/project.json"))["dialects"]))'); do
    echo "CREATE TABLE selftest_upgrade (id BIGINT NOT NULL PRIMARY KEY);" >"db/migration/${d}/V209901010000__selftest_create_upgrade.sql"
  done
  ./scripts/verify.sh upgrade >/dev/null && pass "从 v0.1.0 升级通过"
  echo "CREATE TABLE broken (" >"db/migration/postgresql/V209901010000__selftest_create_upgrade.sql"
  expect_fail "迁移脚本在升级时出错" ./scripts/verify.sh upgrade
  git tag -d v0.1.0 >/dev/null
  git reset -q --hard && git clean -qfd -e node_modules
}

source_tests() {
  echo "▶ 基线来源与 copier update"
  local start src dest src_url
  start="$(pwd)"
  cd "${BASELINE_DIR}"
  python3 - <<'PY'
import sys
from pathlib import Path
sys.path.insert(0, str(Path("template/scripts").resolve()))
from lib.baseline_source import classify_source, sanitize_git_url, source_problem
from lib.proc import maven_argv, prepare_command
from upgrade_path import versions_in_use
assert classify_source(r"C:\Users\a\repo") == "local"
assert classify_source("../baseline") == "local"
assert classify_source("/tmp/baseline-not-here") == "local"
assert classify_source("baseline") == "local"
assert classify_source("https://github.com/org/repo.git") == "git"
assert classify_source("git@github.com:org/repo.git") == "git"
assert classify_source("git+file:///tmp/repo") == "git"
cleaned = sanitize_git_url("https://x-access-token:SECRET@github.com/org/repo.git")
assert cleaned == "https://github.com/org/repo.git"
assert "SECRET" not in cleaned
assert source_problem("/Users/me/baseline")
assert source_problem("https://github.com/org/repo.git") is None
assert prepare_command(["pnpm", "-s", "test"], windows=True)[:2] == ["cmd", "/c"]
assert maven_argv(["test"], windows=False)[0] == "./mvnw"
assert "mvnw.cmd" in maven_argv(["spotless:check", "test"], windows=True)
text = "## 在用版本\n\n- v1.2.0（现场）\n- v1.2.0（重复）\n\n## 部署记录\n- v9.9.9\n"
assert versions_in_use(text) == ["v1.2.0"]
print("  ✓ 来源判断与 Windows 命令拼装")
PY

  src="$(mktemp -d "${TMPDIR:-/tmp}/baseline-src.XXXXXX")"
  dest="$(mktemp -d "${TMPDIR:-/tmp}/baseline-dst.XXXXXX")"
  git clone --quiet "${BASELINE_DIR}" "${src}/repo"
  git -C "${src}/repo" config user.name selftest
  git -C "${src}/repo" config user.email selftest@example.com
  git -C "${src}/repo" tag -a v0.1.0 -m v0.1.0
  printf '\n# selftest-marker-v0.2.0\n' >>"${src}/repo/template/scripts/verify.sh"
  git -C "${src}/repo" add template/scripts/verify.sh
  git -C "${src}/repo" commit -q -m "chore: 基线来源自测标记"
  git -C "${src}/repo" tag -a v0.2.0 -m v0.2.0
  src_url="git+file://${src}/repo"
  python3 "${BASELINE_DIR}/bin/new_project.py" "${dest}/proj" v0.1.0 --source "${src_url}" --defaults \
    -d project_code=park -d project_name=智慧园区 -d tech_lead=selftest
  python3 - "${dest}/proj/.baseline/copier-answers.yml" "${src_url}" <<'PY'
import sys
from pathlib import Path
sys.path.insert(0, str(Path("template/scripts").resolve()))
from lib.baseline_source import classify_source, read_src_path
recorded = read_src_path(Path(sys.argv[1]).read_text(encoding="utf-8"))
if not recorded or classify_source(recorded) != "git":
    raise SystemExit(f"记录的来源不是 Git 地址：{recorded}")
if recorded.startswith(("/", ".")) or (len(recorded) > 2 and recorded[1] == ":"):
    raise SystemExit(f"记录的来源仍是本机路径：{recorded}")
print("  ✓ 创建项目记录的是 Git 地址")
PY
  git -C "${dest}/proj" config user.name selftest
  git -C "${dest}/proj" config user.email selftest@example.com
  git -C "${dest}/proj" add -A
  git -C "${dest}/proj" commit -q -m "chore(baseline): 初始化项目" -m "Refs: BASELINE-v0.1.0"
  printf '\n项目自有内容\n' >>"${dest}/proj/README.md"
  git -C "${dest}/proj" add README.md
  git -C "${dest}/proj" commit -q -m "docs: 项目自有说明" -m "Refs: REQ-20261021-baseline-source"
  set +e
  out="$(python3 "${dest}/proj/scripts/sync_baseline.py" v0.2.0 --source "file:///tmp/baseline-does-not-exist-xyz" 2>&1)"
  status=$?
  set -e
  if [ "${status}" -eq 0 ]; then
    rm -rf "${src}" "${dest}"
    cd "${start}"
    die "不可达的基线来源应当失败"
  fi
  case "${out}" in
    *无法访问*) ;;
    *)
      printf '%s\n' "${out}" >&2
      rm -rf "${src}" "${dest}"
      cd "${start}"
      die "不可达的基线来源没有说明原因"
      ;;
  esac
  pass "不可达的基线来源会失败并说明原因"
  python3 - "${dest}/proj/.baseline/copier-answers.yml" <<'PY'
from pathlib import Path
import sys
path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
lines = []
for line in text.splitlines(keepends=True):
    if line.startswith("_src_path:"):
        nl = "\r\n" if line.endswith("\r\n") else "\n"
        lines.append(f"_src_path: /tmp/old-local-baseline{nl}")
    else:
        lines.append(line)
path.write_bytes("".join(lines).encode("utf-8"))
PY
  git -C "${dest}/proj" add -- .baseline/copier-answers.yml
  BASELINE_SYNC=1 git -C "${dest}/proj" commit -q -m "chore(baseline): 写入旧的本机来源" -m "Refs: BASELINE-v0.1.0"
  set +e
  out="$(python3 "${dest}/proj/scripts/sync_baseline.py" v0.2.0 2>&1)"
  status=$?
  set -e
  if [ "${status}" -eq 0 ]; then
    rm -rf "${src}" "${dest}"
    cd "${start}"
    die "本机路径来源应当被拒绝"
  fi
  case "${out}" in
    *本机路径*) ;;
    *)
      printf '%s\n' "${out}" >&2
      rm -rf "${src}" "${dest}"
      cd "${start}"
      die "本机路径来源没有说明原因"
      ;;
  esac
  pass "本机路径来源会被拒绝"
  python3 "${dest}/proj/scripts/sync_baseline.py" v0.2.0 --source "${src_url}"
  grep -q "selftest-marker-v0.2.0" "${dest}/proj/scripts/verify.sh"
  grep -q "项目自有内容" "${dest}/proj/README.md"
  python3 - "${dest}/proj/.baseline/copier-answers.yml" <<'PY'
import sys
from pathlib import Path
sys.path.insert(0, str(Path("template/scripts").resolve()))
from lib.baseline_source import classify_source, read_src_path
recorded = read_src_path(Path(sys.argv[1]).read_text(encoding="utf-8"))
if classify_source(recorded or "") != "git":
    raise SystemExit(f"同步后来源不是 Git 地址：{recorded}")
PY
  pass "copier update 从 v0.1.0 升到 v0.2.0，项目自有文件仍在"
  rm -rf "${src}" "${dest}"
  cd "${start}"
}

run_default() {
  source_tests
  generate default
  verify_full
  gate_tests
  scaffold_tests
  upgrade_tests
}

run_minimal() {
  generate minimal -d include_example=false -d security_level=classified
  verify_full
}

run_xinchuang() {
  generate xinchuang -d enable_xinchuang=true -d xinchuang_db=dm -d enable_screen=true -d security_level=restricted
  verify_full
  gate_tests
}

mkdir -p "${WORK}"
case "${TARGET}" in
  default) run_default ;;
  minimal) run_minimal ;;
  xinchuang) run_xinchuang ;;
  source) source_tests ;;
  all) run_default; run_minimal; run_xinchuang ;;
  *) echo "用法：$0 [all|default|minimal|xinchuang|source]" >&2; exit 2 ;;
esac
echo
echo "自测通过：${TARGET}"
