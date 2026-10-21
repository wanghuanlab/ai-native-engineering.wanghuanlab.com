#!/usr/bin/env bash
# 找到 Python 3 并执行给定脚本。兼容 macOS Bash 3.2 与 set -u。
set -eu
if [ "$#" -lt 1 ]; then
  echo "用法：_py.sh <python 脚本> [参数...]" >&2
  exit 2
fi
target="$1"
shift
if command -v python3 >/dev/null 2>&1; then
  exec python3 "${target}" "$@"
elif command -v python >/dev/null 2>&1; then
  exec python "${target}" "$@"
elif command -v py >/dev/null 2>&1; then
  exec py -3 "${target}" "$@"
fi
echo "需要 Python 3.10 或更高版本（python3、python 或 py -3）" >&2
exit 1
