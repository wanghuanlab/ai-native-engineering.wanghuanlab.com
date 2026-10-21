---
name: implement
description: 按任务清单实现功能。tasks.md 已就绪（L 级已获 TL 审批）后使用：按"契约 → 后端 → 前端"的顺序逐项实现，每项完成后运行验证命令并更新 tasks.md。
---
# 实现

## 必读文件

1. `docs/changes/<REQ>/tasks.md`（从第一个未勾选的任务开始）
2. `docs/changes/<REQ>/spec-delta.md`、`design.md`（L 级）
3. 当前任务涉及目录的规则：`.ai/rules/20-backend-java.md`、`25-alibaba-java.md`、`40-api-contract.md`、`50-frontend-vue.md`
4. `docs/context/pitfalls.md`

## 步骤

每项任务按以下顺序执行：

1. 确认要改的文件都在「修改范围」内。
2. 契约任务：修改 `contracts/openapi/<模块>.yaml`，运行 `cd frontend && pnpm gen:api`。
3. 后端任务：
   - 新模块先运行 `./scripts/new-module.sh <模块名>`。
   - 按 `domain → service → web` 的顺序写；Controller 实现生成的 `*Api` 接口。
   - 规则实现处用注释标出业务规则编号，例如 `/** BR-visitor-04：…… */`。
4. 前端任务：页面放在 `apps/admin/src/views/<模块>/`，只使用生成的接口函数。
5. 运行任务中写明的验证命令；失败时阅读报错修复，同一问题最多尝试 3 次。
6. 通过后勾选任务，在备注中写下后续会话需要知道的事情。

## 完成标准

- 所有任务已勾选，`./scripts/verify.sh quick` 通过。
- 下一步：执行 Skill `test-accept`。

## 必须停下来

- 需要修改「修改范围」以外的文件。
- 需要新增第三方依赖。
- 实现过程中发现规格有遗漏或矛盾。
