#!/usr/bin/env bash
# 在临时 PostgreSQL 中执行全部迁移脚本，生成表结构摘要 docs/context/db-schema.md。
# AI 改表前读这份摘要，避免为了了解表结构去连真实数据库。
set -euo pipefail
cd "$(dirname "$0")/.."
source scripts/lib/pg.sh

trap pg_stop EXIT
pg_start
for f in $(ls db/migration/postgresql/V*.sql 2>/dev/null | sort); do
  pg_exec <"${f}"
done

TMP="$(mktemp -d)"
pg_query "
SELECT c.table_name,
       coalesce(obj_description(format('%I', c.table_name)::regclass, 'pg_class'), ''),
       c.column_name,
       CASE WHEN c.character_maximum_length IS NOT NULL THEN c.data_type || '(' || c.character_maximum_length || ')'
            WHEN c.data_type = 'numeric' AND c.numeric_precision IS NOT NULL THEN 'numeric(' || c.numeric_precision || ',' || c.numeric_scale || ')'
            ELSE c.data_type END,
       c.is_nullable,
       coalesce(c.column_default, ''),
       coalesce(col_description(format('%I', c.table_name)::regclass, c.ordinal_position), '')
FROM information_schema.columns c
JOIN information_schema.tables t ON t.table_name = c.table_name AND t.table_schema = c.table_schema
WHERE c.table_schema = 'public' AND t.table_type = 'BASE TABLE'
ORDER BY c.table_name, c.ordinal_position" >"${TMP}/columns.tsv"
pg_query "SELECT tablename, indexdef FROM pg_indexes WHERE schemaname = 'public' ORDER BY tablename, indexname" >"${TMP}/indexes.tsv"

python3 scripts/lib/schema_md.py "${TMP}/columns.tsv" "${TMP}/indexes.tsv" >docs/context/db-schema.md
rm -rf "${TMP}"
echo "已更新 docs/context/db-schema.md"
