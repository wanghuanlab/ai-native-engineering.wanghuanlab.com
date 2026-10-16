#!/usr/bin/env bash
# 用法：./scripts/new-change.sh <短名> --intake-only | --level M|L
exec python3 "$(dirname "$0")/lib/new_change.py" "$@"
