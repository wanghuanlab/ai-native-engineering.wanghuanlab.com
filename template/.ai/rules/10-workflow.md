---
id: 10-workflow
title: 研发流程与变更包
scope: requested
summary: 判定任务级别、创建或推进变更包、处理需求变更时读取
---
# 研发流程与变更包

## 任务分级（满足任一条件即升级）

| 级别 | 判定条件 | 需要的产物 |
| :--- | :--- | :--- |
| S 小改 | 不改表、不改接口、不改业务规则，单模块内 | 只需规范的提交说明 |
| M 常规 | 单模块内新增功能或调整业务规则；只新增表或字段 | `proposal.md`、`spec-delta.md`、`tasks.md`、`acceptance.md` |
| L 重大 | 修改或删除已有字段、处理存量数据；改已发布接口；跨模块；涉及权限、安全、个人信息 | M 级全部产物 + `design.md`，TL 审批后才能编码 |

缺陷修复按影响面套用同一分级，并且必须先写能复现缺陷的测试。

## 流程与对应 Skill

| 环节 | Skill | 产出 | 确认人 |
| :--- | :--- | :--- | :--- |
| 需求入库与澄清 | `req-intake` | `docs/requirements/<REQ>/intake.md` | 工程师 |
| 规格 | `spec-change` | `proposal.md`、`spec-delta.md` | PM 确认验收标准 |
| 设计与计划 | `change-design` | `design.md`（L 级）、`tasks.md` | TL（L 级） |
| 数据库迁移 | `db-migration` | `db/migration/<方言>/V*.sql` | — |
| 实现 | `implement` | 代码 | — |
| 测试与验收 | `test-accept` | 测试、`acceptance.md` | 工程师 |
| 合并前自审 | `self-review` | 自审报告 | TL 合并 |

## 变更包

- 用 `./scripts/new-change.sh <英文短名> --level M|L` 创建，目录为 `docs/changes/REQ-<日期>-<短名>/`。
- `spec-delta.md` 只写增量（新增、修改、删除的业务规则 `BR-*` 与验收标准 `AC-*`），不复制整份规格。
- 发布后执行归档：把增量合并进 `docs/specs/<能力>/spec.md`，把变更包移到 `docs/changes/archive/`。

## 需求变更

1. 需求变更是新的变更包，在 `proposal.md` 中写明变更自哪个能力、哪条规则。
2. 先读该能力的当前规格和相关的已归档变更包，再做影响分析。
3. 与已有测试语义冲突的地方要在 `design.md` 中逐条列出，经 TL 确认后才能改这些测试。
