#!/usr/bin/env bash
# 用法：./scripts/new-module.sh <模块名> [--title 中文名]
exec python3 "$(dirname "$0")/lib/new_module.py" "$@"
