#!/usr/bin/env python3
"""把 db-schema.sh 导出的列和索引信息格式化为 Markdown。"""
from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path


def read_tsv(path: str) -> list[list[str]]:
    return [line.split("\t") for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def cell(value: str) -> str:
    return value.replace("|", "\\|") or " "


def main(columns_file: str, indexes_file: str) -> None:
    tables: dict[str, dict] = {}
    for table, comment, column, type_, nullable, default, col_comment in read_tsv(columns_file):
        info = tables.setdefault(table, {"comment": comment, "columns": []})
        info["columns"].append((column, type_, "是" if nullable == "YES" else "否", default, col_comment))
    indexes: dict[str, list[str]] = defaultdict(list)
    for table, definition in read_tsv(indexes_file):
        indexes[table].append(definition)

    out = [
        "<!-- 由 scripts/db-schema.sh 生成，禁止手改；改表后重新执行该脚本 -->",
        "# 表结构摘要（PostgreSQL 方言）",
        "",
    ]
    if not tables:
        out.append("当前没有业务表。")
    for table, info in tables.items():
        out += [f"## {table}" + (f"：{info['comment']}" if info["comment"] else ""), ""]
        out += ["| 字段 | 类型 | 可空 | 默认值 | 说明 |", "| :--- | :--- | :--- | :--- | :--- |"]
        out += [f"| {' | '.join(cell(v) for v in col)} |" for col in info["columns"]]
        if indexes.get(table):
            out += ["", "索引："]
            out += [f"- `{d}`" for d in indexes[table]]
        out.append("")
    print("\n".join(out).rstrip())


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
