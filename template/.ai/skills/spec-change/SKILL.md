---
name: spec-change
description: 起草变更提案与规格增量。需求澄清完成后使用：编写 proposal.md 和 spec-delta.md（业务规则 BR 与验收标准 AC），并导出给产品经理确认的验收清单。
---
# 起草规格

## 适用条件

- `intake.md` 中的澄清问题已全部答复，任务级别为 M 或 L。

## 必读文件

1. `docs/requirements/<REQ>/intake.md`
2. 涉及能力的 `docs/specs/<能力>/spec.md`（新能力则没有）
3. `docs/_templates/proposal.md`、`docs/_templates/spec-delta.md`，以及示范 `docs/_templates/examples/REQ-20261015-visitor-approval/` 中的同名文件

## 步骤

1. 如果还没有变更包，运行 `./scripts/new-change.sh <短名> --level M|L`。
2. 填写 `proposal.md`：背景、目标、变更类型、任务级别与理由、涉及能力、对用户可见的影响。**不要填写 PM 确认区。**
3. 填写 `spec-delta.md`，只写增量：
   - 新增、修改、删除了哪些业务规则，编号 `BR-<能力>-<两位序号>`，接着该能力已有的最大编号继续。
   - 新增、修改、删除了哪些验收标准，编号 `AC-<能力>-<两位序号>`。
   - 每条验收标准用"前提 / 操作 / 结果"三段式写，结果必须可以被测试判断。
4. 检查：每条业务规则至少被一条验收标准覆盖；涉及存量数据的规则，有专门的验收标准。
5. 在 `proposal.md` 末尾生成"给产品经理的确认清单"：用业务语言列出所有业务规则和验收标准，不出现技术词汇。

## 输出

- `docs/changes/<REQ>/proposal.md`
- `docs/changes/<REQ>/spec-delta.md`

## 完成标准

- 确认清单已交给工程师，由工程师发给产品经理。
- 工程师在 PM 确认区登记了确认记录（AI 不得代填）。
- 下一步：执行 Skill `change-design`。

## 必须停下来

- 验收标准无法写成可判断的结果（说明需求还不清楚，退回 `req-intake`）。
- 新规则与现有规则冲突。
