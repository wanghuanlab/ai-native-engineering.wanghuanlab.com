#!/bin/sh
# 临时 PostgreSQL 已改为 scripts/lib/postgres.py。
# db-schema 与 upgrade-path 通过 Python 调用它。保留本文件是为了说明旧的 shell 入口不再实现第二套逻辑。
echo "请改用 scripts/db-schema 或 scripts/upgrade-path（.sh / .cmd / .ps1）。" >&2
exit 1
