---
id: 30-database
title: 数据库演进规范
scope: glob
globs: db/**, backend/**/domain/**/*.java
summary: 新增或修改表结构、实体、迁移脚本前读取
---
# 数据库演进规范

## 动手前

1. 先读 `docs/context/db-schema.md`（由 `./scripts/db-schema.sh` 从真实数据库生成），不要猜表名和字段名。
2. 再读修改过目标表的全部历史迁移脚本。

## 迁移脚本

- 位置：`db/migration/<方言>/`，每个启用的方言（见 `.baseline/project.json` 的 `dialects`）都要有同名脚本。
- 文件名：`V<年月日时分>__<模块>_<英文描述>.sql`，例如 `V202610151400__visitor_add_approval.sql`。
- 脚本开头注释写明：需求编号、回退方式。
- 已合并到 main 的脚本只读（门禁会检查）；每个脚本只能依赖本模块之前的脚本。

## 表设计

- 标识符小写加下划线；表名 `<模块>_<实体>`；不用数据库保留字。
- 主键 `id BIGINT`，由应用生成；在接口契约中以字符串传输。
- 标准字段（与 `BaseEntity` 对应）：`id`、`created_at`、`created_by`、`updated_at`、`updated_by`、`version`、`deleted`。
- 时间类型用 `TIMESTAMP WITH TIME ZONE`，统一存 UTC；金额用 `NUMERIC(p, s)`。
- 公共表只用可移植类型；`JSONB`、PostGIS、pgvector 等专有特性只能在明确不需要信创的模块中使用，并在 `design.md` 中说明。
- 索引命名：主键 `pk_<表>`，唯一 `uk_<表>_<字段>`，普通 `idx_<表>_<字段>`。
- 业务上唯一的列（含组合）建唯一索引。禁止外键、级联和存储过程。
- 业务布尔列用 `is_<含义>`，Java 属性去掉 `is`。标准字段 `deleted` 不加 `is_`。
- 小数用 `NUMERIC`，不用 `float` / `double`。变长字符串不超过 5000，更长用 `TEXT`。
- 查询写明列名，不用 `SELECT *`。`JOIN` 不超过三张表，关联列类型一致。空值判断写 `IS NULL`。
- 分页在总数为 0 时直接返回空页。禁止物理删除，删除走 `deleted`。

## 变更安全

| 操作 | 要求 |
| :--- | :--- |
| 新增表、可空字段、带默认值的字段 | M 级即可 |
| 新增非空字段 | 用默认值让存量数据落到兼容值，新代码显式写入新值；不要用数据库默认值表达业务状态 |
| 修改类型、重命名、删除字段或表 | L 级；按"扩展 → 迁移 → 收缩"分多个版本完成 |
| 回填存量数据 | L 级；大表分批执行，在 `design.md` 写明数据量与预计时长 |
| 大表加索引 | 用不锁表的方式（PostgreSQL 用 `CREATE INDEX CONCURRENTLY`），单独成一个脚本 |

## 实体同步

- 改了表就同步改实体。实体与表不一致时应用启动失败（`ddl-auto=validate`），`ApplicationIT` 会发现。
- 改完运行 `./scripts/verify.sh db` 和 `./scripts/db-schema.sh`。
