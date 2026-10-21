---
id: 00-core
title: 核心工作规则
scope: always
summary: 任务分级、变更包、修改范围、红线与必须停下来的情形
---
## 工作方式

1. 先判定任务级别 S / M / L（标准见 `.ai/rules/10-workflow.md`），拿不准时取更高的级别。
2. M、L 级任务必须先有变更包 `docs/changes/<REQ>/`。没有时先执行 Skill `req-intake`，不得直接写代码。
3. 编码前必须读：变更包的 `tasks.md`、涉及能力的 `docs/specs/<能力>/spec.md`、`docs/context/pitfalls.md`。
4. 只修改 `tasks.md`「修改范围」中列出的文件。
5. 每完成一项任务：运行该任务写明的验证命令，通过后勾选并写备注。
6. 一个会话只做一个环节。结束会话前，把进度和注意事项写进 `tasks.md`。
7. 项目脚本在 macOS / Linux 用 `scripts/<名>.sh`，在 Windows 的 PowerShell 或 cmd 用 `scripts\<名>.cmd`（`.ps1` 同样可用）。文档里的 `./scripts/verify.sh` 在 Windows 上改成 `scripts\verify.cmd`。后端 Maven 包装脚本同理：`./mvnw` 对应 `mvnw.cmd`。

## 红线

- 已合并到 main 的迁移脚本只读，表结构只能通过新增迁移脚本修改。
- 不手改生成的代码（`frontend/packages/api-client/src/generated/`、`target/generated-sources/`）和 `.baseline/managed-files.txt` 列出的基线托管文件。
- 不删除测试、不跳过测试、不降低断言来让校验通过。
- 不填写 PM 确认区、TL 审批区和部署回执，不推送 main 分支。
- 不提交密钥、生产配置和真实个人信息。

## 必须停下来请人确认

遇到以下情形时，输出 `[需要人工决策]`，写明原因和可选方案，然后等待：

1. 没有变更包，或 L 级变更包的 `design.md` 未经 TL 审批。
2. 需要修改「修改范围」以外的文件。
3. 需要删除或修改已有字段、删除表、清空数据、修改已合并的迁移脚本。
4. 需要对已发布接口做破坏性修改。
5. 需要引入新的第三方依赖。
6. 已有测试失败，且原因是业务规则发生了变化。
7. 同一问题连续修复 3 次仍失败。
8. 需求描述与当前规格冲突。
