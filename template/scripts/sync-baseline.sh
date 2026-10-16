#!/usr/bin/env bash
# 把基线升级到指定版本：./scripts/sync-baseline.sh v0.2.0
# 只更新基线托管文件；项目自有文件（业务代码、文档、契约、迁移脚本）不会被覆盖。由技术负责人执行。
set -euo pipefail
cd "$(dirname "$0")/.."

VERSION="${1:?用法：$0 <基线版本，如 v0.2.0>}"

if [ -n "$(git status --porcelain)" ]; then
  echo "工作区有未提交的改动，请先提交或暂存" >&2
  exit 1
fi

if command -v copier >/dev/null 2>&1; then
  COPIER=(copier)
elif command -v uvx >/dev/null 2>&1; then
  COPIER=(uvx copier)
elif command -v pipx >/dev/null 2>&1; then
  COPIER=(pipx run copier)
else
  echo "需要 copier（pip install copier，或安装 uv 后使用 uvx）" >&2
  exit 1
fi

"${COPIER[@]}" update --trust --defaults --vcs-ref "${VERSION}" --answers-file .baseline/copier-answers.yml
python3 scripts/build-ai-config.py

echo
echo "已同步到基线 ${VERSION}。请检查改动（git diff），处理冲突标记后执行："
echo "  ./scripts/verify.sh full"
echo "  git add -A && BASELINE_SYNC=1 git commit -m \"chore(baseline): 同步基线 ${VERSION}\" -m \"Refs: BASELINE-${VERSION}\""
