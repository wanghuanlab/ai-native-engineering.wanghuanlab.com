#!/usr/bin/env bash
# 薄封装。逻辑在 setup.py。兼容 macOS Bash 3.2 与 set -u。
set -eu
HERE="$(cd "$(dirname "$0")" && pwd)"
exec "${HERE}/_py.sh" "${HERE}/setup.py" "$@"
