#!/usr/bin/env python3
"""在临时 PostgreSQL 中执行全部迁移脚本，生成 docs/context/db-schema.md。"""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

from lib.postgres import Postgres
from lib.proc import configure_stdio


ROOT = Path(__file__).resolve().parents[1]
COLUMNS_SQL = """
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
ORDER BY c.table_name, c.ordinal_position
"""


def main(argv: list[str] | None = None) -> int:
    configure_stdio()
    del argv
    migration = ROOT / "db" / "migration" / "postgresql"
    with Postgres() as pg:
        for path in sorted(migration.glob("V*.sql")):
            pg.execute_file(path)
        with tempfile.TemporaryDirectory() as tmp:
            columns = Path(tmp) / "columns.tsv"
            indexes = Path(tmp) / "indexes.tsv"
            columns.write_text(pg.query(COLUMNS_SQL), encoding="utf-8")
            indexes.write_text(
                pg.query("SELECT tablename, indexdef FROM pg_indexes WHERE schemaname = 'public' ORDER BY tablename, indexname"),
                encoding="utf-8",
            )
            rendered = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "lib" / "schema_md.py"), str(columns), str(indexes)],
                check=True,
                capture_output=True,
                text=True,
            )
    (ROOT / "docs" / "context" / "db-schema.md").write_text(rendered.stdout, encoding="utf-8")
    print("已更新 docs/context/db-schema.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
