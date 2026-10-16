---
name: db-migration
description: 编写数据库迁移脚本。任务需要新增表、加字段、改索引或处理存量数据时使用：按规范为每个启用的数据库方言编写增量迁移脚本，同步实体，并在真实数据库上验证。
---
# 数据库迁移

## 必读文件

1. `.ai/rules/30-database.md`
2. `docs/context/db-schema.md`
3. 修改过目标表的全部历史迁移脚本
4. `docs/changes/<REQ>/design.md` 或 `tasks.md` 中的数据库部分
5. `.baseline/project.json` 中的 `dialects`

## 步骤

1. 取当前时间作为版本号：`V<年月日时分>__<模块>_<英文描述>.sql`。
2. 在 `db/migration/postgresql/` 写脚本，开头注释写需求编号和回退方式。
3. 按变更类型套用 `.ai/rules/30-database.md` 的"变更安全"规则。新增非空字段时：
   - 用默认值让存量数据直接落到兼容值，例如 `ADD COLUMN approval_required BOOLEAN NOT NULL DEFAULT FALSE`。
   - 新代码创建数据时显式写入新值，不依赖数据库默认值。
   - 不要先加默认值再全表 `UPDATE`。
4. 为 `dialects` 中的其他每个方言写同名脚本。
5. 同步修改实体（字段、类型、长度、是否可空）。
6. 运行 `./scripts/verify.sh db`（命名与方言一致性检查）和 `./scripts/verify.sh full`（在真实数据库上执行迁移并校验实体）。
7. 运行 `./scripts/db-schema.sh` 更新 `docs/context/db-schema.md`。

## 完成标准

- 迁移在测试容器中执行成功，`ApplicationIT` 通过。
- 每个方言目录下都有同名脚本。
- `db-schema.md` 已更新。

## 必须停下来

- 需要删除、重命名字段或表，修改字段类型，或修改已合并的脚本。
- 回填数据量超过 100 万行，或无法估算执行时长。
