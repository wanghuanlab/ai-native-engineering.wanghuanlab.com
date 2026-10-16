#!/usr/bin/env bash
# 基于 ai-native-engineering 基线创建新项目
# 用法：bin/new-project.sh <目标目录> [基线版本标签，默认当前版本] [其他 copier 参数...]
set -euo pipefail

if [ $# -lt 1 ]; then
  echo "用法：$0 <目标目录> [基线版本标签] [其他 copier 参数...]" >&2
  exit 1
fi

BASELINE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
DEST="$1"; shift
VCS_REF_ARGS=()
if [ $# -gt 0 ] && [[ "$1" != -* ]]; then
  VCS_REF_ARGS=(--vcs-ref "$1"); shift
fi

if command -v copier >/dev/null 2>&1; then
  COPIER=(copier)
elif command -v uvx >/dev/null 2>&1; then
  COPIER=(uvx copier)
elif command -v pipx >/dev/null 2>&1; then
  COPIER=(pipx run copier)
else
  echo "未找到 copier。请先安装：pip install copier 或 brew install uv" >&2
  exit 1
fi

exec "${COPIER[@]}" copy --trust "${VCS_REF_ARGS[@]}" "$@" "$BASELINE_DIR" "$DEST"
