---
name: change-design
description: 影响分析与实施计划。规格经产品经理确认后、写代码之前使用：分析对表、接口、模块、页面、已有测试的影响，L 级编写 design.md，所有级别编写带修改范围和验证命令的 tasks.md。
---
# 影响分析与计划

## 适用条件

- `proposal.md` 的 PM 确认区已由工程师填写。

## 必读文件

1. `docs/changes/<REQ>/proposal.md`、`spec-delta.md`
2. `docs/context/architecture.md`、`docs/context/db-schema.md`、`docs/context/pitfalls.md`
3. 涉及模块的代码、契约 `contracts/openapi/<模块>.yaml`、已有测试

## 步骤

1. 影响分析：搜索涉及的表名、实体、接口路径、页面，列出：
   - 要改的表、实体、迁移脚本
   - 要改的接口（标出是否兼容）
   - 要改的模块和页面
   - 会受影响的已有测试，以及其中哪些断言会因业务规则变化而需要修改
   - 存量数据如何处理
2. L 级：按 `docs/_templates/design.md` 写 `design.md`（示范见 `docs/_templates/examples/REQ-20261015-visitor-approval/design.md`），包括方案取舍、数据库变更与存量兼容、接口变更、风险与回退。**不要填写 TL 审批区。**
3. 写 `tasks.md`：
   - 「修改范围」：精确到目录或文件模式，越小越好。
   - 任务按"迁移脚本 → 契约 → 后端 → 前端 → 测试"排序，每项任务写明验证命令。
   - 每项任务的工作量控制在一个会话内能完成。
4. 需要多人或多个 Agent 并行时，为每个并行任务写互不重叠的修改范围，并把契约和迁移脚本放在最前面单独完成。

## 输出

- `docs/changes/<REQ>/design.md`（L 级）
- `docs/changes/<REQ>/tasks.md`

## 完成标准

- M 级：`tasks.md` 完成即可开始实现。
- L 级：TL 在 `design.md` 审批区签署后才能开始实现。
- 下一步：涉及表结构时执行 `db-migration`，否则执行 `implement`。

## 必须停下来

- 发现必须删除或修改已有字段、修改已发布接口，而任务级别是 M（需要升级为 L）。
- 影响范围超出 `proposal.md` 中声明的能力。
